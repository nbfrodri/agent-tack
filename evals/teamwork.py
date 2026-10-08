#!/usr/bin/env python3
"""Four-session exploratory pilot, separate from the frozen quality batch."""
import argparse
import json
from pathlib import Path
import uuid

from quality import ROOT, digest, run, save
from teamwork_fixture import PROMPTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    if manifest['max_sessions'] != 4 or set(manifest['revisions']) != {'baseline', 'candidate'}:
        raise ValueError('This pilot fixes two products, two roles and at most four sessions, with no retries')
    if args.dry_run:
        print(json.dumps({'sessions': 4, 'model': manifest['model'], 'prompts': PROMPTS}, indent=2))
        return 0
    if not args.auth or not args.auth.is_file() or not args.output:
        parser.error('Provide authentication and a new output directory')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    save(args.output / 'manifest.json', manifest)
    save(args.output / 'controller.json', {path.name: digest(path) for path in [
        ROOT / 'evals/teamwork.py', ROOT / 'evals/teamwork_worker.py', ROOT / 'evals/teamwork_fixture.py', ROOT / 'evals/quality_worker.py']})
    observed_image = json.loads(run(['docker', 'image', 'inspect', manifest['image']]))[0]['Id']
    if observed_image != manifest['image']:
        raise ValueError('Use an exact image ID')
    for condition in ('baseline', 'candidate'):
        revision = manifest['revisions'][condition]
        if run(['git', 'rev-parse', revision + '^{commit}']) != revision:
            raise ValueError('Use full product commit IDs')
        output = args.output / condition
        output.mkdir()
        archive = output / 'product.tar'
        run(['git', 'archive', '--format=tar', '--output', archive, revision])
        save(output / 'product.json', {'revision': revision, 'archive_sha256': digest(archive)})
        save(output / 'job.json', {'condition': condition, 'model': manifest['model']})
        container = 'tack-team-pilot-' + uuid.uuid4().hex[:12]
        try:
            run(['docker', 'create', '--name', container, '--security-opt', 'seccomp=unconfined', manifest['image'], 'sleep', 'infinity'])
            run(['docker', 'start', container])
            mounts = json.loads(run(['docker', 'inspect', container, '--format', '{{json .Mounts}}']))
            if mounts:
                raise ValueError('Unexpected host mounts')
            for source, target in [(archive, 'product.tar'), (output / 'job.json', 'job.json'), (args.auth, 'auth.json')]:
                run(['docker', 'cp', source, container + ':/home/dev/' + target])
            for name in ('teamwork_worker.py', 'teamwork_fixture.py', 'quality_worker.py'):
                run(['docker', 'cp', ROOT / 'evals' / name, container + ':/home/dev/' + name])
            run(['docker', 'exec', container, 'mkdir', '/home/dev/product'])
            run(['docker', 'exec', container, 'tar', '-xf', '/home/dev/product.tar', '-C', '/home/dev/product'])
            run(['docker', 'exec', '--user', 'root', container, 'chown', 'dev:dev', '/home/dev/auth.json'])
            try:
                run(['docker', 'exec', container, 'python3', '/home/dev/teamwork_worker.py'], timeout=1250)
            finally:
                run(['docker', 'cp', container + ':/home/dev/evidence/.', output])
            for role in ('backend', 'frontend'):
                result = json.loads((output / role / 'session.json').read_text(encoding='utf-8'))
                print(condition, role, result['completed'], result['seconds'], flush=True)
        finally:
            run(['docker', 'rm', '-f', container], timeout=30)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
