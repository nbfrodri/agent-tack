"""Publish complete component outcomes without raw transcripts or authentication files."""
import argparse
import json
from pathlib import Path
import re
import statistics

from lean_footprint import measure
from quality import digest, save
from quality_review import production

LABELS = {'plain': 'Short guide', 'current': 'Previous tack', 'improved': 'Small core'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def collect(source, reviews):
    manifest = read(source / 'manifest.json')
    mapping = read(reviews / 'private-label-map.json')
    judgments, scores = [], {}
    for job in read(reviews / 'executed-order.json'):
        directory = reviews / job['id']
        grade = read(directory / 'grade.json')
        bundle = read(directory / 'bundle/bundle.json')
        raw = read(directory / 'evidence/review.json') if (directory / 'evidence/review.json').exists() else None
        judgments.append(dict(id=job['id'], bundle=bundle, review=raw, result=grade,
                              mapping=mapping[job['id']], bundle_sha256=digest(directory / 'bundle/bundle.json')))
        for label, score in grade.get('weighted_scores', {}).items():
            scores[mapping[job['id']][label]] = score
    cases = []
    for result in read(source / 'results.json'):
        directory = source / result['id']
        entry = dict(result)
        entry['quality_score'] = scores.get(result['id'])
        if directory.exists() and (directory / 'git.json').exists():
            git = read(directory / 'git.json')
            history = git['history']['stdout']
            subjects = [match.group(1) for block in re.split(r'^commit [0-9a-f]+$', history, flags=re.M)
                        if (match := re.search(r'^    (\S[^\n]*)$', block, re.M))]
            entry['process'] = dict(commits=subjects,
                conventional=bool(subjects) and all(re.match(r'^[a-z]+(?:\([^)]+\))?!?: .+', title) for title in subjects),
                attribution=bool(re.search(r'Co-authored-by:|Generated.by', history, re.I)),
                status=git['status']['stdout'],
                test_sensitivity=result.get('grade', {}).get('seed_regression_probe'),
                note='No commit is reported as absent, not a conventional commit success. TDD requires separate transcript inspection.')
            entry['production'] = production(directory / 'repo', result['task'])
            entry['public_tests'] = read(directory / 'public-tests.json')
        install = directory / 'install.json'
        entry['install_seconds'] = read(install)['seconds'] if install.exists() else None
        cases.append(entry)
    return dict(version=1, manifest=manifest, products=read(source / 'products.json'),
                controller=read(source / 'controller.json'),
                review_controller=read(reviews / 'controller.json'),
                posthoc=read(source / 'posthoc.json') if (source / 'posthoc.json').exists() else None,
                footprint=[measure(manifest['revisions'][key]) for key in ('current', 'improved')],
                cases=cases, reviews=judgments)


def summary(facts):
    lines = ['| Model | Configuration | Acceptance | Seconds | Input (cached included) | Output | Quality / 10 | Sensitive tests |',
             '| --- | --- | --- | ---: | ---: | ---: | ---: | --- |']
    for model in facts['manifest']['models']:
        for condition, label in LABELS.items():
            rows = [c for c in facts['cases'] if c['model'] == model and c['condition'] == condition]
            accepted = sum(c.get('grade', {}).get('acceptance', {}).get('passed', False)
                           and c.get('public_tests', {}).get('exit_code') == 0 for c in rows)
            sensitive = sum(c.get('grade', {}).get('seed_regression_probe', {}).get('rejected_original_defect', False) for c in rows)
            seconds = sum(c.get('session', {}).get('seconds') or 0 for c in rows)
            usages = [c.get('session', {}).get('usage', {}) for c in rows]
            input_tokens = sum(u['input_tokens'] for u in usages) if all('input_tokens' in u for u in usages) else 'unknown'
            output_tokens = sum(u['output_tokens'] for u in usages) if all('output_tokens' in u for u in usages) else 'unknown'
            quality = [c['quality_score'] for c in rows if c['quality_score'] is not None]
            score = f'{statistics.mean(quality):.2f}' if len(quality) == len(rows) else 'incomplete'
            lines.append(f'| {model} | {label} | {accepted}/{len(rows)} | {seconds:.1f} | {input_tokens} | {output_tokens} | {score} | {sensitive}/{len(rows)} |')
    lines += ['', 'Seconds sum model turns, including failed attempts where measured; installation and review are separate. Missing usage stays unknown. Four attempts per cell are not a population estimate.', '',
              '| Matched block | Guide seconds | Previous seconds | Core seconds | Guide input | Previous input | Core input |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for index in range(8):
        rows = {c['condition']: c for c in facts['cases'] if c['id'].split('-')[0] == str(index)}
        first = next(iter(rows.values()))
        title = f"{first['model']} / {first['task']} / {first['repetition']}"
        times = [str(rows[k].get('session', {}).get('seconds', 'unknown')) for k in LABELS]
        tokens = [str(rows[k].get('session', {}).get('usage', {}).get('input_tokens', 'unknown')) for k in LABELS]
        lines.append('| ' + ' | '.join([title, *times, *tokens]) + ' |')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('reviews', type=Path)
    parser.add_argument('--facts', type=Path, required=True)
    parser.add_argument('--table', type=Path, required=True)
    args = parser.parse_args()
    facts = collect(args.source, args.reviews)
    save(args.facts, facts)
    args.table.write_text(summary(facts), encoding='utf-8', newline='\n')
