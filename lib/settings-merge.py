#!/usr/bin/env python3
"""Merges tack's settings into a Claude Code settings.json.

Usage: lib/settings-merge.py <current settings.json> <tack settings.json>   (prints the result)
Objects are deep-merged and tack's values win; the user's other keys are kept. Hook groups (or
Cursor's plain command entries)
tagged "#tack" (or "#harness" and "#agent-config", the former names) are replaced; the user's own hooks are kept.
Same behaviour as lib/settings-merge.jq, which install.sh uses when python3 is missing.
"""
import json
import sys

# Hooks this repo installs; "#agent-config" is the tag of older versions
TAGS = ("#tack", "#harness", "#agent-config")  # "#harness" and "#agent-config" are former tags

def merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base

def is_ours(hook):
    return isinstance(hook, dict) and any(t in str(hook.get("command", "")) for t in TAGS)

def clean_group(group):
    # Cursor's own format lists commands directly instead of groups of hooks.
    if is_ours(group):
        return None
    if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
        return group
    kept = [hook for hook in group["hooks"] if not is_ours(hook)]
    return dict(group, hooks=kept) if kept else None

with open(sys.argv[1], encoding="utf-8") as f:
    current = json.load(f)
with open(sys.argv[2], encoding="utf-8") as f:
    wanted = json.load(f)
if not isinstance(current, dict):
    sys.exit("settings.json is not a JSON object")

wanted_hooks = wanted.pop("hooks", {}) or {}
merged = merge(current, wanted)
hooks = merged.get("hooks") if isinstance(merged.get("hooks"), dict) else {}
for event in list(hooks):
    if isinstance(hooks[event], list):
        kept = []
        for group in hooks[event]:
            cleaned = clean_group(group)
            if cleaned is not None:
                kept.append(cleaned)
        hooks[event] = kept
        if not hooks[event]:
            del hooks[event]
for event, groups in wanted_hooks.items():
    hooks.setdefault(event, []).extend(groups)
if hooks:
    merged["hooks"] = hooks
else:
    merged.pop("hooks", None)
json.dump(merged, sys.stdout, indent=2, ensure_ascii=False)
sys.stdout.write("\n")
