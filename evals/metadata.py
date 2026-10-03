#!/usr/bin/env python3
"""Record reproducibility inputs and only explicitly observed model identifiers."""
import hashlib
import json
import sys
from pathlib import Path


def finalize(directory):
    path = directory / 'metadata.json'
    if not path.exists():
        return
    metadata = json.loads(path.read_text())
    transcript = directory / 'transcript.jsonl'
    models = set()
    if transcript.exists():
        for line in transcript.read_text(errors='replace').splitlines():
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
    path.write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    directory = Path(sys.argv[2])
    if sys.argv[1] == 'finish':
        finalize(directory)
    else:
        scenario, condition, rep, provider, model, version, revision = sys.argv[3:]
        metadata = dict(scenario=scenario, condition=condition, repetition=int(rep), provider=provider,
                        requested_model=model or None, resolved_model=None, cli_version=version,
                        harness_revision=revision, metrics_version=2,
                        prompt_sha256=hashlib.sha256((directory / 'prompt.txt').read_bytes()).hexdigest(),
                        permission_mode='workspace-write' if provider == 'codex' else 'acceptEdits',
                        configuration_sources='project,local' if condition == 'baseline' and provider == 'claude' else None)
        (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
