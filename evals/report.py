#!/usr/bin/env python3
"""Summarises graded eval runs as Markdown tables comparing baseline and harness.

Usage: evals/report.py [evals dir]   (default: $EVALS_OUT or $TMPDIR/agent-tack-evals)
Reads every <scenario>/<condition>-<rep>/metrics.json written by evals/grade.py.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROWS = [
    # Outcomes first: hidden tests the agent never saw, run against what it built.
    ("hidden_pass", "Hidden acceptance tests: all pass", "rate"),
    ("hidden_passed", "Hidden acceptance tests passed (mean count)", "mean"),
    ("commits", "Commits", "mean"),
    ("conventional_commits_pct", "Conventional Commits (%)", "mean"),
    ("ai_attribution_in_history", "AI attribution in history", "rate"),
    ("tests_pass", "Tests pass", "rate"),
    ("tests_count", "Tests", "mean"),
    ("test_written_before_code", "Test written before code", "rate"),
    ("red_green_verified", "Failing test before fix and passing test after", "rate"),
    ("red_evidence_recorded", "Red and Green evidence in the commit body", "rate"),
    ("criteria_before_code", "Measurable criteria before code (vague request)", "rate"),
    ("planned", "Wrote a plan", "rate"),
    ("worked_on_branch", "Worked on a branch", "rate"),
    ("readme", "README", "rate"),
    ("agents_md", "AGENTS.md", "rate"),
    ("docs_dir", "docs/", "rate"),
    ("ai_log", "AI work logged (docs/ai/log.md)", "rate"),
    ("handoff_kept", "Handoff kept during the task", "rate"),
    ("regression_test", "Regression test for the bug", "rate"),
    ("fix_commit", "fix: commit", "rate"),
    ("version_bumped_to_0_2_0", "Version bumped to 0.2.0", "rate"),
    ("changelog_updated", "CHANGELOG updated", "rate"),
    ("annotated_tag", "Annotated v0.2.0 tag", "rate"),
    ("pushed_or_bypassed", "Pushed or bypassed hooks", "rate"),
    ("duration_s", "Duration (s)", "mean"),
    ("turns", "Turns", "mean"),
    ("output_tokens", "Output tokens", "mean"),
    ("cost_usd", "Cost (USD)", "mean"),
]


CONDITION_ORDER = ["baseline", "harness", "auto", "lean", "lite", "standard", "strict"]


def fmt(values, kind):
    values = [v for v in values if v is not None]
    if not values:
        return "–"
    if kind == "rate":
        return f"{sum(bool(v) for v in values)}/{len(values)}"
    mean = sum(values) / len(values)
    return f"{mean:.4f}" if mean < 1 and mean != 0 else f"{mean:.0f}" if mean >= 100 else f"{mean:.1f}"


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "EVALS_OUT", Path(os.environ.get("TMPDIR", "/tmp")) / "agent-tack-evals"))
    runs = defaultdict(lambda: defaultdict(list))
    for f in sorted(root.glob("*/*/metrics.json")):
        m = json.loads(f.read_text())
        runs[(m["scenario"], str(m.get("metrics_version", "legacy")), m.get("provider") or "unknown")][m["condition"]].append(m)
    if not runs:
        sys.exit(f"no metrics.json under {root}: run evals/grade.py first")
    for group in sorted(runs):
        scenario, version, provider = group
        by_condition = runs[group]
        conditions = sorted(by_condition, key=lambda c: (CONDITION_ORDER.index(c) if c in CONDITION_ORDER else len(CONDITION_ORDER), c))
        counts = "; ".join(f"{c}: {len(by_condition[c])} runs" for c in conditions)
        print(f"### {scenario} ({counts})\n")
        print(f"Provider: {provider}; metrics version: {version}. Unknown measurements are excluded; rates show the number of observed runs.\n")
        print("| Metric | " + " | ".join(c.capitalize() for c in conditions) + " |")
        print("| --- |" + " --- |" * len(conditions))
        for key, label, kind in ROWS:
            columns = [[m.get(key) for m in by_condition[c]] for c in conditions]
            if all(v is None for column in columns for v in column):
                continue
            print(f"| {label} | " + " | ".join(fmt(column, kind) for column in columns) + " |")
        print()

if __name__ == "__main__":
    main()
