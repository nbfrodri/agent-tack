"""Offline evaluator checks: valid implementations pass and real contract defects fail."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
import lifecycle_fixture as fixture  # noqa: E402
import lifecycle_grade as grade  # noqa: E402
import lifecycle  # noqa: E402
import lifecycle_reviews  # noqa: E402

PY_REFERENCE = '''
def inventory(value):
    if not isinstance(value, dict) or any(not isinstance(k, str) or not k or type(v) is not int or v < 0 for k,v in value.items()):
        raise ValueError('inventory')

def quantities(items, available):
    if not isinstance(items, list): raise ValueError('items')
    total = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {'sku', 'quantity'}: raise ValueError('item')
        sku, quantity = item['sku'], item['quantity']
        if not isinstance(sku,str) or not sku or sku not in available or type(quantity) is not int or quantity <= 0: raise ValueError('quantity')
        total[sku] = total.get(sku, 0) + quantity
    if any(quantity > available[sku] for sku,quantity in total.items()): raise ValueError('available')
    return total

def reserve(stock, requests):
    inventory(stock)
    reserved = quantities(requests, stock)
    remaining = dict(stock)
    for sku, quantity in reserved.items(): remaining[sku] -= quantity
    return dict(remaining=remaining, reserved=reserved)

def release(stock, held, returns):
    inventory(stock); inventory(held)
    if set(held) - set(stock): raise ValueError('unknown held')
    returned = quantities(returns, held)
    remaining, result = dict(stock), dict(held)
    for sku, quantity in returned.items(): remaining[sku] += quantity; result[sku] -= quantity
    return dict(remaining=remaining, held=result)
'''
JS_REFERENCE = '''
const integer = (v,min=0) => Number.isSafeInteger(v) && v>=min;
export function quote(lines, options=0) {
 let discountPercent=0,shippingCents=0,freeShippingAtCents=null;
 if(typeof options==='number') discountPercent=options;
 else {
  if(!options || Array.isArray(options) || typeof options!=='object' || Object.keys(options).some(k=>!['discountPercent','shippingCents','freeShippingAtCents'].includes(k)))throw Error('options');
  ({discountPercent=0,shippingCents=0,freeShippingAtCents=null}=options);
 }
 if(!integer(discountPercent)||discountPercent>100||!integer(shippingCents)||(freeShippingAtCents!==null&&!integer(freeShippingAtCents)))throw Error('options');
 if(!Array.isArray(lines))throw Error('lines');
 let subtotalCents=0;
 for(const line of lines){
  if(!line||typeof line!=='object'||Object.keys(line).length!==2||!integer(line.unitCents)||!integer(line.quantity,1))throw Error('line');
  const part=line.unitCents*line.quantity;
  if(!integer(part)||!integer(subtotalCents+part))throw Error('overflow');
  subtotalCents+=part;
 }
 const discountCents=Number(BigInt(subtotalCents)*BigInt(discountPercent)/100n);
 if(freeShippingAtCents!==null && subtotalCents-discountCents>=freeShippingAtCents)shippingCents=0;
 const totalCents=subtotalCents-discountCents+shippingCents;
 if(!integer(totalCents))throw Error('overflow');
 return {version:2,subtotalCents,discountCents,totalCents,total:totalCents,shippingCents};
}
'''
CLIENT_REFERENCE = '''
import {LABEL} from './labels.mjs';
export function renderQuote(value){
 if(!value || typeof value!=='object')throw Error('quote');
 let cents=value.total;
 if(value.version!==undefined){
  if(value.version!==2)throw Error('version');
  const keys=['subtotalCents','discountCents','shippingCents','totalCents'];
  if(keys.some(k=>!Number.isSafeInteger(value[k])||value[k]<0)||value.discountCents>value.subtotalCents||value.totalCents!==value.subtotalCents-value.discountCents+value.shippingCents)throw Error('quote');
  cents=value.totalCents;
 }
 if(!Number.isSafeInteger(cents)||cents<0)throw Error('total');
 const amount=BigInt(cents);
 return `${LABEL}: $${amount/100n}.${String(amount%100n).padStart(2,'0')}`;
}
'''


class LifecycleGrades(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def reference(self, scenario):
        fixture.seed(self.root, scenario, 'plain')
        if scenario == 'stock':
            fixture.write(self.root, 'stock/allocation.py', PY_REFERENCE)
            fixture.write(self.root, 'stock/redirect.py', 'def safe_redirect(value):\n    if not isinstance(value,str) or not value.startswith("/") or value.startswith("//") or "\\\\" in value or any(ord(c)<32 or ord(c)==127 for c in value): raise ValueError("path")\n    return value\n')
        else:
            fixture.write(self.root, 'backend/quote.mjs', JS_REFERENCE)
            fixture.write(self.root, 'frontend/client.mjs', CLIENT_REFERENCE)
            fixture.write(self.root, 'frontend/labels.mjs', 'export const LABEL="Amount due";\n')
            fixture.write(self.root, 'backend/redirect.mjs', 'export function safeRedirect(v){if(typeof v!=="string"||!v.startsWith("/")||v.startsWith("//")||v.includes("\\\\")||/[\\x00-\\x1f\\x7f]/.test(v))throw Error("path");return v;}\n')

    def test_stock_reference_passes_and_mutating_inputs_fails(self):
        self.reference('stock')
        result = grade.acceptance(self.root, 'stock', 'review')
        self.assertTrue(result['passed'], result)
        fixture.write(self.root, 'stock/allocation.py', PY_REFERENCE.replace('remaining = dict(stock)', 'remaining = stock'))
        result = grade.acceptance(self.root, 'stock', 'review')
        self.assertFalse(result['passed'])
        self.assertTrue(any(not c['passed'] and 'independent' in c['name'] for c in result['cases']))

    @unittest.skipUnless(shutil.which('node'), 'Node required')
    def test_order_reference_passes_and_hidden_invalid_shipping_fails(self):
        self.reference('orders')
        result = grade.acceptance(self.root, 'orders', 'review')
        self.assertTrue(result['passed'], result)
        fixture.write(self.root, 'backend/quote.mjs', JS_REFERENCE.replace('||!integer(shippingCents)', ''))
        self.assertFalse(grade.acceptance(self.root, 'orders', 'review')['passed'])

    @unittest.skipUnless(shutil.which('node'), 'Node required')
    def test_initial_order_reference_matches_the_original_numeric_interface(self):
        self.reference('orders')
        initial = JS_REFERENCE.replace(' let discountPercent', ' if(typeof options!=="number")throw Error("discount");\n let discountPercent')
        fixture.write(self.root, 'backend/quote.mjs', initial.replace(',shippingCents};', '};'))
        result = grade.acceptance(self.root, 'orders', 'build')
        self.assertTrue(result['passed'], result)

    def test_review_requires_real_fixes_and_reuses_existing_followup(self):
        state = fixture.review_state('stock')
        fixture.write(self.root, 'review/state.json', json.dumps(state))
        self.assertFalse(grade.dispositions(self.root)['passed'])
        for thread in state['threads']:
            thread.update(resolved=True, response='Fixed and verified' if thread['id'] in ('R1', 'R2') else 'Reuse issue 42; retain simple function')
        fixture.write(self.root, 'review/state.json', json.dumps(state))
        self.assertTrue(grade.dispositions(self.root)['passed'])
        state['issues'].append(dict(id=43, source='local://review/17/R3'))
        fixture.write(self.root, 'review/state.json', json.dumps(state))
        self.assertFalse(grade.dispositions(self.root)['passed'])

    def test_seed_defects_fail_before_any_model_call(self):
        fixture.seed(self.root, 'stock', 'plain')
        self.assertFalse(grade.acceptance(self.root, 'stock', 'build')['passed'])

    def test_matrix_has_fixed_pairing_and_finite_calls(self):
        manifest = dict(conditions=list(fixture.CONDITIONS), scenarios=list(fixture.SCENARIOS),
                        models=['gpt-6-luna', 'gpt-6.1-sol'], effort='medium', repetitions=2,
                        max_sessions=140, concurrency=2, timeout_seconds=300, revision='a'*40,
                        image='sha256:'+'b'*64, seed=20261008)
        cases = lifecycle.matrix(manifest)
        self.assertEqual(len(cases), 24)
        self.assertEqual(len({c['id'] for c in cases}), 24)
        for model in manifest['models']:
            for scenario in fixture.SCENARIOS:
                for repetition in (1, 2):
                    self.assertEqual({c['condition'] for c in cases if (c['model'], c['scenario'], c['repetition']) ==
                                      (model, scenario, repetition)}, set(fixture.CONDITIONS))
        for key, val in [('repetitions', 3), ('max_sessions', 1000), ('timeout_seconds', 301), ('revision', 'main')]:
            with self.assertRaises(ValueError):
                lifecycle.matrix(dict(manifest, **{key: val}))

    def test_plain_implementation_requests_have_no_practice_injection(self):
        for scenario in fixture.SCENARIOS:
            for stage in ('build', 'change'):
                prompt = fixture.PROMPTS[scenario + '-' + stage].lower()
                for practice in ('tdd', 'solid', 'tests', 'conventional', 'modular', 'best practice'):
                    self.assertNotIn(practice, prompt)

    def test_review_bundles_cover_all_pairs_without_process_or_identity_files(self):
        manifest = dict(conditions=list(fixture.CONDITIONS), scenarios=list(fixture.SCENARIOS),
                        models=['gpt-6-luna', 'gpt-6.1-sol'], effort='medium', repetitions=2,
                        max_sessions=140, concurrency=2, timeout_seconds=300, revision='a'*40,
                        image='sha256:'+'b'*64, seed=20261008)
        source, destination = self.root / 'source', self.root / 'reviews'
        for case in lifecycle.matrix(manifest):
            for stage in ('build', 'review'):
                fixture.seed(source / case['id'] / stage / 'repo', case['scenario'], case['condition'])
        jobs = lifecycle_reviews.prepare(source, destination, manifest)
        self.assertEqual(len(jobs), 20)
        mapping = json.loads((destination / 'mapping.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(item['reversed'] for item in mapping.values()), 4)
        for job in jobs:
            bundle = json.loads((Path(job['bundle']) / 'bundle.json').read_text(encoding='utf-8'))
            self.assertEqual(set(bundle['candidates']), {'A', 'B', 'C'})
            for files in bundle['candidates'].values():
                self.assertFalse(any(p.endswith('.md') or p.startswith(('tests/', 'review/')) for p in files))


if __name__ == '__main__':
    unittest.main()
