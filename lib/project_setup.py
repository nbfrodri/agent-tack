#!/usr/bin/env python3
"""Bounded project discovery, minimal scaffolding and read-only readiness checks."""
import argparse
import json
from pathlib import Path
import re
import subprocess

BASE = ('AGENTS.md', 'CLAUDE.md', 'docs/architecture.md', 'docs-map.txt')
MANIFESTS = {'package.json': 'JavaScript/TypeScript', 'pyproject.toml': 'Python',
             'requirements.txt': 'Python', 'Cargo.toml': 'Rust', 'go.mod': 'Go',
             'composer.json': 'PHP', 'Gemfile': 'Ruby', 'pom.xml': 'Java',
             'build.gradle': 'JVM', 'build.gradle.kts': 'JVM'}
PENDING = '<!-- tack:review-needed -->'
CAPABILITY_DIRS = ('.agents/skills/', '.agents/agents/', '.claude/skills/', '.claude/agents/',
                   '.codex/skills/', '.codex/agents/', '.gemini/skills/', '.gemini/agents/',
                   '.github/skills/', '.github/agents/', '.cursor/skills/', '.cursor/agents/',
                   '.opencode/skills/', '.opencode/agents/')


def safe(root, relative):
    path = root / relative
    if path == root or not path.is_relative_to(root) or '..' in Path(relative).parts:
        return False
    return not any(p.is_symlink() for p in (path, *path.parents) if p != root and p.is_relative_to(root))


def read(root, relative):
    path = root / relative
    if not safe(root, relative) or not path.is_file() or path.stat().st_size > 131072:
        return ''
    return path.read_text(encoding='utf-8', errors='replace')


def inventory(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                             '--exclude-standard', '-z'], capture_output=True, check=True, timeout=10)
    paths = sorted(set(result.stdout.decode('utf-8', errors='replace').split('\0')) - {''})
    # A repository may contain much more data than is useful in startup analysis.
    return paths[:3000], len(paths) > 3000


def analyze(root):
    files, truncated = inventory(root)
    manifests = [p for p in files if Path(p).name in MANIFESTS and safe(root, p) and (root / p).is_file()][:40]
    commands = {}
    raw = read(root, 'package.json')
    try:
        package = json.loads(raw) if raw else {}
        scripts = package.get('scripts', {}) if isinstance(package, dict) else {}
        if raw and isinstance(scripts, dict):
            runner = 'pnpm' if (root / 'pnpm-lock.yaml').is_file() else 'yarn' if (root / 'yarn.lock').is_file() else 'bun' if any((root / p).is_file() for p in ('bun.lock', 'bun.lockb')) else 'npm'
            commands['Install'] = (f'{runner} install', 'package.json; review lifecycle scripts before running')
            for name in ('dev', 'start', 'build', 'test', 'lint', 'format', 'typecheck', 'check'):
                if isinstance(scripts.get(name), str) and 'no test specified' not in scripts[name]:
                    commands[name] = (f'{runner} run {name}', f'package.json scripts.{name}')
    except (ValueError, TypeError):
        pass
    for makefile in ('Makefile', 'makefile', 'GNUmakefile'):
        source = read(root, makefile)
        for name in ('test', 'lint', 'check', 'build', 'run'):
            if re.search(rf'^{name}\s*:', source, re.M):
                commands[name] = (f'make {name}', f'{makefile} target')
    for manifest, name, command in [('Cargo.toml', 'test', 'cargo test'), ('go.mod', 'test', 'go test ./...')]:
        if read(root, manifest):
            commands.setdefault(name, (command, manifest))
    if any('pytest' in read(root, p) for p in ('pyproject.toml', 'requirements.txt', 'pytest.ini', 'setup.cfg')) or (root / 'pytest.ini').is_file():
        commands.setdefault('test', ('uv run pytest' if (root / 'uv.lock').is_file() else 'python3 -m pytest', 'pytest configuration'))
    directories = sorted({p.split('/')[0] for p in files if '/' in p and not p.startswith('.') and p.split('/')[0] not in ('node_modules', 'vendor', 'dist', 'build', '__pycache__')})[:20]
    capabilities = [p for p in files if p.startswith(CAPABILITY_DIRS) and safe(root, p) and (root / p).is_file()
                    and (p.endswith('/SKILL.md') or '/agents/' in p and p.endswith(('.md', '.toml')))][:30]
    templates = [p for p in files if 'pull_request_template' in p.lower()][:15]
    candidates = []
    if 'test' not in commands:
        candidates.append({'item': 'tests', 'reason': 'No root test command detected; inspect existing tests and workspace packages first.'})
    if not any(p.startswith(('.github/workflows/', '.gitlab-ci')) or p in ('Jenkinsfile', 'azure-pipelines.yml') for p in files):
        candidates.append({'item': 'CI', 'reason': 'No recognized CI entrypoint; select the repository host and useful checks before creating one.'})
    if not templates:
        candidates.append({'item': 'PR template', 'reason': 'No repository PR template; check organization defaults and whether this project uses pull requests.'})
    if not any(p.lower() == 'readme.md' for p in files):
        candidates.append({'item': 'README', 'reason': 'No root README.md; a short setup and usage guide may help.'})
    issues = []
    for relative in BASE:
        if not safe(root, relative):
            issues.append(f'{relative}: symlink or unsafe path; inspect manually')
        elif not (root / relative).is_file():
            issues.append(f'{relative}: missing base file')
    for relative in ('AGENTS.md', 'docs/architecture.md'):
        content = read(root, relative)
        if PENDING in content or re.search(r'`(?:…|\.\.\.|TODO)`', content):
            issues.append(f'{relative}: guidance still needs review against the project')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
            target = target.split('#')[0].strip('<>')
            if not target or re.match(r'[a-zA-Z][\w+.-]*:', target) or target.startswith('/'):
                continue
            resolved = (root / relative).parent / target
            if not resolved.resolve().is_relative_to(root) or not resolved.exists():
                issues.append(f'{relative}: missing or external local link {target}')
    rules = 0
    for line in read(root, 'docs-map.txt').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if '|' not in line:
            issues.append('docs-map.txt: expected code glob | doc, doc')
            continue
        pattern, docs = line.split('|', 1)
        if not pattern.strip() or not docs.strip():
            issues.append('docs-map.txt: empty pattern or documentation target')
        rules += 1
        for doc in docs.split(','):
            doc = doc.strip()
            if not doc or not safe(root, doc) or not (root / doc).is_file():
                issues.append(f'docs-map.txt: missing or unsafe target {doc}')
    return dict(manifests=[{'path': p, 'stack': MANIFESTS[Path(p).name]} for p in manifests],
                commands=commands, directories=directories, capabilities=capabilities,
                pr_templates=templates, candidates=candidates, issues=issues,
                docs_map_rules=rules, truncated=truncated)


