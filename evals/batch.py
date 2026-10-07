#!/usr/bin/env python3
"""Execute a finite experiment manifest; dry-run and resume never consume extra runs."""
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time
import threading

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = {'new-project', 'bug-fix', 'release', 'vague-requirement', 'conventions', 'attachments', 'search',
             'event-routing', 'project-capabilities', 'capability-existing', 'capability-trivial',
             'capability-review', 'capability-role', 'capability-nodelegation', 'capability-sequential'}
CONDITIONS = {'baseline', 'auto', 'lite', 'standard', 'strict'}
STOP = threading.Event()


def positive(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def expand(manifest):
    if not isinstance(manifest, dict) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', str(manifest.get('batch_id', ''))):
        raise ValueError('batch_id must be a short lowercase slug')
    repetitions = manifest.get('repetitions')
    if set(manifest) - {'batch_id', 'seed', 'repetitions', 'scenarios', 'conditions', 'runtimes', 'limits', 'variant', 'skill_groups'}:
        raise ValueError('unknown manifest fields')
    if manifest.get('variant', 'primary') not in ('primary', 'held-out'):
        raise ValueError('variant must be primary or held-out')
    groups = manifest.get('skill_groups', '')
    if not isinstance(groups, str) or groups and any(g not in ('all', 'core', 'process', 'stack') for g in groups.split(',')):
        raise ValueError('invalid skill_groups')
    limits = manifest.get('limits', {})
    if not positive(repetitions) or not isinstance(limits, dict) or not all(positive(limits.get(k)) for k in ('max_runs', 'timeout_seconds', 'concurrency')):
        raise ValueError('positive repetitions, max_runs, timeout_seconds and concurrency are required')
    if limits['concurrency'] > 8:
        raise ValueError('concurrency cannot exceed 8')
    for key in ('max_cost_usd', 'estimated_cost_per_run_usd'):
        value = limits.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0):
            raise ValueError(f'{key} must be a positive finite amount')
    if 'max_cost_usd' in limits and 'estimated_cost_per_run_usd' not in limits:
        raise ValueError('a spend budget needs an explicit per-run estimate; it is not a hard provider billing cap')
    for key, allowed in [('scenarios', SCENARIOS), ('conditions', CONDITIONS)]:
        values = manifest.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or v not in allowed for v in values) or len(set(values)) != len(values):
            raise ValueError(f'invalid or duplicate {key}')
    runtimes = manifest.get('runtimes')
    if not isinstance(runtimes, list) or not runtimes:
        raise ValueError('runtimes must be a nonempty list')
    for runtime in runtimes:
        if not isinstance(runtime, dict) or runtime.get('provider') not in ('claude', 'codex') or not isinstance(runtime.get('model'), str) or not runtime['model'].strip():
            raise ValueError('each runtime needs a provider and explicit model')
        if runtime.get('effort') is not None:
            raise ValueError('effort selection is not implemented; omit it instead of recording an unapplied setting')
    if len({json.dumps(r, sort_keys=True) for r in runtimes}) != len(runtimes):
        raise ValueError('duplicate runtimes')
    if not isinstance(manifest.get('seed'), int) or isinstance(manifest.get('seed'), bool):
        raise ValueError('an integer ordering seed is required')
    runs = []
    for index, runtime in enumerate(runtimes):
        for scenario in manifest['scenarios']:
            for condition in manifest['conditions']:
                for rep in range(1, repetitions + 1):
                    runs.append(dict(run_id=f'r{index}-{scenario}-{condition}-{rep}', runtime=runtime,
                                     scenario=scenario, condition=condition, repetition=rep))
    if len(runs) > limits['max_runs']:
        raise ValueError(f"manifest needs {len(runs)} runs, exceeding max_runs={limits['max_runs']}")
    if limits.get('max_cost_usd') and len(runs) * limits['estimated_cost_per_run_usd'] > limits['max_cost_usd']:
        raise ValueError('estimated batch spend exceeds max_cost_usd; reduce the matrix')
    random.Random(manifest['seed']).shuffle(runs)
    return runs


