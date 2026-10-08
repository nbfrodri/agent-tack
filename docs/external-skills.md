# Add selected external skills

tack can guide you through choosing skills from other repositories during setup. Installation is optional and uses an existing skill installer. The base tack installer does not download these collections.

Start with a real need: a recurring task or a missing procedure. Compare the candidate with the project's existing skills and tack's own guidance. Installing two workflows for the same job can create conflicting instructions.

## Supported starting points

| Collection | What to review |
| --- | --- |
| [Addy Osmani: agent-skills](https://github.com/addyosmani/agent-skills) | Engineering workflows; some overlap with tack's planning, testing and review skills. Some skills reference shared files outside their own directory. |
| [Matt Pocock: skills](https://github.com/mattpocock/skills) | Composable engineering procedures and a repository setup skill. Reuse tack's agreed conventions, issue tracker and document locations when configuring them. |

These are sources to inspect, not blanket endorsements of every instruction or future update. Both repositories currently publish under MIT; preserve their actual license and notices when copying files. The instructions below were checked against upstream documentation on 2026-10-08.

## Ask tack to help choose

> Review this project's needs and existing skills. Suggest at most a few useful skills from addyosmani/agent-skills or mattpocock/skills. Show the overlap, files and installation scope before I choose. Keep existing conventions and document locations.

The assistant should show a short selection with the skill's purpose, why the project needs it, any conflicts and the proposed destination. It should reuse accepted or declined choices rather than asking on every session. Choosing no external skill is a valid result.

## Browse and install

The [open skills CLI](https://github.com/vercel-labs/skills) needs Node.js/npm. From the application repository, list candidates without installing skills:

```bash
npx skills add addyosmani/agent-skills --list
npx skills add mattpocock/skills --list
```

These commands fetch the CLI and repository data. They do not invoke a model. For an approved choice, replace `SKILL-NAME` below with the selected skill and choose the target tools in the installer's prompts:

```bash
npx skills add mattpocock/skills --skill SKILL-NAME
# Or:
npx skills add addyosmani/agent-skills --skill SKILL-NAME
```

Use project scope, inspect the proposed destination and keep the selection narrow. Avoid `--all` and global installation unless you explicitly want them. Do not overwrite an existing skill with the same name. When a workflow overlaps, choose which one applies and record the boundary in `AGENTS.md`.

For a reproducible team copy, clone the chosen source separately, check out the reviewed full commit SHA and install from that local path with `npx skills add /path/to/reviewed-checkout --skill SKILL-NAME`. Record the installer version too. Commit the selected project files and any project lockfile the installer produces; a teammate then receives the reviewed copy through Git. The CLI also offers updates, but review their diff before adopting them.

## Check the installed result

- Open `SKILL.md` and its scripts and references. Installing instructions does not authorize every command they describe.
- Keep required supporting files. Addy Osmani's upstream docs warn that per-skill installs can omit repository-level references; include the needed references with valid local paths or choose a complete integration deliberately.
- Do not copy a source repository's root `AGENTS.md` or `CLAUDE.md`: those configure work on that repository.
- Do not install the same collection through both a native plugin and copied skills. Matt Pocock's docs explicitly call out this duplication.
- Retain license notices and record local adaptations. Verify the actual procedure on a relevant task, not just whether a file exists.

Index the selected skill from the project's `AGENTS.md`. Use a brief record like this, with real values filled after review:

| Skill and local path | Need and trigger | Source and reviewed commit | Local changes |
| --- | --- | --- | --- |
| Selected name, linked to its SKILL.md | The recurring task it handles | Repository URL, full SHA, license location and installer version | None, or a summary of adaptations |

tack's [project capability validator](customization.md#project-capabilities) can check its own layout, description and link conventions. An upstream skill may use different conventions; do not claim full compatibility from a structural check alone. Native discovery and reload behavior depend on the AI tool.

## Sharing, updates and removal

Share the selected project files and their origin record. Keep execution trust and credentials local. Review upstream updates explicitly; preserve local edits and rerun the relevant procedure/checks after an update. For removal, inspect the destination and remove only the selected skill's files, links and index entry. Keep a backup or Git history for local adaptations.

tack currently guides this process through onboarding instructions. It does not run a background updater, bundle either collection or provide its own external-skill package manager. This keeps the initial integration small while allowing individual and team use.
