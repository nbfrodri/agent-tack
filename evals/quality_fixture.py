"""Public task inputs without injected engineering-policy instructions."""
import json
from pathlib import Path

TASKS = {
    'window': {
        'prompt': 'Fix pageWindow: requests beyond the last item currently return the wrong window. Follow the documented API.',
        'contract': 'pageWindow(items, offset=0, limit=20) returns a new array with at most limit items, starting at offset. '
        'offset is a nonnegative safe integer; limit is a safe integer from 1 through 100. Reject invalid arguments with RangeError. '
        'Do not coerce strings or booleans. Beyond the end returns an empty array. Preserve item identity and the input array.',
        'files': {
            'src/window.js': 'export function pageWindow(items, offset = 0, limit = 20) {\n  return items.slice(offset % items.length, offset % items.length + limit);\n}\n',
            'tests/window.test.js': "import {test} from 'node:test';\nimport assert from 'node:assert/strict';\nimport {pageWindow} from '../src/window.js';\ntest('first window', () => assert.deepEqual(pageWindow([1,2,3], 0, 2), [1,2]));\n",
        },
    },
    'shipment': {
        'prompt': 'Add shipment.cancelled support to the dispatch service according to its event contract.',
        'contract': 'Dispatch accepts an object with a nonempty string id, preserving its exact value. '
        'shipment.created has a nonempty string address and routes to shipments. '
        'shipment.cancelled has a nonempty string reason and an integer revision from 0 through Number.MAX_SAFE_INTEGER; '
        'it routes to shipment-cancellations. Reject whitespace-only required strings, wrong types, invalid revisions and unknown events. '
        'Return {topic, key: original id, payload: a new shallow copy of the event}. Never modify the caller; retain extra fields. '
        'Existing shipment.created behavior and module exports remain compatible.',
        'files': {
            'src/validate.js': "export function validate(event) {\n  if (!event || typeof event.id !== 'string' || !event.id.trim()) throw new Error('invalid id');\n  if (event.type !== 'shipment.created') throw new Error('unknown event');\n  if (typeof event.address !== 'string' || !event.address.trim()) throw new Error('invalid address');\n  return {...event};\n}\n",
            'src/dispatch.js': "import {validate} from './validate.js';\nconst topics = {'shipment.created': 'shipments'};\nexport function dispatch(event) {\n  const payload = validate(event);\n  if (!Object.hasOwn(topics, payload.type)) throw new Error('unknown event');\n  return {topic: topics[payload.type], key: payload.id, payload};\n}\n",
            'tests/dispatch.test.js': "import {test} from 'node:test';\nimport assert from 'node:assert/strict';\nimport {dispatch} from '../src/dispatch.js';\ntest('created shipment', () => assert.equal(dispatch({id:'a',type:'shipment.created',address:'Home'}).topic,'shipments'));\n",
        },
    },
    'settings': {
        'prompt': 'Implement the documented layered settings behavior; overrides currently leak between calls.',
        'contract': 'load_settings(overrides=None, env=None) returns a fresh dict with defaults '
        '{"endpoint":"http://localhost","retry":{"attempts":3,"delay_ms":100},"tags":[]}. '
        'Merge only provided nested retry keys. Overrides must be a dict with supported keys; retry must be a dict with supported keys. '
        'endpoint is a nonempty string, attempts is a non-boolean integer 1..10, delay_ms a non-boolean integer 0..60000, '
        'and tags a list of strings. Invalid override values/unknown keys raise ValueError. '
        'The supplied env mapping overrides endpoint via APP_ENDPOINT and attempts via APP_ATTEMPTS; ignore unrelated env keys. '
        'APP_ATTEMPTS must be a decimal-digit string representing 1..10. env=None means no environment overrides; do not read process environment. '
        'Neither input dictionaries, nested lists, returned values nor DEFAULTS may share mutable state across calls. '
        'All errors leave defaults and caller inputs unchanged. Public exports DEFAULTS and load_settings stay available.',
        'files': {
            'settings.py': "DEFAULTS = {'endpoint': 'http://localhost', 'retry': {'attempts': 3, 'delay_ms': 100}, 'tags': []}\n\ndef load_settings(overrides=None, env=None):\n    result = DEFAULTS\n    result.update(overrides or {})\n    return result\n",
            'tests/test_settings.py': "import unittest\nfrom settings import load_settings\n\nclass SettingsTests(unittest.TestCase):\n    def test_defaults(self):\n        self.assertEqual(load_settings()['retry']['attempts'], 3)\n",
        },
    },
    'assignments': {
        'prompt': 'Fix the config CLI so values containing equals signs survive, and implement the documented unset option.',
        'contract': 'python3 -m config_cli accepts ordered operations: --set KEY=VALUE and --unset KEY. '
        'Split assignments only on the first equals sign; empty values are valid. Keys match [A-Za-z_][A-Za-z0-9_]*. '
        'Last operation for a key wins; unsetting an absent key succeeds. '
        'With valid arguments print one JSON object (keys sorted), newline, exit 0. No arguments prints {}. '
        'Missing operands, invalid keys, assignment without = and unknown arguments write a useful error to stderr, '
        'leave stdout empty and exit 2 without a traceback. Process every argument; never ignore trailing junk. '
        'Keep parse_args(argv) returning a dict and raising ValueError for invalid input; never mutate argv. '
        'The CLI is a pure converter and writes no config files.',
        'files': {
            'config_cli/__init__.py': '',
            'config_cli/options.py': "def parse_args(argv):\n    result = {}\n    for i in range(0, len(argv), 2):\n        if argv[i] == '--set':\n            key, value = argv[i + 1].split('=')\n            result[key] = value\n    return result\n",
            'config_cli/__main__.py': "import json\nimport sys\nfrom .options import parse_args\n\ndef main():\n    print(json.dumps(parse_args(sys.argv[1:]), sort_keys=True))\n    return 0\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n",
            'tests/test_options.py': "import unittest\nfrom config_cli.options import parse_args\n\nclass OptionsTests(unittest.TestCase):\n    def test_assignment(self):\n        self.assertEqual(parse_args(['--set', 'a=b']), {'a': 'b'})\n",
        },
    },
    'pilot': {
        'prompt': 'Fix total so it accepts valid empty inputs according to the documented API.',
        'contract': 'total(values) returns the sum of finite numbers, including 0 for an empty list. '
        'Reject booleans and nonfinite/non-number values with ValueError. Do not change the input list.',
        'files': {
            'totals.py': 'def total(values):\n    if not values:\n        raise ValueError("empty")\n    return sum(values)\n',
            'tests/test_totals.py': 'import unittest\nfrom totals import total\n\nclass TotalTests(unittest.TestCase):\n    def test_sum(self):\n        self.assertEqual(total([1,2]), 3)\n',
        },
    },
}

