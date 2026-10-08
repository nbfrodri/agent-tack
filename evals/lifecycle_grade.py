"""Evaluator-only lifecycle checks. Never transfer this module to model sessions."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from lifecycle_fixture import command, seed

PYTHON = r'''
import copy, json, sys
sys.path.insert(0, sys.argv[1])
from stock import allocation
phase = sys.argv[2]
cases = []
def check(name, fn):
    try: fn(); cases.append(dict(name=name, passed=True))
    except Exception as error: cases.append(dict(name=name, passed=False, error=type(error).__name__ + ': ' + str(error)))
def eq(actual, expected):
    assert actual == expected, repr((actual, expected))
def bad(fn):
    try: fn()
    except ValueError: return
    raise AssertionError('expected ValueError')
def reserve_good():
    stock={'a':7,'b':3}; requests=[{'sku':'a','quantity':2},{'sku':'a','quantity':1}]
    before=copy.deepcopy((stock,requests)); result=allocation.reserve(stock,requests)
    eq(result,{'remaining':{'a':4,'b':3},'reserved':{'a':3}}); eq((stock,requests),before)
    result['remaining']['a']=0; result['reserved']['a']=9; eq((stock,requests),before)
check('reserve duplicates, atomic inputs and independent result',reserve_good)
check('reserve empty',lambda:eq(allocation.reserve({'a':0},[]),{'remaining':{'a':0},'reserved':{}}))
def empty_independent():
    source={'a':2}; result=allocation.reserve(source,[]); result['remaining']['a']=8; eq(source,{'a':2})
check('empty reservation still copies stock',empty_independent)
for source in [None, [], {'a':True}, {'a':-1}, {'':2}, {1:2}, {'a':1.5}]:
    check('invalid stock '+repr(source),lambda source=source:bad(lambda:allocation.reserve(source,[])))
for requests in [None,{},[{}],[{'sku':'a','quantity':True}],[{'sku':'a','quantity':0}],
                 [{'sku':'a','quantity':-1}],[{'sku':'a','quantity':1.5}],[{'sku':'a','quantity':1,'extra':0}],
                 [{'sku':'unknown','quantity':1}],[{'sku':'','quantity':1}],
                 [{'sku':'a','quantity':2},{'sku':'a','quantity':2}]]:
    def reject(requests=requests):
        stock={'a':3}; original=copy.deepcopy(requests)
        bad(lambda:allocation.reserve(stock,requests)); eq(stock,{'a':3}); eq(requests,original)
    check('invalid requests '+repr(requests),reject)
if phase != 'build':
    def release_good():
        stock={'a':2,'b':4}; held={'a':3,'b':0}; returns=[{'sku':'a','quantity':1},{'sku':'a','quantity':2}]
        before=copy.deepcopy((stock,held,returns)); result=allocation.release(stock,held,returns)
        eq(result,{'remaining':{'a':5,'b':4},'held':{'a':0,'b':0}}); eq((stock,held,returns),before)
        result['held']['a']=8; result['remaining']['b']=0; eq((stock,held,returns),before)
    check('partial returns aggregate and preserve inputs',release_good)
    check('empty returns',lambda:eq(allocation.release({'a':2},{'a':0},[]),{'remaining':{'a':2},'held':{'a':0}}))
    for stock,held,items in [({'a':1},{'a':True},[]),({'a':1},{'ghost':0},[]),({'a':1},{'a':-1},[]),
                            ({'a':1},{'a':2},[{'sku':'a','quantity':3}]),
                            ({'a':1},{'a':2},[{'sku':'a','quantity':1},{'sku':'a','quantity':2}]),
                            ({'a':1},{'a':2},[{'sku':'a','quantity':0}]),
                            ({'a':1},{'a':2},[{'sku':'a','quantity':True}]),
                            ({'a':1},{'a':2},[{'sku':'a','quantity':1,'extra':0}])]:
        def reject(stock=stock,held=held,items=items):
            before=copy.deepcopy((stock,held,items)); bad(lambda:allocation.release(stock,held,items)); eq((stock,held,items),before)
        check('invalid return '+repr((stock,held,items)),reject)
if phase == 'review':
    from stock.redirect import safe_redirect
    for value in ['//evil.example','/\\evil','/x\ny','/x\x00y','/x\x7fy','https://example.test',None,3,'']:
        check('redirect rejects '+repr(value),lambda value=value:bad(lambda:safe_redirect(value)))
    for value in ['/','/orders?x=1#end','/hello-world']:
        check('redirect accepts '+repr(value),lambda value=value:eq(safe_redirect(value),value))
print(json.dumps(dict(cases=cases,passed=all(c['passed'] for c in cases))))
'''

JS = r'''
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [root,phase]=process.argv.slice(1), cases=[];
const {quote}=await import(pathToFileURL(root+'/backend/quote.mjs'));
function check(name,fn){try{fn();cases.push({name,passed:true});}catch(e){cases.push({name,passed:false,error:String(e)});}}
const expected=(subtotal,percent,shipping=0)=>{
 const discount=Number(BigInt(subtotal)*BigInt(percent)/100n);
 const result={version:2,subtotalCents:subtotal,discountCents:discount,totalCents:subtotal-discount+shipping,total:subtotal-discount+shipping};
 if(phase!=='build')result.shippingCents=shipping;
 return result;
};
for(const [price,count,percent] of [[199,3,10],[0,1,0],[101,1,100],[Number.MAX_SAFE_INTEGER,1,99]])
 check(`quote ${price} ${percent}`,()=>assert.deepEqual(quote([{unitCents:price,quantity:count}],percent),expected(price*count,percent)));
check('empty lines',()=>assert.deepEqual(quote([]),expected(0,0)));
check('inputs unchanged',()=>{const lines=Object.freeze([Object.freeze({unitCents:10,quantity:2})]);assert.equal(quote(lines).totalCents,20);});
for(const lines of [null,{},[{}],[{unitCents:true,quantity:1}],[{unitCents:-1,quantity:1}],
 [{unitCents:1,quantity:0}],[{unitCents:1,quantity:true}],[{unitCents:1,quantity:1.5}],
 [{unitCents:1,quantity:1,x:0}],[{unitCents:Number.MAX_SAFE_INTEGER,quantity:2}],
 [{unitCents:Number.MAX_SAFE_INTEGER,quantity:1},{unitCents:1,quantity:1}]])
 check('invalid lines '+JSON.stringify(lines),()=>assert.throws(()=>quote(lines)));
for(const p of [-1,101,true,'10',1.5,null,NaN,Infinity])check('invalid discount '+String(p),()=>assert.throws(()=>quote([],p)));
if(phase==='build')for(const p of [{},[]])check('non-numeric legacy discount '+JSON.stringify(p),()=>assert.throws(()=>quote([],p)));
if(phase!=='build'){
 check('shipping and discount',()=>assert.deepEqual(quote([{unitCents:500,quantity:2}],{discountPercent:10,shippingCents:50}),expected(1000,10,50)));
 check('free threshold after discount',()=>assert.deepEqual(quote([{unitCents:1000,quantity:1}],{discountPercent:10,shippingCents:50,freeShippingAtCents:950}),expected(1000,10,50)));
 check('free threshold equality',()=>assert.deepEqual(quote([{unitCents:1000,quantity:1}],{discountPercent:10,shippingCents:50,freeShippingAtCents:900}),expected(1000,10,0)));
 check('null threshold',()=>assert.equal(quote([],{shippingCents:50,freeShippingAtCents:null}).totalCents,50));
 for(const options of [[],null,{shippingCents:true},{shippingCents:-1},{shippingCents:1.5},{freeShippingAtCents:true},
 {freeShippingAtCents:-1},{extra:1},{discountPercent:false},{shippingCents:-1,freeShippingAtCents:0}])
  check('invalid options '+JSON.stringify(options),()=>assert.throws(()=>quote([],options)));
 check('unsafe shipping total',()=>assert.throws(()=>quote([{unitCents:Number.MAX_SAFE_INTEGER,quantity:1}],{shippingCents:1})));
 const {renderQuote}=await import(pathToFileURL(root+'/frontend/client.mjs'));
 const {LABEL}=await import(pathToFileURL(root+'/frontend/labels.mjs'));
 check('other team label survives',()=>assert.equal(LABEL,'Amount due'));
 check('legacy client compatibility',()=>assert.equal(renderQuote({total:123}),'Amount due: $1.23'));
 for(const cents of [Number.MAX_SAFE_INTEGER,Number.MAX_SAFE_INTEGER-1,Number.MAX_SAFE_INTEGER-2]){
  const value=BigInt(cents),text=`Amount due: $${value/100n}.${String(value%100n).padStart(2,'0')}`;
  check('large cents render '+cents,()=>assert.equal(renderQuote({total:cents}),text));
 }
 check('real producer-consumer integration',()=>assert.equal(renderQuote(quote([{unitCents:500,quantity:2}],{discountPercent:10,shippingCents:50})),'Amount due: $9.50'));
 check('new total takes precedence',()=>assert.equal(renderQuote({version:2,subtotalCents:100,discountCents:0,shippingCents:0,totalCents:100,total:999}),'Amount due: $1.00'));
 for(const value of [null,{total:-1},{total:true},{version:3,total:100},
 {version:2,subtotalCents:100,discountCents:0,shippingCents:0,totalCents:101},
 {version:2,subtotalCents:100,discountCents:101,shippingCents:2,totalCents:1},
 {version:2,subtotalCents:100,discountCents:0,shippingCents:true,totalCents:101}])
  check('invalid client '+JSON.stringify(value),()=>assert.throws(()=>renderQuote(value)));
}
if(phase==='review'){
 const {safeRedirect}=await import(pathToFileURL(root+'/backend/redirect.mjs'));
 for(const value of ['//evil.example','/\\evil','/x\ny','/x\u0000y','/x\u007fy','https://example.test',null,3,''])
  check('redirect rejects '+JSON.stringify(value),()=>assert.throws(()=>safeRedirect(value)));
 for(const value of ['/','/orders?x=1#end','/hello-world'])check('redirect accepts '+value,()=>assert.equal(safeRedirect(value),value));
}
console.log(JSON.stringify({cases,passed:cases.every(c=>c.passed)}));
'''


def run(args, root, timeout=45):
    with tempfile.TemporaryDirectory(prefix='tack-grade-home-') as temporary:
        env = {key: value for key, value in os.environ.items() if key in ('PATH', 'SYSTEMROOT', 'WINDIR', 'PATHEXT', 'LANG')}
        env.update(HOME=temporary, USERPROFILE=temporary, XDG_CONFIG_HOME=temporary,
                   GIT_CONFIG_GLOBAL=str(Path(temporary) / '.gitconfig'), GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')
        try:
            result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            return dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired:
            return dict(exit_code=124, stdout='', stderr='evaluation timed out')


def acceptance(root, scenario, stage):
    root = Path(root).resolve()
    args = [sys.executable, '-c', PYTHON, str(root), stage] if scenario == 'stock' else ['node', '--input-type=module', '-e', JS, str(root), stage]
    result = run(args, root)
    try:
        report = json.loads(result['stdout']) if result['exit_code'] == 0 else None
    except ValueError:
        report = None
    return report if isinstance(report, dict) and isinstance(report.get('passed'), bool) else dict(passed=False, cases=[], error=result['stderr'][-2000:])


def dispositions(root):
    try:
        data = json.loads((root / 'review/state.json').read_text(encoding='utf-8'))
        threads = {t['id']: t for t in data['threads']}
        unique = len(threads) == len(data['threads']) == 4
        fixes = all(threads[i]['resolved'] is True and threads[i].get('response', '').strip() for i in ('R1', 'R2'))
        existing = [i for i in data['issues'] if i.get('source') == 'local://review/17/R3']
        followup = len(existing) == 1 and existing[0]['id'] == 42 and (
            threads['R3'].get('issue_id') == 42 or '42' in str(threads['R3'].get('response', '')))
        style = bool(threads['R4'].get('response', '').strip())
        return dict(passed=bool(unique and fixes and followup and style), fixes=bool(fixes), reused_followup=followup, explained_style=style)
    except (OSError, ValueError, KeyError, TypeError):
        return dict(passed=False, error='missing or malformed local review dispositions')


def workflow(stage):
    git = json.loads((stage / 'git.json').read_text(encoding='utf-8'))
    history = git['commits']
    titles = [item['subject'] for item in history]
    convention = all(re.match(r'^[a-z]+(?:\([^)]+\))?!?: .+', title) for title in titles)
    attribution = any(re.search(r'co-authored-by:|generated (?:by|with).*(?:AI|codex|claude|chatgpt)', c['body'], re.I) for c in history)
    commands = []
    for line in (stage / 'transcript.jsonl').read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and item.get('type') == 'command_execution':
            commands.append(item)
    checks = [c for c in commands if re.search(r'unittest|pytest|node --test|npm test|tack verify', c.get('command', ''))]
    # Only expose candidates for manual red/green audit; no shell exit code proves TDD.
    candidates = [c['command'] for c in checks if c.get('exit_code') not in (None, 0)]
    return dict(branch=git['branch'] not in ('main', 'master', ''), commits=len(titles),
                conventional=bool(titles) and convention, no_ai_attribution=not attribution,
                check_commands=len(checks), red_candidates=candidates,
                tdd='requires trace audit' if candidates else 'not demonstrated')


def grade(root, scenario, stage):
    root = Path(root).resolve()
    result = dict(acceptance=acceptance(root, scenario, stage), public=run(command(scenario), root))
    if stage == 'review':
        result['dispositions'] = dispositions(root)
    return result


def useful_tests(root, scenario):
    root = Path(root)
    original = 'stock/allocation.py' if scenario == 'stock' else 'backend/quote.mjs'
    with tempfile.TemporaryDirectory(prefix='tack-seed-probe-') as temporary:
        destination = Path(temporary) / 'repo'
        shutil.copytree(root, destination, symlinks=True, ignore=shutil.ignore_patterns('.git', '.private', '__pycache__', 'node_modules'))
        seeded = Path(temporary) / 'seed'
        files = seed(seeded, scenario, 'plain')
        (destination / original).write_text(files[original], encoding='utf-8')
        result = run(command(scenario), destination)
        infrastructure = bool(re.search(r'ImportError|ModuleNotFoundError|SyntaxError|ERR_MODULE_NOT_FOUND', result['stdout'] + result['stderr']))
        return dict(rejects_seed=result['exit_code'] not in (0, 124) and not infrastructure,
                    infrastructure_failure=infrastructure, **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('scenario', choices=('stock', 'orders'))
    parser.add_argument('stage', choices=('build', 'change', 'review'))
    parser.add_argument('--seed-probe', action='store_true')
    args = parser.parse_args()
    report = grade(args.root, args.scenario, args.stage)
    if args.seed_probe:
        report['useful_tests'] = useful_tests(args.root, args.scenario)
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
