"""Real filesystem regressions: no model calls, network, or user's HOME/configuration."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import ownership
from ownership_platform import (WINDOWS, canonical, no_symlink_ancestors, parent_identity,
                                plain_path, validate_private, windows_acl)

REPO = Path(__file__).resolve().parents[1]


def msys(path):
    if not WINDOWS:
        return str(path)
    return subprocess.check_output(["cygpath", "-u", str(path)], text=True, encoding="utf-8").strip()


def powershell(script, path, destination=""):
    env = dict(os.environ, TACK_TEST_PATH=str(path), TACK_TEST_DEST=str(destination))
    return subprocess.check_output(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                                    "$ErrorActionPreference='Stop'; " + script], env=env, text=True).strip()


class OwnershipPlatformTest(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        self.old_mask = os.umask(0o077)
        self.temp = tempfile.TemporaryDirectory(prefix="ownership spaces ", dir=os.environ["HOME"])
        self.home = Path(self.temp.name) / "home"
        if WINDOWS:
            windows_acl("create", self.home)
        else:
            self.home.mkdir(mode=0o700)
        os.environ.update(HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"))
        self.state = self.home / ".local/state/agent-tack/ownership"
        (self.state / "entries").mkdir(parents=True, mode=0o700)
        for name, value in {"version": "1", "home": msys(self.home), "repo": msys(REPO)}.items():
            self.put(self.state / name, value)

    def tearDown(self):
        self.temp.cleanup()
        os.umask(self.old_mask)
        os.environ.clear()
        os.environ.update(self.original_env)

    @staticmethod
    def put(path, value):
        path.write_text(str(value) + "\n", encoding="utf-8")

    def entry(self, kind, path, **values):
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = self.state / "entries" / str(len(list((self.state / "entries").iterdir())) + 1)
        entry.mkdir(mode=0o700)
        fields = dict(kind=kind, path=msys(path), parent=msys(path.parent.resolve()),
                      repo=msys(REPO), parent_identity=parent_identity(path.parent), **values)
        if WINDOWS:
            fields["native_identity"] = "1"
        for name, value in fields.items():
            self.put(entry / name, value)
        return entry

    def generated(self):
        path = self.home / ".codex/agents/reviewer.toml"
        entry = self.entry("generated", path, sha256=hashlib.sha256(b"installed").hexdigest())
        path.write_bytes(b"installed")
        return entry, path

    def test_path_aliases_and_unsafe_paths(self):
        self.assertEqual(canonical(str(self.home)), canonical(msys(self.home)))
        for suffix in ("/../other", "/./other", "/bad\nname", "/bad\tname"):
            with self.assertRaises(ValueError):
                canonical(str(self.home) + suffix)
        self.assertFalse(plain_path("relative/path"))
        if WINDOWS:
            self.assertEqual(canonical(str(self.home).upper()), canonical(str(self.home)))
            self.assertFalse(plain_path(str(self.home / "config.json") + ":stream"))
            self.assertFalse(plain_path("\\\\server\\share\\file"))
            # /tmp is a mount alias, not C:/tmp; this is the original #111 reproduction.
            temporary = Path(subprocess.check_output(["cygpath", "-m", "/tmp"], text=True).strip())
            self.assertEqual(canonical(str(temporary)), canonical("/tmp"))

    def test_validation_and_generated_uninstall(self):
        entry, path = self.generated()
        self.assertEqual(ownership.validate(self.state, str(self.home)), [entry])
        self.assertTrue(ownership.uninstall_entry(entry, True))
        self.assertTrue(path.exists())
        self.assertTrue(ownership.uninstall_entry(entry, False))
        self.assertFalse(path.exists())

    def test_edited_generated_file_is_preserved(self):
        entry, path = self.generated()
        path.write_bytes(b"user edit")
        self.assertFalse(ownership.uninstall_entry(entry, False))
        self.assertEqual(path.read_bytes(), b"user edit")

    def test_replaced_parent_is_preserved(self):
        entry, path = self.generated()
        path.parent.rename(path.parent.with_name("original"))
        path.parent.mkdir()
        path.write_bytes(b"installed")
        self.assertFalse(ownership.uninstall_entry(entry, False))
        self.assertTrue(path.exists())

    def test_settings_restore_preserves_later_user_keys_and_permissions(self):
        path = self.home / ".claude/settings.json"
        before, after = {"user": "original"}, {"user": "original", "managed": True}
        entry = self.entry("settings", path, before=json.dumps(before), after=json.dumps(after),
                           managed=json.dumps({"managed": True}))
        path.write_text(json.dumps(dict(after, later="preserved")), encoding="utf-8")
        ownership.validate(self.state, str(self.home))
        ownership.uninstall_entry(entry, False)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), dict(before, later="preserved"))
        validate_private(path.parent)

    def test_git_native_target_restores_previous_value(self):
        path = self.home / ".gitconfig"
        entry = self.entry("git", path, target=msys(REPO / "git-hooks"), before="previous hooks", before_present="1")
        (entry / "before").write_text("previous hooks", encoding="utf-8")
        subprocess.run(["git", "config", "--file", str(path), "core.hooksPath", str(REPO / "git-hooks")], check=True)
        ownership.validate(self.state, str(self.home))
        self.assertTrue(ownership.uninstall_entry(entry, False))
        value = subprocess.check_output(["git", "config", "--file", str(path), "core.hooksPath"], text=True)
        self.assertEqual(value.strip(), "previous hooks")

    def test_exposed_metadata_is_refused_before_uninstall(self):
        entry, path = self.generated()
        exposed = entry / "path"
        if WINDOWS:
            powershell("$acl=Get-Acl -LiteralPath $env:TACK_TEST_PATH; "
                       "$sid=[System.Security.Principal.SecurityIdentifier]::new('S-1-1-0'); "
                       "$rule=[System.Security.AccessControl.FileSystemAccessRule]::new($sid,'Read','Allow'); "
                       "$acl.AddAccessRule($rule); Set-Acl -LiteralPath $env:TACK_TEST_PATH -AclObject $acl", exposed)
        else:
            exposed.chmod(0o644)
        with self.assertRaises(ValueError):
            ownership.validate(self.state, str(self.home))
        result = subprocess.run([sys.executable, str(REPO / "lib/ownership.py"), "uninstall",
                                 str(self.state), str(self.home)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), b"installed")

    def test_multiple_git_values_are_preserved(self):
        path = self.home / ".gitconfig"
        entry = self.entry("git", path, target=msys(REPO / "git-hooks"), before="")
        (entry / "before").write_text("", encoding="utf-8")
        command = ["git", "config", "--file", str(path), "--add", "core.hooksPath"]
        subprocess.run(command + [str(REPO / "git-hooks")], check=True)
        subprocess.run(command + [""], check=True)
        previous = path.read_bytes()
        ownership.validate(self.state, str(self.home))
        self.assertFalse(ownership.uninstall_entry(entry, False))
        self.assertEqual(path.read_bytes(), previous)

    @unittest.skipUnless(WINDOWS, "native Windows directory identity")
    def test_legacy_msys_identity_is_verified(self):
        entry, path = self.generated()
        identity = subprocess.check_output(["stat", "-c", "%d:%i", str(path.parent)], text=True).strip()
        self.put(entry / "parent_identity", identity)
        (entry / "native_identity").unlink()
        self.assertTrue(ownership.same_parent(entry, path))
        self.put(entry / "parent_identity", "1:1")
        self.assertFalse(ownership.uninstall_entry(entry, False))
        self.assertTrue(path.exists())

    @unittest.skipUnless(WINDOWS, "native Windows junctions")
    def test_junction_metadata_and_ancestors_are_refused(self):
        destination = self.home / "elsewhere"
        destination.mkdir()
        junction = self.state / "redirect"
        powershell("New-Item -ItemType Junction -Path $env:TACK_TEST_PATH -Target $env:TACK_TEST_DEST | Out-Null",
                   junction, destination)
        try:
            self.assertFalse(no_symlink_ancestors(junction / "child", self.home))
            with self.assertRaises(ValueError):
                ownership.validate(self.state, str(self.home))
        finally:
            junction.rmdir()
        self.assertTrue(destination.is_dir())

    def test_managed_link_restores_original_directory_link(self):
        path = self.home / ".agents/tack"
        original = self.home / "original"
        original.mkdir()
        entry = self.entry("link", path, target=msys(REPO), before_kind="symlink",
                           before_target=msys(original), before_directory="1")
        try:
            path.symlink_to(REPO, target_is_directory=True)
        except OSError as exc:
            if WINDOWS and getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows symlink privilege unavailable; CI smoke requires it")
            raise
        ownership.validate(self.state, str(self.home))
        self.assertTrue(ownership.uninstall_entry(entry, False))
        self.assertTrue(path.is_symlink())
        self.assertEqual(path.resolve(), original.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
