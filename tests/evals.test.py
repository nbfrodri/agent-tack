#!/usr/bin/env python3
"""Offline evaluation runner and transcript regression tests."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('grade', ROOT / 'evals/grade.py')
grade = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grade)


def use(name, **inputs):
    return {'type': 'assistant', 'message': {'content': [
        {'type': 'tool_use', 'id': inputs.pop('id', name), 'name': name, 'input': inputs}]}}


def result(identifier, text, failed=False):
    return {'type': 'user', 'message': {'content': [
        {'type': 'tool_result', 'tool_use_id': identifier, 'content': text, 'is_error': failed}]}}


class Metrics(unittest.TestCase):
    def measure(self, events, scenario='bug-fix', run='exit=0 seconds=7', complete_writes=True):
        if complete_writes:
            result_ids = {block.get('tool_use_id') for event in events
                          for block in event.get('message', {}).get('content', []) if block.get('type') == 'tool_result'}
            completed = []
            for event in events:
                completed.append(event)
                for block in event.get('message', {}).get('content', []):
                    if block.get('name') in ('Write', 'Edit', 'MultiEdit') and block.get('id') not in result_ids:
                        completed.append(result(block.get('id'), 'File updated successfully'))
            events = completed
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / scenario / 'baseline-1'
            (directory / 'repo').mkdir(parents=True)
            (directory / 'transcript.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
            (directory / 'run.txt').write_text(run)
            with patch.object(grade, 'git', return_value=''), patch.object(
                grade.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '1 passed', '')):
                return grade.grade(directory)

    def test_one_line_implementation_edit_precedes_test(self):
        m = self.measure([use('Edit', file_path='src/cart.py', new_string='return 0'),
                          use('Write', file_path='tests/test_cart.py', content='def test_empty():\n    assert total([]) == 0')])
        self.assertIs(m['test_written_before_code'], False)

    def measure_with_bodies(self, bodies, scenario='bug-fix'):
        def fake_git(repo, *args):
            return bodies if '--format=%B' in args else ''
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / scenario / 'baseline-1'
            (directory / 'repo').mkdir(parents=True)
            (directory / 'repo' / 'pyproject.toml').write_text('[project]\nname = "cart"\n')
            (directory / 'transcript.jsonl').write_text('')
            (directory / 'run.txt').write_text('exit=0 seconds=1')
            with patch.object(grade, 'git', side_effect=fake_git), patch.object(
                grade.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '1 passed', '')):
                return grade.grade(directory)

    def test_red_and_green_evidence_in_commit_bodies(self):
        bodies = 'fix: handle empty carts\n\nRed: uv run pytest -q -> 1 failed (test_empty)\nGreen: uv run pytest -q -> 3 passed\n'
        self.assertTrue(self.measure_with_bodies(bodies)['red_evidence_recorded'])
        self.assertFalse(self.measure_with_bodies('fix: handle empty carts\n')['red_evidence_recorded'])
        self.assertIsNone(self.measure_with_bodies(bodies, scenario='release')['red_evidence_recorded'])

    def test_measurable_criteria_before_code(self):
        def text(words):
            return {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': words}]}}
        stated = [text('Acceptance criteria:\n- R1: total() of 10,000 lines runs in under 50 ms'),
                  use('Write', file_path='src/cart/__init__.py', content='x = 1')]
        self.assertTrue(self.measure(stated, scenario='vague-requirement')['criteria_before_code'])
        skipped = [use('Write', file_path='src/cart/__init__.py', content='x = 1'), text('R1: it is faster now')]
        self.assertFalse(self.measure(skipped, scenario='vague-requirement')['criteria_before_code'])
        self.assertIsNone(self.measure(stated, scenario='bug-fix')['criteria_before_code'])
        planned = [use('Write', file_path='docs/plans/2026-10-05-speed.md', content='- R1: total() of 10,000 lines under 50 ms'),
                   use('Write', file_path='src/cart/__init__.py', content='x = 1')]
        self.assertTrue(self.measure(planned, scenario='vague-requirement')['criteria_before_code'])
        shelled = [use('Bash', command='cat > src/cart/fast.py <<EOF\nx = 1\nEOF'), text('R1: it is faster now')]
        self.assertFalse(self.measure(shelled, scenario='vague-requirement')['criteria_before_code'])

    def test_missing_evidence_is_unknown(self):
        m = self.measure([])
        for key in ('test_written_before_code', 'red_green_verified', 'cost_usd', 'input_tokens', 'planned', 'pushed_or_bypassed'):
            self.assertIsNone(m[key], key)
        self.assertEqual(m['duration_s'], 7)

    def test_test_write_without_test_execution_is_not_red_green(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')])
        self.assertTrue(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_claude_red_green_and_usage(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
            use('Bash', id='red', command='uv run pytest'), result('red', '1 failed', True),
            use('Edit', file_path='src/cart.py', new_string='return 0'),
            use('Bash', id='green', command='uv run pytest'), result('green', '1 passed'),
            {'type': 'result', 'duration_ms': 2500, 'total_cost_usd': .012,
             'usage': {'input_tokens': 2, 'cache_read_input_tokens': 3, 'output_tokens': 4}}])
        self.assertTrue(m['red_green_verified'])
        self.assertEqual(m['provider'], 'claude')
        self.assertEqual(m['input_tokens'], 5)
        self.assertEqual(m['duration_s'], 2.5)

    def test_codex_adapter(self):
        def event(item):
            return {'type': 'item.completed', 'item': item}
        m = self.measure([{'type': 'thread.started', 'thread_id': 'fixture'},
            event({'type': 'file_change', 'changes': [{'path': 'tests/test_cart.py', 'kind': 'add'}]}),
            event({'type': 'command_execution', 'command': 'uv run pytest', 'exit_code': 1, 'aggregated_output': '1 failed'}),
            event({'type': 'file_change', 'changes': [{'path': 'src/cart.py', 'kind': 'update'}]}),
            event({'type': 'command_execution', 'command': 'uv run pytest', 'exit_code': 0, 'aggregated_output': '1 passed'}),
            {'type': 'turn.completed', 'usage': {'input_tokens': 12, 'cached_input_tokens': 4, 'output_tokens': 8}}], 'codex-new-project')
        self.assertTrue(m['test_written_before_code'])
        self.assertTrue(m['red_green_verified'])
        self.assertEqual(m['provider'], 'codex')
        self.assertEqual(m['input_tokens'], 12)
        self.assertEqual(m['output_tokens'], 8)
        self.assertIsNone(m['cost_usd'])

    def test_codex_atomic_patch_has_no_file_order(self):
        m = self.measure([{'type': 'item.completed', 'item': {'type': 'file_change', 'changes': [
            {'path': 'tests/test_cart.py', 'kind': 'add'}, {'path': 'src/cart.py', 'kind': 'update'}]}}])
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_failed_test_write_cannot_prove_test_first(self):
        m = self.measure([use('Write', id='test-failed', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          result('test-failed', 'Permission denied; file not written', True),
                          use('Edit', id='implementation', file_path='src/cart.py', new_string='return 0'),
                          result('implementation', 'File updated'),
                          use('Write', id='test-real', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          result('test-real', 'File written')])
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_write_without_result_keeps_order_unknown(self):
        m = self.measure([use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')], complete_writes=False)
        self.assertIsNone(m['test_written_before_code'])
        self.assertIsNone(m['red_green_verified'])

    def test_empty_scaffold_write_does_not_precede_test(self):
        m = self.measure([use('Write', file_path='src/__init__.py', content=''),
                          use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0'),
                          use('Edit', file_path='src/cart.py', new_string='return 0')])
        self.assertTrue(m['test_written_before_code'])

    def test_malformed_transcript_makes_order_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            transcript = Path(temp) / 'transcript.jsonl'
            transcript.write_text('broken JSON\n' + json.dumps(use('Edit', file_path='src/cart.py', new_string='return 0')))
            entries = grade.observations(grade.events(transcript))
            self.assertIn({'opaque': True}, entries)

    def test_shell_writes_make_order_unknown(self):
        m = self.measure([use('Bash', command="printf 'return 0' > src/cart.py"),
                          use('Write', file_path='tests/test_cart.py', content='assert total([]) == 0')])
        self.assertIsNone(m['test_written_before_code'])




class HiddenAcceptance(unittest.TestCase):
    """Hidden tests run against the agent's code after the session; the agent never sees them."""

    def run_hidden(self, scenario, source):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'repo'
            (repo / 'src/cart').mkdir(parents=True)
            (repo / 'src/cart/__init__.py').write_text(source)
            with patch.object(grade, 'HIDDEN_RUNNER', [sys.executable]):
                return grade.hidden_acceptance(repo, scenario)

    def test_a_correct_bug_fix_passes_every_hidden_test(self):
        passed, total = self.run_hidden('bug-fix', (
            'from decimal import Decimal\n'
            'def total(items):\n    return sum((p * q for p, q in items), Decimal("0"))\n'
            'def average_price(items):\n    return sum((p for p, _ in items), Decimal("0")) / len(items) if items else Decimal("0")\n'))
        self.assertGreaterEqual(total, 3)
        self.assertEqual(passed, total)

    def test_the_seeded_bug_fails_a_hidden_test(self):
        passed, total = self.run_hidden('bug-fix', (
            'from decimal import Decimal\n'
            'def total(items):\n    return sum((p * q for p, q in items), Decimal("0"))\n'
            'def average_price(items):\n    return sum((p for p, _ in items), Decimal("0")) / len(items)\n'))
        self.assertLess(passed, total)

    def test_a_correct_new_project_passes_and_a_missing_discount_fails(self):
        correct = ('from decimal import Decimal\n'
                   'def cart_total(items):\n'
                   '    net = sum((Decimal(str(p)) * q * (Decimal("0.9") if q >= 10 else 1) for p, q in items), Decimal("0"))\n'
                   '    return net * Decimal("1.21")\n')
        passed, total = self.run_hidden('new-project', correct)
        self.assertEqual(passed, total)
        passed, total = self.run_hidden('new-project', correct.replace('if q >= 10', 'if q >= 100'))
        self.assertLess(passed, total)

    def test_conventions_pass_only_when_the_agents_md_rules_are_kept(self):
        seed = ('from decimal import ROUND_HALF_UP, Decimal\nCENT = Decimal("0.01")\n'
                'def _check(items):\n'
                '    if any(p < 0 or q < 0 for p, q in items):\n        raise ValueError("negative")\n'
                'def subtotal(items):\n    _check(items)\n'
                '    return sum((p * q for p, q in items), Decimal("0")).quantize(CENT, ROUND_HALF_UP)\n')
        correct = seed + (
            'def total(items, code=None):\n    amount = subtotal(items)\n'
            '    key = None if code is None else code.upper()\n'
            '    if key == "SAVE10":\n        amount = amount * Decimal("0.9")\n'
            '    elif key == "FLAT5":\n        amount = max(amount - 5, Decimal("0"))\n'
            '    elif key is not None:\n        raise ValueError("unknown code")\n'
            '    return amount.quantize(CENT, ROUND_HALF_UP)\n')
        passed, total = self.run_hidden('conventions', correct)
        self.assertEqual((passed, total), (8, 8))
        # The feature without the conventions: unrounded result, unknown codes ignored.
        careless = correct.replace('    elif key is not None:\n        raise ValueError("unknown code")\n', '').replace(
            '    return amount.quantize(CENT, ROUND_HALF_UP)\n', '    return amount\n')
        passed, total = self.run_hidden('conventions', careless)
        self.assertEqual(passed, 6)

    def test_attachments_catch_the_path_traversal_traps(self):
        correct = ('from pathlib import Path\n'
                   'def read_attachment(user_root, name):\n'
                   '    root = Path(user_root).resolve()\n'
                   '    path = (root / name).resolve()\n'
                   '    if not path.is_relative_to(root):\n        raise PermissionError(name)\n'
                   '    return path.read_bytes()\n')
        self.assertEqual(self.run_hidden_package('attachments', 'storage', correct), (7, 7))
        # The classic mistake: a string prefix check on an unresolved symlink-blind path.
        prefix = ('import os\n'
                  'def read_attachment(user_root, name):\n'
                  '    root = os.path.abspath(user_root)\n'
                  '    path = os.path.abspath(os.path.join(root, name))\n'
                  '    if not path.startswith(root):\n        raise PermissionError(name)\n'
                  '    return open(path, "rb").read()\n')
        self.assertEqual(self.run_hidden_package('attachments', 'storage', prefix), (5, 7))

    def run_hidden_package(self, scenario, package, source):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'repo'
            (repo / 'src' / package).mkdir(parents=True)
            (repo / 'src' / package / '__init__.py').write_text(source)
            with patch.object(grade, 'HIDDEN_RUNNER', [sys.executable]):
                return grade.hidden_acceptance(repo, scenario)

    def test_code_that_does_not_import_fails_every_hidden_test(self):
        passed, total = self.run_hidden('new-project', 'raise ImportError("broken")\n')
        self.assertEqual(passed, 0)
        self.assertGreater(total, 0)

    def test_a_missing_runner_is_unknown_not_a_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / 'repo').mkdir()
            with patch.object(grade, 'HIDDEN_RUNNER', ['/nonexistent/uv']):
                self.assertEqual(grade.hidden_acceptance(Path(temp) / 'repo', 'bug-fix')[0], None)
        self.assertIsNone(grade.hidden_verdict(None, 5))
        self.assertFalse(grade.hidden_verdict(3, 5))
        self.assertTrue(grade.hidden_verdict(5, 5))

    def test_a_float_only_new_project_passes(self):
        passed, total = self.run_hidden('new-project', (
            'def cart_total(items):\n'
            '    if any(not isinstance(p, float) for p, _ in items):\n'
            '        raise ValueError("prices must be floats")\n'
            '    return sum(p * q * (0.9 if q >= 10 else 1) for p, q in items) * 1.21\n'))
        self.assertEqual(passed, total)

    def test_scenarios_without_hidden_tests_report_nothing(self):
        self.assertEqual(grade.hidden_acceptance(Path('/nonexistent'), 'release'), (None, None))


