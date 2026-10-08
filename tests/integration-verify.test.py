"""Check prospective integration without merging or changing the source checkout."""
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('team_fixture', ROOT / 'tests/team.test.py')
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURE.TeamTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.env['PYTHONDONTWRITEBYTECODE'] = '1'
        f.write('.gitignore', '__pycache__/\n.ran\n')
        f.write('producer.py', "def emit(): return {'total': 5, 'amount': 5}\n")
        f.write('consumer.py', "def read(record): return record['total'] if 'total' in record else record['amount']\n")
        f.write('check.py', 'from producer import emit\nfrom consumer import read\nassert str(read(emit())) == "5"\n')
        command = shlex.quote(sys.executable.replace('\\', '/')) + ' check.py'
        f.write('checks-map.json', json.dumps(dict(version=1, checks=[dict(
            id='consumer', paths=['producer.py', 'consumer.py', 'check.py'], command=command)])))
        f.commit()
        f.git('branch', '-f', 'main', 'HEAD')
        f.write('producer.py', "def emit(): return {'amount': 5}\n")
        f.commit()
        f.command(sys.executable, 'check.py')
        f.git('checkout', '-qb', 'feat/frontend', 'main')
        f.write('consumer.py', "def read(record): return str(record['total'])\n")
        f.commit()
        f.command(sys.executable, 'check.py')

    def check(self, *args, expected=0):
        return json.loads(self.fixture.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'team',
                         '--against', 'feat/backend', '--json', *args, expected=expected))

    def state(self):
        return {key: self.fixture.git(*args) for key, args in dict(
            head=['rev-parse', 'HEAD'], status=['status', '--porcelain'], refs=['show-ref'],
            index=['write-tree'], worktrees=['worktree', 'list', '--porcelain'],
            objects=['count-objects', '-v']).items()}

    def test_preview_is_read_only_and_execution_requires_local_trust(self):
        before = self.state()
        plan = self.check('--plan')
        self.assertEqual(plan['status'], 'planned')
        self.assertEqual([c['id'] for c in plan['verification']['checks']], ['consumer'])
        self.assertEqual(plan['against']['commit'], self.fixture.git('rev-parse', 'feat/backend'))
        self.assertEqual(self.check('--verify', expected=2)['status'], 'untrusted')
        self.assertEqual(self.state(), before)

    def test_clean_merge_exposes_consumer_failure_and_accepts_compatible_fix(self):
        self.fixture.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'trust')
        before = self.state()
        report = self.check('--verify', expected=1)
        self.assertEqual(report['merge']['status'], 'clean')
        self.assertEqual(report['status'], 'failed')
        self.assertIn('total', report['verification']['checks'][0]['output_tail'])
        self.assertEqual(self.state(), before)
        self.fixture.write('consumer.py', "def read(record): return str(record['amount'])\n")
        self.fixture.commit()
        before = self.state()
        self.assertEqual(self.check('--verify')['status'], 'passed')
        self.assertEqual(self.state(), before)

    def test_dirty_checkout_and_missing_checks_are_not_success(self):
        self.fixture.write('consumer.py', '# unfinished change\n')
        self.assertEqual(self.check('--plan', expected=2)['status'], 'dirty')
        self.fixture.git('checkout', '--', 'consumer.py')
        self.fixture.git('rm', 'checks-map.json')
        self.fixture.commit()
        self.fixture.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'trust')
        self.assertEqual(self.check('--verify', expected=3)['status'], 'unverified')
        raw = self.fixture.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'team', '--verify',
                                  '--against', 'HEAD', '--json', expected=3)
        self.assertEqual(json.loads(raw)['status'], 'unverified')

    def test_conflicts_and_unknown_refs_do_not_run_checks(self):
        self.fixture.write('producer.py', "def emit(): return {'price': 5}\n")
        self.fixture.commit()
        self.assertEqual(self.check('--verify', expected=1)['status'], 'conflict')
        raw = self.fixture.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'team', '--verify',
                                  '--against', 'missing', '--json', expected=3)
        self.assertEqual(json.loads(raw)['status'], 'unknown')

    def test_timeout_and_invalid_arguments_are_explicit(self):
        f = self.fixture
        python = shlex.quote(sys.executable.replace('\\', '/'))
        f.write('checks-map.json', json.dumps(dict(version=1, checks=[dict(
            id='bounded', paths=['*.py'], command=python + ' -c "import time; time.sleep(20)"')])))
        f.commit()
        f.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'trust')
        before = self.state()
        result = self.check('--verify', '--budget-seconds', '1', expected=1)
        self.assertEqual(result['verification']['checks'][0]['status'], 'timed_out')
        self.assertEqual(self.state(), before)
        for args in (['--verify'], ['--plan', '--against', 'main', '--base', 'main'],
                     ['--verify', '--against', 'main', '--budget-seconds', '0']):
            f.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'team', *args, expected=2)

    def test_checks_use_temporary_checkout_and_do_not_copy_dependencies(self):
        f = self.fixture
        f.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'trust')
        f.write('check.py', "from pathlib import Path\nassert Path('.ran').is_file(), 'dependency absent'\n")
        f.commit()
        f.write('.ran', 'local dependency')
        f.command(sys.executable, 'check.py')
        result = self.check('--verify', expected=1)
        self.assertIn('dependency absent', result['verification']['checks'][0]['output_tail'])
        f.write('check.py', "from pathlib import Path\nPath('.ran').write_text('temporary output')\n")
        f.commit()
        self.assertEqual(self.check('--verify')['status'], 'passed')
        self.assertEqual((f.repo / '.ran').read_text(), 'local dependency')

    def test_unit_change_without_a_missing_field_is_detected(self):
        f = self.fixture
        f.git('checkout', '-q', 'main')
        f.write('producer.py', "def emit(): return {'value': 500, 'scale': 100}\n")
        f.write('consumer.py', "def read(record): return record['value'] / record['scale']\n")
        f.write('check.py', 'from producer import emit\nfrom consumer import read\nassert read(emit()) == 5\n')
        f.commit()
        f.git('checkout', '-B', 'feat/backend')
        f.write('producer.py', "def emit(): return {'value': 5, 'scale': 1}\n")
        f.commit()
        f.command(sys.executable, 'check.py')
        f.git('checkout', '-B', 'feat/frontend', 'main')
        f.write('consumer.py', "def read(record): return round(record['value'] / 100, 2)\n")
        f.commit()
        f.command(sys.executable, 'check.py')
        f.command(FIXTURE.BASH, str(ROOT / 'bin/tack'), 'trust')
        result = self.check('--verify', expected=1)
        self.assertEqual(result['merge']['status'], 'clean')
        self.assertIn('AssertionError', result['verification']['checks'][0]['output_tail'])
        f.write('consumer.py', "def read(record): return round(record['value'] / record['scale'], 2)\n")
        f.commit()
        self.assertEqual(self.check('--verify')['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
