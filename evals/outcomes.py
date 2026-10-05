#!/usr/bin/env python3
"""Outcome metrics from a repository's git history: escaped defects and rework, not process.

Usage: evals/outcomes.py <repo> [--days N] [--json]
- Escaped defect: a feat: commit whose lines a later fix: changes within N days (default 14) after
  the feature reached the main line (SZZ-style: git blame on the lines the fix changes or deletes).
  A fix on the same branch before the merge was caught in review or CI instead
  (fixes_before_merge). Docs, Markdown and tests are not linked; a fix that only adds lines is not
  linked either.
- Rework: fix: commits and reverts; bookkeeping: docs(handoffs|plans|ai) commits.
- Lead time: for each merge on the first-parent history, from the branch's first commit to the merge.
Conventional Commit subjects are assumed; a repository without them reports few features.
"""
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

FEAT = re.compile(r"^feat(\([^)]*\))?!?: ")
FIX = re.compile(r"^fix(\([^)]*\))?!?: ")
REVERT = re.compile(r'^(Revert "|revert(\([^)]*\))?!?: )')
BOOKKEEPING = re.compile(r"^docs\((handoffs?|plans?|ai)\)")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def is_code(name):
    """Files that can carry a defect: not docs, Markdown or tests."""
    return not re.search(r"(^|/)(docs|tests?)/|\.md$|(^|/)test_[^/]*$", name)


def commits(repo):
    """Non-merge commits as (sha, time, subject), oldest first."""
    out = []
    for line in git(repo, "log", "--no-merges", "--reverse", "--format=%H%x09%ct%x09%s").splitlines():
        sha, time, subject = line.split("\t", 2)
        out.append((sha, int(time), subject))
    return out


def landing(repo):
    """Maps each commit to (index, time) of the first-parent step that brought it to the main line."""
    landed = {}
    steps = git(repo, "rev-list", "--first-parent", "--reverse", "--parents", "HEAD").splitlines()
    for index, line in enumerate(steps):
        sha, *parents = line.split()
        time = int(git(repo, "show", "-s", "--format=%ct", sha))
        brought = git(repo, "rev-list", f"{parents[0]}..{sha}" if parents else sha).split()
        for commit in brought:
            landed.setdefault(commit, (index, time))
    return landed


def blamed(repo, fix):
    """Commits that wrote the code lines a fix changes or deletes."""
    origins = set()
    diff = git(repo, "diff", "-U0", "--no-renames", f"{fix}^", fix)
    path = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            path = line[6:] if line.startswith("--- a/") else None
            continue
        match = re.match(r"@@ -(\d+)(?:,(\d+))? ", line)
        if not match or not path or not is_code(path):
            continue
        start, count = int(match.group(1)), int(match.group(2) or 1)
        if count == 0:
            continue
        blame = git(repo, "blame", "--porcelain", "-L", f"{start},{start + count - 1}", f"{fix}^", "--", path)
        origins.update(re.findall(r"^([0-9a-f]{40}) \d+ \d+", blame, re.M))
    return origins


def lead_times(repo):
    """Hours from a merged branch's first commit to its merge, per merge on the main line."""
    hours = []
    for merge in git(repo, "rev-list", "--merges", "--first-parent", "HEAD").split():
        merged_at = int(git(repo, "show", "-s", "--format=%ct", merge))
        times = [int(t) for t in git(repo, "log", "--format=%ct", f"{merge}^1..{merge}^2").split()]
        if times:
            hours.append((merged_at - min(times)) / 3600)
    return hours


def measure(repo, days=14):
    history = commits(repo)
    window = days * 86400
    landed = landing(repo)
    features = {sha for sha, _, subject in history if FEAT.match(subject)}
    escaped, before_merge = set(), 0
    for fix, _, subject in history:
        if not FIX.match(subject) or fix not in landed:
            continue
        fix_step, fix_time = landed[fix]
        caught = False
        for origin in blamed(repo, fix) & features:
            if origin not in landed:
                continue
            feature_step, feature_time = landed[origin]
            if feature_step == fix_step:
                caught = True
            elif feature_step < fix_step and fix_time <= feature_time + window:
                escaped.add(origin)
        before_merge += caught
    hours = lead_times(repo)
    return {
        "window_days": days,
        "commits": len(history),
        "features": len(features),
        "escaped_defects": len(escaped),
        "escaped_defect_rate": round(100 * len(escaped) / len(features)) if features else None,
        "fixes": sum(1 for _, _, subject in history if FIX.match(subject)),
        "fixes_before_merge": before_merge,
        "reverts": sum(1 for _, _, subject in history if REVERT.match(subject)),
        "bookkeeping_commits": sum(1 for _, _, subject in history if BOOKKEEPING.match(subject)),
        "merges": len(hours),
        "median_lead_time_hours": round(statistics.median(hours), 1) if hours else None,
    }


ROWS = [("commits", "Commits (no merges)"), ("features", "Features (feat:)"),
        ("escaped_defects", "Escaped defects"), ("escaped_defect_rate", "Escaped defect rate (%)"),
        ("fixes", "Fixes (fix:)"),
        ("fixes_before_merge", "Fixes to a feature before its merge"), ("reverts", "Reverts"), ("bookkeeping_commits", "Bookkeeping commits"),
        ("merges", "Merges"), ("median_lead_time_hours", "Median lead time to merge (h)")]


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 14
    metrics = measure(Path(argv[0]), days)
    if "--json" in argv:
        print(json.dumps(metrics, indent=2))
        return
    print(f"| Metric ({days}-day window) | Value |\n| --- | --- |")
    for key, label in ROWS:
        print(f"| {label} | {'–' if metrics[key] is None else metrics[key]} |")


if __name__ == "__main__":
    main(sys.argv[1:])
