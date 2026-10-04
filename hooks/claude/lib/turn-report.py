#!/usr/bin/env python3
"""Summarise the part of an agent transcript added since the last stop.

Usage: turn-report.py TRANSCRIPT CLIENT MODE STATE_FILE [--init]

Prints one tab-separated "event<TAB>detail" line per finding for the activity log:
  turn   model=<m> input=<n> output=<n> cache_read=<n> cache_write=<n>   (tokens per model)
  skill  <name>                                                         (a skill loaded)
  agent  <type or model>                                                (a subagent started)
  level  <mode> <reason> | missing                                      (the workflow level)

STATE_FILE (JSON) keeps how far each transcript was read, so no line is counted twice. With
--init (SessionStart) it only records where the transcripts end now, so history from before
the session, or from before the log was turned on, is never counted as today's work; without
a state file a stop records nothing and starts from there. Input tokens exclude cached ones
for every tool. Unknown formats print "turn unknown". Never raises: a hook must not fail
because a transcript changed shape.
"""
import glob
import json
import os
import re
import sys

MODES = ("lean", "lite", "standard", "strict", "unleash")
MARK = r"[*_`]*"
# A whole line: a one-word label in any language ("Level:", "**Nivel:**"), the mode name, then
# either nothing or a parenthesised reason. Prose such as "Python: standard library" is not one.
LEVEL = re.compile(r"^[ \t>#*_`-]*\w+" + MARK + r"[ \t]*:" + MARK + r"[ \t]*" + MARK
                   + r"(" + "|".join(MODES) + r")" + MARK + r"[ \t]*(?:\(([^)\n]*)\)[^\n]*)?$",
                   re.IGNORECASE | re.MULTILINE)
SKILL_FILE = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")
CLAUDE_EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def number(value):
    return value if isinstance(value, int) else 0


class Turn:
    def __init__(self, state, mode):
        self.state = state
        self.mode = mode
        self.tokens = {}  # model -> [input, output, cache_read, cache_write]
        self.skills = []
        self.agents = []
        self.levels = []  # the first level each task states, or "missing"
        self.edited = False
        self.known = False

    def add_tokens(self, model, inp, out, read, write):
        totals = self.tokens.setdefault(model or "unknown", [0, 0, 0, 0])
        for i, value in enumerate((inp, out, read, write)):
            totals[i] += max(number(value), 0)

    def add_text(self, text):
        for match in LEVEL.finditer(text or ""):
            if self.state.get("level_seen"):
                return
            reason = (match.group(2) or "").strip()
            self.levels.append(f"{match.group(1).lower()} {reason[:120]}".strip())
            self.state["level_seen"] = True

    def close_task(self):
        """An auto task that edited files without stating its level is recorded as missing."""
        if self.edited and not self.state.get("level_seen") and self.mode == "auto":
            self.levels.append("missing")
            self.state["level_seen"] = True

    def new_task(self):
        # A new prompt is a new task, which states its own level.
        self.close_task()
        self.state["level_seen"] = False
        self.edited = False


def claude_entry(entry, turn, seen, main=True):
    message = entry.get("message") or {}
    if not isinstance(message, dict):
        return
    if entry.get("type") == "user" and main:
        content = message.get("content")
        is_text = isinstance(content, str) or any(
            isinstance(block, dict) and block.get("type") == "text" for block in content or [])
        # Only a person's prompt starts a task: hook feedback, loaded skills, task notifications
        # and messages from other agents are user entries too, marked isMeta or by origin.
        origin = entry.get("origin") if isinstance(entry.get("origin"), dict) else {}
        if is_text and not entry.get("isMeta") and origin.get("kind", "human") == "human":
            turn.new_task()
        return
    if entry.get("type") != "assistant":
        return
    turn.known = True
    # Claude Code writes placeholder replies under "<synthetic>"; no model ran for them.
    if str(message.get("model", "")).startswith("<"):
        return
    usage = message.get("usage") or {}
    if message.get("id") not in seen:
        seen.add(message.get("id"))
        turn.add_tokens(message.get("model"), usage.get("input_tokens"), usage.get("output_tokens"),
                        usage.get("cache_read_input_tokens"), usage.get("cache_creation_input_tokens"))
    for block in message.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and main:
            turn.add_text(block.get("text"))
        elif block.get("type") == "tool_use":
            name, args = block.get("name"), block.get("input") or {}
            if name == "Skill" and args.get("skill"):
                turn.skills.append(str(args["skill"]))
            elif name in ("Agent", "Task") and main:
                turn.agents.append(str(args.get("subagent_type") or "general-purpose"))
            elif name in CLAUDE_EDITS and main:
                turn.edited = True


