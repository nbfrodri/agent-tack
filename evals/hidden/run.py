"""Runs one hidden acceptance test file: plain test_* functions, no pytest needed.

Usage (from the project's directory, so its code is importable): python run.py <test file>
Prints "N passed, M failed" last. Code that cannot even be imported fails every test.
"""
import importlib.util
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
names = re.findall(r"^def (test_\w+)", path.read_text(), re.M)
try:
    spec = importlib.util.spec_from_file_location("hidden_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
except Exception as exc:  # the agent's code may fail in any way on import
    print(f"FAIL import: {exc!r}")
    print(f"0 passed, {len(names)} failed")
    sys.exit(1)
failed = 0
for name in names:
    try:
        getattr(module, name)()
    except Exception as exc:  # an assertion or a crash in the agent's code both fail the test
        failed += 1
        print(f"FAIL {name}: {exc!r}")
print(f"{len(names) - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)