SETUP_PROMPT = (
    'Configure tack for this existing project and a teammate using a separate clone. '
    'We choose shared activation, auto mode, brief replies, Conventional Commits, '
    'architecture at docs/architecture.md, plans at work/plans and handoffs at work/handoffs. '
    'Reuse existing project code and documentation. Add a suitable PR template and record these choices. '
    'We decline extra skills, agents, dependencies, release automation and CI. '
    'Select the existing useful check command, finish setup review and commit the setup locally. '
    'Do not change production behavior during setup.'
)


def seed(name, root):
    root = Path(root)
    task = TASKS[name]
    files = dict(task['files'])
    javascript = name in ('window', 'shipment')
    if javascript:
        files['package.json'] = json.dumps({'name': 'fixture', 'private': True, 'type': 'module',
                                           'scripts': {'test': 'node --test'}}, indent=2) + '\n'
    files['.gitignore'] = '__pycache__/\n*.pyc\nnode_modules/\n'
    files['docs/contract.md'] = '# Product contract\n\n' + task['contract'] + '\n'
    files['docs/architecture.md'] = '# Architecture\n\n' + '\n'.join(
        '- `' + path + '`' for path in task['files'] if not path.startswith('tests/')) + '\n'
    files['README.md'] = '# Example project\n\nSee [contract](docs/contract.md) and [architecture](docs/architecture.md).\n\n' + (
        'Available command: `npm test`.\n' if javascript else 'Available command: `python3 -m unittest discover -s tests`.\n')
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')
    return files


def test_command(task):
    return ['npm', 'test'] if task in ('window', 'shipment') else ['python3', '-m', 'unittest', 'discover', '-s', 'tests']