def codex_entry(entry, turn, context):
    payload = entry.get("payload") or {}
    kind = entry.get("type")
    if kind == "turn_context":
        turn.known = True
        context["model"] = payload.get("model") or context.get("model")
    elif kind == "event_msg" and payload.get("type") == "token_count":
        turn.known = True
        info = payload.get("info") or {}
        total = info.get("total_token_usage")
        # Codex sometimes repeats a count; the unchanged running total gives it away.
        if total is not None and total == turn.state.get("codex_total"):
            return
        turn.state["codex_total"] = total
        usage = info.get("last_token_usage") or {}
        read, write = number(usage.get("cached_input_tokens")), number(usage.get("cache_write_input_tokens"))
        # Codex counts cached tokens inside input_tokens; report them once, as cache.
        turn.add_tokens(context.get("model"), number(usage.get("input_tokens")) - read - write,
                        usage.get("output_tokens"), read, write)
    elif kind == "event_msg" and payload.get("type") == "task_started":
        turn.new_task()
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


def read_lines(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return None


def entries(lines, start):
    for line in lines[start:]:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            yield entry


def subagent_files(path):
    """Claude Code keeps each subagent's transcript in <session>/subagents/agent-*.jsonl."""
    return sorted(glob.glob(os.path.join(os.path.splitext(path)[0], "subagents", "*.jsonl")))


def load_state(state_file):
    try:
        raw = open(state_file).read().strip()
    except OSError:
        return None
    try:
        state = json.loads(raw)
    except ValueError:
        return None
    if isinstance(state, int):  # the first format held only the offset
        state = {"offset": state}
    return state if isinstance(state, dict) else None


def save_state(state_file, state):
    try:
        with open(state_file, "w") as handle:
            json.dump(state, handle)
    except OSError:
        pass


def main(path, client, mode, state_file, init=""):
    lines = read_lines(path)
    if lines is None:
        return
    state = load_state(state_file)
    if init == "--init" or state is None:
        # Start from here: nothing written before this point belongs to this session's turns.
        subs = {os.path.basename(sub): len(read_lines(sub) or []) for sub in subagent_files(path)}
        save_state(state_file, {"offset": len(lines), "subagents": subs, "level_seen": False})
        return
    done = state.get("offset", 0) if isinstance(state.get("offset"), int) else 0
    if len(lines) < done:  # a rewritten transcript starts over
        done = 0
    turn, seen, context = Turn(state, mode), set(), {}
    for entry in entries(lines, done):
        if client == "codex":
            codex_entry(entry, turn, context)
        else:
            claude_entry(entry, turn, seen)
    changed = len(lines) > done
    if client != "codex":
        subs = state.get("subagents") if isinstance(state.get("subagents"), dict) else {}
        for sub in subagent_files(path):
            sub_lines = read_lines(sub) or []
            start = subs.get(os.path.basename(sub), 0)
            start = start if isinstance(start, int) and start <= len(sub_lines) else 0
            if len(sub_lines) > start:
                changed = True
                for entry in entries(sub_lines, start):
                    claude_entry(entry, turn, seen, main=False)
            subs[os.path.basename(sub)] = len(sub_lines)
        state["subagents"] = subs
    state["offset"] = len(lines)
    turn.close_task()
    save_state(state_file, state)
    if not changed:
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


if __name__ == "__main__":
    try:
        main(*sys.argv[1:6])
    except Exception:  # noqa: BLE001 - a hook never fails on a transcript
        pass
