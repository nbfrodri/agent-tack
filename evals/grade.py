#!/usr/bin/env python3
"""Measures what one eval run did: inspects its repo and transcript and writes metrics.json.

Usage: evals/grade.py <run dir>...     (e.g. $EVALS_OUT/bug-fix/harness-1)
Prints the metrics and writes <run dir>/metrics.json. evals/report.py aggregates them.
Ordering uses explicit Claude writes and Codex file_change events; opaque shell writes remain unknown.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w./-]+\))?!?: \S")
AI_ATTRIBUTION = re.compile(r"co-authored-by:.*(claude|anthropic|openai|codex|copilot|gemini|cursor)|generated with|🤖", re.I)
SEEDED_COMMITS = {"new-project": 0, "codex-new-project": 0, "bug-fix": 1, "release": 5, "vague-requirement": 1, "conventions": 1, "attachments": 1}
HIDDEN = Path(__file__).resolve().parent / "hidden"
# The project's own environment (uv) runs the hidden tests, so its dependencies are installed.
HIDDEN_RUNNER = ["uv", "run", "--quiet", "python"]


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def events(path):
    out = []
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
                out.append(event if isinstance(event, dict) else {"type": "unparsed"})
            except json.JSONDecodeError:
                out.append({"type": "unparsed"})
    return out


def tool_uses(evs):
    for e in evs:
        if e.get("type") == "assistant":
            for block in e.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    yield block.get("name"), block.get("input", {})


def observations(evs):
    """Adapt explicit provider events; arbitrary shell mutations remain opaque."""
    out = []
    pending = {}
    pending_writes = {}
    for batch, event in enumerate(evs):
        if event.get("type") == "unparsed":
            out.append({"opaque": True})
        if event.get("type") in ("assistant", "user"):
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    name, inputs = block.get("name"), block.get("input", {})
                    if name in ("Write", "Edit", "MultiEdit") and inputs.get("file_path") and not (
                            name == "Write" and not inputs.get("content", "").strip()):
                        write = {"path": inputs["file_path"], "opaque": True}
                        out.append(write)
                        if block.get("id") is not None:
                            pending_writes[block["id"]] = write
                    if name == "Bash":
                        command = inputs.get("command", "")
                        pending[block.get("id")] = command
                        out.append({"command": command})
                elif block.get("type") == "tool_result":
                    write = pending_writes.pop(block.get("tool_use_id"), None)
                    if write is not None:
                        if block.get("is_error"):
                            write.pop("path", None)
                        else:
                            write.pop("opaque", None)
                    command = pending.get(block.get("tool_use_id"))
                    if command:
                        out.append({"command": command, "failed": bool(block.get("is_error")),
                                    "output": str(block.get("content", ""))})
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "file_change" and item.get("status", "completed") == "completed":
                out.extend({"path": change["path"], "batch": batch} for change in item.get("changes", []) if "path" in change)
            if item.get("type") == "command_execution":
                observation = {"command": item.get("command", ""), "output": item.get("aggregated_output", "")}
                if item.get("exit_code") is not None:
                    observation["failed"] = item["exit_code"] != 0
                out.append(observation)
    return out


CRITERIA = re.compile(r"\bR1\b|acceptance criteri|criterios de aceptaci", re.I)


SHELL_WRITE = re.compile(r"(?<![<>=])>(?![=])|\btee\b|\bsed\s+-i|\bapply_patch\b")


def criteria_before_code(evs):
    """True when numbered or explicit acceptance criteria appear before the first code change.

    Criteria count in the assistant's text or in a document it writes (a plan, an issue draft);
    a write to any other file, or a shell command that writes, is code.
    """
    for event in evs:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "text" and CRITERIA.search(block.get("text", "")):
                return True
            if block.get("type") != "tool_use":
                continue
            name, inputs = block.get("name"), block.get("input", {})
            if name in ("Write", "Edit", "MultiEdit"):
                path = inputs.get("file_path", "")
                written = inputs.get("content") or inputs.get("new_string") or ""
                if path.endswith(".md") and CRITERIA.search(written):
                    return True
                if not path.endswith(".md"):
                    return False
            if name == "Bash" and SHELL_WRITE.search(inputs.get("command", "")):
                return False
    return None


def written_paths(evs):
    return [entry["path"] for entry in observations(evs) if "path" in entry]


def ordering_metrics(entries):
    test_at = next((i for i, e in enumerate(entries) if re.search(r"tests?/|test_", e.get("path", ""))), None)
    impl_at = next((i for i, e in enumerate(entries) if e.get("path", "").endswith(".py")
                    and not re.search(r"tests?/|test_", e["path"])), None)
    # Shell commands can change files without emitting file_change events.
    opaque = any(e.get("opaque") or re.search(r"(?<![<>=])>(?![=])|\b(tee|sed|perl|python3?|apply_patch|cp|mv|rm)\b", e.get("command", ""))
                 for e in entries)
    if test_at is not None and impl_at is not None and entries[test_at].get("batch") is not None:
        opaque = opaque or entries[test_at]["batch"] == entries[impl_at].get("batch")
    order = test_at < impl_at if test_at is not None and impl_at is not None and not opaque else None
    executions = [(i, e) for i, e in enumerate(entries)
                  if "failed" in e and re.search(r"\b(pytest|unittest)\b", e.get("command", ""))]
    red = next((i for i, e in executions if e["failed"] and re.search(r"failed|FAIL|AssertionError", e.get("output", ""))
                and test_at is not None and impl_at is not None and test_at < i < impl_at), None)
    green = red is not None and any(i > impl_at and not e["failed"] and re.search(r"passed|\bOK\b", e.get("output", ""))
                                    for i, e in executions)
    verified = True if green and not opaque else False if order is False else None
    return order, verified


def work_branch_tip(repo):
    """The branch tip holding the most work beyond the checked-out commit (lines changed, lockfiles
    aside), or None when no branch holds any. An agent may commit on a branch and switch back to
    main; its work is then on that branch, not in the checkout."""
    def git(*args):
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ""
    head = git("rev-parse", "HEAD")
    best, best_size = None, 0
    for tip in git("for-each-ref", "--sort=-committerdate", "--format=%(objectname)", "refs/heads").splitlines():
        if not head or tip == head:
            continue
        stat = git("diff", "--numstat", f"{head}...{tip}", "--", ".", ":!*.lock", ":!*-lock.json", ":!*-lock.yaml")
        size = sum(int(n) for line in stat.splitlines() for n in line.split("\t")[:2] if n.isdigit())
        if size > best_size:
            best, best_size = tip, size
    return best


def hidden_acceptance(repo, scenario):
    """(passed, total) for the scenario's hidden tests run against the repo, or (None, None)."""
    tests = HIDDEN / scenario.replace("codex-", "") / "test_hidden.py"
    if not tests.exists() or not repo.is_dir():
        return None, None
    tip = work_branch_tip(repo)
    if tip:
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp) / "work"
            subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(checkout), tip],
                           capture_output=True)
            try:
                return hidden_acceptance_at(checkout, tests) if checkout.is_dir() else (None, None)
            finally:
                subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(checkout)],
                               capture_output=True)
    return hidden_acceptance_at(repo, tests)


