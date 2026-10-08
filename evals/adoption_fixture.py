"""Public project fixture and identical prompts for the adoption comparison."""
import json
from pathlib import Path


def write(root, name, content):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')


def seed(root):
    files = {
        'package.json': json.dumps({'name': 'dispatch-service', 'version': '0.1.0', 'private': True,
                                   'type': 'module', 'scripts': {
                                       'test': 'node --test',
                                       'test:validation': 'node --test tests/validation.test.js',
                                       'test:routing': 'node --test tests/routing.test.js'}}, indent=2) + '\n',
        '.gitignore': 'node_modules/\ncoverage/\n',
        'src/events.js': '''export function validate(event) {
  if (!event || typeof event.id !== 'string' || !event.id.trim()) {
    throw new Error('invalid id');
  }
  if (event.type === 'order.created' &&
      (!Number.isInteger(event.quantity) || event.quantity < 0)) {
    throw new Error('invalid quantity');
  }
  return {...event};
}
''',
        'src/routes.js': '''import {validate} from './events.js';
const topics = {'order.created': 'orders'};

export function handle(event) {
  const payload = validate(event);
  if (!Object.hasOwn(topics, payload.type)) throw new Error('unknown event');
  return {topic: topics[payload.type], key: payload.id, payload};
}
''',
        'tests/validation.test.js': '''import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validate} from '../src/events.js';

test('accepts a valid order without mutating it', () => {
  const input = Object.freeze({type: 'order.created', id: 'o1', quantity: 2});
  assert.deepEqual(validate(input), input);
  assert.notEqual(validate(input), input);
});
test('rejects missing id', () => assert.throws(() => validate({type: 'order.created', quantity: 1})));
''',
        'tests/routing.test.js': '''import {test} from 'node:test';
import assert from 'node:assert/strict';
import {handle} from '../src/routes.js';

test('routes orders', () => assert.equal(handle({type: 'order.created', id: 'o1', quantity: 2}).topic, 'orders'));
test('rejects unknown types', () => assert.throws(() => handle({type: 'unknown', id: 'o1'})));
''',
        'guide/architecture.md': '# Architecture\n\n`src/events.js` validates public event contracts. '
        '`src/routes.js` selects a topic and uses the unchanged ID as key. Node built-in tests need no dependencies.\n',
        'guide/contracts.md': '# Event contracts\n\nEvery event has a nonempty string ID; reject whitespace-only IDs. '
        'Preserve the original ID, including surrounding spaces. Return a new payload object and never mutate the caller.\n\n'
        '`order.created` routes to `orders`. Its quantity must be a positive safe integer. '
        'Zero, negatives, fractions, strings, booleans, missing values, Infinity, NaN and unsafe integers are invalid.\n\n'
        'Invoice events route to `invoices`. Their `amountCents` must be a nonnegative safe integer. '
        'Zero is valid; strings, booleans, negatives, fractions, missing values, Infinity, NaN and unsafe integers are invalid. '
        'Never coerce numeric strings. Unknown event types must be rejected. Update the event catalog for each supported type.\n',
        'guide/catalog.md': '# Supported events\n\n- `order.created`: `orders`\n',
        'README.md': '# Dispatch service\n\nA small Node event service. No third-party runtime or test dependencies.\n\n'
        'Run `npm test`; focused checks are `npm run test:validation` and `npm run test:routing`.\n\n'
        'See [architecture](guide/architecture.md), [contracts](guide/contracts.md) and [catalog](guide/catalog.md).\n',
        'AGENTS.md': '# Project instructions\n\nRead guide/architecture.md and guide/contracts.md for relevant changes. '
        'Run npm test; focused checks are npm run test:validation and npm run test:routing.\n\n'
        'Keep Node built-in tests and current module boundaries. Use TDD for behavior, SOLID with KISS/YAGNI, '
        'meaningful boundary/regression tests and docs in the same change. Work on branches with Conventional Commits '
        'and no AI attribution. Use PR templates when publishing is requested.\n\n'
        'Architecture stays at guide/architecture.md; necessary plans at work/plans and handoffs at work/handoffs. '
        'Use brief actionable replies and task-scaled effort. Do not create empty artifact directories.\n',
    }
    for name, content in files.items():
        write(root, name, content)
    return files


COMMON = (' You may inspect files, run local checks, create a branch and commit verified work. '
          'Do not publish, install dependencies, download external skills, launch subagents or ask questions; '
          'the setup choices are already approved. Preserve unrelated files. Report actual checks and limitations briefly.')
PROMPTS = {
    'setup': 'Configure this existing service for two developers using AI in separate clones. '
    'Keep the existing conventions, contracts, commands and guide/architecture.md; use work/plans and work/handoffs '
    'only when needed. We choose brief replies, task-scaled effort, TDD for behavior, SOLID with KISS/YAGNI, '
    'Conventional Commits without AI attribution, branches, useful tests and same-change documentation. '
    'Add a suitable PR template and record accepted choices so a teammate need not answer again. '
    'We decline extra agents/skills, release automation and new dependencies. If tack is installed, use it to '
    'share activation and allowed preferences in this repository, configure the agreed paths, map existing meaningful '
    'checks, and complete setup review. Otherwise use native project guidance to share the same choices. '
    'Commit the setup locally. Do not fix or extend production behavior during this setup task.' + COMMON,
    'bug': 'You are the second developer in a new clone. Reuse the committed project setup and conventions. '
    'A zero quantity is incorrectly accepted for order.created. Fix this according to the documented event contract '
    'and preserve valid orders. Protect the behavior with meaningful regression tests and commit the verified fix.' + COMMON,
    'feature': 'Add support for invoice.paid events following the existing event contracts and shared project conventions. '
    'Keep order behavior, preserve caller inputs, update the catalog and add useful tests. '
    'Commit the verified feature. Reuse the setup already agreed by the team.' + COMMON,
}
