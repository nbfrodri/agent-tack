#!/usr/bin/env bash
# Cursor beforeShellExecution hook: a thin adapter around the shared command guard
# (hooks/claude/guard-bash.sh), so Cursor gets the same deny and ask rules without a copy of them.
# Input: Cursor's hook JSON ({"command", "cwd", ...}). Output: {"permission", "user_message",
# "agent_message"}. Fails open (allows) when it cannot read the input, like the guard itself.
set -u

input="$(cat)"
guard="$(cd "$(dirname "$0")/../claude" && pwd)/guard-bash.sh"

# Translates Cursor's input into the guard's, runs it and translates the decision back.
python3 - "$guard" "$input" <<'PY' 2>/dev/null || printf '{"permission": "allow"}\n'
import json, subprocess, sys

guard, raw = sys.argv[1], sys.argv[2]
try:
    event = json.loads(raw)
    command = event["command"] if isinstance(event.get("command"), str) else ""
except (ValueError, TypeError, KeyError):
    command = ""
if not command:
    print(json.dumps({"permission": "allow"}))
    sys.exit(0)
request = {"tool_name": "Bash", "tool_input": {"command": command}}
if isinstance(event.get("cwd"), str):
    request["cwd"] = event["cwd"]
result = subprocess.run(["bash", guard], input=json.dumps(request), capture_output=True, text=True, timeout=9)
try:
    decision = json.loads(result.stdout)["hookSpecificOutput"] if result.stdout.strip() else {}
except (ValueError, KeyError):
    decision = {}
permission = decision.get("permissionDecision", "allow")
answer = {"permission": permission if permission in ("allow", "ask", "deny") else "allow"}
reason = decision.get("permissionDecisionReason")
if reason:
    answer["user_message"] = "tack: " + reason
    answer["agent_message"] = reason
print(json.dumps(answer))
PY