def hidden_acceptance_at(repo, tests):
    total = len(re.findall(r"^def test_", tests.read_text(), re.M))
    # src/ layouts and flat packages both import, installed or not.
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(repo / "src"), str(repo)]))
    try:
        result = subprocess.run([*HIDDEN_RUNNER, str(HIDDEN / "run.py"), str(tests)], cwd=repo, env=env,
                                capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired):
        return None, total
    # The runner's summary is its last line; the agent's code may print anything before it.
    lines = result.stdout.strip().splitlines()
    passed = re.fullmatch(r"(\d+) passed, \d+ failed", lines[-1]) if lines else None
    return (int(passed.group(1)) if passed else 0), total


def hidden_verdict(passed, total):
    """True when every hidden test passed, False when one failed, None when they could not run."""
    return passed == total if passed is not None and total else None


def provider_metrics(evs, run_dir):
    provider = "codex" if any(e.get("type") in ("thread.started", "turn.completed", "item.completed") for e in evs) else (
        "claude" if any(e.get("type") in ("assistant", "result", "system") for e in evs) else None)
    result = next((e for e in reversed(evs) if e.get("type") == "result"), {})
    usage = result.get("usage", {})
    if provider == "codex":
        usages = [e["usage"] for e in evs if e.get("type") == "turn.completed" and isinstance(e.get("usage"), dict)]
        usage = {key: sum(u[key] for u in usages if key in u) for key in ("input_tokens", "output_tokens")
                 if any(key in u for u in usages)}
    input_tokens = usage.get("input_tokens")
    if provider == "claude" and input_tokens is not None:
        input_tokens += (usage.get("cache_read_input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0)
    duration = result.get("duration_ms")
    duration = round(duration / 1000, 1) if duration is not None else None
    duration_source = "provider" if duration is not None else None
    if duration is None and (run_dir / "run.txt").exists():
        match = re.search(r"seconds=(\d+)", (run_dir / "run.txt").read_text())
        if match:
            duration, duration_source = int(match[1]), "runner_wall_clock"
    cost = result.get("total_cost_usd")
    return {"metrics_version": 2, "provider": provider, "duration_s": duration, "duration_source": duration_source,
            "cost_usd": round(cost, 4) if cost is not None else None, "turns": len(usages) if provider == "codex" and usages else result.get("num_turns"),
            "input_tokens": input_tokens, "output_tokens": usage.get("output_tokens")}


def grade(run_dir: Path):
    scenario = run_dir.parent.name
    condition, _, rep = run_dir.name.rpartition("-")
    repo = run_dir / "repo"
    transcript = run_dir / "transcript.jsonl"
    evs = events(transcript)
    raw = transcript.read_text(errors="replace") if transcript.exists() else ""
    entries = observations(evs)
    bash = " ".join(e["command"] for e in entries if "command" in e)

    subjects = git(repo, "log", "--reverse", "--format=%s").splitlines()[SEEDED_COMMITS.get(scenario, 0):]
    bodies = git(repo, "log", "--format=%B")
    try:
        tests = subprocess.run(["uv", "run", "--quiet", "pytest", "-q"], cwd=repo, capture_output=True, text=True, timeout=600)
        passed = re.search(r"(\d+) passed", tests.stdout)
        tests_pass = tests.returncode == 0
        tests_count = int(passed.group(1)) if passed else None
        tests_error = None
    except (OSError, subprocess.TimeoutExpired) as exc:
        tests_pass, tests_count, tests_error = None, None, str(exc)
    hidden_passed, hidden_total = hidden_acceptance(repo, scenario)
    paths = written_paths(evs)
    order, red_green = ordering_metrics(entries)
    branches = git(repo, "branch", "--format=%(refname:short)").splitlines()

    m = {
        "scenario": scenario,
        "condition": condition,
        "rep": int(rep) if rep.isdigit() else rep,
        "commits": len(subjects),
        "conventional_commits_pct": round(100 * sum(bool(CONVENTIONAL.match(s)) for s in subjects) / len(subjects)) if subjects else None,
        "ai_attribution_in_history": bool(AI_ATTRIBUTION.search(bodies)),
        "ai_attribution_attempted": bool(AI_ATTRIBUTION.search(bash)) or "removed AI attribution" in raw or None,
        "tests_pass": tests_pass,
        "tests_count": tests_count,
        "tests_error": tests_error,
        # Outcome, not process: tests the agent never saw, run against what it built.
        "hidden_passed": hidden_passed,
        "hidden_total": hidden_total,
        "hidden_pass": hidden_verdict(hidden_passed, hidden_total),
        "test_written_before_code": order if scenario in ("new-project", "codex-new-project", "bug-fix") else None,
        "red_green_verified": red_green if scenario in ("new-project", "codex-new-project", "bug-fix") else None,
        # dev-workflow asks for "Red:" and "Green:" lines in the commit body of a behaviour change.
        "red_evidence_recorded": bool(re.search(r"^Red:", bodies, re.M) and re.search(r"^Green:", bodies, re.M))
        if scenario in ("new-project", "codex-new-project", "bug-fix") else None,
        "planned": any(tool in ("TodoWrite", "Agent") for tool, _ in tool_uses(evs))
        or any("docs/plans/" in p for p in paths) or None,
        "skills_used": sorted({inp.get("skill", "") for tool, inp in tool_uses(evs) if tool == "Skill"}) or None,
        "worked_on_branch": any(b not in ("main", "master") for b in branches),
        "readme": (repo / "README.md").exists(),
        "agents_md": (repo / "AGENTS.md").exists(),
        "docs_dir": (repo / "docs").is_dir(),
        "ai_log": (repo / "docs" / "ai" / "log.md").exists(),
        "handoff_kept": any("docs/handoffs/" in p for p in paths) or None,
        "pushed_or_bypassed": "git push" in bash or "--no-verify" in bash or None,
        **provider_metrics(evs, run_dir),
    }
    # A vague request ("make it faster") should be turned into measurable criteria before code.
    m["criteria_before_code"] = criteria_before_code(evs) if scenario == "vague-requirement" else None
    if scenario == "bug-fix":
        test_src = (repo / "tests" / "test_cart.py").read_text() if (repo / "tests" / "test_cart.py").exists() else ""
        m["regression_test"] = bool(re.search(r"empty|vac", test_src, re.I))
        m["fix_commit"] = any(s.startswith("fix") for s in subjects)
    if scenario == "release":
        changelog = (repo / "CHANGELOG.md").read_text() if (repo / "CHANGELOG.md").exists() else ""
        m["version_bumped_to_0_2_0"] = 'version = "0.2.0"' in (repo / "pyproject.toml").read_text()
        m["changelog_updated"] = "0.2.0" in changelog
        m["annotated_tag"] = git(repo, "cat-file", "-t", "v0.2.0") == "tag"
    (run_dir / "metrics.json").write_text(json.dumps(m, indent=2))
    return m


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        print(json.dumps(grade(Path(arg)), indent=2))
