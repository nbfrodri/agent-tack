#!/usr/bin/env python3
"""Grades the eval runs: inspects each repo and transcript and prints pass/fail per check.

Usage: evals/grade.py [scenario ...]   (reads $EVALS_OUT, default $TMPDIR/agent-harness-evals)
Note: Codex writes files through shell commands, so the TDD-order and planning checks
can't be detected for it; read its transcript for those.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EVALS = Path(os.environ.get("EVALS_OUT", Path(os.environ.get("TMPDIR", "/tmp")) / "agent-harness-evals"))
CC = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w./-]+\))?!?: \S")
AI = re.compile(r"co-authored-by:.*(claude|anthropic|openai|codex)|generated with|🤖", re.I)
SEEDED = {"s2-claude-bug": 1, "s3-claude-release": 5}


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def transcript_events(path):
    events = []
    if not path.exists():
        return events
    for line in path.read_text(errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return events


def claude_tool_uses(events):
    """Yields (name, input) for every tool call in a claude stream-json transcript, in order."""
    for e in events:
        if e.get("type") == "assistant":
            for block in e.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    yield block.get("name"), block.get("input", {})


def written_files_in_order(name, events, raw):
    """Paths of files written, in order (Write/Edit for Claude, apply_patch/file changes for Codex)."""
    paths = []
    if name.startswith("s4"):
        for m in re.finditer(r"(?:\*\*\* (?:Add|Update) File: |\"path\":\s*\")([^\"\\n]+)", raw):
            paths.append(m.group(1))
    else:
        for tool, inp in claude_tool_uses(events):
            if tool in ("Write", "Edit", "MultiEdit") and "file_path" in inp:
                body = inp.get("content") or inp.get("new_string") or ""
                # Skip scaffold placeholders (empty __init__.py and similar)
                if len(body.strip().splitlines()) > 2:
                    paths.append(inp["file_path"])
    return paths


def first_index(paths, pattern):
    for i, p in enumerate(paths):
        if re.search(pattern, p):
            return i
    return None


def grade(name):
    out = EVALS / name
    repo = out / "repo"
    raw = (out / "transcript.jsonl").read_text(errors="replace") if (out / "transcript.jsonl").exists() else ""
    events = transcript_events(out / "transcript.jsonl")
    checks = []

    def check(label, ok, detail=""):
        checks.append((label, bool(ok), detail))

    all_subjects = git(repo, "log", "--reverse", "--format=%s").splitlines()
    new_subjects = all_subjects[SEEDED.get(name, 0):]
    bodies = git(repo, "log", "--format=%B")

    check("hizo commits", len(new_subjects) >= 1, f"{len(new_subjects)} commits nuevos")
    bad = [s for s in new_subjects if not CC.match(s) and not s.startswith(("Merge ", "Revert "))]
    check("todos los commits siguen Conventional Commits", not bad and new_subjects, "; ".join(bad))
    check("sin atribución de IA en el historial", not AI.search(bodies))
    check("no intentó meter atribución (el hook no tuvo que limpiarla)", "removed AI attribution" not in raw)
    executed = " ".join(inp.get("command", "") for tool, inp in claude_tool_uses(events) if tool == "Bash") if not name.startswith("s4") else raw
    check("no usó --no-verify", "--no-verify" not in executed)

    if name.startswith("s4"):
        skills_used = sorted(set(re.findall(r"skills/([a-z-]+)/SKILL\.md", raw)))
    else:
        skills_used = sorted({inp.get("skill", "") for tool, inp in claude_tool_uses(events) if tool == "Skill"})
        skills_used += sorted(set(re.findall(r"skills/([a-z-]+)/(?:SKILL|references)", raw)) - set(skills_used))
    check("consultó las skills", skills_used, ", ".join(skills_used))

    tests = subprocess.run(["uv", "run", "--quiet", "pytest", "-q"], cwd=repo, capture_output=True, text=True, timeout=300)
    last = (tests.stdout.strip().splitlines() or [""])[-1]
    check("los tests pasan", tests.returncode == 0, last)

    paths = written_files_in_order(name, events, raw)
    if name in ("s1-claude-new", "s4-codex-new"):
        check("es un repo git", (repo / ".git").exists())
        check("varios commits (no uno gigante)", len(new_subjects) >= 2, f"{len(new_subjects)}")
        readme = (repo / "README.md").read_text().lower() if (repo / "README.md").exists() else ""
        check("tiene README con uso", "usage" in readme or "uso" in readme or "```" in readme)
        check("tiene .gitignore", (repo / ".gitignore").exists())
        check("tiene AGENTS.md", (repo / "AGENTS.md").exists())
        t = first_index(paths, r"tests?/|test_")
        impl = [p if not re.search(r"tests?/|test_", p) else "" for p in paths]
        s = first_index(impl, r"src/.*\.py$|cart[^/]*\.py$")
        check("escribió tests antes que la implementación (TDD)", t is not None and (s is None or t < s), f"test#{t} src#{s}")
        planned = any(tool in ("TodoWrite", "Agent") for tool, _ in claude_tool_uses(events)) or '"plan' in raw.lower()
        check("planificó (TodoWrite/plan/planner)", planned)
    if name == "s2-claude-bug":
        t, s = first_index(paths, r"tests/"), first_index(paths, r"src/")
        check("test de regresión antes del arreglo", t is not None and s is not None and t < s, f"test#{t} src#{s}")
        check("commit de tipo fix", any(x.startswith("fix") for x in new_subjects))
        test_src = (repo / "tests" / "test_cart.py").read_text() if (repo / "tests" / "test_cart.py").exists() else ""
        check("hay un test para el carrito vacío", re.search(r"empty|vac", test_src, re.I))
    if name == "s3-claude-release":
        pyproject = (repo / "pyproject.toml").read_text()
        check("versión 0.2.0 en pyproject", 'version = "0.2.0"' in pyproject)
        changelog = (repo / "CHANGELOG.md").read_text()
        check("CHANGELOG con sección 0.2.0", "[0.2.0]" in changelog)
        check("CHANGELOG menciona item count y el fix", re.search(r"item count", changelog, re.I) and re.search(r"empty|average", changelog, re.I))
        check("tag v0.2.0 anotado", git(repo, "cat-file", "-t", "v0.2.0") == "tag")
        check("commit chore(release)", any(s.startswith("chore(release)") for s in new_subjects))
        commands = " ".join(inp.get("command", "") for tool, inp in claude_tool_uses(events) if tool == "Bash")
        check("no ejecutó git push", "git push" not in commands)

    run = (out / "run.txt").read_text().strip() if (out / "run.txt").exists() else "running"
    return checks, run


def main():
    names = sys.argv[1:] or ["s1-claude-new", "s2-claude-bug", "s3-claude-release", "s4-codex-new"]
    total_pass = total = 0
    for name in names:
        checks, run = grade(name)
        passed = sum(ok for _, ok, _ in checks)
        total_pass += passed
        total += len(checks)
        print(f"\n## {name}  ({passed}/{len(checks)})  [{run}]")
        for label, ok, detail in checks:
            print(f"  {'✔' if ok else '✘'} {label}" + (f"  — {detail}" if detail else ""))
    print(f"\nTOTAL {total_pass}/{total}")


if __name__ == "__main__":
    main()
