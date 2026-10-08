"""Private setup preserves files and works with linked worktrees and local excludes."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notes', ROOT / 'skills/project-docs/assets/setup-private.py')
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class PrivateNotes(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        home = self.base / 'home'
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update(HOME=str(home), USERPROFILE=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                   GIT_CONFIG_GLOBAL=str(home / '.gitconfig'), GIT_CONFIG_NOSYSTEM='1')
        guard = patch.dict(os.environ, env, clear=True)
        guard.start()
        self.addCleanup(guard.stop)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')

    def git(self, *args, root=None):
        return subprocess.check_output(['git', '-C', str(root or self.repo), *args], text=True, encoding='utf-8').strip()

    def test_preview_and_repeat_preserve_notes_and_shared_ignore(self):
        notes.prepare(self.repo, shared=True, preview=True)
        self.assertFalse((self.repo / '.private').exists())
        (self.repo / '.gitignore').write_bytes(b'build/\r\n')
        notes.prepare(self.repo, shared=True)
        note = self.repo / '.private/tack/task.md'
        note.write_text('personal context', encoding='utf-8')
        before = (self.repo / '.gitignore').read_bytes()
        notes.prepare(self.repo, shared=True)
        self.assertEqual((self.repo / '.gitignore').read_bytes(), before)
        self.assertTrue(before.startswith(b'build/\r\n'))
        self.assertEqual(note.read_text(encoding='utf-8'), 'personal context')
        self.assertEqual(self.git('check-ignore', '.private/tack/task.md'), '.private/tack/task.md')

    def test_local_exclude_in_linked_worktree_preserves_shared_settings(self):
        self.git('commit', '--allow-empty', '-qm', 'test: seed')
        self.git('config', 'tack.mode', 'strict')
        linked = self.base / 'linked'
        self.git('worktree', 'add', '-q', '-b', 'task', str(linked))
        notes.prepare(linked)
        self.assertTrue((linked / '.private/tack').is_dir())
        self.assertFalse((linked / '.gitignore').exists())
        self.assertFalse((self.repo / '.private').exists())
        self.assertEqual(self.git('config', '--local', '--get', 'tack.mode', root=linked), 'strict')
        self.assertTrue(Path(notes.git(linked, 'rev-parse', '--path-format=absolute', '--git-path', 'info/exclude')).is_file())

    def test_tracked_private_files_and_file_destinations_are_rejected_before_writes(self):
        (self.repo / '.private').mkdir()
        (self.repo / '.private/keep.txt').write_text('keep', encoding='utf-8')
        self.git('add', '.private/keep.txt')
        with self.assertRaises(ValueError):
            notes.prepare(self.repo, shared=True)
        self.assertFalse((self.repo / '.gitignore').exists())

    def test_project_exception_cannot_silently_expose_private_notes(self):
        (self.repo / '.gitignore').write_text('!/.private/\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'overriding rules'):
            notes.prepare(self.repo)
        self.assertFalse((self.repo / '.private').exists())
        notes.prepare(self.repo, shared=True)
        self.assertEqual(self.git('check-ignore', '.private/tack/task.md'), '.private/tack/task.md')

    def test_linked_notes_destination_is_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        try:
            (self.repo / '.private').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):
            notes.prepare(self.repo, shared=True)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
