"""Aggregate every frozen journey; keep cost, correctness and observed process separate."""
import argparse
from collections import defaultdict
import difflib
import json
from pathlib import Path
import re
import statistics

from adoption import transcript_metrics
from lifecycle import matrix
from lifecycle_grade import workflow
from quality_review import production
from quality import digest


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def stage_metrics(path, saved):
    metrics = transcript_metrics(path / 'transcript.jsonl')
    if metrics['usage'] != saved['usage']:
        raise ValueError(f'token ledger mismatch: {path.name}')
    if metrics['usage']['cached_input_tokens'] > metrics['usage']['input_tokens']:
        raise ValueError('cached input must be a subset')
    return dict(seconds=saved['seconds'], completed=saved['completed'], **metrics['usage'],
                token_usage_complete=bool(metrics['completed_turns']), errors=metrics['errors'], workflow=workflow(path))


def authored_history(directory, stages):
    """Integrated commits and controller snapshots are not new work by the current actor."""
    seen = set()
    for name, metrics in stages.items():
        evidence = load(directory / name / 'git.json')
        commits = [c for c in evidence['commits'] if c['subject'] != 'chore: transport evaluation snapshot']
        new = [c for c in commits if c['hash'] not in seen]
        seen.update(c['hash'] for c in commits)
        metrics['workflow'].update(
            new_authored_commits=len(new),
            new_conventional=bool(new) and all(re.match(r'^[a-z]+(?:\([^)]+\))?!?: .+', c['subject']) for c in new),
            controller_commits_excluded=len(evidence['commits']) - len(commits),
            clean_delivery=not evidence['status'],
            unresolved_merge=bool(evidence['unresolved']),
            branch_evidence_limit='Observed end branch; review/repair inherit a controller transport branch. Not proof the actor created it.')


def changes(before, after, scenario):
    task = 'settings' if scenario == 'stock' else 'shipment'
    original, current = production(before, task), production(after, task)
    paths, added, removed = [], 0, 0
    for path in sorted(set(original) | set(current)):
        old, new = original.get(path, ''), current.get(path, '')
        if old == new:
            continue
        paths.append(path)
        diff = list(difflib.unified_diff(old.splitlines(), new.splitlines()))
        added += sum(line.startswith('+') and not line.startswith('+++') for line in diff)
        removed += sum(line.startswith('-') and not line.startswith('---') for line in diff)
    return dict(paths=paths, added=added, removed=removed,
                limit='Observed delivered-code change, not an automatic maintainability or complexity score.')


def setup_evidence(directory, case):
    root = directory / 'setup/repo'
    agents = (root / 'AGENTS.md').read_text(encoding='utf-8') if (root / 'AGENTS.md').is_file() else ''
    profile = load(root / 'tack.json') if (root / 'tack.json').is_file() else None
    # Do not score text presence as actual behavioral compliance.
    result = dict(has_instructions=bool(agents), instructions_characters=len(agents),
                  recorded_choices='setup choices' in agents.lower(), profile=profile,
                  shared_activation=(root / '.tack').is_file(),
                  declined_capability_files=[str(p.relative_to(root)) for p in root.rglob('SKILL.md')])
    clone = directory / 'change/clone.json'
    if clone.exists():
        result['clone_observations'] = load(clone)
    return result


