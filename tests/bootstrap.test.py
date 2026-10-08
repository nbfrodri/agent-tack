#!/usr/bin/env python3
"""Collaborator setup with local Git sources and disposable machine configuration."""
import json
import importlib.util
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
SOURCE = 'https://fixture.invalid/team/tack.git'


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tack-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.home = self.directory / 'home'
        self.project = self.directory / 'project'
        self.source = self.directory / 'source'
        for path in (self.home, self.project, self.source):
            path.mkdir()
        real_home = Path.home().resolve()
        paths = [p for p in os.environ.get('PATH', '').split(os.pathsep)
                 if p and not Path(p).resolve().is_relative_to(real_home)]
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / '.config'), XDG_DATA_HOME=str(self.home / '.local/share'),
                        XDG_STATE_HOME=str(self.home / '.state'), GIT_CONFIG_GLOBAL=str(self.home / '.gitconfig'),
                        GIT_CONFIG_NOSYSTEM='1', PATH=os.pathsep.join(paths))
        for key in list(self.env):
            if key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) or key in (
                    'GIT_CONFIG_COUNT', 'GIT_DIR', 'GIT_WORK_TREE', 'BASH_ENV', 'ENV'):
                self.env.pop(key)
        # Keep the interpreter available even when the real user's PATH entries are removed.
        tool_dir = self.directory / 'tools'
        tool_dir.mkdir()
        python_shim = tool_dir / 'python3'
        python_shim.write_bytes(('#!/usr/bin/env bash\nexec ' + shlex.quote(Path(sys.executable).as_posix()) + ' "$@"\n').encode())
        python_shim.chmod(0o755)
        self.env['PATH'] = str(tool_dir) + os.pathsep + self.env['PATH']
        for path in (self.project, self.source):
            self.command('git', 'init', '-q', '-b', 'main', cwd=path)
            self.command('git', 'config', 'user.name', 'Test', cwd=path)
            self.command('git', 'config', 'user.email', 'test@example.invalid', cwd=path)
        self.source.joinpath('bin').mkdir()
        self.source.joinpath('bin/tack').write_bytes(b'#!/usr/bin/env bash\necho fixture\n')
        self.source.joinpath('install.sh').write_bytes(
            b'#!/usr/bin/env bash\nset -eu\nprintf "%s\\n" "$@" >> "$HOME/installed.txt"\n')
        self.command('git', 'add', '.', cwd=self.source)
        self.command('git', 'commit', '-qm', 'test: source', cwd=self.source)
        self.revision = self.command('git', 'rev-parse', 'HEAD', cwd=self.source).strip()
        self.command('git', 'config', '--global', 'url.' + self.source.as_uri() + '.insteadOf', SOURCE)

    def command(self, *args, cwd=None, expected=0):
        result = subprocess.run(args, cwd=cwd or self.project, env=self.env, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=40)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def generate(self, *args, expected=0):
        return self.command(BASH, str(ROOT / 'bin/tack'), 'bootstrap', '--source', SOURCE,
                            '--revision', self.revision, *args, expected=expected)

    def run_setup(self, *args, expected=0):
        return self.command(sys.executable, str(self.project / 'scripts/setup-tack.py'),
                            *args, expected=expected)

    def recipe(self):
        return self.project / 'scripts/tack-install.json'

    def cache(self):
        return next((self.home / '.local/share/agent-tack/bootstrap').glob('*/*/install.sh')).parent

    def test_preview_and_generation_do_not_install_activate_or_overwrite(self):
        before = self.command('git', 'config', '--local', '--list')
        self.generate('--dry-run')
        self.assertFalse((self.project / 'scripts').exists())
        self.generate()
        recipe = json.loads(self.recipe().read_text(encoding='utf-8'))
        self.assertEqual(recipe, {'version': 1, 'source': SOURCE, 'revision': self.revision})
        self.assertEqual(self.command('git', 'config', '--local', '--list'), before)
        self.assertFalse((self.project / '.tack').exists())
        self.assertFalse((self.project / 'tack.json').exists())
        self.assertFalse((self.home / 'installed.txt').exists())
        original = self.recipe().read_bytes()
        self.generate(expected=2)
        self.assertEqual(self.recipe().read_bytes(), original)

    def test_noninteractive_setup_requires_consent_and_preview_writes_nothing(self):
        self.generate()
        self.run_setup('--dry-run')
        self.run_setup(expected=2)
        self.assertFalse((self.home / '.local/share').exists())
        self.assertFalse((self.home / 'installed.txt').exists())

    def test_installs_exact_revision_without_plugins_and_preserves_project_state(self):
        self.generate()
        before = self.command('git', 'config', '--local', '--list')
        self.run_setup('--yes')
        self.assertEqual((self.home / 'installed.txt').read_text(encoding='utf-8'), '--skip-plugins\n')
        self.assertEqual(self.command('git', 'rev-parse', 'HEAD', cwd=self.cache()).strip(), self.revision)
        self.assertEqual(self.command('git', 'config', '--local', '--list'), before)
        self.assertFalse((self.project / '.tack').exists())
        self.assertFalse((self.project / 'tack.json').exists())
        self.run_setup('--yes')
        self.assertEqual(len(list((self.home / '.local/share/agent-tack/bootstrap').glob('*/*/install.sh'))), 1)

    def test_existing_installation_is_preserved(self):
        existing = self.home / '.local/bin/tack'
        existing.parent.mkdir(parents=True)
        existing.write_text('#!/usr/bin/env bash\necho personal\n', encoding='utf-8')
        existing.chmod(0o755)
        self.generate()
        output = self.run_setup('--yes')
        self.assertIn('existing', output.lower())
        self.assertFalse((self.home / 'installed.txt').exists())
        self.assertFalse((self.home / '.local/share').exists())
        self.assertIn('personal', existing.read_text(encoding='utf-8'))

    def test_inherited_git_directory_cannot_redirect_setup_into_the_project(self):
        self.generate()
        before = self.command('git', 'config', '--local', '--list')
        self.env.update(GIT_DIR=str(self.project / '.git'), GIT_WORK_TREE=str(self.project),
                        GIT_INDEX_FILE=str(self.project / '.git/custom-index'))
        self.run_setup('--yes')
        for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
            self.env.pop(key)
        self.assertEqual(self.command('git', 'config', '--local', '--list'), before)
        self.assertFalse((self.project / '.git/custom-index').exists())
        self.assertFalse((self.project / 'install.sh').exists())

    def test_rejects_bad_revision_credentials_duplicate_keys_and_extra_recipe_options(self):
        for extra in [('--revision', 'main'), ('--source', 'https://user:secret@example.invalid/tack'),
                      ('--source', 'file:///tmp/source'), ('--directory', '../outside')]:
            self.generate(*extra, expected=2)
        self.generate()
        for content in ['{"version":1,"version":1}', json.dumps({
                'version': 1, 'source': SOURCE, 'revision': self.revision, 'command': 'anything'})]:
            self.recipe().write_text(content, encoding='utf-8')
            self.run_setup('--yes', expected=2)
        self.assertFalse((self.home / 'installed.txt').exists())

    def test_mismatched_or_dirty_cached_checkout_is_not_executed(self):
        self.generate()
        self.run_setup('--yes')
        installed = (self.home / 'installed.txt').read_bytes()
        self.cache().joinpath('install.sh').write_text('exit 99\n', encoding='utf-8')
        self.run_setup('--yes', expected=2)
        self.assertEqual((self.home / 'installed.txt').read_bytes(), installed)
        self.command('git', 'restore', 'install.sh', cwd=self.cache())
        self.command('git', 'remote', 'set-url', 'origin', 'https://different.invalid/tack', cwd=self.cache())
        self.run_setup('--yes', expected=2)
        self.assertEqual((self.home / 'installed.txt').read_bytes(), installed)

    def test_invalid_fetched_revision_never_runs_installer(self):
        self.generate('--revision', 'a' * 40)
        self.run_setup('--yes', expected=2)
        self.assertFalse((self.home / 'installed.txt').exists())

    def test_linked_cache_parent_is_not_followed(self):
        self.generate()
        data = self.home / '.local/share'
        data.mkdir(parents=True)
        outside = self.directory / 'outside-cache'
        outside.mkdir()
        try:
            (data / 'agent-tack').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation requires local permission')
        self.run_setup('--yes', expected=2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_destination_is_preserved(self):
        outside = self.directory / 'outside'
        outside.mkdir()
        try:
            (self.project / 'scripts').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation requires local permission')
        self.generate(expected=2)
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == 'nt', 'Windows junction behavior')
    def test_junction_destination_is_preserved(self):
        outside = self.directory / 'junction-target'
        outside.mkdir()
        link = self.project / 'scripts'
        self.command('cmd', '/d', '/c', 'mklink', '/J', str(link), str(outside))
        self.addCleanup(link.rmdir)
        self.generate(expected=2)
        self.assertEqual(list(outside.iterdir()), [])
        spec = importlib.util.spec_from_file_location('bootstrap', ROOT / 'skills/new-project/assets/setup-tack.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # This API did not exist on the project's minimum supported Python version.
        with patch.object(type(link), 'is_junction', return_value=False, create=True):
            with self.assertRaises(ValueError):
                module.no_symlinks(link, self.project)

    def test_failed_installer_reports_failure_and_keeps_checkout_for_review(self):
        self.source.joinpath('install.sh').write_bytes(b'exit 7\n')
        self.command('git', 'add', '.', cwd=self.source)
        self.command('git', 'commit', '-qm', 'test: failing installer', cwd=self.source)
        self.revision = self.command('git', 'rev-parse', 'HEAD', cwd=self.source).strip()
        self.generate()
        output = self.run_setup('--yes', expected=2)
        self.assertIn('7', output)
        self.assertTrue(self.cache().is_dir())


if __name__ == '__main__':
    unittest.main()
