"""Publish bounded lifecycle evidence, preserving failures and anonymous review source."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'evals'))
from lifecycle_report import collect, load, review_results  # noqa: E402
from quality import digest  # noqa: E402


def publish(source, reviews):
    report = collect(source)
    judged = review_results(reviews)
    facts = dict(version=1, manifest=report['manifest'], aggregate=report['aggregate'],
                 product=load(source / 'product.json'), controller=load(source / 'controller.json'),
                 journeys=[], reviews=judged['scores'], review_attempts=[], bundles={}, paired=[])
    facts['analysis_sources'] = {str(path.relative_to(ROOT)).replace('\\', '/'): digest(path)
                                for path in (Path(__file__).resolve(), ROOT / 'evals/lifecycle_report.py')}
    probe = source / 'transport-probe.json'
    if probe.is_file():
        facts['supplemental_transport_probe'] = load(probe)
    boundaries = source / 'boundary-probe.json'
    if boundaries.is_file():
        facts['supplemental_boundary_probe'] = load(boundaries)
    for row in report['journeys']:
        directory = source / row['id']
        item = {key: value for key, value in row.items() if key not in ('grades', 'setup', 'stages')}
        item['setup'] = {key: value for key, value in row['setup'].items() if key != 'clone_observations'}
        clone = row['setup'].get('clone_observations')
        if clone:
            item['setup']['clone'] = {key: clone[key] for key in ('status', 'trust')}
            item['setup']['clone_config_sha256'] = digest(directory / 'change/clone.json')
        item['stages'] = row['stages']
        item['grades'] = {stage: dict(acceptance=grade['acceptance'], public_exit_code=grade['public']['exit_code'],
                           useful_tests=grade.get('useful_tests', {}).get('rejects_seed'),
                           dispositions=grade.get('dispositions'), evaluation_seconds=grade['evaluation_seconds'])
                          for stage, grade in row['grades'].items()}
        item['evidence_sha256'] = {str(p.relative_to(directory)).replace('\\', '/'): digest(p)
                                  for stage in row['stages'] for p in (directory / stage).iterdir() if p.is_file()}
        facts['journeys'].append(item)
    for attempt in judged['attempts']:
        grade = attempt['grade']
        facts['review_attempts'].append(dict(id=attempt['id'], phase=attempt['phase'], block=attempt['block'],
            reversed=attempt['reversed'], candidates=attempt['candidates'],
            metrics={key: grade[key] for key in ('completed', 'seconds', 'total_seconds', 'usage', 'review_error',
                                                'runtime', 'weighted_scores', 'prompt_sha256') if key in grade}))
        bundle = reviews / attempt['id'] / 'bundle/bundle.json'
        facts['bundles'][attempt['id']] = dict(sha256=digest(bundle), data=load(bundle))
    blocks = defaultdict(dict)
    for row in report['journeys']:
        blocks[(row['model'], row['scenario'], row['repetition'])][row['condition']] = row
    for (model, scenario, repetition), block in sorted(blocks.items()):
        item = dict(model=model, scenario=scenario, repetition=repetition,
                    interrupted=any(row['interrupted_stages'] for row in block.values()), comparisons={})
        for other in ('plain', 'project'):
            candidate, baseline = block['tack'], block[other]
            item['comparisons'][other] = dict(
                accepted=[candidate['accepted'], baseline['accepted']],
                seconds_ratio=candidate['seconds']/baseline['seconds'],
                input_ratio=candidate['usage']['input_tokens']/baseline['usage']['input_tokens']
                if candidate['token_usage_complete'] and baseline['token_usage_complete'] else None,
                build_scores={condition: next((r['weighted'] for r in judged['scores'] if r['case'] == block[condition]['id']
                    and r['phase'] == 'build' and not r['reversed']), None) for condition in ('tack', other)},
                final_scores={condition: next((r['weighted'] for r in judged['scores'] if r['case'] == block[condition]['id']
                    and r['phase'] == 'final' and not r['reversed']), None) for condition in ('tack', other)})
        facts['paired'].append(item)
    return facts


def tables(facts):
    by_condition = defaultdict(list)
    for row in facts['journeys']:
        by_condition[(row['model'], row['condition'])].append(row)
    for (model, condition), rows in sorted(by_condition.items()):
        ids = {r['id'] for r in rows}
        print(model, condition, 'accepted', sum(r['accepted'] for r in rows), 'of', len(rows),
              'seconds', round(sum(r['seconds'] for r in rows), 3),
              'input', sum(r['usage']['input_tokens'] for r in rows),
              'complete_usage', all(r['token_usage_complete'] for r in rows))
        for phase in ('build', 'final'):
            grades = [r['weighted'] for r in facts['reviews'] if r['case'] in ids and r['phase'] == phase and not r['reversed']]
            print(phase, 'review_n', len(grades), 'mean', round(statistics.mean(grades), 3) if grades else None)
        for stage in ('setup', 'build', 'change', 'review', 'repair'):
            values = [r['stages'][stage] for r in rows if stage in r['stages']]
            print(stage, 'sessions', len(values), 'seconds', round(sum(s['seconds'] for s in values), 3),
                  'input', sum(s['input_tokens'] for s in values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('reviews', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    facts = publish(args.source, args.reviews)
    args.output.write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')
    tables(facts)


if __name__ == '__main__':
    main()
