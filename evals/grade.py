#!/usr/bin/env python3
"""Measures what one eval run did: inspects its repo and transcript and writes metrics.json.

Usage: evals/grade.py <run dir>...     (e.g. $EVALS_OUT/bug-fix/harness-1)
Prints the metrics and writes <run dir>/metrics.json. evals/report.py aggregates them.
Codex writes files through shell commands, so file-order metrics are only reliable for Claude.
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
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def tool_uses(evs):
    for e in evs:
        if e.get("type") == "assistant":
            for block in e.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    yield block.get("name"), block.get("input", {})


def written_paths(evs):
    """Files written with Write/Edit, in order, skipping scaffold placeholders."""
    paths = []
    for tool, inp in tool_uses(evs):
        if tool in ("Write", "Edit", "MultiEdit") and "file_path" in inp:
            body = inp.get("content") or inp.get("new_string") or ""
            if len(body.strip().splitlines()) > 2:
                paths.append(inp["file_path"])
    return paths


def first(paths, pattern, exclude=None):
    for i, p in enumerate(paths):
        if re.search(pattern, p) and not (exclude and re.search(exclude, p)):
            return i
    return None


def grade(run_dir: Path):
    scenario = run_dir.parent.name
    condition, _, rep = run_dir.name.rpartition("-")
    repo = run_dir / "repo"
    transcript = run_dir / "transcript.jsonl"
    evs = events(transcript)
    raw = transcript.read_text(errors="replace") if transcript.exists() else ""
    result = next((e for e in reversed(evs) if e.get("type") == "result"), {})
    usage = result.get("usage", {})
    bash = " ".join(inp.get("command", "") for tool, inp in tool_uses(evs) if tool == "Bash")

    subjects = git(repo, "log", "--reverse", "--format=%s").splitlines()[SEEDED_COMMITS.get(scenario, 0):]
    bodies = git(repo, "log", "--format=%B")
    tests = subprocess.run(["uv", "run", "--quiet", "pytest", "-q"], cwd=repo, capture_output=True, text=True, timeout=600)
    passed = re.search(r"(\d+) passed", tests.stdout)
    paths = written_paths(evs)
    all_written = [inp.get("file_path", "") for tool, inp in tool_uses(evs) if tool in ("Write", "Edit", "MultiEdit")]
    test_at = first(paths, r"tests?/|test_")
    impl_at = first(paths, r"\.py$", exclude=r"tests?/|test_")
    branches = git(repo, "branch", "--format=%(refname:short)").splitlines()

    m = {
        "scenario": scenario,
        "condition": condition,
        "rep": int(rep) if rep.isdigit() else rep,
        "commits": len(subjects),
        "conventional_commits_pct": round(100 * sum(bool(CONVENTIONAL.match(s)) for s in subjects) / len(subjects)) if subjects else None,
        "ai_attribution_in_history": bool(AI_ATTRIBUTION.search(bodies)),
        "ai_attribution_attempted": bool(AI_ATTRIBUTION.search(bash)) or "removed AI attribution" in raw,
        "tests_pass": tests.returncode == 0,
        "tests_count": int(passed.group(1)) if passed else 0,
        "test_written_before_code": (test_at is not None and (impl_at is None or test_at < impl_at))
        if scenario in ("new-project", "bug-fix") else None,
        "planned": any(tool in ("TodoWrite", "Agent") for tool, _ in tool_uses(evs))
        or any("docs/plans/" in p for p in all_written),
        "skills_used": sorted({inp.get("skill", "") for tool, inp in tool_uses(evs) if tool == "Skill"}),
        "worked_on_branch": any(b not in ("main", "master") for b in branches),
        "readme": (repo / "README.md").exists(),
        "agents_md": (repo / "AGENTS.md").exists(),
        "docs_dir": (repo / "docs").is_dir(),
        "ai_log": (repo / "docs" / "ai" / "log.md").exists(),
        "handoff_kept": any("docs/handoffs/" in p for p in all_written),
        "pushed_or_bypassed": "git push" in bash or "--no-verify" in bash,
        "duration_s": round(result.get("duration_ms", 0) / 1000, 1),
        "cost_usd": round(result.get("total_cost_usd", 0) or 0, 4),
        "turns": result.get("num_turns"),
        "output_tokens": usage.get("output_tokens"),
        "input_tokens": (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0),
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
