#!/usr/bin/env python3
"""Record reproducibility inputs and only explicitly observed model identifiers."""
import hashlib
import json
import os
import sys
from pathlib import Path
import subprocess


def fingerprint(root, names):
    digest = hashlib.sha256()
    for name in sorted(set(names)):
        path = root / name
        if path.is_file():
            digest.update(name.encode('utf-8') + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def source_fingerprint(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z'],
                            capture_output=True, check=True)
    return fingerprint(root, [p.decode('utf-8') for p in result.stdout.split(b'\0') if p])


def hidden_fingerprint(root):
    return fingerprint(root, [p.relative_to(root).as_posix() for p in root.rglob('*')
                              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'])


def finalize(directory):
    path = directory / 'metadata.json'
    if not path.exists():
        return
    metadata = json.loads(path.read_text(encoding='utf-8'))
    models = set()
    for transcript in sorted(directory.glob('transcript*.jsonl')):
        for line in transcript.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get('type') == 'system' and event.get('subtype') == 'init' and event.get('model'):
                models.add(event['model'])
    metadata['resolved_model'] = next(iter(models)) if len(models) == 1 else None
    metadata['observed_models'] = sorted(models)
    metadata['source_changed'] = source_fingerprint(Path(__file__).resolve().parent.parent) != metadata.get('source_sha256')
    path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    directory = Path(sys.argv[2])
    if sys.argv[1] == 'finish':
        finalize(directory)
    else:
        scenario, condition, rep, provider, model, version, revision = sys.argv[3:10]
        root = Path(__file__).resolve().parent.parent
        fixture = directory / 'repo'
        files = subprocess.check_output(['git', '-C', str(fixture), 'ls-files', '-z']).decode('utf-8').split('\0')
        config = dict(skill_groups=os.environ.get('EVALS_SKILL_GROUPS', 'default'), condition=condition,
                      provider=provider, effort=os.environ.get('EVALS_EFFORT'),
                      endpoints={key: os.environ.get(key) for key in ('ANTHROPIC_BASE_URL', 'OPENAI_BASE_URL')})
        hidden_name = 'project-capabilities' if scenario in ('capability-existing', 'capability-role', 'capability-nodelegation', 'capability-sequential') else scenario.replace('codex-', '')
        hidden = root / 'evals/hidden' / hidden_name
        metadata = dict(scenario=scenario, condition=condition, repetition=int(rep), provider=provider,
                        requested_model=model or None, resolved_model=None, cli_version=version,
                        harness_revision=revision, metrics_version=3,
                        source_dirty=bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'])),
                        source_sha256=source_fingerprint(root),
                        configuration_sha256=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                        fixture_sha256=fingerprint(fixture, files),
                        hidden_sha256=hidden_fingerprint(hidden),
                        effort=os.environ.get('EVALS_EFFORT'), batch_id=os.environ.get('EVALS_BATCH_ID'),
                        run_id=os.environ.get('EVALS_RUN_ID', f'{scenario}/{condition}-{rep}'),
                        timeout_seconds=os.environ.get('EVALS_TIMEOUT_SECONDS'),
                        setup_seconds=int(os.environ.get('EVALS_SETUP_SECONDS', '0')),
                        workflow_mode=None if condition == 'baseline' else ('auto' if condition == 'harness' else condition),
                        prompt_sha256=hashlib.sha256((directory / ('prompts.json' if (directory / 'prompts.json').exists() else 'prompt.txt')).read_bytes()).hexdigest(),
                        allowed_tools=sys.argv[10:] if provider == 'claude' else None,
                        permission_mode='workspace-write' if provider == 'codex' else 'acceptEdits',
                        configuration_sources='project,local' if condition == 'baseline' and provider == 'claude' else None)
        (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
