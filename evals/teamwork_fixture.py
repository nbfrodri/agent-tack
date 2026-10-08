"""Small cross-language monorepo for a two-session integration pilot."""
import json

PROMPTS = {
    'backend': 'Implement POST /orders as specified in contracts/orders.md. The frontend is being built on a separate branch.',
    'frontend': 'Connect the order form to the order API implemented on feat/backend, including a useful validation error. The backend branch has not been merged into main yet.',
}


def seed(root):
    files = {
        '.gitignore': '__pycache__/\n*.pyc\n',
        'README.md': '# Order app\n\nPython backend, JavaScript frontend. Contract: contracts/orders.md.\n'
                     'Checks: `python3 -m unittest discover -s tests` and `node --test frontend/client.test.mjs`.\n',
        'AGENTS.md': '# Project\n\nContract: contracts/orders.md. Architecture: docs/architecture.md.\n'
                     'Backend: backend/. Frontend: frontend/. Handoffs: docs/handoffs/.\n'
                     'Checks: python3 -m unittest discover -s tests; node --test frontend/client.test.mjs.\n',
        'CLAUDE.md': '@AGENTS.md\n',
        'docs/architecture.md': '# Architecture\n\nbackend/orders.py provides the POST /orders handler as create_order(payload).\n'
                                'It returns (HTTP status, JSON body). frontend/client.mjs provides submitOrder(form, request).\n'
                                'request is an injected async HTTP transport returning {status, body}; no running server is needed.\n',
        'docs/handoffs/zz-analytics.md': '# Analytics\nStatus: paused\nBranch: `feat/analytics`\n'
                                      'Next: discuss chart colors. This work does not change order creation.\n',
        'contracts/orders.md': '# Order creation\n\nPOST /orders accepts {sku: string, quantity: integer}.\n'
                               'The catalog contains WIDGET at 1250 cents. Quantity must be a positive integer; booleans are invalid.\n'
                               'Success: HTTP 201 with {id: nonempty string, status: "pending", totalCents: integer}.\n'
                               'Invalid quantity: HTTP 422 with {error: {code: "invalid_quantity", message: nonempty string}}.\n'
                               'Unknown SKU: HTTP 404 with {error: {code: "unknown_sku", message: nonempty string}}.\n'
                               'The order form supplies quantity as a string. submitOrder(form, request) calls request("POST", "/orders", payload).\n'
                               'On success it returns {ok: true, orderId: string, totalCents: integer}; on API failure {ok: false, error: message}.\n',
        'backend/__init__.py': '',
        'backend/orders.py': 'CATALOG = {"WIDGET": 1250}\n\n\ndef create_order(payload):\n    raise NotImplementedError("Order creation is not implemented")\n',
        'frontend/client.mjs': 'export async function submitOrder(form, request) {\n  throw new Error("Order submission is not implemented");\n}\n',
        'tests/test_catalog.py': 'import unittest\nfrom backend.orders import CATALOG\n\nclass CatalogTest(unittest.TestCase):\n'
                                 '    def test_known_price(self):\n        self.assertEqual(CATALOG["WIDGET"], 1250)\n',
        'frontend/client.test.mjs': 'import test from "node:test";\nimport assert from "node:assert/strict";\n'
                                    'import {submitOrder} from "./client.mjs";\n'
                                    'test("client entry point exists", () => assert.equal(typeof submitOrder, "function"));\n',
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')
    return files


def profile(candidate):
    config = {'reply-style': 'brief', 'conventional-commits': True, 'check-fast':
              'python3 -m unittest discover -s tests && node --test frontend/client.test.mjs'}
    if candidate:
        config['collaboration'] = 'team'
    return json.dumps({'version': 1, 'mode': 'auto', 'config': config}, indent=2) + '\n'
