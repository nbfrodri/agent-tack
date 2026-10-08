#!/usr/bin/env python3
"""Grade delivered producer/consumer code offline, outside model containers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PROBE = r'''
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {submitOrder} from './frontend/client.mjs';
const python = 'import json,sys; from backend.orders import create_order; print(json.dumps(create_order(json.load(sys.stdin))))';
function backend(payload) {
  const child = spawnSync('python3', ['-c', python], {input: JSON.stringify(payload), encoding: 'utf8', timeout: 5000});
  assert.equal(child.status, 0, child.stderr);
  const [status, body] = JSON.parse(child.stdout);
  return {status, body};
}
async function request(method, path, payload) {
  assert.equal(method, 'POST'); assert.equal(path, '/orders');
  return backend(payload);
}
const checks = {
  'backend-success': () => {
    const r = backend({sku: 'WIDGET', quantity: 2});
    assert.equal(r.status, 201); assert.equal(r.body.status, 'pending');
    assert.equal(typeof r.body.id, 'string'); assert.ok(r.body.id.length);
    assert.equal(r.body.totalCents, 2500);
  },
  'backend-invalid-quantity': () => {
    for (const quantity of [0, -1, 1.5, true, '2']) {
      const r = backend({sku: 'WIDGET', quantity});
      assert.equal(r.status, 422); assert.equal(r.body.error.code, 'invalid_quantity');
      assert.equal(typeof r.body.error.message, 'string'); assert.ok(r.body.error.message.length);
    }
  },
  'backend-unknown-sku': () => {
    const r = backend({sku: 'MISSING', quantity: 1});
    assert.equal(r.status, 404); assert.equal(r.body.error.code, 'unknown_sku');
  },
  'frontend-successful-integration': async () => {
    let called = false;
    const r = await submitOrder({sku: 'WIDGET', quantity: '2'}, async (...args) => {
      called = true; assert.deepEqual(args[2], {sku: 'WIDGET', quantity: 2}); return request(...args);
    });
    assert.ok(called); assert.equal(r.ok, true); assert.equal(r.totalCents, 2500);
    assert.equal(typeof r.orderId, 'string'); assert.ok(r.orderId.length);
  },
  'frontend-validation-integration': async () => {
    for (const quantity of ['0', '1.5']) {
      const r = await submitOrder({sku: 'WIDGET', quantity}, request);
      assert.equal(r.ok, false); assert.equal(typeof r.error, 'string'); assert.ok(r.error.length);
    }
  },
  'frontend-api-error-message': async () => {
    const r = await submitOrder({sku: 'WIDGET', quantity: '2'}, async () => ({status: 422, body: {
      error: {code: 'invalid_quantity', message: 'Choose a positive whole quantity.'}
    }}));
    assert.deepEqual(r, {ok: false, error: 'Choose a positive whole quantity.'});
  },
  'frontend-unknown-sku-integration': async () => {
    const r = await submitOrder({sku: 'MISSING', quantity: '1'}, request);
    assert.equal(r.ok, false); assert.equal(typeof r.error, 'string'); assert.ok(r.error.length);
  }
};
const results = {};
for (const [name, check] of Object.entries(checks)) {
  try { await check(); results[name] = {passed: true}; }
  catch (error) { results[name] = {passed: false, error: String(error).slice(0, 700)}; }
}
console.log(JSON.stringify(results));
'''


def grade(condition):
    with tempfile.TemporaryDirectory(prefix='tack-team-grade-') as directory:
        root = Path(directory)
        for component, role in [('backend', 'backend'), ('frontend', 'frontend')]:
            source = condition / role / 'repo' / component
            if any(path.is_symlink() for path in source.rglob('*')):
                raise ValueError('Review symlink delivery before grading')
            shutil.copytree(source, root / component)
        (root / 'probe.mjs').write_text(PROBE, encoding='utf-8')
        env = dict(os.environ, HOME=str(root / 'home'), XDG_CONFIG_HOME=str(root / 'home/.config'),
                   GIT_CONFIG_GLOBAL=str(root / 'home/.gitconfig'), GIT_CONFIG_NOSYSTEM='1')
        result = subprocess.run(['node', 'probe.mjs'], cwd=root, env=env, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=60)
        return {'exit_code': result.returncode, 'checks': json.loads(result.stdout) if result.returncode == 0 else {},
                'error': result.stderr[-1500:] if result.returncode else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps({name: grade(args.results / name) for name in ('baseline', 'candidate')}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
