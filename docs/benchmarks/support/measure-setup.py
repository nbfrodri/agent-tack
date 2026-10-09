#!/usr/bin/env python3
"""Measure equivalent clone inspection, not human onboarding or model productivity.

Usage: python3 measure-setup.py BASELINE_CHECKOUT CANDIDATE_CHECKOUT PROJECT_CHECKOUT
All checkouts are local. Creates disposable clones and HOME; invokes no models.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import tempfile
import time


def measure(baseline, candidate, project, repeats):
    bash = shutil.which('bash')
    if not bash:
        raise ValueError('Bash is required')
    with tempfile.TemporaryDirectory(prefix='tack-setup-measure-') as temporary:
        work = Path(temporary)
        home = work / 'home'
        home.mkdir()
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('GIT_') and key not in ('BASH_ENV', 'ENV')}
        env.update(HOME=str(home), USERPROFILE=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                   XDG_STATE_HOME=str(home / '.state'), GIT_CONFIG_GLOBAL=str(home / '.gitconfig'),
                   GIT_CONFIG_NOSYSTEM='1')

        def run(*args, cwd=work):
            return subprocess.run(args, cwd=cwd, env=env, capture_output=True, check=True, timeout=30)

        owner, clone = work / 'owner', work / 'colleague'
        run('git', 'clone', '-q', '--no-hardlinks', str(project), str(owner))
        revision = run('git', 'rev-parse', 'HEAD', cwd=owner).stdout.decode().strip()
        (owner / '.tack').write_text('# Shared activation\n', encoding='utf-8')
        (owner / 'tack.json').write_text(json.dumps(dict(version=1, mode='auto', config={
            'collaboration': 'solo', 'reply-style': 'brief', 'architecture-path': 'docs/architecture.md'})), encoding='utf-8')
        run('git', 'add', '.tack', 'tack.json', cwd=owner)
        run('git', '-c', 'user.name=Measurement', '-c', 'user.email=measurement@example.invalid',
            'commit', '-qm', 'test: share selected setup', cwd=owner)
        run('git', 'config', 'tack.trusted', 'true', cwd=owner)
        run('git', 'clone', '-q', '--no-hardlinks', str(owner), str(clone))
        run('git', 'config', 'tack.replyStyle', 'visual', cwd=clone)
        run('git', 'config', 'tack.mode', 'strict', cwd=clone)
        config_before = (clone / '.git/config').read_bytes()
        status_before = run('git', 'status', '--porcelain', cwd=clone).stdout
        commands = {
            'baseline': [['setup', '--json'], ['config', '--json'], ['mode'], ['status']],
            'candidate': [['setup', '--json']],
        }
        sources = {'baseline': baseline, 'candidate': candidate}
        samples = {name: [] for name in sources}
        outputs = {}
        # Alternate execution order; retain every sample. Includes one first call.
        for repetition in range(repeats):
            order = list(sources) if repetition % 2 == 0 else list(reversed(sources))
            for name in order:
                start = time.perf_counter()
                result = [run(bash, str(sources[name] / 'bin/tack'), *args, cwd=clone).stdout
                          for args in commands[name]]
                samples[name].append(time.perf_counter() - start)
                outputs[name] = result
        old_settings = {item['name']: item for item in json.loads(outputs['baseline'][1])}
        report = json.loads(outputs['candidate'][0])
        assert {(item['name'], item['value'], item['source']) for item in report['preferences']} == {
            (item['name'], item['value'], item['source']) for item in old_settings.values()}
        assert outputs['baseline'][2].decode().strip() == 'strict (local)'
        assert b'enabled\n' in outputs['baseline'][3] and b'untrusted' in outputs['baseline'][3]
        assert report['workflow']['enabled'] and not report['workflow']['trusted']
        assert report['workflow']['mode']['value'] == 'strict'
        assert {item['name'] for item in report['differences']} == {'mode', 'reply-style'}
        assert (clone / '.git/config').read_bytes() == config_before
        assert run('git', 'status', '--porcelain', cwd=clone).stdout == status_before
        return dict(project_revision=revision, repeats=repeats, commands=commands,
                    seconds=samples, median_seconds={name: statistics.median(value) for name, value in samples.items()},
                    stdout_bytes={name: sum(map(len, value)) for name, value in outputs.items()},
                    source_sha256={name: {file: hashlib.sha256((source / file).read_bytes()).hexdigest()
                                           for file in ('bin/tack', 'lib/project_setup.py', 'lib/project_config.py', 'features.txt')}
                                   for name, source in sources.items()},
                    checks=['effective values and origins agree', 'local differences exposed',
                            'trust not inherited', 'Git status and local config unchanged'],
                    limitations='Local CLI measurement; no model tokens, human time or causal code-quality comparison.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('project', type=Path)
    parser.add_argument('--repeats', type=int, default=8)
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error('--repeats must be at least 2')
    print(json.dumps(measure(args.baseline.resolve(), args.candidate.resolve(), args.project.resolve(), args.repeats), indent=2))


if __name__ == '__main__':
    main()
