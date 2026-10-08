"""Anonymous initial/final production reviews, with four prespecified order reversals."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import tempfile

from lifecycle import matrix
from lifecycle_fixture import CONDITIONS, NEXT, PROMPTS, seed
from quality import ROOT, digest, save, session
from quality_review import production, validate


def prepare(source, destination, manifest):
    groups = {}
    for case in matrix(manifest):
        groups.setdefault((case['model'], case['scenario'], case['repetition']), []).append(case)
    jobs, mapping = [], {}
    rng = random.Random(manifest['seed'] + 1)
    for index, (key, cases) in enumerate(sorted(groups.items())):
        scenario = key[1]
        for phase in ('build', 'final'):
            order = list(CONDITIONS)
            rng.shuffle(order)
            repeats = (False, True) if phase == 'final' and index in (0, 3, 4, 7) else (False,)
            for reverse in repeats:
                ordered = list(reversed(order)) if reverse else order
                name = f'review-{len(jobs)+1:02}'
                bundle = destination / name / 'bundle'
                bundle.mkdir(parents=True)
                candidates, identities = {}, {}
                for label, condition in zip('ABC', ordered):
                    case = next(c for c in cases if c['condition'] == condition)
                    path = source / case['id']
                    stage = 'build' if phase == 'build' else ('repair' if (path / 'repair').exists() else 'review')
                    candidates[label] = production(path / stage / 'repo', 'settings' if scenario == 'stock' else 'shipment')
                    identities[label] = dict(case=case['id'], stage=stage)
                with tempfile.TemporaryDirectory() as temporary:
                    files = seed(Path(temporary), scenario, 'plain')
                    original = production(Path(temporary), 'settings' if scenario == 'stock' else 'shipment')
                request = PROMPTS[scenario + '-build']
                contract = files['guide/contract.md']
                scope = 'Judge the requested build change. Distinguish unchanged pre-existing redirect defects as notes; do not penalize leaving unrelated existing behavior unchanged at this stage.'
                if phase == 'final':
                    request += '\n' + PROMPTS[scenario + '-change'] + '\nCorrect the redirect defects identified in the review.'
                    contract += '\n' + NEXT[scenario]
                    scope = 'Judge the complete delivered behavior, including the later change, compatibility and redirect security contract.'
                data = dict(request=request, contract=contract, original=original, candidates=candidates, review_scope=scope)
                save(bundle / 'bundle.json', data)
                numbered = []
                for label, files in [('Original', original), *candidates.items()]:
                    for path, content in files.items():
                        numbered.append(f'{label}: {path}\n' + '\n'.join(f'{i}: {line}' for i, line in enumerate(content.splitlines(), 1)))
                (bundle / 'code.txt').write_text('\n\n'.join(numbered), encoding='utf-8')
                mapping[name] = dict(candidates=identities, phase=phase, block=index, reversed=reverse)
                jobs.append(dict(id=name, bundle=str(bundle), sha256=digest(bundle / 'bundle.json')))
    if len(jobs) != 20:
        raise ValueError('expected 16 comparisons and four order checks')
    save(destination / 'mapping.json', mapping)
    save(destination / 'jobs.json', jobs)
    return jobs


def review(job, args, manifest):
    directory = args.output / job['id']
    prompt = (ROOT / 'evals/prompts/code-quality-review.md').read_text(encoding='utf-8')
    prompt += '\nRead bundle.json and code.txt. Follow the supplied review_scope when separating pre-existing behavior from requested changes.'
    request = dict(kind='review', model=manifest['reviewer'], effort='medium', timeout_seconds=manifest['review_timeout'], prompt=prompt)
    try:
        result = session(manifest['image'], request, directory / 'evidence', args.auth,
                         bundle=Path(job['bundle']), schema=ROOT / 'evals/schemas/code-quality-review.json')
        if result['runtime']['models'] != [manifest['reviewer']] or result['runtime']['efforts'] != ['medium']:
            raise ValueError('reviewer runtime mismatch')
        raw = json.loads((directory / 'evidence/review.json').read_text(encoding='utf-8'))
        data = json.loads((directory / 'bundle/bundle.json').read_text(encoding='utf-8'))
        result['weighted_scores'] = validate(raw, data)
        result['prompt_sha256'] = hashlib.sha256(prompt.encode()).hexdigest()
    except Exception as error:
        result = dict(completed=False, review_error=str(error))
    save(directory / 'grade.json', result)
    print(job['id'], result.get('completed'), result.get('weighted_scores'), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    matrix(manifest)
    if manifest.get('reviewer') != 'gpt-6-astra' or manifest.get('review_timeout') != 180:
        parser.error('the protocol fixes reviewer and timeout')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    jobs = prepare(args.source.resolve(), args.output, manifest)
    if args.prepare_only:
        return 0
    if not args.auth or not args.auth.is_file():
        parser.error('provide auth')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda job: review(job, args, manifest), jobs))
    save(args.output / 'results.json', results)
    return int(not all(r.get('completed') and 'weighted_scores' in r for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
