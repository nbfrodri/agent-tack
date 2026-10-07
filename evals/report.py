#!/usr/bin/env python3
"""Summarises graded eval runs as Markdown tables comparing baseline and harness.

Usage: evals/report.py [evals dir]   (default: $EVALS_OUT or $TMPDIR/agent-tack-evals)
Reads every <scenario>/<condition>-<rep>/metrics.json written by evals/grade.py.
"""
import json
import os
import sys
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROWS = [
    # Outcomes first: hidden tests the agent never saw, run against what it built.
    ("hidden_pass", "Hidden acceptance tests: all pass", "rate"),
    ("hidden_passed", "Hidden acceptance tests passed (mean count)", "mean"),
    ("completed", "Runner completed successfully", "rate"),
    ("timed_out", "Runner timed out", "rate"),
    ("scope_respected", "Requested scope respected", "rate"),
    ("capability_count", "Local capability definitions", "mean"),
    ("new_capability_count", "New local capability definitions", "mean"),
    ("capability_read_in_reuse", "Existing capability read in fresh session", "rate"),
    ("unnecessary_capability_created", "Unnecessary capability created", "rate"),
    ("delegation_observed", "Subagent invocation observed", "rate"),
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
    ("setup_s", "Setup duration (s)", "mean"),
    ("turns", "Turns", "mean"),
    ("output_tokens", "Output tokens", "mean"),
    ("input_tokens", "Input tokens", "mean"),
    ("cost_usd", "Cost (USD)", "mean"),
]


CONDITION_ORDER = ["baseline", "harness", "auto", "lean", "lite", "standard", "strict"]


def comparison(m, path):
    version = str(m.get('metrics_version', 'legacy'))
    base = (m['scenario'], version, m.get('provider') or 'unknown')
    if version != '3':
        return base, m['condition']
    meta = m.get('metadata') or {}
    fields = ('resolved_model', 'requested_model', 'cli_version', 'prompt_sha256', 'fixture_sha256',
              'hidden_sha256', 'permission_mode', 'effort', 'timeout_seconds')
    cohort = json.dumps({key: meta.get(key) for key in fields}, sort_keys=True)
    # No observation cannot certify compatibility. Such runs get an individual cohort.
    identity_fields = ('harness_revision', 'source_sha256', 'configuration_sha256')
    required = tuple(key for key in fields if key not in ('effort', 'requested_model', 'timeout_seconds')) + identity_fields
    if any(not meta.get(key) or meta[key] == 'unknown' for key in required) or meta.get('source_changed'):
        cohort += str(path)
    variant = ' '.join(str(meta.get(k) or 'unknown')[:12] for k in
                       identity_fields)
    return (*base, cohort), m['condition'] + ' @ ' + variant


def interval(values):
    known = [v for v in values if v is not None]
    if not known:
        return 'unknown'
    n, z = len(known), 1.96
    p = sum(bool(v) for v in known) / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    margin = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1+z*z/n)
    return f'{100*(center-margin):.1f}–{100*(center+margin):.1f}%'


def outcome_details(samples):
    verdicts = [m.get('hidden_pass') for m in samples]
    known_costs = [m['cost_usd'] for m in samples if m.get('cost_usd') is not None]
    successes = sum(v is True for v in verdicts)
    complete_cost = len(known_costs) == len(samples)
    yield 'Success rate, 95% Wilson interval', interval(verdicts)
    yield 'Unknown acceptance outcomes', str(sum(v is None for v in verdicts))
    yield 'Observed total spend (USD)', f'{sum(known_costs):.4f}' + ('' if complete_cost else ' (incomplete)')
    yield 'Total spend per accepted outcome (USD)', f'{sum(known_costs)/successes:.4f}' if complete_cost and successes and None not in verdicts else 'unknown'
    for key, label in [('duration_s', 'Duration'), ('cost_usd', 'Cost')]:
        values = [m[key] for m in samples if m.get(key) is not None]
        yield label + ' median [min, max]', f'{statistics.median(values):.2f} [{min(values):.2f}, {max(values):.2f}]' if values else 'unknown'


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
    for f in sorted(root.rglob("metrics.json")):
        m = json.loads(f.read_text(encoding='utf-8'))
        group, variant = comparison(m, f)
        runs[group][variant].append(m)
    if not runs:
        sys.exit(f"no metrics.json under {root}: run evals/grade.py first")
    for group in sorted(runs):
        scenario, version, provider = group[:3]
        by_condition = runs[group]
        conditions = sorted(by_condition, key=lambda c: (CONDITION_ORDER.index(c.split(' @ ')[0]) if c.split(' @ ')[0] in CONDITION_ORDER else len(CONDITION_ORDER), c))
        counts = "; ".join(f"{c}: {len(by_condition[c])} runs" for c in conditions)
        print(f"### {scenario} ({counts})\n")
        print(f"Provider: {provider}; metrics version: {version}. Unknown measurements are excluded; rates show the number of observed runs.\n")
        if version == '3':
            print('Comparison identity: ' + group[3] + '\n')
        print("| Metric | " + " | ".join(c.capitalize() for c in conditions) + " |")
        print("| --- |" + " --- |" * len(conditions))
        for key, label, kind in ROWS:
            columns = [[m.get(key) for m in by_condition[c]] for c in conditions]
            if all(v is None for column in columns for v in column):
                continue
            print(f"| {label} | " + " | ".join(fmt(column, kind) for column in columns) + " |")
        if version == '3':
            details = [list(outcome_details(by_condition[c])) for c in conditions]
            for index, (label, _) in enumerate(details[0]):
                print(f'| {label} | ' + ' | '.join(d[index][1] for d in details) + ' |')
        print()

if __name__ == "__main__":
    main()