def prepare(path, manifest, source):
    endpoints = {key: os.environ.get(key) for key in ('ANTHROPIC_BASE_URL', 'OPENAI_BASE_URL')}
    identity = dict(manifest=manifest, source_sha256=source,
                    environment_sha256=hashlib.sha256(json.dumps(endpoints, sort_keys=True).encode()).hexdigest())
    if path.exists():
        saved = path / 'batch.json'
        if not saved.is_file() or json.loads(saved.read_text(encoding='utf-8')) != identity:
            raise ValueError('output belongs to a different manifest/source or an incomplete initialization')
    else:
        path.mkdir(parents=True)
        (path / 'batch.json').write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'evals' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def execute(run, path, manifest):
    out = path / run['run_id']
    state = path / (run['run_id'] + '.json')
    if state.exists():
        saved = json.loads(state.read_text(encoding='utf-8'))
        if saved.get('run') == run and saved.get('finished') and (out / run['scenario'] / f"{run['condition']}-{run['repetition']}" / 'metrics.json').is_file():
            return saved
        raise ValueError(f"incomplete or mismatched run: {run['run_id']}; retain it and choose a new batch ID")
    if out.exists():
        raise ValueError(f"unfinished output: {out}; choose a new batch ID")
    out.mkdir()
    env = dict(os.environ, EVALS_OUT=str(out), EVALS_PROVIDER=run['runtime']['provider'],
               EVALS_MODEL=run['runtime']['model'], EVALS_BATCH_ID=manifest['batch_id'],
               EVALS_RUN_ID=run['run_id'], EVALS_TIMEOUT_SECONDS=str(manifest['limits']['timeout_seconds']),
               EVALS_VARIANT=manifest.get('variant', 'primary'), EVALS_SKILL_GROUPS=manifest.get('skill_groups', ''))
    started = time.monotonic()
    with (out / 'runner.log').open('w', encoding='utf-8') as stream:
        process = subprocess.Popen(['bash', str(ROOT / 'evals/run.sh'), run['scenario'], run['condition'], str(run['repetition'])],
                                   env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = started + manifest['limits']['timeout_seconds']
            while True:
                if STOP.is_set():
                    raise KeyboardInterrupt
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(process.args, manifest['limits']['timeout_seconds'])
                try:
                    rc = process.wait(timeout=min(1, remaining))
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        raise
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            rc = 124
        except BaseException:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    directory = out / run['scenario'] / f"{run['condition']}-{run['repetition']}"
    directory.mkdir(parents=True, exist_ok=True)
    if not (directory / 'run.txt').exists() or rc == 124:
        (directory / 'run.txt').write_text(f'exit={rc} seconds={int(time.monotonic() - started)}\n', encoding='utf-8')
    metrics = load('grade').grade(directory)
    result = dict(run=run, finished=True, exit_code=rc, cost_usd=metrics.get('cost_usd'))
    state.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'evals/out')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    runs = expand(manifest)
    limits = manifest['limits']
    print(f"{len(runs)} runs; concurrency {limits['concurrency']}; timeout {limits['timeout_seconds']}s each")
    estimate = limits.get('estimated_cost_per_run_usd')
    print(f'Estimated spend: ${len(runs) * estimate:.2f}' if estimate else 'Spend unknown; run count and timeout are bounded.')
    if args.dry_run:
        for run in runs:
            print(run['run_id'], run['runtime']['provider'], run['runtime']['model'])
        return 0
    if any('<' in runtime['model'] for runtime in manifest['runtimes']):
        raise ValueError('select explicit models in the manifest before execution')
    if os.name != 'posix':
        raise ValueError('execute batches on Linux/macOS or WSL; dry-run is portable')
    source = load('metadata').source_fingerprint(ROOT)
    path = args.output.resolve() / manifest['batch_id']
    prepare(path, manifest, source)
    lock = path / '.running'
    STOP.clear()
    def stop_batch(_signum, _frame):
        STOP.set()
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, stop_batch)
    signal.signal(signal.SIGTERM, stop_batch)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('batch is locked; inspect an interrupted run before removing its .running marker') from None
    os.close(descriptor)
    failed, spend = False, 0.0
    try:
        # Submit one bounded wave at a time so budget checks also limit queued work.
        with ThreadPoolExecutor(max_workers=limits['concurrency']) as pool:
            for offset in range(0, len(runs), limits['concurrency']):
                if load('metadata').source_fingerprint(ROOT) != source:
                    raise ValueError('source changed during the batch; remaining runs were not started')
                wave = runs[offset:offset + limits['concurrency']]
                pending = sum(not (path / (run['run_id'] + '.json')).exists() for run in wave)
                if limits.get('max_cost_usd') and spend + pending * estimate > limits['max_cost_usd']:
                    raise ValueError('remaining estimated spend exceeds the batch budget')
                for future in as_completed([pool.submit(execute, run, path, manifest) for run in wave]):
                    result = future.result()
                    print(result['run']['run_id'], 'exit', result['exit_code'], flush=True)
                    failed |= result['exit_code'] != 0
                    cost = result['cost_usd']
                    if cost is None and limits.get('max_cost_usd'):
                        raise ValueError('spend was not observed; no additional wave will be started')
                    spend += cost or 0
    finally:
        lock.unlink()
    return int(failed)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        sys.exit(f'batch: {error}')
    except KeyboardInterrupt:
        sys.exit('batch interrupted; unfinished evidence is retained')
