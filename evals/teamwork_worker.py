#!/usr/bin/env python3
"""Two fresh Codex homes, linked only by a committed monorepo; disposable container only."""
import json
from pathlib import Path
import shutil

import quality_worker as worker
from teamwork_fixture import PROMPTS, profile, seed

ROOT = Path('/home/dev')


def main():
    job = json.loads((ROOT / 'job.json').read_text(encoding='utf-8'))
    (ROOT / 'evidence').mkdir()
    work = ROOT / 'work'
    work.mkdir()
    seed(work)
    private_auth = (ROOT / 'auth.json').read_bytes()
    (ROOT / 'auth.json').unlink()
    product_before = worker.product_hash()
    for role in ('backend', 'frontend'):
        home = ROOT / (role + '-home')
        (home / '.codex').mkdir(parents=True, mode=0o700)
        (home / '.codex/auth.json').write_bytes(private_auth)
        (home / '.codex/auth.json').chmod(0o600)
        env = worker.environment(home)
        worker.WORK = work
        worker.OUT = ROOT / 'evidence' / role
        worker.OUT.mkdir()
        for key, value in [('user.name', 'Eval'), ('user.email', 'eval@example.invalid')]:
            worker.checked(['git', 'config', '--global', key, value], env)
        if role == 'backend':
            worker.checked(['git', 'init', '-q', '-b', 'main'], env)
            (work / 'tack.json').write_text(profile(job['condition'] == 'candidate'), encoding='utf-8')
            (work / '.tack').write_text('', encoding='utf-8')
            worker.checked(['git', 'add', '.'], env)
            worker.checked(['git', 'commit', '-qm', 'feat: seed application'], env)
            worker.checked(['git', 'checkout', '-qb', 'feat/backend'], env)
        else:
            original = work
            work = ROOT / 'consumer'
            worker.checked(['git', 'clone', '-q', '--no-hardlinks', original, work], env, ROOT)
            worker.WORK = work
            worker.checked(['git', 'checkout', '-qb', 'feat/frontend', 'origin/main'], env)
            # Make the producer branch visible locally without merging its implementation.
            worker.checked(['git', 'branch', '-f', 'feat/backend', 'origin/feat/backend'], env)
        worker.save('install.json', worker.checked(['bash', ROOT / 'product/install.sh', '--skip-plugins'], env, timeout=180))
        tack = ['bash', ROOT / 'product/bin/tack']
        worker.checked([*tack, 'config', 'setup-review', 'done'], env)
        worker.checked([*tack, 'trust'], env)
        worker.save('base.json', {'head': worker.checked(['git', 'rev-parse', 'HEAD'], env)['stdout'].strip()})
        permissions = ('permissions.benchmark={extends=":workspace",'
                       'filesystem={":workspace_roots"={".git"="write"}},network={enabled=false}}')
        arguments = ['/usr/local/bin/codex', 'exec', '--json', '--skip-git-repo-check', '--model', job['model'],
                     '-c', 'model_reasoning_effort="medium"', '-C', str(work),
                     '-c', 'default_permissions="benchmark"', '-c', permissions, '--dangerously-bypass-hook-trust',
                     '-c', 'developer_instructions=' + json.dumps(
                         'Work only in this local repository. Do not publish, install dependencies, contact external services, '
                         'launch subagents or ask questions. Return the local result.'), PROMPTS[role]]
        result = worker.invoke(arguments, env, 480)
        result['runtime'] = worker.observe(home)
        events = [json.loads(line) for line in (worker.OUT / 'transcript.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        result['completed'] = result['exit_code'] == 0 and any(e.get('type') == 'turn.completed' for e in events)
        result['product_unchanged'] = worker.product_hash() == product_before
        worker.save('session.json', result)
        worker.capture({'test_command': ['bash', '-c', 'python3 -m unittest discover -s tests && node --test frontend/client.test.mjs']}, env)
        if not result['completed'] or not result['product_unchanged']:
            return 1
        if role == 'backend':
            # Transport normalization is outside model time and recorded; preserve the model diff separately.
            worker.checked(['git', 'checkout', '-B', 'feat/backend'], env)
            worker.checked(['git', 'add', '.'], env)
            if worker.call(['git', 'diff', '--cached', '--quiet'], env)['exit_code']:
                worker.checked(['git', 'commit', '-qm', 'feat: capture producer delivery'], env)
        shutil.rmtree(home / '.codex')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
