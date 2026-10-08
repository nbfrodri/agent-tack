"""Finite lifecycle experiment; private graders stay in separate networkless containers."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import tarfile
import threading
import time
import uuid

from adoption import transcript_metrics
from lifecycle_fixture import CONDITIONS, PROMPTS, SCENARIOS, STAGES
from quality import ROOT, digest, run, save


def matrix(manifest):
    if manifest.get('conditions') != list(CONDITIONS) or manifest.get('scenarios') != list(SCENARIOS):
        raise ValueError('use all three conditions and both scenarios')
    if manifest.get('models') != ['gpt-6-luna', 'gpt-6.1-sol'] or manifest.get('effort') != 'medium':
        raise ValueError('this experiment pins two implementers and medium effort')
    if manifest.get('repetitions') != 2 or manifest.get('max_sessions') != 140 or manifest.get('concurrency') != 2:
        raise ValueError('fixed repetitions, concurrency and session cap')
    if type(manifest.get('timeout_seconds')) is not int or not 1 <= manifest['timeout_seconds'] <= 300:
        raise ValueError('implementation timeout must be 1..300 seconds')
    revision = manifest.get('revision', '')
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('pin a full product commit')
    if not manifest.get('image', '').startswith('sha256:') or len(manifest['image']) != 71:
        raise ValueError('pin a Docker image digest')
    blocks = [(m, s, r) for m in range(2) for s in SCENARIOS for r in (1, 2)]
    random.Random(manifest['seed']).shuffle(blocks)
    result = []
    for i, (model, scenario, repetition) in enumerate(blocks):
        offset = i % len(CONDITIONS)
        for condition in CONDITIONS[offset:] + CONDITIONS[:offset]:
            result.append(dict(id=f'm{model}-{scenario}-{repetition}-{condition}', model=manifest['models'][model],
                               scenario=scenario, repetition=repetition, condition=condition))
    return result


def archive_product(revision, output):
    if run(['git', '-C', ROOT, 'rev-parse', revision + '^{commit}']) != revision:
        raise ValueError('unresolved product revision')
    run(['git', '-C', ROOT, 'archive', '--output', output, revision, '--', '.',
         ':(exclude)evals', ':(exclude)tests', ':(exclude)docs/benchmarks', ':(exclude)docs/plans',
         ':(exclude)docs/archive', ':(exclude)docs/audits', ':(exclude).github'])
    with tarfile.open(output) as archive:
        if any(p.name.startswith(('evals/', 'tests/')) for p in archive):
            raise ValueError('private evaluator code leaked into runtime archive')


def isolated_grade(image, snapshot, scenario, stage, seed_probe=False):
    container = 'tack-lifecycle-grade-' + uuid.uuid4().hex[:12]
    created = False
    started = time.monotonic()
    try:
        run(['docker', 'create', '--name', container, '--network', 'none', image, 'sleep', 'infinity'])
        created = True
        run(['docker', 'start', container])
        run(['docker', 'cp', snapshot, container + ':/home/dev/repo'])
        for name in ('lifecycle_grade.py', 'lifecycle_fixture.py'):
            run(['docker', 'cp', ROOT / 'evals' / name, container + ':/home/dev/' + name])
        args = ['docker', 'exec', container, 'python3', '/home/dev/lifecycle_grade.py', '/home/dev/repo', scenario, stage]
        if seed_probe:
            args.append('--seed-probe')
        report = json.loads(run(args, timeout=150))
        report['evaluation_seconds'] = round(time.monotonic() - started, 3)
        return report
    finally:
        if created:
            run(['docker', 'rm', '-f', container], timeout=30)


def accepted(grade):
    return (grade['acceptance']['passed'] and grade['public']['exit_code'] == 0
            and grade.get('dispositions', {'passed': True})['passed'])


def repair_feedback(grade):
    failures = [c for c in grade['acceptance'].get('cases', []) if not c['passed']]
    feedback = dict(failures=failures, error=grade['acceptance'].get('error'),
                    public_tests=grade['public'] if grade['public']['exit_code'] else 'passed',
                    review=grade.get('dispositions'))
    return ('The delivered application has the following independently observed failures. Correct them while preserving '
            'the documented behavior and addressed review. This is the final correction opportunity.\n' + json.dumps(feedback, indent=2))


def journey(case, args, manifest, archive, stopped):
    if stopped.is_set():
        return {**case, 'skipped': 'infrastructure failure in an earlier journey'}
    output = args.output / case['id']
    output.mkdir()
    save(output / 'case.json', case)
    job = dict(case, timeout_seconds=manifest['timeout_seconds'])
    save(output / 'job.json', job)
    container = 'tack-lifecycle-' + uuid.uuid4().hex[:12]
    created = False
    result = {**case, 'stages': {}, 'grades': {}}
    try:
        run(['docker', 'create', '--name', container, '--security-opt', 'seccomp=unconfined', manifest['image'], 'sleep', 'infinity'])
        created = True
        run(['docker', 'start', container])
        if json.loads(run(['docker', 'inspect', container, '--format', '{{json .Mounts}}'])):
            raise ValueError('unexpected container mounts')
        for path, name in [(args.auth, 'auth.json'), (output / 'job.json', 'job.json')]:
            run(['docker', 'cp', path, container + ':/home/dev/' + name])
        run(['docker', 'exec', '--user', 'root', container, 'chown', 'dev:dev', '/home/dev/auth.json'])
        run(['docker', 'exec', container, 'chmod', '600', '/home/dev/auth.json'])
        for name in ('lifecycle_worker.py', 'lifecycle_fixture.py', 'quality_worker.py'):
            run(['docker', 'cp', ROOT / 'evals' / name, container + ':/home/dev/' + name])
        if case['condition'] == 'tack':
            run(['docker', 'cp', archive, container + ':/home/dev/product.tar'])
            run(['docker', 'exec', container, 'mkdir', '/home/dev/product'])
            run(['docker', 'exec', container, 'tar', '-xf', '/home/dev/product.tar', '-C', '/home/dev/product'])

        def stage(name):
            run(['docker', 'exec', container, 'python3', '/home/dev/lifecycle_worker.py', name], timeout=manifest['timeout_seconds'] + 240)
            run(['docker', 'cp', container + ':/home/dev/evidence/.', output])
            data = json.loads((output / name / 'session.json').read_text(encoding='utf-8'))
            if data.get('infrastructure_error'):
                raise RuntimeError(data['infrastructure_error'])
            if data.get('runtime', {}).get('models') != [case['model']] or data.get('runtime', {}).get('efforts') != ['medium']:
                raise RuntimeError('runtime model/effort mismatch or missing observation')
            data.update(transcript_metrics(output / name / 'transcript.jsonl'))
            save(output / name / 'session.json', data)
            result['stages'][name] = data
            print(case['id'], name, data['completed'], data['seconds'], flush=True)
            save(output / 'journey.json', result)

        for name in STAGES:
            stage(name)
            if name != 'setup':
                grade = isolated_grade(manifest['image'], output / name / 'repo', case['scenario'], name, name == 'build')
                result['grades'][name] = grade
                save(output / name / 'grade.json', grade)
        if not accepted(result['grades']['review']):
            (output / 'feedback.txt').write_text(repair_feedback(result['grades']['review']), encoding='utf-8')
            run(['docker', 'cp', output / 'feedback.txt', container + ':/home/dev/feedback.txt'])
            stage('repair')
            grade = isolated_grade(manifest['image'], output / 'repair/repo', case['scenario'], 'review')
            result['grades']['repair'] = grade
            save(output / 'repair/grade.json', grade)
        result['accepted'] = accepted(result['grades'].get('repair', result['grades']['review']))
    except Exception as error:
        result['infrastructure_error'] = str(error)
        stopped.set()
    finally:
        save(output / 'journey.json', result)
        if created:
            run(['docker', 'rm', '-f', container], timeout=30)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    cases = matrix(manifest)
    if args.dry_run:
        print(json.dumps(dict(journeys=cases, implementation_sessions=96, maximum_repairs=24, review_sessions=20,
                              prompt_hashes={k: hashlib.sha256(v.encode()).hexdigest() for k, v in PROMPTS.items()}), indent=2))
        return 0
    if not args.auth or not args.auth.is_file() or not args.output:
        parser.error('provide auth and a new output directory')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    if json.loads(run(['docker', 'image', 'inspect', manifest['image']]))[0]['Id'] != manifest['image']:
        raise ValueError('image mismatch')
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'order.json', cases)
    save(args.output / 'controller.json', {p.name: digest(p) for p in (ROOT / 'evals').glob('lifecycle*.py')})
    archive = args.output / 'product.tar'
    archive_product(manifest['revision'], archive)
    save(args.output / 'product.json', dict(revision=manifest['revision'], sha256=digest(archive),
         excludes=['evals', 'tests', 'docs/benchmarks', 'docs/plans', 'docs/archive', 'docs/audits', '.github']))
    stopped = threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda case: journey(case, args, manifest, archive, stopped), cases))
    save(args.output / 'results.json', results)
    return int(stopped.is_set())


if __name__ == '__main__':
    raise SystemExit(main())
