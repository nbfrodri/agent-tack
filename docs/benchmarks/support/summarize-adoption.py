#!/usr/bin/env python3
"""Export non-secret adoption facts and per-model tables from completed, graded runs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_sequence(path):
    writes, red, green = [], [], []
    for index, line in enumerate(path.read_text(encoding='utf-8').splitlines()):
        event = json.loads(line)
        if event.get('type') != 'item.completed':
            continue
        item = event.get('item', {})
        if item.get('type') == 'file_change' and any('/src/' in c.get('path', '') or c.get('path', '').startswith('src/')
                                                    for c in item.get('changes', [])):
            writes.append(index)
        if item.get('type') != 'command_execution':
            continue
        output = item.get('aggregated_output', '')
        if re.search(r'^# fail [1-9]', output, re.M):
            red.append(index)
        passed = bool(re.search(r'^# fail 0$|^Verification: passed ', output, re.M))
        for candidate in output.splitlines():
            if not candidate.startswith('{'):
                continue
            try:
                report = json.loads(candidate)
            except ValueError:
                continue
            if isinstance(report, dict) and report.get('checks') and all(c.get('status') == 'passed' for c in report['checks']):
                passed = True
        if passed:
            green.append(index)
    return {'production_edit_events': writes, 'failing_test_events': red, 'passing_check_events': green,
            'red_before_first_edit': bool(writes and any(i < writes[0] for i in red)),
            'green_after_last_edit': bool(writes and any(i > writes[-1] for i in green)),
            'limit': 'Observed event ordering, manually reviewed for this fixture; not a universal TDD detector.'}


def facts(root, archive_hash):
    graded = load(root / 'graded.json')
    result = {'manifest': load(root / 'manifest.json'), 'versions': load(root / 'versions.json'),
              'fingerprints': load(root / 'fingerprints.json'), 'source_integrity': load(root / 'source-integrity.json'),
              'hidden_sha256': graded['hidden_sha256'], 'raw_archive_sha256': archive_hash,
              'review_note': 'Public counters and fixture diffs only. Full transcripts and private Codex session files are not published.',
              'journeys': []}
    for journey in graded['journeys']:
        directory = root / journey['run_id']
        row = {k: journey[k] for k in ('run_id', 'model', 'condition', 'product_revision')}
        row['infrastructure_error'] = journey.get('infrastructure_error')
        adoption = journey.get('adoption', {}).copy()
        config = adoption.pop('clone_configuration', None)
        if isinstance(config, list):
            adoption['shared_preferences'] = {c['name']: {'value': c['value'], 'source': c['source']} for c in config
                if c['name'] in ('architecture-path', 'plans-path', 'handoffs-path', 'reply-style', 'conventional-commits', 'delegation')}
        row['adoption'] = adoption
        row['installation_seconds'] = {name: load(directory / f'install-{name}.json')['seconds']
                                       for name in ('a', 'b') if (directory / f'install-{name}.json').exists()}
        row['stages'] = {}
        for name, stage in journey['stages'].items():
            artifact = directory / name
            data = {key: stage.get(key) for key in ('completed', 'exit_code', 'seconds', 'usage', 'public_tests', 'runtime')}
            data['commands'] = len(stage['commands'])
            data['failed_commands'] = sum(c['exit_code'] not in (None, 0) for c in stage['commands'])
            data['transcript_sha256'] = hashlib.sha256((artifact / 'transcript.jsonl').read_bytes()).hexdigest()
            data['status'] = (artifact / 'status.txt').read_text(encoding='utf-8')
            data['history'] = (artifact / 'history.txt').read_text(encoding='utf-8')
            data['diff'] = (artifact / 'diff.txt').read_text(encoding='utf-8')
            if 'acceptance' in stage:
                data['acceptance'] = stage['acceptance']
                data['test_sequence'] = test_sequence(artifact / 'transcript.jsonl')
                data['mutations'] = {key: {'detected': value['detected'], 'exit_code': value['exit_code']}
                                     if isinstance(value, dict) else value for key, value in stage['mutations'].items()}
            verify = artifact / 'verify.json'
            if verify.exists():
                wrapper = load(verify)
                try:
                    report = json.loads(wrapper['stdout'])
                    data['verification'] = {'exit_code': wrapper['exit_code'], 'status': report['status'],
                         'unmapped_paths': report.get('unmapped_paths'), 'inputs_changed': report.get('inputs_changed'),
                         'checks': [{k: c.get(k) for k in ('id', 'command', 'status', 'matched_paths', 'duration_s')}
                                    for c in report.get('checks', [])]}
                except (KeyError, ValueError):
                    data['verification'] = {'exit_code': wrapper['exit_code'], 'report_unavailable': True}
            row['stages'][name] = data
        result['journeys'].append(row)
    return result


def table(result):
    print('| Model | Condition | Correct tasks | Median setup s | Median task s | Total session s | Input / cached / output tokens |')
    print('| --- | --- | --- | --- | --- | --- | --- |')
    for model in result['manifest']['models']:
        for condition in result['manifest']['conditions']:
            rows = [r for r in result['journeys'] if r['model'] == model and r['condition'] == condition]
            stages = [s for row in rows for s in row['stages'].values()]
            tasks = [row['stages'][name] for row in rows for name in ('bug', 'feature') if name in row['stages']]
            correct = sum(s['completed'] and s.get('acceptance', {}).get('passed', False) for s in tasks)
            setup = [row['stages']['setup']['seconds'] for row in rows if 'setup' in row['stages']]
            tokens = [sum(s['usage'][key] for s in stages) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')]
            print(f'| {model} | {condition} | {correct}/{len(rows) * 2} | '
                  f'{statistics.median(setup):.1f} | {statistics.median(s["seconds"] for s in tasks):.1f} | '
                  f'{sum(s["seconds"] for s in stages):.1f} | {tokens[0]:,} / {tokens[1]:,} / {tokens[2]:,} |')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--archive-sha256', required=True)
    args = parser.parse_args()
    result = facts(args.root, args.archive_sha256)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + '\n', encoding='utf-8', newline='\n')
    table(result)


if __name__ == '__main__':
    main()
