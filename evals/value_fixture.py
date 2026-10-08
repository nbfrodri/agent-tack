"""Small early comparison; product requests and hidden graders reuse frozen fixtures."""
from quality_fixture import TASKS, test_command

PILOT_TASKS = ('settings', 'shipment')
PROJECT_GUIDE = '''# Project conventions

Read docs/contract.md for behavior and docs/architecture.md for the component map.
Reuse the existing structure. Make the smallest complete change; avoid speculative abstractions.
Use a branch, meaningful regression tests and Conventional Commits without AI attribution.
For behavior changes use red/green/refactor. Run the affected tests and inspect the diff.
Update documentation only when behavior makes it inaccurate. Report the outcome and actual checks.
'''


def request(task, condition, model, effort, timeout):
    return dict(kind='code', task=task, condition=condition, model=model, effort=effort,
                timeout_seconds=timeout, prompt=TASKS[task]['prompt'], test_command=test_command(task),
                project_guide=PROJECT_GUIDE if condition == 'project' else '')
