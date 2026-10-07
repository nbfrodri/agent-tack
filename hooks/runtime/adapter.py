#!/usr/bin/env python3
"""Translate Gemini and Copilot hook protocols to tack's shared hook scripts."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys

HOOKS = Path(__file__).resolve().parents[1] / 'claude'
SHELLS = {'run_shell_command', 'bash', 'Bash', 'powershell'}
EDITS = {'replace', 'write_file', 'edit', 'create', 'apply_patch', 'Edit', 'Write'}


def normalize(tool, data):
    if not isinstance(data, dict):
        raise ValueError('hook input must be an object')
    payload = dict(data)
    if tool == 'copilot':
        for source, target in [('sessionId', 'session_id'), ('toolName', 'tool_name'),
                               ('toolArgs', 'tool_input'), ('stopHookActive', 'stop_hook_active')]:
            if source in data:
                payload[target] = data[source]
    args = payload.get('tool_input', {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            if payload.get('tool_name') in SHELLS:
                raise
            args = {}
    if not isinstance(args, dict):
        if payload.get('tool_name') in SHELLS:
            raise ValueError('shell tool arguments must be an object')
        args = {}
    payload['tool_input'] = args
    if payload.get('tool_name') in SHELLS:
        command = args.get('command')
        if not isinstance(command, str) or not command.strip():
            raise ValueError('shell command is missing')
        if payload['tool_name'] == 'powershell':
            payload['tool_input'] = dict(args, command='pwsh -Command ' + shlex.quote(command))
    return payload


def invoke(name, payload, tool, timeout):
    with subprocess.Popen(['bash', str(HOOKS / name), f'--{tool}'], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          encoding='utf-8', start_new_session=os.name == 'posix') as process:
        try:
            stdout, _ = process.communicate(json.dumps(payload), timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.communicate()
            raise
        if process.returncode:
            raise ValueError('shared hook failed')
    parsed = json.loads(stdout) if stdout.strip() else {}
    if not isinstance(parsed, dict) or not isinstance(parsed.get('hookSpecificOutput', {}), dict):
        raise ValueError('invalid shared hook response')
    return parsed


def permission(tool, decision, reason):
    if decision == 'allow':
        return {}
    if tool == 'gemini':
        if decision == 'ask':
            reason = 'Needs user confirmation before retrying: ' + reason
        return {'decision': 'deny', 'reason': reason}
    return {'permissionDecision': decision, 'permissionDecisionReason': reason}


def context(tool, text):
    return {'hookSpecificOutput': {'additionalContext': text}} if tool == 'gemini' else {'additionalContext': text}


def dispatch(tool, event, data):
    payload = normalize(tool, data)
    if event == 'before':
        scripts = ['budget.sh']
        if payload.get('tool_name') in SHELLS:
            scripts.insert(0, 'guard-bash.sh')
        for script in scripts:
            output = invoke(script, payload, tool, 9).get('hookSpecificOutput', {})
            decision = output.get('permissionDecision', 'allow')
            if decision != 'allow':
                return permission(tool, decision, output.get('permissionDecisionReason', 'Command requires review.'))
        return {}
    if event == 'session':
        result = invoke('session-context.sh', payload, tool, 25)
        return context(tool, result.get('hookSpecificOutput', {}).get('additionalContext', ''))
    if event == 'after':
        if payload.get('tool_name') not in EDITS:
            return {}
        result = invoke('fast-check.sh', payload, tool, 70)
        return context(tool, result['reason']) if result.get('reason') else {}
    result = invoke('stop-check.sh', payload, tool, 135)
    if result.get('decision') == 'block':
        return {'decision': 'deny' if tool == 'gemini' else 'block', 'reason': result['reason']}
    return {}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ('gemini', 'copilot') or sys.argv[2] not in ('session', 'before', 'after', 'stop'):
        sys.exit('usage: adapter.py gemini|copilot session|before|after|stop')
    tool, event = sys.argv[1:]
    try:
        result = dispatch(tool, event, json.load(sys.stdin))
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError):
        # Advisory failures do not end a session. A command cannot silently bypass the guard.
        result = permission(tool, 'deny', 'tack could not inspect this tool call; repair the hook before retrying.') if event == 'before' else {}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
