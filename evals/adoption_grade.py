#!/usr/bin/env python3
"""Post-run hidden acceptance and mutation probes; keep outside the live model container."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from adoption_fixture import seed


HIDDEN = r'''
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const root = process.argv[1], stage = process.argv[2];
const {handle} = await import(pathToFileURL(path.join(root, 'src/routes.js')));
const {validate} = await import(pathToFileURL(path.join(root, 'src/events.js')));
const results = [];
function check(name, fn) {
  try { fn(); results.push({name, passed: true}); }
  catch (e) { results.push({name, passed: false, error: e.message}); }
}
const invalid = [0, -1, 1.5, '1', true, null, undefined, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1];
invalid.forEach((quantity, index) => check(`order quantity boundary ${index}`, () => {
  const input = {type: 'order.created', id: 'o1', quantity};
  assert.throws(() => validate(input)); assert.throws(() => handle(input));
}));
for (const quantity of [1, 2, Number.MAX_SAFE_INTEGER]) {
  check(`valid order ${quantity}`, () => {
    const input = Object.freeze({type: 'order.created', id: ' o1 ', quantity, extra: 'keep'});
    const result = handle(input);
    assert.deepEqual(result, {topic: 'orders', key: ' o1 ', payload: input});
    assert.notEqual(result.payload, input);
  });
}
for (const id of ['', '   ', null, 3]) {
  check(`invalid id ${JSON.stringify(id)}`, () => assert.throws(() => handle({type: 'order.created', id, quantity: 1})));
}
for (const type of ['unknown', '__proto__', 'constructor']) {
  check(`unknown type ${type}`, () => assert.throws(() => handle({type, id: 'o1', quantity: 1})));
}
if (stage === 'feature') {
  for (const amountCents of [0, 1, 9999, Number.MAX_SAFE_INTEGER]) {
    check(`valid invoice ${amountCents}`, () => {
      const input = Object.freeze({type: 'invoice.paid', id: ' i1 ', amountCents, extra: 'keep'});
      const result = handle(input);
      assert.deepEqual(result, {topic: 'invoices', key: ' i1 ', payload: input});
      assert.notEqual(result.payload, input);
    });
  }
  invalid.filter(v => v !== 0).forEach((amountCents, index) => check(`invoice amount boundary ${index}`, () => {
    const input = {type: 'invoice.paid', id: 'i1', amountCents};
    assert.throws(() => validate(input)); assert.throws(() => handle(input));
  }));
}
console.log(JSON.stringify(results));
'''

VALIDATOR_MUTANT = """export function validate(event) {
  if (!event || typeof event.id !== 'string' || !event.id.trim()) throw new Error('invalid id');
  return {...event};
}
"""
ROUTING_MUTANT = """import {validate} from './events.js';
const topics = {'order.created': 'orders', 'invoice.paid': 'orders'};
export function handle(event) {
  const payload = validate(event);
  if (!Object.hasOwn(topics, payload.type)) throw new Error('unknown event');
  return {topic: topics[payload.type], key: payload.id, payload};
}
"""


def acceptance(root, stage):
    result = subprocess.run(['node', '--input-type=module', '-e', HIDDEN, str(root.resolve()), stage],
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    try:
        cases = json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'cases': [], 'error': (result.stdout + result.stderr)[-3000:]}
    return {'passed': result.returncode == 0 and bool(cases) and all(c['passed'] for c in cases), 'cases': cases}


def mutations(root, stage):
    probes = [('validation', 'src/events.js', VALIDATOR_MUTANT)]
    if stage == 'feature':
        probes.append(('routing', 'src/routes.js', ROUTING_MUTANT))
    outcomes = {}
    for name, file, content in probes:
        with tempfile.TemporaryDirectory(prefix='tack-adoption-mutation-') as temp:
            clone = Path(temp) / 'repo'
            shutil.copytree(root, clone, symlinks=True)
            (clone / file).write_text(content, encoding='utf-8')
            result = subprocess.run(['npm', 'test'], cwd=clone, capture_output=True, text=True, encoding='utf-8', timeout=30)
            outcomes[name] = {'detected': result.returncode != 0, 'exit_code': result.returncode,
                              'output': (result.stdout + result.stderr)[-5000:]}
    return outcomes


def adoption(directory):
    root = directory / 'setup/repo'
    with tempfile.TemporaryDirectory(prefix='tack-adoption-seed-') as temp:
        original = seed(Path(temp))
    unchanged = [name for name in original if name.startswith(('src/', 'tests/'))]
    result = {'production_and_tests_preserved': all((root / n).is_file() and (root / n).read_text(encoding='utf-8') == original[n]
                                                   for n in unchanged),
              'architecture_preserved': (root / 'guide/architecture.md').is_file(),
              'pr_template': any(p.is_file() and p.name.lower() == 'pull_request_template.md'
                                 for folder in (root, root / '.github', root / 'docs') if folder.is_dir()
                                 for p in folder.iterdir()),
              'no_extra_capabilities': not (root / '.agents').exists(),
              'setup_committed_cleanly': not (directory / 'setup/status.txt').read_text(encoding='utf-8').strip()}
    observations = directory / 'second-clone-observations.json'
    if observations.exists():
        data = json.loads(observations.read_text(encoding='utf-8'))
        result['clone_untrusted_before_local_grant'] = data['trust']['exit_code'] == 1
        result['clone_enabled'] = data['enabled']['exit_code'] == 0 and 'enabled' in data['enabled']['stdout']
        result['clone_mode'] = data['mode']['stdout'].strip()
        try:
            result['clone_configuration'] = json.loads(data['config']['stdout'])
        except ValueError:
            result['clone_configuration'] = {'error': data['config']}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    summary = []
    for directory in sorted(args.output.iterdir()):
        if not (directory / 'journey.json').exists():
            continue
        result = json.loads((directory / 'journey.json').read_text(encoding='utf-8'))
        if (directory / 'setup/repo').exists():
            result['adoption'] = adoption(directory)
        for stage, metrics in result['stages'].items():
            root = directory / stage / 'repo'
            metrics['public_tests'] = json.loads((directory / stage / 'public-tests.json').read_text(encoding='utf-8'))['exit_code'] == 0
            if stage != 'setup':
                metrics['acceptance'] = acceptance(root, stage)
                metrics['mutations'] = mutations(root, stage) if metrics['public_tests'] else {'not_run': 'public suite already fails'}
        summary.append(result)
    result = {'hidden_sha256': hashlib.sha256(HIDDEN.encode()).hexdigest(), 'journeys': summary}
    (args.output / 'graded.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps([{'run': r['run_id'], 'stages': {s: m.get('acceptance', {}).get('passed') for s, m in r['stages'].items()}}
                      for r in summary], indent=2))


if __name__ == '__main__':
    main()
