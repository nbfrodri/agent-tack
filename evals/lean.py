"""Bounded small-core comparison reusing the existing isolated runner and graders."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import threading
import uuid

from quality import ROOT, digest, run, save, session
from quality_fixture import TASKS, test_command
from quality_review import grade as review_grade, prepare as prepare_reviews
from product_archive import create as archive

CONDITIONS = ('plain', 'current', 'improved')


def guide(task):
    return ('# Project\n\nRead docs/contract.md for product behavior and docs/architecture.md for structure.\n'
            'Keep changes focused, preserve existing interfaces and follow the current code style.\n'
            'Work on a feature branch. Use a regression check for changed behavior and run relevant checks.\n'
            'Update documentation made inaccurate. Use Conventional Commits without AI attribution.\n'
            'Command: `' + ' '.join(test_command(task)) + '`.\n')


def matrix(manifest):
    if (manifest.get('models') != ['gpt-6-luna', 'gpt-6.1-sol'] or manifest.get('effort') != 'medium'
            or manifest.get('reviewer') != 'gpt-6-astra' or manifest.get('review_timeout') != 300):
        raise ValueError('use the predeclared models, medium effort and 300-second review budget')
    for revision in manifest['revisions'].values():
        if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
            raise ValueError('pin full product revisions')
    if set(manifest['revisions']) != {'current', 'improved'} or not manifest['image'].startswith('sha256:') or len(manifest['image']) != 71:
        raise ValueError('pin both product revisions and the image digest')
    blocks = [(model, task, repetition) for model in manifest['models']
              for task in ('shipment', 'settings') for repetition in (1, 2)]
    random.Random(manifest['seed']).shuffle(blocks)
    return [dict(id=f'{i}-{condition}', model=model, task=task, repetition=repetition, condition=condition)
            for i, (model, task, repetition) in enumerate(blocks)
            for condition in CONDITIONS[i % 3:] + CONDITIONS[:i % 3]]


def acceptance(image, snapshot, task):
    container = 'tack-lean-grade-' + uuid.uuid4().hex[:12]
    created = False
    try:
        run(['docker', 'create', '--name', container, '--network', 'none', image, 'sleep', 'infinity'])
        created = True
        run(['docker', 'start', container])
        run(['docker', 'cp', snapshot, container + ':/home/dev/repo'])
        for name in ('quality_grade.py', 'quality_fixture.py'):
            run(['docker', 'cp', ROOT / 'evals' / name, container + ':/home/dev/' + name])
        expression = 'import json; from pathlib import Path; from quality_grade import grade; print(json.dumps(grade(Path("/home/dev/repo"), ' + repr(task) + ')))'
        return json.loads(run(['docker', 'exec', container, 'python3', '-c', expression], timeout=150))
    finally:
        if created:
            run(['docker', 'rm', '-f', container])


def coding(case, args, manifest, products, stopped):
    if stopped.is_set():
        return {**case, 'skipped': 'infrastructure failure; no selective retry'}
    target = args.output / case['id']
    result = dict(case)
    try:
        job = dict(kind='code', task=case['task'], model=case['model'], effort='medium', timeout_seconds=300,
                   prompt=TASKS[case['task']]['prompt'], test_command=test_command(case['task']),
                   project_guide=guide(case['task']))
        result['session'] = session(manifest['image'], job, target, args.auth, products.get(case['condition']))
        observed = result['session'].get('runtime', {})
        if (result['session'].get('infrastructure_error') or observed.get('models') != [case['model']]
                or observed.get('efforts') != ['medium']):
            raise ValueError('missing/mismatched runtime or infrastructure failure')
        transcript = (target / 'transcript.jsonl').read_text(encoding='utf-8')
        if any(json.loads(line).get('type') == 'turn.failed' for line in transcript.splitlines() if line.strip()):
            raise ValueError('provider failure: preserve attempt and stop unscheduled work')
        result['grade'] = acceptance(manifest['image'], target / 'repo', case['task'])
    except Exception as error:
        stopped.set()
        result['infrastructure_error'] = str(error)
    target.mkdir(exist_ok=True)
    save(target / 'case.json', case)
    save(target / 'result.json', result)
    print(case['id'], result.get('session', {}).get('seconds'), result.get('grade', {}).get('acceptance'), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reviews', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    cases = matrix(manifest)
    if args.dry_run:
        print(json.dumps(cases, indent=2))
        return 0
    if not args.auth or not args.auth.is_file() or not args.output:
        parser.error('provide auth and a new output directory')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'controller.json', {p.name: digest(p) for p in (ROOT / 'evals').glob('*.py')})
    if args.reviews:
        jobs = prepare_reviews(args.reviews, args.output, manifest['seed'])
        # One blinded review per complete block; the existing preparer also writes reversed bundles.
        jobs = [job for job in jobs if job['id'].endswith('-1')]
        if len(jobs) != 8:
            raise ValueError('all eight complete triplets are required')
        save(args.output / 'executed-order.json', jobs)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda job: review_grade(job, args, manifest), jobs))
    else:
        products = {}
        for condition, revision in manifest['revisions'].items():
            products[condition] = args.output / (condition + '.tar')
            archive(ROOT, revision, products[condition])
        save(args.output / 'products.json', {key: digest(path) for key, path in products.items()})
        save(args.output / 'order.json', cases)
        stopped = threading.Event()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda case: coding(case, args, manifest, products, stopped), cases))
    save(args.output / 'results.json', results)
    return int(any(r.get('infrastructure_error') or r.get('review_error') or r.get('skipped') for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
