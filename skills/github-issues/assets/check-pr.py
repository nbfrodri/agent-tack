#!/usr/bin/env python3
"""Check PR metadata locally or in read-only CI. Does not validate code or issue existence."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

TITLE = re.compile(r'^(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(?:\([^\r\n()]+\))?!?: \S[^\r\n]*$')
ISSUE = re.compile(r'\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?)\s+(?:[\w.-]+/[\w.-]+)?#[1-9][0-9]*\b', re.I)
PLACEHOLDER = re.compile(r'^(?:todo|tbd|n/?a|none|\.\.\.|…|\[?(?:describe|list|replace|insert)\b.*)$', re.I)


def sections(body):
    body = re.sub(r'<!--.*?(?:-->|\Z)', '', body, flags=re.S)
    result = {}
    current = None
    fence = None
    for line in body.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r'^##\s+(.+?)\s*#*\s*$', line)
        if heading:
            current = heading.group(1).casefold()
            result.setdefault(current, [])
        elif current:
            result[current].append(line)
    return result


def check(pr, summary, validation, title_policy, require_issue):
    if not isinstance(pr, dict) or not isinstance(pr.get('title'), str) or not isinstance(pr.get('draft'), bool):
        raise ValueError('Expected a pull_request object with title and draft fields')
    if pr['draft']:
        return [], True
    body = pr.get('body') or ''
    if not isinstance(body, str):
        raise ValueError('PR body must be text')
    findings = []
    if not pr['title'].strip() or (title_policy == 'conventional' and not TITLE.fullmatch(pr['title'])):
        findings.append('Use a descriptive PR title' + (' in Conventional Commit format.' if title_policy == 'conventional' else '.'))
    parsed = sections(body)
    for heading in (summary, validation):
        lines = parsed.get(heading.casefold(), [])
        content = [re.sub(r'^\s*[-*]?\s*(?:\[[ xX]\]\s*)?', '', line).strip() for line in lines]
        content = [line for line in content if line]
        if not content or all(not re.search(r'\w', line) for line in content):
            findings.append('Fill the required ' + heading + ' section.')
        elif any(PLACEHOLDER.fullmatch(line) for line in content):
            findings.append('Replace template placeholders in ' + heading + '.')
    # Only prose outside comments/code fences counts, so the template's example cannot satisfy this.
    if require_issue and not ISSUE.search('\n'.join(line for lines in parsed.values() for line in lines)):
        findings.append('Add a real closing or partial issue reference (for example, Refs #123). Syntax only is checked.')
    return findings, False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', default=os.environ.get('GITHUB_EVENT_PATH'))
    parser.add_argument('--summary-heading', default='Summary')
    parser.add_argument('--validation-heading', default='Validation')
    parser.add_argument('--title-policy', choices=('conventional', 'any'), default='conventional')
    parser.add_argument('--require-issue', action='store_true')
    args = parser.parse_args()
    if not args.event:
        raise ValueError('Provide --event FILE or GITHUB_EVENT_PATH')
    event = Path(args.event)
    if event.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Event exceeds 2 MiB')
    payload = json.loads(event.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('Event must be a JSON object')
    findings, draft = check(payload.get('pull_request'), args.summary_heading,
                            args.validation_heading, args.title_policy, args.require_issue)
    if draft:
        print('PR metadata: deferred for draft; checked when ready for review.')
    elif findings:
        for finding in findings:
            print('PR metadata: ' + finding)
    else:
        print('PR metadata: passed. This checks presentation, not code quality or test execution.')
    return 1 if findings else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print('PR metadata: cannot read a valid event: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
