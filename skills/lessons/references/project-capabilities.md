# Project capabilities

During authorized implementation in an enabled project, decide whether persistent project knowledge would help the current work or a concrete later task. Create or refine a local skill or role without another permission round when justified; state the reason in the normal change summary. An evaluation, explanation or planning request does not authorize unrelated capability writes.

## Choose the smallest useful artifact

Search the project's AGENTS.md, existing project capabilities and installed skills/roles first. Reuse existing definitions, including a project's established layout. Update overlapping guidance instead of generating a second name.

| Need | Artifact |
| --- | --- |
| A command or short convention | The relevant project instruction or documentation |
| A procedure with project-specific steps, references or deterministic helpers | `.agents/skills/<name>/SKILL.md` |
| A reusable specialist with distinct responsibility, inputs and output contract | `.agents/agents/<name>.md` |

Repeated work, explicitly planned repeated work or a substantial procedure learned during implementation can justify persistence. A typo, a one-off subtask or generic framework advice does not. An existing useful capability may be enough; creating nothing is a valid outcome.

For example, recurring event-schema changes may need a skill linking this repository's schemas, compatibility rules and consumer-test command. A contract reviewer may justify a separate role when several services need independent compatibility reviews. Ordinary code review can use an existing reviewer with project context.

## Write and validate

- Use a lowercase hyphenated name (under 64 characters) and English instructions. `name` must match the skill folder or agent filename. The YAML frontmatter needs `name` and a single-line `description` stating the purpose and trigger, at most 400 characters for a skill or 300 for a role.
- A skill contains the actual procedure and observable success checks. Link detailed project knowledge instead of copying it. Add references, assets or scripts only when needed; test executable helpers with representative inputs.
- A role states its responsibility, required context, allowed work and output contract. Keep model selection inherited or capability-based; do not hard-code a vendor's model. Creating a role grants it no additional permissions.
- Add the name, trigger and relative file link to a short capability index in the project's AGENTS.md. Keep unrelated instructions. The index lets a fresh session find the relevant definition even when native skill discovery is unavailable.
- Validate with `python3 ~/.agents/tack/lib/capability_validation.py project .` from the project root. For an established layout, pass `--skills-dir` and `--agents-dir` with project-relative directories. The validator reads files only and checks naming, budgets, discovery links and local references; it does not prove behavioral usefulness.
- Verify the underlying procedure or role's checks on the actual task. Reuse the same definition next time; do not add numbered duplicates. If existing files belong to another workflow, preserve them and integrate deliberately.

## Discover and use

Read the project index when a task needs project-specific procedures or review. Load only matching definitions and their relevant references. If the tool cannot discover a local skill automatically, read its SKILL.md explicitly.

`.agents/agents/` is tack's portable role convention, not universal native registration. Use the role as instructions through the existing delegation interface when delegation is authorized and supported. Otherwise perform its checks sequentially and say so. Never claim that writing a file started an agent or that a running tool reloaded it.

Invocation continues to follow the user's instructions, the workflow level and `tack config delegation`. Creating a role does not bypass disabled delegation, justify parallel work, enable remote actions or weaken hooks. A native adapter, when useful, must use the actual runtime's supported project format and preserve unrelated definitions.

## Review and promotion

Keep a capability while concrete work benefits from it; merge overlapping local definitions when their consumers are updated. Report unused or obsolete definitions with evidence before deleting project knowledge. Lack of transcript evidence alone does not establish lack of use.

After demonstrated cross-project usefulness, propose a separate shared-catalog change: remove local assumptions, check overlap, choose its group, update component docs and validate the diff. Local implementation does not authorize writing global preferences, installing configuration or publishing changes.
