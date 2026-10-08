#!/usr/bin/env python3
"""Bounded four-condition preflight and offline cost observations; no calls in dry-run."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import re
import threading

from quality import ROOT, digest, run, save, session
from value_fixture import PILOT_TASKS, request
from product_archive import create as create_product_archive

CONDITIONS = ('plain', 'project', 'current', 'lean')


def matrix(manifest):
    if manifest.get('conditions') != list(CONDITIONS) or manifest.get('tasks') != list(PILOT_TASKS):
        raise ValueError('preflight requires settings/shipment and all four conditions')
    if manifest.get('max_sessions') != 8 or type(manifest.get('concurrency')) is not int or not 1 <= manifest['concurrency'] <= 2:
        raise ValueError('preflight cap is eight sessions, at most two concurrent')
    if type(manifest.get('timeout_seconds')) is not int or not 1 <= manifest['timeout_seconds'] <= 600:
        raise ValueError('timeout must be 1..600 seconds')
    if not all(isinstance(manifest.get(k), str) and manifest[k] for k in ('model', 'effort', 'image')):
        raise ValueError('model, effort and image must be explicit')
    revisions = manifest.get('revisions', {})
    if set(revisions) != {'current', 'lean'} or not all(re.fullmatch('[0-9a-f]{40}', r) for r in revisions.values()):
        raise ValueError('pin current and lean full commit hashes')
    result = []
    for index, task in enumerate(PILOT_TASKS):
        order = list(CONDITIONS[index:] + CONDITIONS[:index])
        for condition in order:
            job = request(task, condition, manifest['model'], manifest['effort'], manifest['timeout_seconds'])
            result.append(dict(id=f'{task}-{condition}', task=task, condition=condition, repetition=1,
                               model=manifest['model'], prompt_sha256=hashlib.sha256(job['prompt'].encode()).hexdigest()))
    return result


def observations(source):
    groups = {}
    for path in sorted(source.glob('*/case.json')):
        case = json.loads(path.read_text(encoding='utf-8'))
        counts = Counter()
        transcript = path.parent / 'transcript.jsonl'
        if not transcript.exists():
            continue
        for line in transcript.read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            item = event.get('item', {})
            if event.get('type') != 'item.completed' or item.get('type') != 'command_execution':
                continue
            command = item.get('command', '')
            counts['commands'] += 1
            counts['output_characters'] += len(item.get('aggregated_output', ''))
            for category, pattern in {
                'checks': r'pytest|unittest|npm test|node --test|tack verify',
                'workflow_reads': r'SKILL\.md|/references/|AGENTS\.md|tack context',
                'git_writes': r'git (?:commit|add|switch|checkout)',
                'documentation': r'docs/|handoff|work/plans',
            }.items():
                counts[category] += bool(re.search(pattern, command))
        key = case['condition']
        groups.setdefault(key, Counter()).update(counts)
        groups[key]['sessions'] += 1
    return {'counts': {key: dict(value) for key, value in groups.items()},
            'limits': 'Overlapping command categories; not durations, causal attribution or injected-context tokens.'}


def reviews(source, destination, seed=20261008):
    """Prepare anonymous four-way bundles; mapping is outside the bundles."""
    from quality_fixture import TASKS
    from quality_review import production
    rng = random.Random(seed)
    mapping, jobs = {}, []
    for index, task in enumerate(PILOT_TASKS):
        order = list(CONDITIONS)
        rng.shuffle(order)
        name = f'review-{index + 1:02}'
        bundle = destination / name / 'bundle'
        bundle.mkdir(parents=True)
        candidates = {label: production(source / f'{task}-{condition}' / 'repo', task)
                      for label, condition in zip('ABCD', order)}
        data = dict(request=TASKS[task]['prompt'], contract=TASKS[task]['contract'],
                    original={p: c for p, c in TASKS[task]['files'].items() if not p.startswith('tests/')},
                    candidates=candidates)
        save(bundle / 'bundle.json', data)
        numbered = []
        for label, files in [('Original', data['original']), *candidates.items()]:
            for path, content in files.items():
                numbered.append(f'{label}: {path}\n' + '\n'.join(f'{i}: {line}' for i, line in enumerate(content.splitlines(), 1)))
        (bundle / 'code.txt').write_text('\n\n'.join(numbered), encoding='utf-8')
        mapping[name] = dict(zip('ABCD', order))
        jobs.append(dict(id=name, bundle=str(bundle)))
    save(destination / 'mapping.json', mapping)
    save(destination / 'jobs.json', jobs)
    return jobs


def execute(args, manifest, cases):
    args.output.mkdir(parents=True)
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'order.json', cases)
    save(args.output / 'controller.json', {p.name: digest(p) for p in (ROOT / 'evals').glob('*.py')})
    archives = {}
    for condition, revision in manifest['revisions'].items():
        archives[condition] = args.output / (condition + '.tar')
        create_product_archive(ROOT, revision, archives[condition])
    save(args.output / 'products.json', {k: digest(v) for k, v in archives.items()})
    save(args.output / 'image.json', json.loads(run(['docker', 'image', 'inspect', manifest['image']]))[0]['Id'])
    stopped = threading.Event()

    def one(case):
        if stopped.is_set():
            return {**case, 'skipped': 'infrastructure failure'}
        job = request(case['task'], case['condition'], manifest['model'], manifest['effort'], manifest['timeout_seconds'])
        directory = args.output / case['id']
        try:
            result = session(manifest['image'], job, directory, args.auth, archives.get(case['condition']))
            if result.get('infrastructure_error'):
                stopped.set()
        except Exception as error:
            stopped.set()
            result = dict(completed=False, infrastructure_error=str(error))
        directory.mkdir(exist_ok=True)
        save(directory / 'case.json', {**case, 'result': result})
        print(case['id'], result.get('completed'), result.get('seconds'), flush=True)
        return {**case, **result}

    with ThreadPoolExecutor(max_workers=manifest['concurrency']) as pool:
        results = list(pool.map(one, cases))
    save(args.output / 'results.json', results)
    return int(stopped.is_set() or not all(item.get('completed') for item in results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, nargs='?')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--observe', type=Path)
    parser.add_argument('--prepare-reviews', type=Path)
    args = parser.parse_args()
    if args.observe:
        print(json.dumps(observations(args.observe), indent=2))
        return 0
    if args.prepare_reviews:
        if not args.output:
            parser.error('--prepare-reviews requires a new --output')
        args.output.mkdir(parents=True)
        print(json.dumps(reviews(args.prepare_reviews, args.output), indent=2))
        return 0
    if not args.manifest:
        parser.error('provide a manifest')
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    cases = matrix(manifest)
    if args.dry_run:
        print(json.dumps(cases, indent=2))
        return 0
    if not args.output or not args.auth or not args.auth.is_file():
        parser.error('execution requires --auth and a new --output')
    args.output = args.output.resolve()
    return execute(args, manifest, cases)


if __name__ == '__main__':
    raise SystemExit(main())
