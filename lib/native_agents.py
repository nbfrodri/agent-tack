#!/usr/bin/env python3
"""Translate portable role text to a target's native Markdown agent format."""
import json
from pathlib import Path
import sys

from codex_agents import READ_ONLY_TOOLS, parse

FORMATS = {
    'gemini': dict(extension='.md', fields={'kind': 'local'}, tools={
        'Read': 'read_file', 'Grep': 'grep_search', 'Glob': 'glob', 'Bash': 'run_shell_command',
        'Edit': 'replace', 'Write': 'write_file', 'WebFetch': 'web_fetch', 'WebSearch': 'google_web_search'}),
    'copilot': dict(extension='.agent.md', fields={}, tools={
        'Read': 'read', 'Grep': 'search', 'Glob': 'search', 'Bash': 'execute',
        'Edit': 'edit', 'Write': 'edit', 'WebFetch': 'web', 'WebSearch': 'web'}),
    'opencode': dict(extension='.md', fields={'mode': 'subagent'}, tools={
        'Read': 'read', 'Grep': 'grep', 'Glob': 'glob', 'Bash': 'bash',
        'Edit': 'edit', 'Write': 'edit', 'WebFetch': 'webfetch', 'WebSearch': 'websearch'}),
    'cursor': dict(extension='.md', fields={}, tools={}),
}


def render(tool, path):
    profile = FORMATS[tool]
    fields, body = parse(path)
    data = dict(name=fields['name'], description=fields['description'], **profile['fields'])
    tools = {item.strip() for item in fields.get('tools', '').split(',') if item.strip()}
    if tool == 'cursor':
        if tools and tools <= READ_ONLY_TOOLS:
            data['readonly'] = True
    elif tools:
        unknown = tools - profile['tools'].keys()
        if unknown:
            raise ValueError(f'{path}: unsupported {tool} tools: {sorted(unknown)}')
        mapped = sorted({profile['tools'][item] for item in tools})
        if tool == 'opencode':
            # Native permissions replace deprecated tools; mutating tools still require review.
            data['permission'] = {'*': 'deny', **{item: 'ask' if item in ('bash', 'edit') else 'allow' for item in mapped}}
        else:
            data['tools'] = mapped
    # JSON strings and arrays are valid YAML scalars/flow collections; no vendor model aliases leak.
    header = '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in data.items())
    return '---\n' + header + '\n---\n\n' + body


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--extension':
        print(FORMATS[sys.argv[2]]['extension'])
    elif len(sys.argv) == 3 and sys.argv[1] in FORMATS:
        sys.stdout.buffer.write(render(sys.argv[1], Path(sys.argv[2])).encode('utf-8'))
    else:
        sys.exit('usage: native_agents.py TOOL AGENT.md | --extension TOOL')
