#!/usr/bin/env python3
"""Summarise the part of an agent transcript added since the last stop.

Usage: turn-report.py TRANSCRIPT CLIENT MODE STATE_FILE

Prints one tab-separated "event<TAB>detail" line per finding for the activity log:
  turn   model=<m> input=<n> output=<n> cache_read=<n> cache_write=<n>   (tokens per model)
  skill  <name>                                                         (a skill loaded)
  agent  <type or model>                                                (a subagent started)
  level  <mode> <reason> | missing                                      (the workflow level)

STATE_FILE keeps how many transcript lines were already read, so a second stop in the same
turn, or the next turn, never counts a line twice. Unknown formats print "turn unknown".
Never raises: a hook must not fail because a transcript changed shape.
"""
import json
import re
import sys

MODES = ("lean", "lite", "standard", "strict", "unleash")
# A one-word label in any language ("Level:", "Nivel:"), then a mode name, at a line start.
LEVEL = re.compile(r"^[\W_]*\w+\s*:\s*[*_`]*(" + "|".join(MODES) + r")\b[*_`]*\s*(.*)$",
                   re.IGNORECASE | re.MULTILINE)
SKILL_FILE = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")
CLAUDE_EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def number(value):
    return value if isinstance(value, int) else 0


class Turn:
    def __init__(self):
        self.tokens = {}  # model -> [input, output, cache_read, cache_write]
        self.skills = []
        self.agents = []
        self.levels = []
        self.edited = False
        self.known = False

    def add_tokens(self, model, inp, out, read, write):
        totals = self.tokens.setdefault(model or "unknown", [0, 0, 0, 0])
        for i, value in enumerate((inp, out, read, write)):
            totals[i] += number(value)

    def add_text(self, text):
        for match in LEVEL.finditer(text or ""):
            reason = match.group(2).strip().strip("()").strip()
            self.levels.append(f"{match.group(1).lower()} {reason}".strip())


def claude_entry(entry, turn, seen):
    message = entry.get("message") or {}
    if entry.get("type") != "assistant" or not isinstance(message, dict):
        return
    turn.known = True
    usage = message.get("usage") or {}
    if message.get("id") not in seen:
        seen.add(message.get("id"))
        turn.add_tokens(message.get("model"), usage.get("input_tokens"), usage.get("output_tokens"),
                        usage.get("cache_read_input_tokens"), usage.get("cache_creation_input_tokens"))
    for block in message.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            turn.add_text(block.get("text"))
        elif block.get("type") == "tool_use":
            name, args = block.get("name"), block.get("input") or {}
            if name == "Skill" and args.get("skill"):
                turn.skills.append(str(args["skill"]))
            elif name in ("Agent", "Task"):
                turn.agents.append(str(args.get("subagent_type") or "general-purpose"))
            elif name in CLAUDE_EDITS:
                turn.edited = True


def codex_entry(entry, turn, context):
    payload = entry.get("payload") or {}
    kind = entry.get("type")
    if kind == "turn_context":
        turn.known = True
        context["model"] = payload.get("model") or context.get("model")
    elif kind == "event_msg" and payload.get("type") == "token_count":
        turn.known = True
        usage = (payload.get("info") or {}).get("last_token_usage") or {}
        turn.add_tokens(context.get("model"), usage.get("input_tokens"), usage.get("output_tokens"),
                        usage.get("cached_input_tokens"), usage.get("cache_write_input_tokens"))
    elif kind == "response_item":
        item = payload.get("type")
        if item == "message" and payload.get("role") == "assistant":
            turn.known = True
            for block in payload.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    turn.add_text(block.get("text"))
        elif item in ("custom_tool_call", "function_call"):
            turn.known = True
            raw = payload.get("input") or payload.get("arguments") or ""
            raw = raw if isinstance(raw, str) else json.dumps(raw)
            if payload.get("name") == "spawn_agent":
                try:
                    args = json.loads(raw)
                except ValueError:
                    args = {}
                turn.agents.append(str(args.get("model") or args.get("task_name") or "agent"))
            else:
                turn.skills.extend(SKILL_FILE.findall(raw))
                if "apply_patch" in raw:
                    turn.edited = True


def main(path, client, mode, state_file):
    try:
        done = int(open(state_file).read().strip() or 0)
    except (OSError, ValueError):
        done = 0
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return
    if len(lines) < done:  # a rewritten transcript starts over
        done = 0
    turn, seen, context = Turn(), set(), {}
    for line in lines[done:]:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        if client == "codex":
            codex_entry(entry, turn, context)
        else:
            claude_entry(entry, turn, seen)
    try:
        with open(state_file, "w") as handle:
            handle.write(str(len(lines)))
    except OSError:
        pass
    if len(lines) == done:
        return
    if not turn.known:
        print("turn\tunknown")
        return
    for model, (inp, out, read, write) in sorted(turn.tokens.items()):
        print(f"turn\tmodel={model} input={inp} output={out} cache_read={read} cache_write={write}")
    for name in dict.fromkeys(turn.skills):
        print(f"skill\t{name}")
    for name in turn.agents:
        print(f"agent\t{name}")
    for level in turn.levels:
        print(f"level\t{level}")
    if not turn.levels and turn.edited and mode == "auto":
        print("level\tmissing")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:5])
    except Exception:  # noqa: BLE001 - a hook never fails on a transcript
        pass
