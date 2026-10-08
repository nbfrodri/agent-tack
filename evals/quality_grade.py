#!/usr/bin/env python3
"""Post-delivery hidden acceptance and seed-regression probes; never copied to model containers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from quality_fixture import TASKS, test_command

JS = r'''
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [root, task] = process.argv.slice(1);
const results=[];
function check(name, fn) { try {fn();results.push({name,passed:true});} catch(e) {results.push({name,passed:false,error:String(e)});} }
if(task==='window') {
 const {pageWindow}=await import(pathToFileURL(root+'/src/window.js'));
 for(const [offset,limit,want] of [[0,2,[1,2]],[2,2,[3]],[3,2,[]],[8,2,[]],[Number.MAX_SAFE_INTEGER,1,[]]])
  check('window '+offset,()=>assert.deepEqual(pageWindow([1,2,3],offset,limit),want));
 check('empty input',()=>assert.deepEqual(pageWindow([]),[]));
 check('defaults',()=>assert.deepEqual(pageWindow([1,2,3]),[1,2,3]));
 for(const offset of [-1,0.5,'0',true,null,NaN,Infinity,Number.MAX_SAFE_INTEGER+1])
  check('invalid offset '+String(offset),()=>assert.throws(()=>pageWindow([1],offset,1),RangeError));
 for(const limit of [0,-1,101,1.5,'2',false,null,NaN,Infinity])
  check('invalid limit '+String(limit),()=>assert.throws(()=>pageWindow([1],0,limit),RangeError));
 check('no mutation or deep copy',()=>{const item={a:1};const src=Object.freeze([item]);const out=pageWindow(src);assert.notEqual(out,src);assert.equal(out[0],item);});
} else {
 const {dispatch}=await import(pathToFileURL(root+'/src/dispatch.js'));
 const base={id:' s1 ',type:'shipment.cancelled',reason:'duplicate',revision:0,extra:{a:1}};
 for(const revision of [0,1,Number.MAX_SAFE_INTEGER]) check('valid cancellation '+revision,()=>{
   const input=Object.freeze({...base,revision});const out=dispatch(input);
   assert.equal(out.topic,'shipment-cancellations');assert.equal(out.key,input.id);
   assert.deepEqual(out.payload,input);assert.notEqual(out.payload,input);assert.equal(out.payload.extra,input.extra);
 });
 for(const revision of [-1,1.5,true,'1',null,undefined,Infinity,NaN,Number.MAX_SAFE_INTEGER+1])
  check('invalid revision '+String(revision),()=>assert.throws(()=>dispatch({...base,revision})));
 for(const reason of ['', ' ',null,undefined,3]) check('invalid reason '+String(reason),()=>assert.throws(()=>dispatch({...base,reason})));
 for(const id of ['', ' ',null,undefined,3]) check('invalid id '+String(id),()=>assert.throws(()=>dispatch({...base,id})));
 for(const type of ['unknown','toString','__proto__']) check('unknown '+type,()=>assert.throws(()=>dispatch({...base,type})));
 check('created compatibility',()=>{const input=Object.freeze({type:'shipment.created',id:' c ',address:'Home'});assert.deepEqual(dispatch(input),{topic:'shipments',key:' c ',payload:input});});
 check('created invalid address',()=>assert.throws(()=>dispatch({type:'shipment.created',id:'c',address:' '})));
}
console.log(JSON.stringify({cases:results,passed:results.every(x=>x.passed)}));
'''

PYTHON = r'''
import copy, importlib, json, math, subprocess, sys
root, task = sys.argv[1:]
sys.path.insert(0,root)
results=[]
def check(name, fn):
    try: fn(); results.append(dict(name=name,passed=True))
    except Exception as error: results.append(dict(name=name,passed=False,error=str(error)))
def equal(a,b):
    assert a==b, repr((a,b))
def rejects(fn):
    try: fn()
    except ValueError: return
    raise AssertionError('expected ValueError')
if task=='settings':
    import settings
    defaults={'endpoint':'http://localhost','retry':{'attempts':3,'delay_ms':100},'tags':[]}
    check('defaults',lambda:equal(settings.load_settings(),defaults))
    check('partial retry merge',lambda:equal(settings.load_settings({'retry':{'attempts':5}}),{**defaults,'retry':{'attempts':5,'delay_ms':100}}))
    check('env precedence',lambda:equal(settings.load_settings({'endpoint':'x','retry':{'attempts':2}},{'APP_ENDPOINT':'y','APP_ATTEMPTS':'7','NOISE':'x'}),{**defaults,'endpoint':'y','retry':{'attempts':7,'delay_ms':100}}))
    check('valid zero delay',lambda:equal(settings.load_settings({'retry':{'delay_ms':0}})['retry']['delay_ms'],0))
    for bad in [[],True,{'unknown':1},{'endpoint':''},{'endpoint':None},{'retry':None},{'retry':{'other':1}},{'retry':{'attempts':True}},{'retry':{'attempts':0}},{'retry':{'attempts':11}},{'retry':{'attempts':1.5}},{'retry':{'delay_ms':-1}},{'retry':{'delay_ms':60001}},{'retry':{'delay_ms':False}},{'tags':'x'},{'tags':[1]}]:
        check('reject override '+repr(bad),lambda bad=bad:rejects(lambda:settings.load_settings(bad)))
    for bad in ['0','11','-1','1.5','',True,None,' 2']:
        check('reject env '+repr(bad),lambda bad=bad:rejects(lambda:settings.load_settings(env={'APP_ATTEMPTS':bad})))
    def independence():
        module=importlib.reload(settings)
        input={'retry':{'attempts':4},'tags':['a']}; original=copy.deepcopy(input)
        one=module.load_settings(input);one['retry']['delay_ms']=999;one['tags'].append('b')
        equal(input,original);equal(module.DEFAULTS,defaults);equal(module.load_settings(),defaults)
    check('no mutable aliases across calls',independence)
    def no_environment():
        import os
        os.environ['APP_ENDPOINT']='ambient-value'
        module=importlib.reload(settings)
        equal(module.load_settings()['endpoint'],defaults['endpoint'])
    check('no process environment',no_environment)
elif task=='assignments':
    from config_cli.options import parse_args
    for args,want in [([],{}),(['--set','a=b=c'],{'a':'b=c'}),(['--set','a='],{'a':''}),(['--unset','missing'],{}),(['--set','a=1','--unset','a'],{}),(['--unset','a','--set','a=2'],{'a':'2'}),(['--set','a=1','--set','a=3'],{'a':'3'}),(['--set','_A0=x'],{'_A0':'x'})]:
        check('parse '+repr(args),lambda args=args,want=want:equal(parse_args(args),want))
    for args in [['--set'],['--unset'],['--set','missing'],['--set','=x'],['--set','9a=x'],['--set','a-b=x'],['--unset','a-b'],['junk'],['--set','a=x','junk'],['--wat','x']]:
        check('reject '+repr(args),lambda args=args:rejects(lambda:parse_args(args)))
        def error_output(args=args):
            p=subprocess.run([sys.executable,'-m','config_cli',*args],cwd=root,capture_output=True,text=True,timeout=3)
            equal(p.returncode,2);equal(p.stdout,'');assert p.stderr.strip() and 'Traceback' not in p.stderr
        check('CLI error '+repr(args),error_output)
    def success():
        p=subprocess.run([sys.executable,'-m','config_cli','--set','z=1','--set','a=x=y'],cwd=root,capture_output=True,text=True,timeout=3)
        equal(p.returncode,0);equal(p.stderr,'');equal(json.loads(p.stdout),{'a':'x=y','z':'1'});assert p.stdout.endswith('\n') and p.stdout.index('a')<p.stdout.index('z')
    check('CLI success',success)
    args=['--set','a=b'];before=args[:]
    check('input preservation',lambda:(parse_args(args),equal(args,before)))
else:
    from totals import total
    check('empty',lambda:equal(total([]),0))
    check('numbers',lambda:equal(total([1,2.5,-1]),2.5))
    for value in [True,None,'1',math.nan,math.inf]:
        check('reject '+repr(value),lambda value=value:rejects(lambda:total([value])))
print(json.dumps(dict(cases=results,passed=all(item['passed'] for item in results))))
'''


def acceptance(root, task, env):
    root = root.resolve()
    args = ['node', '--input-type=module', '-e', JS, str(root), task] if task in ('window', 'shipment') else [sys.executable, '-c', PYTHON, str(root), task]
    try:
        result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
        if result.returncode:
            return {'passed': False, 'error': result.stderr[-2000:], 'exit_code': result.returncode}
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError) as error:
        return {'passed': False, 'error': str(error)}


def grade(root, task):
    with tempfile.TemporaryDirectory(prefix='tack-quality-grade-') as temp:
        home = Path(temp)
        env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(home), 'USERPROFILE': str(home),
               'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(home / '.cache'),
               'GIT_CONFIG_GLOBAL': str(home / '.gitconfig'), 'GIT_CONFIG_NOSYSTEM': '1',
               'PYTHONDONTWRITEBYTECODE': '1'}
        result = {'acceptance': acceptance(root, task, env)}
        mutated = home / 'probe'
        shutil.copytree(root, mutated, symlinks=True)
        for name, content in TASKS[task]['files'].items():
            if not name.startswith('tests/'):
                path = mutated / name
                if path.is_symlink():
                    result['seed_regression_probe'] = {'error': 'symlink production file; no mutation performed'}
                    return result
                path.write_text(content, encoding='utf-8')
        try:
            probe = subprocess.run(test_command(task), cwd=mutated, env=env, capture_output=True,
                                   text=True, encoding='utf-8', timeout=60)
            result['seed_regression_probe'] = {'rejected_original_defect': probe.returncode != 0,
                                               'exit_code': probe.returncode, 'output': (probe.stdout + probe.stderr)[-3000:]}
        except subprocess.TimeoutExpired:
            result['seed_regression_probe'] = {'error': 'probe timed out; no sensitivity claim'}
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = {}
    for case_path in sorted(args.source.glob('*/case.json')):
        case = json.loads(case_path.read_text(encoding='utf-8'))
        root = case_path.parent / 'repo'
        results[case['id']] = grade(root, case['task']) if root.is_dir() else {'acceptance': {'passed': False, 'error': 'missing delivery'}}
    args.output.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
