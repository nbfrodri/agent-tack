#!/usr/bin/env python3
"""Merges the harness settings into a Claude Code settings.json.

Usage: lib/settings-merge.py <current settings.json> <harness settings.json>   (prints the result)
Objects are deep-merged and the harness values win; the user's other keys are kept. Hook groups
tagged "#harness" (or "#agent-config", the old name) are replaced; the user's own hooks are kept.
Same behaviour as lib/settings-merge.jq, which install.sh uses when python3 is missing.
"""
import json, sys

# Hooks this repo installs; "#agent-config" is the tag of older versions
TAGS = ("#harness", "#agent-config")

def merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base

def is_ours(group):
    return isinstance(group, dict) and any(
        isinstance(h, dict) and any(t in str(h.get("command", "")) for t in TAGS) for h in group.get("hooks", [])
    )

with open(sys.argv[1]) as f:
    current = json.load(f)
with open(sys.argv[2]) as f:
    wanted = json.load(f)
if not isinstance(current, dict):
    sys.exit("settings.json is not a JSON object")

wanted_hooks = wanted.pop("hooks", {}) or {}
merged = merge(current, wanted)
hooks = merged.get("hooks") if isinstance(merged.get("hooks"), dict) else {}
for event in list(hooks):
    if isinstance(hooks[event], list):
        hooks[event] = [g for g in hooks[event] if not is_ours(g)]
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
