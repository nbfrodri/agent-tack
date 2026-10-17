#!/usr/bin/env python3
"""Print how many tokens the last main-thread reply of a Claude Code transcript had in context.

Usage: context-size.py TRANSCRIPT

The size is input plus cached input of the newest assistant entry that is not a subagent's and
not a placeholder, which is what the next request starts from. Prints nothing when it cannot
tell. Never raises: a hook must not fail because a transcript changed shape.
"""
import json
import sys


def size(path):
    last = None
    with open(path, encoding="utf-8", errors="replace") as lines:
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict) or entry.get("type") != "assistant" or entry.get("isSidechain"):
                continue
            message = entry.get("message")
            if not isinstance(message, dict) or str(message.get("model", "")).startswith("<"):
                continue
            usage = message.get("usage")
            if isinstance(usage, dict):
                last = usage
    if last is None:
        return None
    parts = (last.get("input_tokens"), last.get("cache_read_input_tokens"), last.get("cache_creation_input_tokens"))
    return sum(value for value in parts if isinstance(value, int) and value > 0)


try:
    total = size(sys.argv[1])
    if total:
        print(total)
except Exception:
    pass
