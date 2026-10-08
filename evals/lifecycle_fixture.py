"""Public repositories and product requests for the frozen lifecycle comparison."""
import json
from pathlib import Path

CONDITIONS = ('plain', 'project', 'tack')
STAGES = ('setup', 'build', 'change', 'review')
SCENARIOS = ('stock', 'orders')
GUIDE = '''# Project instructions

Read README.md and the relevant guide/contract.md before changes. Reuse the existing structure.
Use branches, Conventional Commits without AI attribution, red/green/refactor for behavior,
meaningful regression tests, and the smallest complete change. Check affected consumers.
Update inaccurate canonical docs; record useful handoff information, not empty process files.
Reuse the setup choices in guide/working-agreement.md. Report actual checks and limitations.
'''
AGREEMENT = '''# Working agreement

Use existing built-in test runners; no new dependencies, external skills, extra agents or release automation.
Project context stays in guide/architecture.md and guide/contract.md. Supported behavior is listed in
guide/capabilities.md. Plans and handoffs, when needed, belong in work/plans and work/handoffs.
We want brief replies and effort proportional to the task. Use TDD for behavior, simple cohesive code,
branches, Conventional Commits with no AI attribution, useful checks and current documentation.
Record accepted and declined choices once in AGENTS.md so another participant can reuse them.
Keep execution trust local. If tack is available, use one shared root profile and shared activation.
If it is absent, ordinary project guidance is sufficient. Do not invent another tool manager.
'''
STOCK_CONTRACT = '''# Stock contract

Current interface: stock.allocation.reserve(stock, requests). The next requested release must implement
atomic reservation. stock is a dict of nonempty string SKU keys to nonnegative Python ints, excluding bool.
requests is a list of dicts with exactly sku (nonempty string) and quantity (positive int, excluding bool).
Reject every invalid field, unknown SKU and insufficient aggregate quantity with ValueError, even when a
later request or field would hide it. Aggregate duplicate SKU requests. Return a new dict with exactly
remaining (new stock dict) and reserved (new dict containing only requested SKUs and aggregate amounts).
Empty requests returns a fresh stock copy and empty reserved dict. Never mutate or alias caller containers.
Preserve unrelated stock entries. Do not read process environment, disk or network in domain functions.

stock.redirect.safe_redirect(value): accept only strings beginning with a single slash; reject double
slashes, any backslash, ASCII control characters (U+0000..001F and U+007F), or nonstrings with ValueError.
Return the original accepted path, including query/fragment. This is an existing security requirement.
'''
ORDER_CONTRACT = '''# Order contract

backend/quote.mjs exports quote(lines, discountPercent=0). lines is an array of objects with exactly
unitCents (nonnegative safe integer) and quantity (positive safe integer). Reject invalid entries,
unknown keys, unsafe products/sums and non-array inputs; never coerce values or mutate input.
discountPercent must be an integer from 0 to 100. The next requested release must return exactly
{version:2, subtotalCents, discountCents, totalCents, total}, where discountCents is
Math.floor(subtotalCents * discountPercent / 100), totalCents is subtotalCents - discountCents,
and total is a legacy alias for totalCents. Empty lines is valid. Preserve exact safe-integer arithmetic
even when the intermediate percentage multiplication would exceed Number.MAX_SAFE_INTEGER.
frontend/client.mjs exports renderQuote(value), currently reading legacy total. Its label comes from
frontend/labels.mjs. Do not change the frontend during the backend-only release.

backend/redirect.mjs exports safeRedirect(value): accept only strings beginning with a single slash;
reject double slashes, any backslash, ASCII control characters (U+0000..001F and U+007F), and nonstrings.
Return the original accepted path, including query/fragment. This is an existing security requirement.
'''
NEXT = {
    'stock': '''# Next release: partial returns

Add stock.allocation.release(stock, held, returns). stock and held are dicts of nonempty SKU strings to
nonnegative ints, excluding bool. Every held SKU must already exist in stock, including zero-held entries.
returns has the same request format as reserve. Aggregate duplicates; reject unknown SKUs, malformed
values, and totals exceeding held quantities with ValueError before making changes. Return exactly
{remaining: fresh stock plus returned quantities, held: fresh held minus returned quantities}, retaining
zero-held entries. No caller mutation/aliasing. Keep every reserve behavior unchanged.
''',
    'orders': '''# Next release: shipping and migrated client

quote must also accept an options object as argument two, with exactly discountPercent (default 0),
shippingCents (default 0, nonnegative safe integer), freeShippingAtCents (default null; null or nonnegative
safe integer). Keep the numeric second argument and all prior validation. Reject null/array/nonobject
options, unknown keys and every invalid supplied field even if shipping would be free. Compute discounts
exactly as before. Shipping becomes zero when the discounted merchandise total is at least the non-null
threshold. Return all previous fields plus shippingCents (effective charge); total/totalCents include it.
Reject unsafe totals. Inputs remain unchanged.

renderQuote must support both legacy {total} and new version-2 objects. For v2 use totalCents even if
legacy total differs, require nonnegative safe integers for subtotalCents, discountCents, shippingCents
and totalCents, enforce discount <= subtotal and total == subtotal - discount + shipping, and reject
malformed values/unsupported versions. Missing version means legacy. Output exactly LABEL + ': $' +
two-decimal dollars, preserving every cent throughout the safe-integer range, using the label from frontend/labels.mjs. The labels branch changes LABEL to
'Amount due'; preserve that team change. The backend release is branch-only until integrated.
'''
}
PROMPTS = {
    'setup': 'Prepare this repository for the next participant using the already agreed choices in guide/working-agreement.md. Keep production behavior unchanged and preserve existing files.',
    'stock-build': 'Implement atomic stock reservation according to guide/contract.md.',
    'stock-change': 'Add partial returns according to guide/next-contract.md while keeping reservation behavior.',
    'orders-build': 'Implement the new backend quote response described in guide/contract.md. Keep the current frontend working and leave its migration for the next contributor.',
    'orders-change': 'Finish the shipping release and migrate the frontend according to guide/next-contract.md. The backend release is on feat/backend and the other team changed labels on feat/labels; include both in the delivered application.',
    'review': 'Address the pending review in review/state.json against the current code. Record each disposition and any justified follow-up in that local review record. Existing records are part of the project. Deliver the application with the review addressed.',
}


