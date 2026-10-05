#!/usr/bin/env python3
"""Outcome metrics from a repository's git history: escaped defects and rework, not process.

Usage: evals/outcomes.py <repo> [--ref REF] [--days N] [--json]
- Escaped defect: a feat: commit whose lines a later fix: changes within N days (default 14) after
  the feature reached the main line of REF (default HEAD; pass main when on a feature branch).
  The link is SZZ-style: git blame on the lines the fix changes or deletes. A fix that reached the
  main line in the same step as its feature (the same merged branch) was caught in review or CI
  instead (fixes_before_merge). Docs, Markdown and tests are not linked, and neither is a fix that
  only adds lines.
- Rework: fix: commits and reverts; bookkeeping: docs(handoffs|plans|ai) commits.
- Lead time: for each merge on the main line, from the merged branch's first commit to the merge.
The before/after-merge split assumes branches merged with merge commits (--no-ff); with squash,
rebase or fast-forward merges every fix is its own step and counts as escaped.
"""
import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

FEAT = re.compile(r"^feat(\([^)]*\))?!?: ")
FIX = re.compile(r"^fix(\([^)]*\))?!?: ")
REVERT = re.compile(r'^(Revert "|revert(\([^)]*\))?!?: )')
BOOKKEEPING = re.compile(r"^docs\((handoffs?|plans?|ai)\)")
# Output that does not depend on the user's git settings (prefixes, colour, quoting, external diff).
STABLE = ["-c", "core.quotePath=false", "-c", "color.ui=never", "-c", "diff.noprefix=false"]


def git(repo, *args):
    return subprocess.run(["git", *STABLE, "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def has_commits(repo, ref):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                          capture_output=True).returncode == 0


def is_code(name):
    """Files that can carry a defect: not docs, Markdown or tests."""
    return not re.search(r"(^|/)(docs|tests?)/|\.md$|(^|/)test_[^/]*$", name)


def commits(repo, ref):
    """Non-merge commits as (sha, time, subject, parents), oldest first."""
    out = []
    for line in git(repo, "log", "--no-merges", "--reverse", "--format=%H%x09%ct%x09%P%x09%s", ref).splitlines():
        sha, time, parents, subject = line.split("\t", 3)
        out.append((sha, int(time), subject, parents.split()))
    return out


def landing(repo, ref):
    """Maps each commit to (index, time) of the first-parent step that brought it to the main line."""
    landed = {}
    steps = git(repo, "log", "--first-parent", "--reverse", "--format=%H %ct %P", ref).splitlines()
    for index, line in enumerate(steps):
        sha, time, *parents = line.split()
        brought = git(repo, "rev-list", f"{parents[0]}..{sha}").split() if len(parents) > 1 else [sha]
        for commit in brought:
            landed.setdefault(commit, (index, int(time)))
    return landed


def blamed(repo, fix):
    """Commits that wrote the code lines a fix changes or deletes."""
    origins = set()
    diff = git(repo, "diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames",
               "--src-prefix=a/", "--dst-prefix=b/", f"{fix}^", fix)
    path = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            # git appends a tab to names with spaces; /dev/null means the file is new.
            name = line[4:].rstrip("\t")
            path = name[2:] if name.startswith("a/") else None
            continue
        match = re.match(r"@@ -(\d+)(?:,(\d+))? ", line)
        if not match or not path or not is_code(path):
            continue
        start, count = int(match.group(1)), int(match.group(2) or 1)
        if count == 0:
            continue
        blame = git(repo, "blame", "--porcelain", "-L", f"{start},{start + count - 1}", f"{fix}^", "--", path)
        origins.update(re.findall(r"^([0-9a-f]{40,64}) \d+ \d+", blame, re.M))
    return origins


def lead_times(repo, ref):
    """Hours from a merged branch's first commit to its merge, per merge on the main line."""
    hours = []
    for line in git(repo, "log", "--first-parent", "--merges", "--format=%H %ct", ref).splitlines():
        merge, merged_at = line.split()
        times = [int(t) for t in git(repo, "log", "--format=%ct", f"{merge}^1..{merge}^2").split()]
        if times:
            hours.append((int(merged_at) - min(times)) / 3600)
    return hours


def measure(repo, days=14, ref="HEAD"):
    if not has_commits(repo, ref):
        history, landed, hours = [], {}, []
    else:
        history, landed, hours = commits(repo, ref), landing(repo, ref), lead_times(repo, ref)
    window = days * 86400
    features = {sha for sha, _, subject, _ in history if FEAT.match(subject)}
    escaped, before_merge = set(), 0
    for fix, _, subject, parents in history:
        # A root commit has nothing to correct.
        if not FIX.match(subject) or not parents or fix not in landed:
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
    return {
        "ref": ref,
        "window_days": days,
        "commits": len(history),
        "features": len(features),
        "escaped_defects": len(escaped),
        "escaped_defect_rate": round(100 * len(escaped) / len(features)) if features else None,
        "fixes": sum(1 for _, _, subject, _ in history if FIX.match(subject)),
        "fixes_before_merge": before_merge,
        "reverts": sum(1 for _, _, subject, _ in history if REVERT.match(subject)),
        "bookkeeping_commits": sum(1 for _, _, subject, _ in history if BOOKKEEPING.match(subject)),
        "merges": len(hours),
        "median_lead_time_hours": round(statistics.median(hours), 1) if hours else None,
    }


ROWS = [("commits", "Commits (no merges)"), ("features", "Features (feat:)"),
        ("escaped_defects", "Escaped defects"), ("escaped_defect_rate", "Escaped defect rate (%)"),
        ("fixes", "Fixes (fix:)"), ("fixes_before_merge", "Fixes to a feature before its merge"),
        ("reverts", "Reverts"), ("bookkeeping_commits", "Bookkeeping commits"),
        ("merges", "Merges"), ("median_lead_time_hours", "Median lead time to merge (h)")]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--ref", default="HEAD", help="history to measure (default HEAD)")
    parser.add_argument("--days", type=int, default=14, help="window for a fix to count as escaped (default 14)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a Markdown table")
    args = parser.parse_args()
    metrics = measure(args.repo, args.days, args.ref)
    if args.json:
        print(json.dumps(metrics, indent=2))
        return
    print(f"| Metric ({args.ref}, {args.days}-day window) | Value |\n| --- | --- |")
    for key, label in ROWS:
        print(f"| {label} | {'–' if metrics[key] is None else metrics[key]} |")


if __name__ == "__main__":
    main()
