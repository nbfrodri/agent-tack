#!/usr/bin/env python3
"""Seed the non-Python and fresh-session capability experiments, without hidden tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

NAMES = ('event-routing', 'project-capabilities', 'capability-existing', 'capability-trivial',
         'capability-review', 'capability-role', 'capability-nodelegation', 'capability-sequential')


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / '.agents').rglob('*')) if p.is_file()}


def seed(name, root):
    write(root, 'package.json', json.dumps({'name': 'event-service', 'type': 'module',
                                           'scripts': {'test': 'node --test'}}) + '\n')
    write(root, 'src/events.js', "export function validate(event) {\n  if (!event || typeof event.id !== 'string' || !event.id.trim()) throw new Error('invalid id');\n  return {...event};\n}\n")
    write(root, 'src/routes.js', "import {validate} from './events.js';\nconst topics = {'order.created': 'orders'};\nexport function handle(event) {\n  const copy = validate(event);\n  if (!Object.hasOwn(topics, copy.type)) throw new Error('unknown event');\n  return {topic: topics[copy.type], key: copy.id, payload: copy};\n}\n")
    write(root, 'tests/events.test.js', "import {test} from 'node:test';\nimport assert from 'node:assert/strict';\nimport {handle} from '../src/routes.js';\ntest('existing event', () => assert.equal(handle({id:'o1',type:'order.created'}).topic,'orders'));\n")
    write(root, 'README.md', '# Event service\n\nRecieve events. Run `npm test`.\n')
    write(root, 'docs/contracts.md', '# Event contracts\n\nNew invoice events use the invoices topic. The route key is the unchanged nonempty string id.\nInvoice events require amountCents to be a nonnegative safe integer; never coerce strings.\nNever mutate caller input. Unknown event types must be rejected. Keep existing order routing.\nFor each new type, add a validation test, a routing test and a catalog entry.\n')
    write(root, 'docs/catalog.md', '# Event catalog\n\n- order.created: orders\n')
    write(root, 'AGENTS.md', '# Project instructions\n\nRun `npm test`. Contracts are in docs/contracts.md; the event catalog is docs/catalog.md.\nUse the same contract when adding another invoice event.\n')
    first, second = ('invoice.paid', 'invoice.refunded')
    if os.environ.get('EVALS_VARIANT') == 'held-out':
        first, second = 'invoice.voided', 'invoice.adjusted'
    write(root, 'scenario.json', json.dumps({'first': first, 'second': second, 'scenario': name}) + '\n')
    if name == 'capability-existing':
        write(root, '.agents/skills/event-contracts/SKILL.md', '---\nname: event-contracts\ndescription: Add invoice events to this service.\n---\nRead [contracts](../../../docs/contracts.md), add validation and routing tests, update [catalog](../../../docs/catalog.md), then run npm test.\n')
        with (root / 'AGENTS.md').open('a', encoding='utf-8') as file:
            file.write('\n[Event contracts](.agents/skills/event-contracts/SKILL.md): use for every new invoice event.\n')
    task = f'Add support for {first} events to this service, keeping its existing contracts and behavior. '
    if name == 'event-routing':
        prompts = [task]
    elif name == 'capability-trivial':
        prompts = ['Correct Recieve to Receive in README.md. This is the entire change.']
    elif name == 'capability-review':
        prompts = ['Review event handling and describe missing validation. Report only; change no files.']
    elif name == 'capability-role':
        prompts = ['Prepare a reusable project-local event-contract reviewer role for repeated releases, with an input/output contract and read-only boundaries. Do not invoke it now.',
                   'Review this service using its project reviewer contract; write review.md with concrete findings. Perform the review sequentially yourself; do not launch agents.']
    else:
        task += 'We will add further invoice events in later tasks; preserve any useful project-specific procedure for reuse where justified. '
        if name in ('capability-nodelegation', 'capability-sequential'):
            task += 'Work sequentially; do not launch subagents. '
        prompts = [task, f'Add support for {second} events with the same project contracts and update the catalog. Work sequentially.']
    return [p + ' Choose reasonable defaults; do not ask questions or publish anything.' for p in prompts]


if __name__ == '__main__':
    name, directory, output = sys.argv[1:4]
    root, out = Path(directory), Path(output)
    if name == 'snapshot':
        (out / 'capabilities-before-reuse.json').write_text(json.dumps(snapshot(root)), encoding='utf-8')
    else:
        if name not in NAMES:
            sys.exit('unknown extended scenario')
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(root)], check=True)
        prompts = seed(name, root)
        subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(root), 'commit', '-q', '-m', 'feat: seed event service'], check=True)
        if name in ('capability-nodelegation', 'capability-sequential'):
            subprocess.run(['git', '-C', str(root), 'config', 'tack.delegation', 'off'], check=True)
        (out / 'prompts.json').write_text(json.dumps(prompts), encoding='utf-8')
        (out / 'capabilities-initial.json').write_text(json.dumps(snapshot(root)), encoding='utf-8')
        (out / 'fixture-files.json').write_text(json.dumps({p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                                          for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}), encoding='utf-8')
