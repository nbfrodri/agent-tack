#!/usr/bin/env python3
"""Post-hoc probes from blind code review; never replace frozen acceptance."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PYTHON = r'''
import json
import sys
from collections import UserDict
sys.path.insert(0, sys.argv[1])
import settings
out = {}
def check(name, call, wanted):
    try:
        out[name] = {'passed': call() == wanted}
    except Exception as error:
        out[name] = {'passed': False, 'error': type(error).__name__}
def invalid_masked():
    try:
        settings.load_settings({'endpoint': False}, {'APP_ENDPOINT': 'valid'})
    except ValueError:
        return True
    return False
check('mapping env', lambda: settings.load_settings(env=UserDict({'APP_ATTEMPTS': '4'}))['retry']['attempts'], 4)
check('long leading zeros', lambda: settings.load_settings(env={'APP_ATTEMPTS': '0' * 5000 + '1'})['retry']['attempts'], 1)
check('masked invalid override', invalid_masked, True)
check('Unicode decimal (ambiguous contract scope)', lambda: settings.load_settings(env={'APP_ATTEMPTS': '\u0663'})['retry']['attempts'], 3)
print(json.dumps(out))
'''

JAVASCRIPT = r'''
import {pathToFileURL} from 'node:url';
const {dispatch} = await import(pathToFileURL(process.argv[1] + '/src/dispatch.js'));
const inherited = Object.assign(Object.create({id: 'original'}), {
  type: 'shipment.cancelled', reason: 'cancel', revision: 0,
});
const func = Object.assign(() => {}, {
  id: 'id', type: 'shipment.cancelled', reason: 'cancel', revision: 0,
});
const out = {};
try {
  out['inherited id (non-JSON object)'] = {passed: dispatch(inherited).key === 'original'};
} catch (error) {
  out['inherited id (non-JSON object)'] = {passed: false, error: error.name};
}
try {
  dispatch(func);
  out['function envelope'] = {passed: false};
} catch {
  out['function envelope'] = {passed: true};
}
console.log(JSON.stringify(out));
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    results = {}
    with tempfile.TemporaryDirectory(prefix='quality-supplement-') as temp:
        env = {'PATH': os.environ['PATH'], 'HOME': temp, 'XDG_CONFIG_HOME': temp,
               'GIT_CONFIG_NOSYSTEM': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        for path in sorted(args.source.glob('*/case.json')):
            case = json.loads(path.read_text(encoding='utf-8'))
            root = (path.parent / 'repo').resolve()
            if case['task'] == 'settings':
                command = [sys.executable, '-c', PYTHON, str(root)]
            elif case['task'] == 'shipment':
                command = ['node', '--input-type=module', '-e', JAVASCRIPT, str(root)]
            else:
                continue
            try:
                result = subprocess.run(command, env=env, cwd=root, capture_output=True,
                                        text=True, encoding='utf-8', timeout=10)
                results[case['id']] = json.loads(result.stdout) if result.returncode == 0 else {
                    'error': 'probe process failed', 'exit_code': result.returncode}
            except (subprocess.TimeoutExpired, ValueError) as error:
                results[case['id']] = {'error': type(error).__name__}
    report = {'status': 'Post-hoc supplementary evidence; not frozen acceptance.',
              'seconds': time.monotonic() - started, 'cases': results}
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Supplementary evidence saved without displaying condition outcomes.')


if __name__ == '__main__':
    main()
