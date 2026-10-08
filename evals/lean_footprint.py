"""Count shipped default instruction/catalog characters; these are not token measurements."""
import argparse
import json
import re
import subprocess


def measure(revision):
    def read(path):
        return subprocess.check_output(['git', 'show', revision + ':' + path]).decode('utf-8')

    features = read('features.txt').splitlines()
    groups = next(line.split()[2] for line in features if line.startswith('skill-groups '))
    roles = next((line.split()[2] == 'true' for line in features if line.startswith('agent-roles ')), True)
    selected = {'core', 'process', 'stack'} if groups == 'all' else {'core', *groups.split(',')}
    skills = [line.split()[0] for line in read('skill-groups.txt').splitlines()
              if line.strip() and not line.startswith('#') and line.split()[1] in selected]
    descriptions = [re.search(r'^description:\s*(.+)$', read('skills/' + name + '/SKILL.md'), re.M).group(1).strip('"')
                    for name in skills]
    agents = subprocess.check_output(['git', 'ls-tree', '--name-only', revision, 'agents/']).decode().splitlines()
    instructions = read('global/AGENTS.md')
    return dict(revision=revision, global_instruction_characters=len(instructions),
                skill_count=len(skills), skill_description_characters=sum(map(len, descriptions)),
                agent_count=len(agents) if roles else 0, skills=skills,
                note='Unicode characters, not model tokens. Excludes tool wrappers, hooks and task-loaded references.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revisions', nargs='+')
    args = parser.parse_args()
    print(json.dumps([measure(rev) for rev in args.revisions], indent=2))
