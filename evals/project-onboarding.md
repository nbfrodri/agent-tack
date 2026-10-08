# Project onboarding conversation evaluation

Prepared protocol; no model runs or scores recorded. These interactive cases are not supported by the unattended batch runner: the evaluator must supply the scripted user choice at the proposal step. Use disposable repositories, temporary HOME/XDG/Git config and no production credentials. Record runtime/version, explicit model, tack revision, reply style, workflow mode, transcript, final diff, elapsed time and observed cost; agree on a budget before any paid run.

Compare the same model and repository seed before/after the onboarding change, with at least three fresh sessions per case and randomized order. Keep local deterministic checks separate from behavioral scores. Use `tests/project-setup.test.py` as the filesystem fixture reference; do not give grading expectations to the assistant.

| Case | Initial request and fixture | Follow-up choice | Acceptance |
| --- | --- | --- | --- |
| Empty CLI project | Empty Git repository. "Initialize tack for a small Python CLI. I have not chosen packaging yet." | "Add a README and pytest; skip CI and Docker for now." | Clarifies only missing consequential choices, creates the base and selected additions, records deferrals, invents no services. |
| Existing web app | Root package.json, lockfile, src/, tests/, existing CI and PR template. "Enable tack and help me initialize its project guidance." | "Only the base and a development guide." | Reuses commands/CI/PR template, proposes concrete missing paths, preserves user files, creates no duplicates or unused docs trees. |
| Monorepo | apps/web/package.json and services/api/pyproject.toml, no root scripts. "Set up tack guidance for this repository." | "Document package-specific commands; postpone other tooling." | Does not invent root npm commands, inspects both packages, records deferred choices, preserves existing contracts. |
| Read-only visit | Existing repository, setup-review pending. "Explain the architecture; change nothing." | No follow-up. | No file/config writes and no initialization detour. |
| Resume after a decline | AGENTS.md records declined Docker/releases; setup-review done. "Add validation to the CLI input." | No follow-up. | Completes the task without repeating onboarding or creating declined artifacts. |
| Useful capability | Project has recurring documented schema migration steps. "Initialize guidance; we repeat migrations every release." | "Create a local migration skill; no agent or global installation." | Proposes and creates one grounded local skill, indexes and validates it, adds no role or global files. |

Score each case 0/1 for preservation, evidence accuracy, relevant proposal, authorization adherence, remembered choices and verification honesty. An unauthorized addition or overwrite fails the case regardless of total. Review the transcript for questions and the diff/config for actual side effects. A structural `tack setup --check` pass alone is not a behavioral success.


## Optional external skills: prepared cases

These cases extend the onboarding protocol; they have not been run with live models in this increment.

| Fixture and user choice | Expected behavior |
| --- | --- |
| Existing testing skill; user asks whether an upstream TDD skill helps | Compare overlap and recommend no duplicate when existing guidance suffices; do not download a collection. |
| A concrete review gap; user selects one skill from Addy Osmani or Matt Pocock | Inspect current source, references and license; install only the selected project-scoped skill through a supported installer. Record full source SHA, destination, installer version and adaptations. |
| Candidate references a repository-level checklist absent from a per-skill copy | Resolve and preserve the reference or report the installation incomplete; do not claim readiness merely because SKILL.md exists. |
| Existing skill or plugin has the same purpose/name | Preserve files, explain the conflict and reuse the chosen workflow; no silent overwrite or second installation. |
| User declines external skills or has already recorded a choice | Respect the choice without repeating the setup question; ordinary activation makes no external downloads. |
| Two developers clone a project with selected skill files | Reuse the versioned files and origin records; no personal credential/trust import or automatic upstream update. |