def collect(source):
    manifest = load(source / 'manifest.json')
    results = []
    for case in matrix(manifest):
        directory = source / case['id']
        journey = load(directory / 'journey.json')
        if journey.get('infrastructure_error') or not set(('setup', 'build', 'change', 'review')).issubset(journey['stages']):
            raise ValueError('incomplete journey: ' + case['id'])
        stages = {name: stage_metrics(directory / name, saved) for name, saved in journey['stages'].items()}
        authored_history(directory, stages)
        install = {who: load(directory / f'install-{who}.json')['seconds'] if (directory / f'install-{who}.json').exists() else 0 for who in ('a', 'b')}
        row = dict(case, accepted=journey['accepted'], before_repair=journey['grades']['review']['acceptance']['passed'] and
                   journey['grades']['review']['public']['exit_code'] == 0 and journey['grades']['review']['dispositions']['passed'],
                   repair='repair' in stages, stages=stages, installation_seconds=install,
                   seconds=sum(s['seconds'] for s in stages.values()) + sum(install.values()),
                   usage={key: sum(s[key] for s in stages.values()) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')},
                   token_usage_complete=all(s['token_usage_complete'] for s in stages.values()),
                   interrupted_stages=[name for name, stage in stages.items() if not stage['completed']],
                   build_acceptance=journey['grades']['build']['acceptance']['passed'],
                   change_acceptance=journey['grades']['change']['acceptance']['passed'],
                   useful_tests=journey['grades']['build']['useful_tests']['rejects_seed'],
                   setup=setup_evidence(directory, case),
                   later_change=changes(directory / 'build/repo', directory / 'change/repo', case['scenario']),
                   grades=journey['grades'])
        results.append(row)
    groups = defaultdict(list)
    for row in results:
        groups[(row['model'], row['scenario'], row['condition'])].append(row)
    aggregate = []
    for (model, scenario, condition), rows in sorted(groups.items()):
        count = sum(r['accepted'] for r in rows)
        aggregate.append(dict(model=model, scenario=scenario, condition=condition, attempts=len(rows), accepted=count,
            before_repair=sum(r['before_repair'] for r in rows), repairs=sum(r['repair'] for r in rows),
            useful_tests=sum(r['useful_tests'] for r in rows),
            seconds=sum(r['seconds'] for r in rows), median_seconds=statistics.median(r['seconds'] for r in rows),
            range_seconds=[min(r['seconds'] for r in rows), max(r['seconds'] for r in rows)],
            seconds_per_accepted=sum(r['seconds'] for r in rows)/count if count else None,
            token_usage_complete=all(r['token_usage_complete'] for r in rows),
            usage={k: sum(r['usage'][k] for r in rows) for k in ('input_tokens','cached_input_tokens','output_tokens')}))
    return dict(version=1, manifest=manifest, journeys=results, aggregate=aggregate,
                limits='All attempts and repairs included. Interrupted turns may omit usage; affected token totals are lower bounds, not free work. Synthetic agent work, not measured human time or general scalability. Code review is separate.')


def review_results(source):
    identities = load(source / 'mapping.json')
    attempts, scores = [], []
    for job in load(source / 'jobs.json'):
        directory = source / job['id']
        if digest(directory / 'bundle/bundle.json') != job['sha256']:
            raise ValueError('review bundle changed: ' + job['id'])
        grade = load(directory / 'grade.json')
        attempt = dict(id=job['id'], **identities[job['id']], grade=grade)
        attempts.append(attempt)
        if not grade.get('completed') or not grade.get('weighted_scores'):
            continue
        raw = load(directory / 'evidence/review.json')
        for candidate in raw['candidates']:
            identity = identities[job['id']]['candidates'][candidate['id']]
            scores.append(dict(review=job['id'], case=identity['case'], phase=attempt['phase'],
                               reversed=attempt['reversed'], weighted=grade['weighted_scores'][candidate['id']],
                               dimensions=candidate['dimensions'], findings=candidate['findings']))
    return dict(attempts=attempts, scores=scores,
                limit='Primary and reversed-order scores remain separate; missing reviews are not zero scores.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviews', type=Path)
    args = parser.parse_args()
    report = collect(args.source)
    if args.reviews:
        report['reviews'] = review_results(args.reviews)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for row in report['aggregate']:
        print(row['model'], row['scenario'], row['condition'], str(row['accepted']) + '/2',
              f"{row['seconds']:.2f}s", row['usage']['input_tokens'])


if __name__ == '__main__':
    main()
