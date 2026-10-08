"""Post-hoc contract probes; run delivered code only inside the networkless evaluator."""
import importlib.util
from collections import UserDict
import json
from pathlib import Path
import subprocess
import sys


def probe(root, task):
    if task == 'shipment':
        script = '''
import {pathToFileURL} from 'node:url';
const {dispatch} = await import(pathToFileURL(process.argv[1] + '/src/dispatch.js'));
const rows = [];
for (const type of ['shipment.created', 'shipment.cancelled']) {
  const fields = {type, address: 'A', reason: 'R', revision: 1};
  for (const [name, value] of [
    ['function', Object.assign(function () {}, fields, {id: ' exact '})],
    ['inherited_id', Object.assign(Object.create({id: ' exact '}), fields)],
    ['nonenumerable_id', Object.defineProperty({...fields}, 'id', {value: ' exact '})],
  ]) {
    let accepted = false, key;
    try { key = dispatch(value).key; accepted = true; } catch {}
    rows.push({type, name, accepted, preserves_key: key === ' exact '});
  }
}
console.log(JSON.stringify(rows));
'''
        result = subprocess.run(['node', '--input-type=module', '-e', script, str(root)],
                                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
        if result.returncode:
            return {'error': result.stderr[-1000:]}
        return json.loads(result.stdout)
    sys.path.insert(0, str(root))
    rows = []
    for name, overrides, env in [
        ('invalid_endpoint_masked', {'endpoint': ''}, {'APP_ENDPOINT': 'valid'}),
        ('invalid_attempts_masked', {'retry': {'attempts': True}}, {'APP_ATTEMPTS': '3'}),
    ]:
        spec = importlib.util.spec_from_file_location('candidate', root / 'settings.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        error = None
        try:
            module.load_settings(overrides, env)
        except Exception as exception:
            error = type(exception).__name__
        rows.append(dict(name=name, rejected_with_value_error=error == 'ValueError', error=error))
    for name, overrides, env, field, expected in [
        ('mapping_environment', None, UserDict(APP_ENDPOINT='valid'), 'endpoint', 'valid'),
        ('unicode_decimal', None, {'APP_ATTEMPTS': '\u0663'}, 'attempts', 3),
        ('long_decimal', None, {'APP_ATTEMPTS': '0' * 5000 + '1'}, 'attempts', 1),
    ]:
        spec = importlib.util.spec_from_file_location('candidate', root / 'settings.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        error, actual = None, None
        try:
            result = module.load_settings(overrides, env)
            actual = result[field] if field == 'endpoint' else result['retry'][field]
        except Exception as exception:
            error = type(exception).__name__
        rows.append(dict(name=name, passed=error is None and actual == expected, error=error))
    return rows


if __name__ == '__main__':
    print(json.dumps(probe(Path(sys.argv[1]).resolve(), sys.argv[2])))
