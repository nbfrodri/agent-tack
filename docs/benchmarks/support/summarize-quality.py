#!/usr/bin/env python3
"""Join completed evidence only after the orchestrator has saved its blind assessment."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'evals'))
from quality_review import validate  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_facts(directory):
    facts = []
    wanted = {'reply-style': 'brief', 'conventional-commits': 'true',
              'architecture-path': 'docs/architecture.md', 'plans-path': 'work/plans', 'handoffs-path': 'work/handoffs'}
    for path in sorted(directory.glob('*/case.json')):
        case = read(path)
        observations = path.parent / 'teammate.json'
        record = {key: case[key] for key in ('id', 'model', 'condition')}
        record['session'] = session_facts(path.parent)
        record['artifacts'] = artifact_facts(path.parent)
        hashes = record['artifacts']['snapshot_hashes']
        initial_path = path.parent / 'fixture-hashes.json'
        initial = read(initial_path) if initial_path.exists() else {}
        record['initial_production_and_tests_unchanged'] = all(
            hashes.get(name) == value for name, value in initial.items()
            if name.endswith(('.py', '.js')))
        record['pr_templates'] = [name for name in hashes if 'pull_request_template' in name.lower()]
        record['shared_preferences'] = {}
        if observations.exists():
            observed = read(observations)
            records = json.loads(observed['config']['stdout']) if observed['config']['exit_code'] == 0 else []
            by_name = {entry['name']: entry for entry in records}
            for key, value in wanted.items():
                entry = by_name.get(key, {})
                record['shared_preferences'][key] = {'value': entry.get('value'), 'source': entry.get('source'),
                                                     'passed': entry.get('value') == value and entry.get('source') == 'shared'}
            record.update(shared_mode=observed['mode']['stdout'].strip(),
                          shared_activation=observed['activation']['exit_code'] == 0,
                          locally_untrusted=observed['trust']['exit_code'] == 1,
                          local_override=observed['local_override']['stdout'].strip())
        facts.append(record)
    return facts


def session_facts(directory):
    path = directory / 'session.json'
    if not path.exists():
        return {'completed': False, 'evidence_missing': True}
    source = read(path)
    result = {key: source.get(key) for key in ('completed', 'exit_code', 'seconds', 'total_seconds',
                                              'usage', 'runtime', 'product_unchanged', 'container_mounts', 'infrastructure_error')}
    result['command_count'] = len(source.get('commands', []))
    commands = source.get('commands', [])
    result['command_categories'] = {
        # Categories overlap and count shell events, not subprocesses or time attribution.
        'test_or_verify': sum(bool(re.search(r'npm test|node --test|unittest|tack verify', c['command'])) for c in commands),
        'nonzero_shell_event_with_check': sum(c.get('exit_code') not in (0, None) and bool(re.search(
            r'npm test|node --test|unittest|tack verify', c['command'])) for c in commands),
        'context_or_setup': sum(bool(re.search(r'tack (?:context|setup|config)', c['command'])) for c in commands),
        'branch_creation': sum(bool(re.search(r'git (?:switch -c|checkout -b)', c['command'])) for c in commands),
    }
    result['transcript_sha256'] = sha(directory / 'transcript.jsonl') if (directory / 'transcript.jsonl').exists() else None
    for name in ('install', 'versions', 'public-tests'):
        file = directory / (name + '.json')
        if file.exists():
            data = read(file)
            result[name] = data if name == 'versions' else {key: data.get(key) for key in ('seconds', 'exit_code')}
    return result


def artifact_facts(directory):
    repo = directory / 'repo'
    initial = directory / 'fixture-hashes.json'
    original = read(initial) if initial.exists() else {}
    delivered = {p.relative_to(repo).as_posix(): sha(p) for p in sorted(repo.rglob('*'))
                 if p.is_file() and not p.is_symlink()}
    changed = [name for name, digest in delivered.items()
               if original.get(name) != digest]
    deleted = sorted(set(original) - set(delivered))
    git = read(directory / 'git.json') if (directory / 'git.json').exists() else {}
    history = git.get('history', {}).get('stdout', '')
    subjects = [line.strip() for line in history.splitlines() if line.startswith('    ') and line.strip()]
    return {'snapshot_hashes': delivered, 'different_from_public_fixture': changed, 'deleted': deleted,
            'commit_count': len(re.findall(r'^commit [0-9a-f]+$', history, re.MULTILINE)),
            'commit_messages': subjects, 'git_status': git.get('status', {}).get('stdout'),
            'note': 'Differences include preseeded tack configuration. File counts and overlapping shell-event categories are not quality points, time attribution or proven TDD.'}


def build(root):
    reviews = root / 'reviews'
    assessment = reviews / 'orchestrator-blind.json'
    if not assessment.is_file():
        raise ValueError('Save the complete blind orchestrator assessment before opening label mappings')
    adjudication = read(assessment)
    mapping = read(reviews / 'private-label-map.json')
    if set(adjudication) != set(mapping):
        raise ValueError('The blind assessment must cover both reviews of every matched triplet')
    grades, dimensions, source_scores, review_facts = defaultdict(list), defaultdict(list), defaultdict(list), []
    for review_id, labels in sorted(mapping.items()):
        directory = reviews / review_id
        bundle_path = directory / 'bundle/bundle.json'
        if adjudication[review_id].get('bundle_sha256') != sha(bundle_path):
            raise ValueError('Blind assessment does not match the reviewed bundle')
        bundle = read(bundle_path)
        grade_path = directory / 'evidence/review.json'
        item = {'id': review_id, 'labels': labels, 'bundle_sha256': sha(bundle_path),
                'bundle': bundle, 'session': session_facts(directory / 'evidence'), 'orchestrator': adjudication[review_id]}
        if grade_path.is_file():
            raw = read(grade_path)
            item['raw_review'] = raw
            item['review_sha256'] = sha(grade_path)
            try:
                totals = validate(raw, bundle)
                item['weighted_scores'] = totals
                if item['session']['completed']:
                    for label, value in totals.items():
                        grades[labels[label]].append(value)
                        identity = json.dumps({'contract': bundle['contract'], 'code': bundle['candidates'][label]}, sort_keys=True)
                        source_scores[hashlib.sha256(identity.encode()).hexdigest()].append(
                            {'review': review_id, 'label': label, 'score': value})
                    for candidate in raw['candidates']:
                        dimensions[labels[candidate['id']]].append(
                            {name: entry['score'] for name, entry in candidate['dimensions'].items()})
            except ValueError as error:
                item['validation_error'] = str(error)
        review_facts.append(item)
    acceptance = read(root / 'coding-grade.json')
    cases, groups = [], defaultdict(list)
    for path in sorted((root / 'coding').glob('*/case.json')):
        case = read(path)
        record = {key: case[key] for key in ('id', 'model', 'task', 'repetition', 'condition', 'prompt_sha256')}
        record['session'] = session_facts(path.parent)
        record['artifacts'] = artifact_facts(path.parent)
        record['fixture_hashes'] = read(path.parent / 'fixture-hashes.json')
        record['grade'] = acceptance.get(case['id'], {'acceptance': {'passed': False, 'error': 'missing grader result'}})
        record['blind_scores'] = grades[case['id']]
        record['mean_blind_score'] = statistics.mean(record['blind_scores']) if len(record['blind_scores']) == 2 else None
        scores = dimensions[case['id']]
        record['mean_dimension_scores'] = {name: statistics.mean(s[name] for s in scores) for name in scores[0]} if len(scores) == 2 else None
        cases.append(record)
        groups[(record['model'], record['condition'])].append(record)
    summary = []
    for (model, condition), records in sorted(groups.items()):
        times = [r['session']['seconds'] for r in records if isinstance(r['session'].get('seconds'), (int, float))]
        scores = [r['mean_blind_score'] for r in records if r['mean_blind_score'] is not None]
        passed = sum(bool(r['grade']['acceptance'].get('passed')) and bool(r['session']['completed']) for r in records)
        summary.append({'model': model, 'condition': condition, 'attempts': len(records),
                        'completed': sum(bool(r['session']['completed']) for r in records), 'accepted': passed,
                        'mean_seconds': statistics.mean(times) if times else None,
                        'median_seconds': statistics.median(times) if times else None, 'total_seconds': sum(times),
                        'seconds_per_accepted': sum(times) / passed if passed else None,
                        'mean_blind_score': statistics.mean(scores) if scores else None, 'fully_reviewed': len(scores),
                        'mean_dimensions': {name: statistics.mean(r['mean_dimension_scores'][name] for r in records
                                                                if r['mean_dimension_scores'] is not None)
                                            for name in ('responsibilities', 'readability', 'robustness', 'changeability', 'simplicity', 'consistency')}
                                           if scores else None,
                        'tokens': {key: sum((r['session'].get('usage') or {}).get(key, 0) for r in records)
                                   for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')}})
    consistency = [{'source_and_contract_sha256': key, 'observations': values,
                    'spread': max(v['score'] for v in values) - min(v['score'] for v in values)}
                   for key, values in source_scores.items() if len(values) > 1]
    return {'manifest': read(root / 'coding/manifest.json'), 'cases': cases, 'reviews': review_facts,
            'setup': setup_facts(root / 'setup'), 'summary': summary,
            'identical_source_score_spread': consistency,
            'products': read(root / 'coding/products.json'), 'controller_sha256': read(root / 'coding/controller.json'),
            'image_id': read(root / 'coding/image.json'),
            'orchestrator_assessment_sha256': sha(assessment),
            'limits': 'Small synthetic study. Agent grades are subjective; repeated judgments share one model. Functional acceptance, code quality and time remain separate. Token counts are not USD costs.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    main()
