#!/usr/bin/env python3
"""Summarises graded eval runs as Markdown tables comparing baseline and harness.

Usage: evals/report.py [evals dir]   (default: $EVALS_OUT or $TMPDIR/agent-harness-evals)
Reads every <scenario>/<condition>-<rep>/metrics.json written by evals/grade.py.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROWS = [
    ("commits", "Commits", "mean"),
    ("conventional_commits_pct", "Conventional Commits (%)", "mean"),
    ("ai_attribution_in_history", "AI attribution in history", "rate"),
    ("tests_pass", "Tests pass", "rate"),
    ("tests_count", "Tests", "mean"),
    ("test_written_before_code", "Test written before code", "rate"),
    ("planned", "Planned (todo list/agent)", "rate"),
    ("worked_on_branch", "Worked on a branch", "rate"),
    ("readme", "README", "rate"),
    ("agents_md", "AGENTS.md", "rate"),
    ("docs_dir", "docs/", "rate"),
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
        "EVALS_OUT", Path(os.environ.get("TMPDIR", "/tmp")) / "agent-harness-evals"))
    runs = defaultdict(lambda: defaultdict(list))
    for f in sorted(root.glob("*/*/metrics.json")):
        m = json.loads(f.read_text())
        runs[m["scenario"]][m["condition"]].append(m)
    if not runs:
        sys.exit(f"no metrics.json under {root}: run evals/grade.py first")
    for scenario in sorted(runs):
        by_condition = runs[scenario]
        n = max(len(v) for v in by_condition.values())
        print(f"### {scenario} ({n} runs per condition)\n")
        print("| Metric | Baseline | Harness |")
        print("| --- | --- | --- |")
        for key, label, kind in ROWS:
            base = [m.get(key) for m in by_condition.get("baseline", [])]
            harn = [m.get(key) for m in by_condition.get("harness", [])]
            if all(v is None for v in base + harn):
                continue
            print(f"| {label} | {fmt(base, kind)} | {fmt(harn, kind)} |")
        print()


if __name__ == "__main__":
    main()
