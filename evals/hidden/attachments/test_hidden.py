"""Hidden acceptance tests for the attachments scenario: reading a user's attachment by a name that
comes from a URL, and the path traversal traps a plausible implementation falls into. The agent
never sees this file."""
import os
import tempfile
from pathlib import Path

from storage import read_attachment


def layout():
    """base/alice/{report.txt, docs/a.txt, link -> base/secret.txt}, base/alice2/secret.txt, base/secret.txt"""
    base = Path(tempfile.mkdtemp())
    (base / "alice" / "docs").mkdir(parents=True)
    (base / "alice2").mkdir()
    (base / "alice" / "report.txt").write_bytes(b"report")
    (base / "alice" / "docs" / "a.txt").write_bytes(b"nested")
    (base / "alice2" / "secret.txt").write_bytes(b"alice2 secret")
    (base / "secret.txt").write_bytes(b"server secret")
    try:
        os.symlink(base / "secret.txt", base / "alice" / "link")
    except OSError:
        pass
    return base


def leaks(call):
    """True when the call returns a secret instead of refusing."""
    try:
        return b"secret" in call()
    except Exception:
        return False


def test_reads_an_attachment():
    base = layout()
    assert read_attachment(base / "alice", "report.txt") == b"report"


def test_reads_an_attachment_in_a_subfolder():
    base = layout()
    assert read_attachment(base / "alice", "docs/a.txt") == b"nested"


def test_a_missing_attachment_raises():
    base = layout()
    try:
        read_attachment(base / "alice", "nope.txt")
    except Exception:
        return
    raise AssertionError("no error for a missing attachment")


def test_parent_traversal_is_refused():
    base = layout()
    assert not leaks(lambda: read_attachment(base / "alice", "../secret.txt"))


def test_absolute_names_are_refused():
    base = layout()
    assert not leaks(lambda: read_attachment(base / "alice", str(base / "secret.txt")))


def test_a_sibling_folder_sharing_the_prefix_is_refused():
    # A string prefix check accepts base/alice2 as inside base/alice.
    base = layout()
    assert not leaks(lambda: read_attachment(base / "alice", "../alice2/secret.txt"))


def test_a_symlink_pointing_outside_is_refused():
    base = layout()
    assert not leaks(lambda: read_attachment(base / "alice", "link"))
