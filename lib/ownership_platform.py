"""Filesystem boundaries shared by ownership restoration and settings writes."""
from functools import lru_cache
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

WINDOWS = os.name == "nt"


def plain_path(value):
    if WINDOWS:
        value = value.replace("\\", "/")
        if re.match(r"^[a-zA-Z]:/", value):
            value = value[2:]
        if ":" in value or value.startswith("//"):
            return False  # No alternate streams, device paths or network shares.
    return (value.startswith("/") and not any(c in value for c in "\n\r\t")
            and all(p not in (".", "..") for p in value.split("/")))


@lru_cache(maxsize=4096)
def canonical(value):
    """Comparable absolute path; convert recorded MSYS paths before native filesystem access."""
    value = os.fspath(value)
    if WINDOWS and value.startswith("\\\\?\\") and re.match(r"[a-zA-Z]:", value[4:]):
        value = value[4:]
    if not plain_path(value):
        raise ValueError("unsafe absolute path")
    if WINDOWS:
        if value.startswith("/"):
            result = subprocess.run(["cygpath", "-m", "--", value], capture_output=True, text=True,
                                    encoding="utf-8", check=True)
            value = result.stdout.rstrip("\r\n")
        value = os.path.normcase(value).replace("\\", "/")
    if WINDOWS and re.fullmatch(r"[a-z]:/", value):
        return value
    return value.rstrip("/") or "/"


def redirected(path):
    info = path.lstat()
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))


def no_symlink_ancestors(path, floor):
    for current in [path, *path.parents]:
        try:
            if redirected(current):
                return False
        except FileNotFoundError:
            pass
        if current == floor:
            return True
    return True


def windows_acl(action, path, destination=None):
    script = Path(__file__).with_name("windows-acl.ps1")
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", str(script), "-Action", action, "-Path", str(path)]
    if destination is not None:
        command += ["-Destination", str(destination)]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode:
        raise ValueError("native ACL operation failed: " + result.stderr.strip())


def validate_private(state):
    if WINDOWS:
        windows_acl("validate", state)
        return
    for root, dirs, files in os.walk(state, followlinks=False):
        for path in [Path(root), *(Path(root) / n for n in dirs + files)]:
            info = path.lstat()
            if (redirected(path) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077
                    or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
                raise ValueError("ownership state is not private or contains unsupported files")


def copy_permissions(source, destination):
    """Keep an existing file's security when atomically replacing its contents."""
    if WINDOWS:
        windows_acl("copy", source, destination)
    os.chmod(destination, stat.S_IMODE(os.stat(source).st_mode))


def parent_identity(path):
    info = os.stat(path)
    return f"{info.st_dev}:{info.st_ino}"


def main():
    action, value = sys.argv[1:3]
    path = Path(canonical(value))
    if action == "create":
        if not WINDOWS or not no_symlink_ancestors(path, Path(path.anchor)):
            raise ValueError("unsafe native ownership directory")
        windows_acl("create", path)
    elif action == "identity":
        print(parent_identity(path))
    elif action == "link-directory":
        print(int(bool(getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_DIRECTORY)))
    else:
        raise ValueError("unknown platform operation")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
