# Merges the harness settings into a Claude Code settings.json (same behaviour as settings-merge.py).
# Usage: jq -s -f lib/settings-merge.jq <current settings.json> <harness settings.json>
def ours: type == "object" and ((.command? // "") | tostring | (contains("#tack") or contains("#harness") or contains("#agent-config")));  # "#harness" and "#agent-config" are former tags
def clean: if ours then empty elif type == "object" and (.hooks | type) == "array" then .hooks |= map(select(ours | not)) | select(.hooks | length > 0) else . end;
.[0] as $d | .[1] as $s
| ($d * ($s | del(.hooks))) as $m
| (($d.hooks // {})
    | with_entries(.value |= (if type == "array" then map(clean) else . end))
    | with_entries(select(.value != []))) as $kept
| (reduce (($s.hooks // {}) | to_entries[]) as $e ($kept; .[$e.key] = ((.[$e.key] // []) + $e.value))) as $h
| $m | if ($h | length) > 0 then .hooks = $h else del(.hooks) end