def scaffold(root):
    # Preflight every destination, including parent symlinks, before writing any file.
    for relative in BASE:
        if not safe(root, relative):
            raise ValueError(f'unsafe scaffold path: {relative}; no files created')
        if (root / relative).exists() and not (root / relative).is_file():
            raise ValueError(f'scaffold destination is not a file: {relative}')
    report = analyze(root)
    commands = '\n'.join(f'- {name}: `{command}` ({source}; declared, not verified).' for name, (command, source) in report['commands'].items())
    manifests = '\n'.join(f"- `{item['path']}`: {item['stack']}." for item in report['manifests'])
    directories = '\n'.join(f'- `{directory}/`: inspect its contents before assigning a responsibility.' for directory in report['directories'] if directory != 'docs')
    agents = f'''# Project instructions

{PENDING}
Review these instructions against the code and user intent. Remove the review marker after resolving the unknowns; declared commands have not been executed by tack.

## Commands
{commands or 'No root commands detected. Ask about the intended stack for an empty project; inspect existing tooling for an established project.'}

## Architecture
See [architecture](docs/architecture.md). Keep it current when components or flows change.

## Initialization
Run `tack setup` and follow the new-project onboarding workflow. Before optional repository additions, present concrete paths, their purpose and the evidence for them; ask the user which to create. Respect previous choices and existing files. Record accepted, declined or deferred additions here, then set `tack config setup-review done` (or `deferred` to postpone).

## Project capabilities
Reuse existing local skills and agent definitions. Add and index project-local capabilities when authorized work demonstrates a reusable need; follow the lessons skill's project-capabilities policy. Do not create empty catalogs.
'''
    architecture = f'''# Architecture

{PENDING}
This initial inventory is evidence from the repository, not a verified system design. Describe real component responsibilities, dependencies and important flows after inspecting the code or clarifying the intended project. Remove this marker when reviewed.

## Detected manifests
{manifests or 'No recognized manifests yet. The project stack is not established.'}

## Observed directories
{directories or 'No application directories identified yet.'}

## Decisions and flows
Document only decisions and flows supported by the project. Add diagrams and links to existing documents when they clarify the implementation.
'''
    patterns = [f'{directory}/*' for directory in report['directories'] if directory not in ('docs', 'tests', 'test', 'assets')]
    files, _ = inventory(root)
    patterns += [p for p in files if '/' not in p and Path(p).suffix in ('.py', '.sh', '.js', '.ts', '.go', '.rs')][:20]
    mapping = '# code glob | documentation targets (a change to any listed document covers the rule)\n# Initial architecture coverage; refine by component after reviewing the project.\n'
    mapping += ''.join(f'{pattern} | docs/architecture.md\n' for pattern in patterns if not any(c in pattern for c in '\n\r|,'))
    if not patterns:
        mapping += '# No source paths detected yet. Add real rules when implementation exists.\n'
    for relative, content in zip(BASE, (agents, '@AGENTS.md\n', architecture, mapping)):
        path = root / relative
        if path.exists():
            print(f'kept {relative}')
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='\n') as output:
            output.write(content)
        print(f'created {relative}')
    print('Next: review and fill AGENTS.md and docs/architecture.md from the code; run tack setup and select optional additions with the assistant.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--scaffold', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.scaffold:
            scaffold(root)
            return 0
        report = analyze(root)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print('Project setup (read-only; declared commands are not verified)')
            for item in report['manifests']:
                print(f"Stack: {item['stack']} ({item['path']})")
            for name, (command, source) in report['commands'].items():
                print(f'Command: {name}: {command} ({source})')
            for key, label in [('capabilities', 'Existing capability'), ('pr_templates', 'Existing PR template'), ('issues', 'Review')]:
                for value in report[key]:
                    print(f'{label}: {value}')
            for item in report['candidates']:
                print(f"Propose: {item['item']}: {item['reason']}")
            print(f"Docs-map: {report['docs_map_rules']} active rule(s)")
            if report['truncated']:
                print('Inventory limited to 3000 paths; inspect omitted packages before proposing additions.')
            print('Ask which optional files to add; record choices in AGENTS.md. Finish with tack setup --check and tack config setup-review done, or deferred to postpone.')
        return 1 if args.check and report['issues'] else 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'tack setup: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
