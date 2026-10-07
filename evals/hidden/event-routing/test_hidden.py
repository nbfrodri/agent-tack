"""Acceptance tests on public JavaScript behavior; not installed in the working repository."""
import json
from pathlib import Path
import subprocess

CONFIG = json.loads(Path('scenario.json').read_text())


def node(body):
    code = "import assert from 'node:assert/strict'; import {handle} from './src/routes.js';\n" + body
    result = subprocess.run(['node', '--input-type=module', '-e', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_new_event_routing():
    kind = json.dumps(CONFIG['first'])
    node(f"const result=handle({{id:'x',type:{kind},amountCents:0}}); assert.equal(result.topic,'invoices'); assert.equal(result.key,'x');")


def test_amount_validation():
    kind = json.dumps(CONFIG['first'])
    node(f"for(const value of [-1,1.5,'10',null,NaN,Infinity,Number.MAX_SAFE_INTEGER+1]) assert.throws(()=>handle({{id:'x',type:{kind},amountCents:value}}));")


def test_preserves_input():
    kind = json.dumps(CONFIG['first'])
    node(f"const value=Object.freeze({{id:'x',type:{kind},amountCents:200}}); handle(value); assert.equal(value.amountCents,200);")


def test_keeps_existing_and_rejects_unknown():
    node("assert.equal(handle({id:'o',type:'order.created'}).topic,'orders'); for (const type of ['unknown','__proto__','constructor']) assert.throws(()=>handle({id:'x',type}));")


def test_rejects_invalid_ids():
    kind = json.dumps(CONFIG['first'])
    node(f"for (const id of ['', ' ', null, 2]) assert.throws(()=>handle({{id,type:{kind},amountCents:3}}));")


def test_catalog_updated():
    assert CONFIG['first'] in Path('docs/catalog.md').read_text()