def write(root, name, content):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')


def command(scenario):
    return ['python3', '-m', 'unittest', 'discover', '-s', 'tests'] if scenario == 'stock' else ['node', '--test']


def seed(root, scenario, condition):
    stock = scenario == 'stock'
    files = {
        '.gitignore': '__pycache__/\n.private/\nnode_modules/\n',
        'README.md': '# Example application\n\nCommands: `' + ' '.join(command(scenario)) + '`. No external dependencies.\n'
                     'Read guide/architecture.md, guide/contract.md and guide/working-agreement.md.\n',
        'guide/working-agreement.md': AGREEMENT + ('\nOne developer works on this application.\n' if stock else '\nAPI and frontend developers work in separate clones of this monorepo.\n'),
        'guide/contract.md': STOCK_CONTRACT if stock else ORDER_CONTRACT,
        'guide/architecture.md': '# Architecture\n\n' + ('stock/allocation.py owns stock operations; stock/redirect.py validates return URLs.\n' if stock else
            'backend/quote.mjs owns money calculations; frontend/client.mjs renders the public quote; frontend/labels.mjs owns labels. backend/redirect.mjs validates return URLs.\n'),
        'guide/capabilities.md': '# Available behavior\n\n' + ('Legacy reservation is available. Atomic validation and partial returns are planned.\n' if stock else
            'Legacy totals are available. Version-2 quotes, shipping and the migrated frontend are planned.\n'),
    }
    if stock:
        files.update({
            'stock/__init__.py': '',
            'stock/allocation.py': 'def reserve(stock, requests):\n    reserved = {}\n    for item in requests:\n        sku, quantity = item["sku"], item["quantity"]\n        stock[sku] -= quantity\n        reserved[sku] = quantity\n    return {"remaining": stock, "reserved": reserved}\n',
            'stock/redirect.py': 'def safe_redirect(value):\n    if not isinstance(value, str) or not value.startswith("/"):\n        raise ValueError("path")\n    return value\n',
            'pyproject.toml': '[project]\nname = "stock-example"\nversion = "0.1.0"\n',
            'tests/test_public.py': 'import unittest\nfrom stock.allocation import reserve\nfrom stock.redirect import safe_redirect\n\nclass Public(unittest.TestCase):\n    def test_reserve(self):\n        self.assertEqual(reserve({"a": 4}, [{"sku": "a", "quantity": 2}])["remaining"], {"a": 2})\n    def test_redirect(self):\n        self.assertEqual(safe_redirect("/orders?view=1"), "/orders?view=1")\n',
        })
    else:
        files.update({
            'backend/quote.mjs': 'export function quote(lines, discountPercent = 0) {\n  const total = lines.reduce((sum, line) => sum + line.unitCents * line.quantity, 0);\n  return {total: total - Math.floor(total * discountPercent / 100)};\n}\n',
            'frontend/labels.mjs': 'export const LABEL = "Total";\n',
            'frontend/client.mjs': 'import {LABEL} from "./labels.mjs";\nexport function renderQuote(value) { return `${LABEL}: $${(value.total / 100).toFixed(2)}`; }\n',
            'backend/redirect.mjs': 'export function safeRedirect(value) {\n  if (typeof value !== "string" || !value.startsWith("/")) throw new Error("path");\n  return value;\n}\n',
            'package.json': json.dumps({'name': 'order-example', 'private': True, 'type': 'module', 'scripts': {'test': 'node --test'}}) + '\n',
            'tests/public.test.mjs': 'import {test} from "node:test";\nimport assert from "node:assert/strict";\nimport {quote} from "../backend/quote.mjs";\nimport {renderQuote} from "../frontend/client.mjs";\nimport {LABEL} from "../frontend/labels.mjs";\nimport {safeRedirect} from "../backend/redirect.mjs";\ntest("legacy calculation", () => assert.equal(quote([{unitCents: 250, quantity: 2}], 10).total, 450));\ntest("client", () => assert.equal(renderQuote({total: 123}), `${LABEL}: $1.23`));\ntest("redirect", () => assert.equal(safeRedirect("/orders"), "/orders"));\n',
        })
    if condition == 'project':
        files['AGENTS.md'] = GUIDE
    for name, content in files.items():
        write(root, name, content)
    return files


def review_state(scenario):
    path = 'stock/redirect.py' if scenario == 'stock' else 'backend/redirect.mjs'
    return dict(version=1, threads=[
        dict(id='R1', url='local://review/17/R1', path=path, outdated=False, resolved=False,
             body='A //evil.example path is accepted as a redirect. This violates the single-slash contract and can redirect to another host.', response=''),
        dict(id='R2', url='local://review/17/R2', path=path, outdated=True, resolved=False,
             body='ASCII controls and backslashes in redirect paths must be rejected. The line anchor is outdated; verify current behavior.', response=''),
        dict(id='R3', url='local://review/17/R3', path='guide/architecture.md', outdated=False, resolved=False,
             body='Consider optimizing allocation/quote throughput on large batches in a follow-up; no benchmark establishes a current bottleneck.', response=''),
        dict(id='R4', url='local://review/17/R4', path=path, outdated=False, resolved=False,
             body='Optional style preference: introduce a RedirectManager class. Not a requirement; explain if the existing function is more appropriate.', response=''),
    ], issues=[dict(id=42, title='Measure large-batch throughput before optimizing', source='local://review/17/R3', state='open')])
