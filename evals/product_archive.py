"""Archive runtime product files without exposing private evaluation inputs to models."""
import subprocess
import tarfile

EXCLUDES = ('evals', 'tests', 'docs/benchmarks', 'docs/plans', 'docs/archive', 'docs/audits', '.github')


def create(root, revision, output):
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('pin a full product commit')
    resolved = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', revision + '^{commit}'],
                              check=True, capture_output=True, text=True, timeout=60).stdout.strip()
    if resolved != revision:
        raise ValueError('unresolved product revision')
    subprocess.run(['git', '-C', str(root), 'archive', '--output', str(output), revision, '--', '.',
                    *(':(exclude)' + path for path in EXCLUDES)], check=True, capture_output=True, timeout=60)
    with tarfile.open(output) as archive:
        if any(member.name == path or member.name.startswith(path + '/')
               for member in archive for path in EXCLUDES):
            raise ValueError('private evaluator files leaked into runtime archive')
