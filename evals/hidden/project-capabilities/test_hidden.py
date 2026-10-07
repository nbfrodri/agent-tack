"""Acceptance of useful local artifacts and second-task behavior; traces are graded separately."""
import importlib.util
import json
from pathlib import Path
import subprocess

CONFIG = json.loads(Path('scenario.json').read_text())
ROOT = Path(__file__).resolve().parents[3]


def test_definitions_are_valid_and_discoverable():
    spec = importlib.util.spec_from_file_location('validation', ROOT / 'lib/capability_validation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert not module.project(Path.cwd())


def test_relevant_capability_exists_without_duplicates():
    role = CONFIG['scenario'] == 'capability-role'
    paths = list(Path('.agents/agents').glob('*.md')) if role else list(Path('.agents/skills').glob('*/SKILL.md'))
    assert len(paths) == 1
    text = paths[0].read_text().lower()
    assert 'contract' in text and ('npm test' in text or 'docs/contracts.md' in text)


def test_later_task_outcome():
    if CONFIG['scenario'] == 'capability-role':
        assert Path('review.md').is_file() and 'event' in Path('review.md').read_text().lower()
        return
    for kind in (CONFIG['first'], CONFIG['second']):
        code = "import assert from 'node:assert/strict';import {handle} from './src/routes.js';" + \
               f"assert.equal(handle({{id:'x',type:{json.dumps(kind)},amountCents:1}}).topic,'invoices');assert.throws(()=>handle({{id:'x',type:{json.dumps(kind)},amountCents:-1}}));"
        assert subprocess.run(['node', '--input-type=module', '-e', code], capture_output=True).returncode == 0
        assert kind in Path('docs/catalog.md').read_text()
