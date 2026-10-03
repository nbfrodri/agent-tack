#!/usr/bin/env python3
"""Measures what one eval run did: inspects its repo and transcript and writes metrics.json.

Usage: evals/grade.py <run dir>...     (e.g. $EVALS_OUT/bug-fix/harness-1)
Prints the metrics and writes <run dir>/metrics.json. evals/report.py aggregates them.
Ordering uses explicit Claude writes and Codex file_change events; opaque shell writes remain unknown.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w./-]+\))?!?: \S")
AI_ATTRIBUTION = re.compile(r"co-authored-by:.*(claude|anthropic|openai|codex|copilot|gemini|cursor)|generated with|🤖", re.I)
SEEDED_COMMITS = {"new-project": 0, "codex-new-project": 0, "bug-fix": 1, "release": 5}


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
        "test_written_before_code": order if scenario in ("new-project", "codex-new-project", "bug-fix") else None,
        "red_green_verified": red_green if scenario in ("new-project", "codex-new-project", "bug-fix") else None,
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
