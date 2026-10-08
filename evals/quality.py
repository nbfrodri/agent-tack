#!/usr/bin/env python3
"""Finite Codex comparisons; each session gets a separate container without host mounts."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile
import threading
import time
import uuid

from adoption import transcript_metrics
from quality_fixture import SETUP_PROMPT, TASKS, seed, test_command

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ['plain', 'current', 'improved']


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(arguments, timeout=120):
    result = subprocess.run([str(x) for x in arguments], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{arguments[0]} failed ({result.returncode}): {result.stderr[-2000:]}')
    return result.stdout.strip()


def matrix(manifest, stage):
    if manifest.get('conditions') != CONDITIONS or len(manifest.get('models', [])) != 2:
        raise ValueError('expected two explicit models and plain/current/improved conditions')
    for key in ('repetitions', 'concurrency', 'implementation_timeout', 'review_timeout', 'max_sessions', 'seed'):
        if type(manifest.get(key)) is not int or manifest[key] < 1:
            raise ValueError(f'{key} must be a positive integer')
    if manifest['concurrency'] > 2 or manifest['implementation_timeout'] > 600 or manifest['review_timeout'] > 300:
        raise ValueError('session concurrency or timeout exceeds the protocol')
    if manifest['tasks'] != ['window', 'shipment', 'settings', 'assignments'] or manifest['repetitions'] != 2:
        raise ValueError('this protocol fixes four tasks and two repetitions')
    if not all(isinstance(m, str) and m for m in manifest['models']) or len(set(manifest['models'])) != 2:
        raise ValueError('implementer models must be distinct explicit strings')
    if not isinstance(manifest.get('reviewer'), str) or not manifest['reviewer'] or manifest.get('effort') != 'medium':
        raise ValueError('a reviewer and medium effort must be explicit')
    if manifest['max_sessions'] != 93:
        raise ValueError('the protocol caps the complete pilot, setup, coding and reviews at 93 sessions')
    if stage == 'pilot':
        blocks = [(0, 'pilot', 1)]
    elif stage == 'setup':
        blocks = [(m, 'settings', r) for m in range(2) for r in (1, 2)]
    elif stage == 'coding':
        blocks = [(m, t, r) for m in range(2) for t in manifest['tasks'] for r in (1, 2)]
    else:
        raise ValueError('unknown stage')
    random.Random(manifest['seed']).shuffle(blocks)
    result = []
    for i, (model, task, repetition) in enumerate(blocks):
        conditions = CONDITIONS[1:] if stage == 'setup' else CONDITIONS
        ordered = conditions[i % len(conditions):] + conditions[:i % len(conditions)]
        for condition in ordered:
            result.append({'id': f'm{model}-{task}-{repetition}-{condition}', 'model': manifest['models'][model],
                           'task': task, 'repetition': repetition, 'condition': condition})
    return result


def session(image, job, output, auth, product=None, bundle=None, schema=None, launch=run):
    """Only copied inputs enter the container; identity mappings and other outputs stay outside."""
    output.mkdir()
    container = 'tack-quality-' + uuid.uuid4().hex[:16]
    created = False
    started = time.monotonic()
    try:
        launch(['docker', 'create', '--name', container, '--security-opt', 'seccomp=unconfined', image, 'sleep', 'infinity'])
        created = True
        launch(['docker', 'start', container])
        mounts = json.loads(launch(['docker', 'inspect', container, '--format', '{{json .Mounts}}']))
        if mounts:
            raise RuntimeError('isolation failure: unexpected container mounts')
        with tempfile.TemporaryDirectory(prefix='tack-quality-input-') as temp:
            staging = Path(temp)
            save(staging / 'job.json', job)
            launch(['docker', 'cp', staging / 'job.json', container + ':/home/dev/job.json'])
            launch(['docker', 'cp', ROOT / 'evals/quality_worker.py', container + ':/home/dev/worker.py'])
            launch(['docker', 'cp', auth, container + ':/home/dev/auth.json'])
            if bundle:
                launch(['docker', 'cp', bundle, container + ':/home/dev/work'])
                launch(['docker', 'cp', schema, container + ':/home/dev/schema.json'])
            else:
                fixture = staging / 'work'
                files = seed(job['task'], fixture)
                save(output / 'fixture-hashes.json', {name: hashlib.sha256(text.encode()).hexdigest() for name, text in files.items()})
                launch(['docker', 'cp', fixture, container + ':/home/dev/work'])
            if product:
                launch(['docker', 'cp', product, container + ':/home/dev/product.tar'])
                launch(['docker', 'exec', container, 'mkdir', '/home/dev/product'])
                launch(['docker', 'exec', container, 'tar', '-xf', '/home/dev/product.tar', '-C', '/home/dev/product'])
            launch(['docker', 'exec', '--user', 'root', container, 'chown', '-R', 'dev:dev',
                    '/home/dev/work', '/home/dev/auth.json', '/home/dev/job.json', '/home/dev/worker.py'])
            launch(['docker', 'exec', container, 'python3', '/home/dev/worker.py'], timeout=job['timeout_seconds'] + 300)
            launch(['docker', 'cp', container + ':/home/dev/evidence/.', output])
        result = json.loads((output / 'session.json').read_text(encoding='utf-8'))
        if (output / 'transcript.jsonl').exists():
            result.update(transcript_metrics(output / 'transcript.jsonl'))
        result['container_mounts'] = mounts
        result['total_seconds'] = round(time.monotonic() - started, 3)
        save(output / 'session.json', result)
        return result
    finally:
        if created:
            launch(['docker', 'rm', '-f', container], timeout=30)


def product_archives(manifest, destination):
    result = {}
    for condition in ('current', 'improved'):
        revision = manifest['revisions'][condition]
        resolved = run(['git', '-C', ROOT, 'rev-parse', '--verify', revision + '^{commit}'])
        if revision != resolved:
            raise ValueError('product revisions must be full commit hashes')
        archive = destination / (condition + '.tar')
        run(['git', '-C', ROOT, 'archive', '--format=tar', '--output', archive, resolved])
        result[condition] = archive
    return result


def execute_case(case, args, manifest, archives, stopped):
    directory = args.output / case['id']
    if stopped.is_set():
        return {'id': case['id'], 'skipped': 'batch stopped after an infrastructure failure'}
    job = {'kind': 'setup' if args.stage == 'setup' else 'code', 'task': case['task'],
           'model': case['model'], 'effort': manifest['effort'], 'timeout_seconds': manifest['implementation_timeout'],
           'prompt': SETUP_PROMPT if args.stage == 'setup' else TASKS[case['task']]['prompt'],
           'test_command': test_command(case['task'])}
    try:
        result = session(manifest['image'], job, directory, args.auth, archives.get(case['condition']))
        if result.get('infrastructure_error'):
            stopped.set()
    except Exception as error:
        stopped.set()
        result = {'completed': False, 'infrastructure_error': str(error)}
    directory.mkdir(exist_ok=True)
    save(directory / 'case.json', {**case, 'prompt_sha256': hashlib.sha256(job['prompt'].encode()).hexdigest(), 'result': result})
    print(case['id'], result.get('completed'), result.get('seconds'), flush=True)
    return {'id': case['id'], **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--stage', choices=('pilot', 'setup', 'coding'), required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    cases = matrix(manifest, args.stage)
    if args.dry_run:
        print(json.dumps(cases, indent=2))
        return 0
    if not args.auth or not args.auth.is_file() or not args.output:
        parser.error('execution requires --auth and a new --output directory')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'order.json', cases)
    save(args.output / 'controller.json', {p.name: digest(p) for p in (ROOT / 'evals').glob('quality*.py')})
    save(args.output / 'image.json', json.loads(run(['docker', 'image', 'inspect', manifest['image']]))[0]['Id'])
    archives = product_archives(manifest, args.output)
    save(args.output / 'products.json', {key: digest(path) for key, path in archives.items()})
    stopped = threading.Event()
    with ThreadPoolExecutor(max_workers=manifest['concurrency']) as pool:
        futures = [pool.submit(execute_case, case, args, manifest, archives, stopped) for case in cases]
        results = [future.result() for future in as_completed(futures)]
    save(args.output / 'results.json', results)
    return 1 if stopped.is_set() else 0


if __name__ == '__main__':
    raise SystemExit(main())