class Outcomes(unittest.TestCase):
    """evals/outcomes.py reads escaped defects and rework from a repository's history."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.env = dict(os.environ, HOME=self.temp.name, XDG_CONFIG_HOME=self.temp.name, GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=str(Path(self.temp.name) / 'gitconfig'))
        self.git('init', '-q', '-b', 'main', str(self.repo), cwd=self.temp.name)
        self.day = 0

    def git(self, *args, cwd=None, day=None):
        env = dict(self.env, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com', GIT_COMMITTER_NAME='T',
                   GIT_COMMITTER_EMAIL='t@example.com')
        if day is not None:
            env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = f'2026-01-{day + 1:02d}T12:00:00Z'
        return subprocess.run(['git', *args], cwd=cwd or self.repo, env=env, check=True, capture_output=True, text=True).stdout

    def commit(self, day, subject, path):
        """Adds a line to path; a fix: rewrites the file's last line, as a correction would."""
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = target.read_text().splitlines() if target.exists() else []
        if subject.startswith('fix') and lines:
            lines[-1] = subject
        else:
            lines.append(subject)
        target.write_text('\n'.join(lines) + '\n')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', subject, day=day)

    def report(self, *args, **kwargs):
        spec = importlib.util.spec_from_file_location('outcomes', ROOT / 'evals/outcomes.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # measure() runs git in this process: keep it away from the real HOME and git config.
        with patch.dict(os.environ, self.env):
            return module.measure(self.repo, *args, **kwargs)

    def build(self):
        self.commit(0, 'feat: add a', 'a.py')
        self.commit(2, 'fix: correct a', 'a.py')
        self.commit(3, 'feat: add b', 'b.py')
        self.commit(20, 'fix: correct b much later', 'b.py')
        self.commit(21, 'Revert "feat: add b"', 'b.py')
        self.commit(21, 'docs(handoffs): record progress', 'docs/handoffs/x.md')
        self.git('switch', '-q', '-c', 'feat/c')
        self.commit(22, 'feat: add c', 'c.py')
        self.git('switch', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '-m', 'Merge branch feat/c', 'feat/c', day=23)

    def test_a_fix_to_a_feature_within_the_window_is_an_escaped_defect(self):
        self.build()
        metrics = self.report(14)
        self.assertEqual(metrics['features'], 3)
        self.assertEqual(metrics['escaped_defects'], 1)
        self.assertEqual(metrics['escaped_defect_rate'], 33)

    def test_a_wider_window_counts_the_later_fix_too(self):
        self.build()
        self.assertEqual(self.report(30)['escaped_defects'], 2)

    def test_rework_reverts_bookkeeping_and_lead_time(self):
        self.build()
        metrics = self.report(14)
        self.assertEqual(metrics['commits'], 7)
        self.assertEqual(metrics['fixes'], 2)
        self.assertEqual(metrics['fixes_before_merge'], 0)
        self.assertEqual(metrics['reverts'], 1)
        self.assertEqual(metrics['bookkeeping_commits'], 1)
        self.assertEqual(metrics['merges'], 1)
        self.assertEqual(metrics['median_lead_time_hours'], 24)

    def test_a_fix_before_the_merge_is_caught_not_escaped(self):
        self.commit(0, 'chore: start', 'README.md')
        self.git('switch', '-q', '-c', 'feat/d')
        self.commit(0, 'feat: add d', 'd.py')
        self.commit(1, 'fix: review finding in d', 'd.py')
        self.git('switch', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '-m', 'Merge branch feat/d', 'feat/d', day=2)
        metrics = self.report(14)
        self.assertEqual(metrics['escaped_defects'], 0)
        self.assertEqual(metrics['fixes_before_merge'], 1)

    def test_shared_docs_and_tests_do_not_link_a_fix_to_a_feature(self):
        self.commit(0, 'feat: add e', 'docs/usage.md')
        self.commit(0, 'feat: add e code', 'e.py')
        self.commit(1, 'fix: unrelated, same docs and tests', 'docs/usage.md')
        self.commit(1, 'test: cover f', 'tests/test_e.py')
        metrics = self.report(14)
        self.assertEqual(metrics['escaped_defects'], 0)

    def test_a_fix_that_only_adds_lines_is_not_linked(self):
        self.commit(0, 'feat: add g', 'g.py')
        (self.repo / 'g.py').write_text((self.repo / 'g.py').read_text() + 'extra guard\n')
        self.git('commit', '-qam', 'fix: add a missing guard', day=1)
        self.assertEqual(self.report(14)['escaped_defects'], 0)

    def test_the_measured_ref_excludes_a_feature_branch_s_own_fixes(self):
        self.commit(0, 'chore: start', 'README.md')
        self.git('switch', '-q', '-c', 'feat/h')
        self.commit(1, 'feat: add h', 'h.py')
        self.commit(2, 'fix: review finding in h', 'h.py')
        self.assertEqual(self.report(14, ref='main')['features'], 0)
        self.assertEqual(self.report(14, ref='feat/h')['features'], 1)

    def test_paths_with_spaces_and_user_diff_settings_still_link(self):
        self.git('config', 'diff.noprefix', 'true')
        self.git('config', 'color.diff', 'always')
        self.commit(0, 'feat: add spaced', 'sp ace.py')
        self.commit(1, 'chore: next step', 'other.py')
        self.commit(2, 'fix: correct spaced', 'sp ace.py')
        self.assertEqual(self.report(14)['escaped_defects'], 1)

    def test_empty_repositories_and_root_fixes_report_without_errors(self):
        self.assertEqual(self.report(14)['commits'], 0)
        self.commit(0, 'fix: first commit', 'a.py')
        self.assertEqual(self.report(14)['fixes'], 1)

    def test_cli_rejects_bad_options_without_a_traceback(self):
        for args in (['--days'], ['--days', 'abc']):
            result = subprocess.run([sys.executable, str(ROOT / 'evals/outcomes.py'), str(self.repo), *args],
                                    env=self.env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_cli_prints_a_table_and_json(self):
        self.build()
        table = subprocess.run([sys.executable, str(ROOT / 'evals/outcomes.py'), str(self.repo)], env=self.env,
                               capture_output=True, text=True, check=True).stdout
        self.assertIn('| Escaped defects |', table)
        data = json.loads(subprocess.run([sys.executable, str(ROOT / 'evals/outcomes.py'), str(self.repo), '--json'],
                                         env=self.env, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(data['reverts'], 1)

class Runner(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'home/.codex').mkdir(parents=True)
        (self.root / 'home/.codex/auth.json').write_text('{"fixture": "fake-auth"}')
        (self.root / 'bin').mkdir()
        self.env = dict(os.environ, HOME=str(self.root / 'home'), XDG_CONFIG_HOME=str(self.root / 'home/.config'),
                        CODEX_HOME=str(self.root / 'home/.codex'), GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=str(self.root / 'gitconfig'), EVALS_OUT=str(self.root / 'out'),
                        PATH=str(self.root / 'bin') + ':' + os.environ['PATH'])
        subprocess.run(['git', 'config', '--file', self.env['GIT_CONFIG_GLOBAL'], 'user.name', 'Eval'], env=self.env, check=True)
        subprocess.run(['git', 'config', '--file', self.env['GIT_CONFIG_GLOBAL'], 'user.email', 'eval@example.com'], env=self.env, check=True)

    def stub(self, name, body):
        path = self.root / 'bin' / name
        path.write_text('#!/usr/bin/env bash\n' + body + '\n')
        path.chmod(0o755)

    def run_eval(self, scenario, condition='baseline'):
        return subprocess.run(['bash', str(ROOT / 'evals/run.sh'), scenario, condition], env=self.env, capture_output=True, text=True)

    def test_mode_conditions_enable_the_project_at_that_mode(self):
        self.stub('claude', 'if [ "$1" = --version ]; then echo fixture-cli; exit; fi\n'
                  '{ harness status --quiet && echo enabled; git config --local --get tack.mode; } > "' + str(self.root / 'state') + '"')
        (self.root / 'bin/harness').symlink_to(ROOT / 'bin/tack')
        for condition, mode in (('lite', 'lite'), ('lean', 'lean'), ('standard', 'standard'), ('strict', 'strict'), ('auto', 'auto'), ('harness', 'auto')):
            with self.subTest(condition=condition):
                outcome = self.run_eval('bug-fix', condition)
                self.assertEqual(outcome.returncode, 0, outcome.stderr)
                self.assertEqual((self.root / 'state').read_text().split(), ['enabled', mode])
                metadata = json.loads((self.root / 'out/bug-fix' / (condition + '-1') / 'metadata.json').read_text())
                self.assertEqual(metadata['workflow_mode'], mode)

    def test_baseline_has_no_workflow_mode(self):
        self.stub('claude', 'exit 0')
        self.assertEqual(self.run_eval('bug-fix').returncode, 0)
        metadata = json.loads((self.root / 'out/bug-fix/baseline-1/metadata.json').read_text())
        self.assertIsNone(metadata['workflow_mode'])

    def test_unknown_condition_is_rejected(self):
        self.assertEqual(self.run_eval('bug-fix', 'turbo').returncode, 2)

    def test_cli_failure_retains_transcript_and_status(self):
        self.stub('claude', 'echo partial; echo diagnostic >&2; exit 42')
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 42)
        run = self.root / 'out/bug-fix/baseline-1'
        self.assertIn('exit=42', (run / 'run.txt').read_text())
        self.assertIn('partial', (run / 'transcript.jsonl').read_text())
        self.assertIn('diagnostic', (run / 'stderr.log').read_text())

    def test_explicit_model_and_reproducibility_metadata(self):
        self.env['EVALS_MODEL'] = 'fixture-model'
        self.stub('claude', 'if [ "$1" = --version ]; then echo fixture-cli; exit; fi\n'
                  'printf "%s\\n" "$@" > "' + str(self.root / 'args') + '"\n'
                  "echo '{\"type\":\"system\",\"subtype\":\"init\",\"model\":\"fixture-resolved\"}'")
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        metadata = json.loads((self.root / 'out/bug-fix/baseline-1/metadata.json').read_text())
        import hashlib
        prompt = (self.root / 'out/bug-fix/baseline-1/prompt.txt').read_bytes()
        self.assertEqual(metadata['prompt_sha256'], hashlib.sha256(prompt).hexdigest())
        self.assertEqual(metadata['requested_model'], 'fixture-model')
        self.assertEqual(metadata['resolved_model'], 'fixture-resolved')
        self.assertEqual(metadata['cli_version'], 'fixture-cli')
        self.assertEqual(metadata['metrics_version'], 2)
        self.assertEqual(metadata['permission_mode'], 'acceptEdits')
        self.assertIn('Bash(uv *)', metadata['allowed_tools'])
        # Agents often run `python -m pytest`, sometimes with an environment prefix; a blocked test
        # command makes the workflow stop before committing, which skews every comparison.
        for rule in ('Bash(python *)', 'Bash(PYTHONPATH=*)', 'Bash(tail *)'):
            self.assertIn(rule, metadata['allowed_tools'])
        self.assertIn('Agent', metadata['allowed_tools'])
        self.assertEqual(metadata['condition'], 'baseline')
        self.assertEqual(metadata['provider'], 'claude')
        self.assertEqual(len(metadata['harness_revision']), 40)
        self.assertIn('--model\nfixture-model', (self.root / 'args').read_text())

    def test_setup_failure_does_not_invoke_cli(self):
        self.stub('git', 'if [ "$1" = init ]; then echo setup-failed >&2; exit 23; fi\nexec /usr/bin/git "$@"')
        self.stub('claude', 'echo wrongly-invoked')
        outcome = self.run_eval('bug-fix')
        self.assertEqual(outcome.returncode, 23)
        run = self.root / 'out/bug-fix/baseline-1'
        self.assertFalse((run / 'transcript.jsonl').exists())
        self.assertIn('exit=23', (run / 'run.txt').read_text())

    def test_successful_claude_scenarios_have_baseline_flags(self):
        self.stub('claude', 'printf "%s\\n" "$@"; exit 0')
        for scenario in ('new-project', 'bug-fix', 'release', 'vague-requirement'):
            with self.subTest(scenario=scenario):
                outcome = self.run_eval(scenario)
                self.assertEqual(outcome.returncode, 0, outcome.stderr)
                transcript = self.root / 'out' / scenario / 'baseline-1/transcript.jsonl'
                self.assertIn('--setting-sources', transcript.read_text())
                self.assertIn('--disable-slash-commands', transcript.read_text())

    def test_codex_baseline_isolates_config_and_retains_auth(self):
        self.stub('codex', 'test "$HOME" != "' + str(self.root / 'home') + '" || exit 61\n'
                  'test -f "$CODEX_HOME/auth.json" || exit 62\n'
                  'test ! -f "$CODEX_HOME/config.toml" || exit 63\n'
                  "python3 - <<'CHECK'\nimport os, stat\nassert stat.S_IMODE(os.stat(os.environ['CODEX_HOME'] + '/auth.json').st_mode) == 0o600\nCHECK\n"
                  'echo "$CODEX_HOME" > "' + str(self.root / 'isolated-home') + '"\necho fixture')
        (self.root / 'home/.codex/config.toml').write_text('fixture = true')
        outcome = self.run_eval('codex-new-project')
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertFalse(Path((self.root / 'isolated-home').read_text().strip()).exists())
        self.assertTrue((self.root / 'home/.codex/auth.json').exists())
        self.assertFalse(list((self.root / 'out').rglob('auth.json')))


class Report(unittest.TestCase):
    def test_unknowns_and_incompatible_versions_are_not_combined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rep, version, provider, value in ((1, 2, 'claude', None), (2, 2, 'codex', True), (3, None, None, False)):
                directory = root / 'new-project' / ('baseline-' + str(rep))
                directory.mkdir(parents=True)
                metrics = {'scenario': 'new-project', 'condition': 'baseline', 'test_written_before_code': value}
                if version is not None:
                    metrics.update(metrics_version=version, provider=provider)
                (directory / 'metrics.json').write_text(json.dumps(metrics))
            output = subprocess.run(['python3', str(ROOT / 'evals/report.py'), str(root)], capture_output=True, text=True, check=True).stdout
            self.assertEqual(output.count('### new-project'), 3)
            self.assertIn('Provider: codex', output)
            self.assertIn('metrics version: legacy', output)
            self.assertIn('| Test written before code | 1/1 |', output)
            self.assertNotIn('1/3', output)

    def test_every_condition_gets_a_column_in_a_stable_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for condition, value in (('strict', True), ('baseline', False), ('lite', True)):
                directory = root / 'bug-fix' / (condition + '-1')
                directory.mkdir(parents=True)
                metrics = {'scenario': 'bug-fix', 'condition': condition, 'metrics_version': 2, 'provider': 'claude',
                           'test_written_before_code': value}
                (directory / 'metrics.json').write_text(json.dumps(metrics))
            output = subprocess.run(['python3', str(ROOT / 'evals/report.py'), str(root)], capture_output=True, text=True, check=True).stdout
            self.assertIn('| Metric | Baseline | Lite | Strict |', output)
            self.assertIn('| Test written before code | 0/1 | 1/1 | 1/1 |', output)
            self.assertIn('baseline: 1 runs; lite: 1 runs; strict: 1 runs', output)

    def test_hidden_acceptance_is_reported_first_as_an_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for condition, passed in (('baseline', 3), ('auto', 5)):
                directory = root / 'bug-fix' / (condition + '-1')
                directory.mkdir(parents=True)
                metrics = {'scenario': 'bug-fix', 'condition': condition, 'metrics_version': 2, 'provider': 'claude',
                           'hidden_passed': passed, 'hidden_total': 5, 'hidden_pass': passed == 5, 'commits': 1}
                (directory / 'metrics.json').write_text(json.dumps(metrics))
            output = subprocess.run(['python3', str(ROOT / 'evals/report.py'), str(root)], capture_output=True, text=True, check=True).stdout
            self.assertIn('| Hidden acceptance tests: all pass | 0/1 | 1/1 |', output)
            self.assertIn('| Hidden acceptance tests passed (mean count) | 3.0 | 5.0 |', output)
            self.assertLess(output.index('Hidden acceptance'), output.index('| Commits |'))


if __name__ == '__main__':
    unittest.main()
