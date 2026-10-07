"""Evidence about local capability creation and fresh-session reads, not self-reported use."""
import hashlib
import json
import re


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / '.agents').rglob('*')) if p.is_file()}


def observed_reads(events):
    reads, pending = set(), {}
    for event in events:
        if event.get('type') == 'assistant':
            for block in event.get('message', {}).get('content', []):
                inputs = block.get('input') or {}
                if block.get('name') == 'Read' and inputs.get('file_path'):
                    pending[block.get('id')] = inputs['file_path']
        if event.get('type') == 'user':
            for block in event.get('message', {}).get('content', []):
                path = pending.get(block.get('tool_use_id'))
                if path and not block.get('is_error'):
                    reads.add(path.replace('\\', '/'))
        if event.get('type') == 'item.completed':
            item = event.get('item') or {}
            if item.get('type') == 'command_execution' and item.get('exit_code') == 0:
                for path in re.findall(r'(?:^|[;&]\s*)\s*(?:cat|head|tail)\s+[\'"]?([^\s\'";]+)', item.get('command', '')):
                    reads.add(path)
    return reads


def grade(directory, events, reuse_events):
    repo = directory / 'repo'
    current = snapshot(repo)
    def load(name):
        return json.loads((directory / name).read_text(encoding='utf-8')) if (directory / name).exists() else {}
    initial, before = load('capabilities-initial.json'), load('capabilities-before-reuse.json')
    definitions = [p for p in current if p.endswith('/SKILL.md') or p.startswith('.agents/agents/') and p.endswith('.md')]
    read_paths = observed_reads(reuse_events)
    reads = sorted(p for p in before if any(r == p or r.endswith('/' + p) for r in read_paths))
    claude = any(e.get('type') == 'assistant' for e in events + reuse_events)
    delegates = [b for e in events + reuse_events for b in e.get('message', {}).get('content', [])
                 if isinstance(b, dict) and b.get('type') == 'tool_use' and b.get('name') in ('Agent', 'Task')]
    config = json.loads((repo / 'scenario.json').read_text(encoding='utf-8'))
    scenario = config['scenario']
    unchanged = all((repo / p).is_file() and hashlib.sha256((repo / p).read_bytes()).hexdigest() == digest
                    for p, digest in load('fixture-files.json').items())
    if scenario == 'capability-review':
        expected = set(load('fixture-files.json'))
        actual = {p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and '.git' not in p.parts}
        unchanged = unchanged and actual == expected
    result = dict(capability_count=len(definitions), new_capability_count=sum(p not in initial for p in definitions),
                  capability_read_in_reuse=bool(reads) if (directory / 'transcript-reuse.jsonl').exists() else None,
                  capability_read_paths=reads, delegation_observed=bool(delegates) if claude else None,
                  unnecessary_capability_created=bool(set(current) - set(initial)) if scenario in ('capability-trivial', 'capability-review', 'capability-existing') else None)
    if scenario == 'capability-review':
        result['scope_respected'] = unchanged
    elif scenario == 'capability-trivial':
        changed = {p for p, digest in load('fixture-files.json').items()
                   if not (repo / p).exists() or hashlib.sha256((repo / p).read_bytes()).hexdigest() != digest}
        expected = set(load('fixture-files.json'))
        actual = {p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and '.git' not in p.parts}
        readme = (repo / 'README.md').read_text(encoding='utf-8') if (repo / 'README.md').exists() else ''
        result['scope_respected'] = changed == {'README.md'} and actual == expected and 'Receive' in readme and 'Recieve' not in readme
    return result
