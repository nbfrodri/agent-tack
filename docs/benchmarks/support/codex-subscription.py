#!/usr/bin/env python3
"""Pinned subscription benchmark launcher; writes only non-secret runtime observations.

Put a symlink named codex to this file on PATH before the official CLI. Set
TACK_BENCH_CODEX to the official executable. Both conditions use medium effort;
the automation explicitly trusts the reviewed, locally installed tack hooks.
The outer container is disposable and has no host mounts. Codex uses a workspace
profile with an explicit write grant for the fixture's .git directory, permitting
temporary commits while keeping outside paths read-only. This launcher is not
installed by tack.
"""
import json
import os
from pathlib import Path
import subprocess
import sys


def observe(directory, home):
    models, efforts = set(), set()
    sessions = home / "sessions"
    for path in sessions.rglob("*.jsonl") if sessions.exists() else []:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") != "turn_context":
                continue
            context = event.get("payload", {})
            if isinstance(context.get("model"), str):
                models.add(context["model"])
            effort = context.get("effort", context.get("reasoning_effort"))
            if isinstance(effort, str):
                efforts.add(effort)
    result = {"authentication": "ChatGPT subscription", "requested_effort": "medium",
              "runtime_models": sorted(models), "runtime_efforts": sorted(efforts),
              "permissions": "workspace plus fixture .git write; network enabled",
              "hook_trust": "reviewed installed hooks explicitly trusted for this invocation",
              "note": "Runtime configuration is not independent server-side model identification; no USD charge is reported."}
    (directory / "runtime-observation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main():
    arguments = sys.argv[1:]
    executable = os.environ["TACK_BENCH_CODEX"]
    if arguments and arguments[0] == "exec":
        # Replace only the runner's known legacy sandbox flags with the scoped profile.
        index = arguments.index("-s")
        if arguments[index + 1] != "workspace-write":
            raise ValueError("unexpected benchmark sandbox")
        del arguments[index:index + 2]
        index = arguments.index("sandbox_workspace_write.network_access=true")
        if arguments[index - 1] != "-c":
            raise ValueError("unexpected benchmark network flag")
        del arguments[index - 1:index + 1]
        profile = ('permissions.benchmark={extends=":workspace",'
                   'filesystem={":workspace_roots"={".git"="write"}},network={enabled=true}}')
        arguments[1:1] = ["-c", 'model_reasoning_effort="medium"', "-c", 'default_permissions="benchmark"',
                          "-c", profile, "--dangerously-bypass-hook-trust"]
    result = subprocess.run([executable, *arguments], stdin=subprocess.DEVNULL)
    if "-C" in arguments:
        fixture = Path(arguments[arguments.index("-C") + 1])
        observe(fixture.parent, Path(os.environ["CODEX_HOME"]))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
