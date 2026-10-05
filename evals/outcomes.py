#!/usr/bin/env python3
"""Outcome metrics from a repository's git history: escaped defects and rework, not process.

Usage: evals/outcomes.py <repo> [--days N] [--json]
- Escaped defect: a feat: commit whose files a fix: commit touches within N days (default 14).
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


def commits(repo):
    """Non-merge commits as (time, subject, files), oldest first."""
    out = []
    for record in git(repo, "log", "--no-merges", "--reverse", "--format=%x00%ct%x09%s", "--name-only").split("\0")[1:]:
        header, _, names = record.partition("\n")
        time, _, subject = header.partition("\t")
        out.append((int(time), subject, {name for name in names.splitlines() if name}))
    return out


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
    features = [(t, files) for t, subject, files in history if FEAT.match(subject)]
    fixes = [(t, files) for t, subject, files in history if FIX.match(subject)]
    escaped = sum(1 for t, files in features
                  if any(t < fixed_at <= t + window and files & fixed for fixed_at, fixed in fixes))
    hours = lead_times(repo)
    return {
        "window_days": days,
        "commits": len(history),
        "features": len(features),
        "escaped_defects": escaped,
        "escaped_defect_rate": round(100 * escaped / len(features)) if features else None,
        "fixes": len(fixes),
        "reverts": sum(1 for _, subject, _ in history if REVERT.match(subject)),
        "bookkeeping_commits": sum(1 for _, subject, _ in history if BOOKKEEPING.match(subject)),
        "merges": len(hours),
        "median_lead_time_hours": round(statistics.median(hours), 1) if hours else None,
    }


ROWS = [("commits", "Commits (no merges)"), ("features", "Features (feat:)"),
        ("escaped_defects", "Escaped defects"), ("escaped_defect_rate", "Escaped defect rate (%)"),
        ("fixes", "Fixes (fix:)"), ("reverts", "Reverts"), ("bookkeeping_commits", "Bookkeeping commits"),
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
