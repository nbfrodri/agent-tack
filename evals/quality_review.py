#!/usr/bin/env python3
"""Prepare anonymous production-only bundles and validate independent agent judgments."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import re
import shutil

from quality import ROOT, digest, matrix, save, session
from quality_fixture import TASKS

WEIGHTS = {'responsibilities': .25, 'readability': .20, 'robustness': .20,
           'changeability': .15, 'simplicity': .10, 'consistency': .10}


def production(root, task):
    """Include new production helpers, not only files in the initial fixture."""
    javascript = task in ('window', 'shipment')
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and p.is_relative_to(root)):
            raise ValueError('review input contains a symlink')
        if not path.is_file() or any(p.startswith('.') or p in ('tests', 'test', 'docs', 'work', 'node_modules', '__pycache__') for p in relative.parts):
            continue
        if path.suffix not in (('.js', '.mjs', '.cjs') if javascript else ('.py',)) or re.search(r'(?:^test_|[._]test[._]|_test\.)', path.name):
            continue
        if path.stat().st_size > 131072:
            raise ValueError('production file exceeds review budget')
        result[relative.as_posix()] = path.read_text(encoding='utf-8')
    if sum(len(value.encode()) for value in result.values()) > 262144:
        raise ValueError('production snapshot exceeds review budget')
    if not result:
        raise ValueError('no reviewable production files')
    return result


def prepare(source, destination, seed):
    cases = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(source.glob('*/case.json'))]
    groups = {}
    for case in cases:
        key = (case['model'], case['task'], case['repetition'])
        groups.setdefault(key, []).append(case)
    rng = random.Random(seed)
    blocks = list(groups.values())
    rng.shuffle(blocks)
    mapping, jobs = {}, []
    for index, cases in enumerate(blocks):
        if {case['condition'] for case in cases} != {'plain', 'current', 'improved'} or len(cases) != 3:
            raise ValueError('review needs every attempt in each matched triplet')
        task = cases[0]['task']
        ordered = list(cases)
        rng.shuffle(ordered)
        for repeat in (1, 2):
            review_id = f'review-{index + 1:02}-{repeat}'
            bundle = destination / review_id / 'bundle'
            bundle.mkdir(parents=True)
            current = ordered if repeat == 1 else list(reversed(ordered))
            labels = rng.sample(['A', 'B', 'C', 'D', 'E', 'F'], 3)
            reference = {name: content for name, content in TASKS[task]['files'].items() if not name.startswith('tests/')}
            candidates = {}
            for label, case in zip(labels, current):
                candidates[label] = production(source / case['id'] / 'repo', task)
            data = {'request': TASKS[task]['prompt'], 'contract': TASKS[task]['contract'],
                    'original': reference, 'candidates': candidates}
            save(bundle / 'bundle.json', data)
            # Numbered source allows precise citations without exposing Git or run identity.
            with (bundle / 'code.txt').open('w', encoding='utf-8', newline='\n') as stream:
                for label, files in [('Original', reference), *candidates.items()]:
                    for name, text in files.items():
                        stream.write(f'\n{label}: {name}\n')
                        stream.writelines(f'{n}: {line}\n' for n, line in enumerate(text.splitlines(), 1))
            mapping[review_id] = {label: case['id'] for label, case in zip(labels, current)}
            jobs.append({'id': review_id, 'bundle': str(bundle.resolve()), 'bundle_sha256': digest(bundle / 'bundle.json')})
    save(destination / 'private-label-map.json', mapping)
    save(destination / 'order.json', jobs)
    return jobs


def validate(review, bundle):
    expected = set(bundle['candidates'])
    if not isinstance(review, dict) or set(review) != {'candidates', 'preferred', 'uncertainty', 'origin_hints'}:
        raise ValueError('invalid review fields')
    if not isinstance(review['candidates'], list) or len(review['candidates']) != len(expected):
        raise ValueError('every candidate needs one grade')
    seen, totals = set(), {}
    for candidate in review['candidates']:
        if not isinstance(candidate, dict) or set(candidate) != {'id', 'dimensions', 'findings'}:
            raise ValueError('invalid candidate fields')
        label = candidate['id']
        if label not in expected or label in seen:
            raise ValueError('unknown or duplicate candidate')
        seen.add(label)
        dimensions = candidate['dimensions']
        if not isinstance(dimensions, dict) or set(dimensions) != set(WEIGHTS):
            raise ValueError('all rubric dimensions are required')
        total = 0
        for name, entry in dimensions.items():
            if not isinstance(entry, dict) or set(entry) != {'score', 'path', 'line', 'reason'}:
                raise ValueError('dimension needs a score and cited evidence')
            score = entry['score']
            if type(score) not in (int, float) or not 0 <= score <= 10:
                raise ValueError('scores must be finite numbers from 0 to 10')
            cite(entry, bundle['candidates'][label])
            total += WEIGHTS[name] * score
        if not isinstance(candidate['findings'], list):
            raise ValueError('findings must be a list')
        for finding in candidate['findings']:
            if set(finding) != {'severity', 'path', 'line', 'reason'} or finding['severity'] not in ('critical', 'major', 'minor', 'note'):
                raise ValueError('invalid finding')
            cite(finding, bundle['candidates'][label])
        totals[label] = round(total, 3)
    preferred = review['preferred']
    if not isinstance(preferred, list) or not preferred or any(p not in expected for p in preferred) or len(set(preferred)) != len(preferred):
        raise ValueError('preference must name one or more distinct candidates')
    if not all(isinstance(review[key], str) for key in ('uncertainty', 'origin_hints')):
        raise ValueError('uncertainty and origin hints must be recorded')
    return totals


def cite(entry, files):
    if entry['path'] not in files or type(entry['line']) is not int or not 1 <= entry['line'] <= len(files[entry['path']].splitlines()):
        raise ValueError('citation must identify an existing candidate path and line')
    if not isinstance(entry['reason'], str) or not entry['reason'].strip():
        raise ValueError('citation needs a reason')


def grade(job, args, manifest):
    directory = args.output / job['id']
    prompt = (ROOT / 'evals/prompts/code-quality-review.md').read_text(encoding='utf-8') + '\nRead bundle.json and code.txt in this directory.'
    request = {'kind': 'review', 'model': manifest['reviewer'], 'effort': manifest['effort'],
               'timeout_seconds': manifest['review_timeout'], 'prompt': prompt}
    try:
        result = session(manifest['image'], request, directory / 'evidence', args.auth,
                         bundle=Path(job['bundle']), schema=ROOT / 'evals/schemas/code-quality-review.json')
        raw = json.loads((directory / 'evidence/review.json').read_text(encoding='utf-8'))
        totals = validate(raw, json.loads((directory / 'bundle/bundle.json').read_text(encoding='utf-8')))
        result['weighted_scores'] = totals
    except Exception as error:
        result = {'completed': False, 'review_error': str(error)}
    save(directory / 'grade.json', result)
    print(job['id'], result.get('completed'), result.get('weighted_scores'), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    matrix(manifest, 'coding')
    args.output.mkdir()
    jobs = prepare(args.source, args.output, manifest['seed'])
    if len(jobs) not in (2, 32):
        raise ValueError('expected two pilot or 32 confirmation reviews')
    if args.prepare_only:
        return 0
    if not args.auth or not args.auth.is_file():
        parser.error('execution requires --auth')
    with ThreadPoolExecutor(max_workers=manifest['concurrency']) as pool:
        results = list(pool.map(lambda job: grade(job, args, manifest), jobs))
    save(args.output / 'results.json', results)
    # Review bundles and grades are safe to inspect before revealing the separate mapping.
    review_copy = args.output / 'blinded'
    review_copy.mkdir()
    for job in jobs:
        target = review_copy / job['id']
        shutil.copytree(args.output / job['id'] / 'bundle', target)
        raw = args.output / job['id'] / 'evidence/review.json'
        if raw.exists():
            shutil.copyfile(raw, target / 'review.json')
    return 0 if all(result.get('completed') and 'weighted_scores' in result for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
