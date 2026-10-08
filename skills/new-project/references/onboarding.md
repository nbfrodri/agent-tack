# Project onboarding

Use the same flow for a new repository and an existing repository adopting tack. An activation command does not run an AI conversation itself: the next assistant session receives a pending-setup hint. Run this flow when initializing or when setup is requested. For a focused task, reuse existing guidance and postpone unrelated onboarding; address only missing setup that blocks that task. A pending hint alone is not a reason to load this flow, add files or interrupt implementation. Read-only explanations and reviews remain read-only.

## Inspect before proposing

Run `tack setup --json` and `tack config --json` once for discovery and current preference origins, then inspect relevant project instructions, manifests and source entrypoints. Reuse these results during this setup; read help for an unresolved option rather than inspecting tack's implementation. Discovery is bounded and can miss nested packages or custom tooling. Do not run commands merely because the detector found them. Use the user's stated purpose and preferences; for an empty project ask only for missing decisions that affect the foundations.

Read existing setup choices in AGENTS.md and `tack config setup-review`. `done` and `deferred` suppress routine startup prompts; revisit when the user asks or a material project change makes a new proposal useful. Preserve declined choices. A cloned repository may have shared choices but no local review flag: reuse the choices and finish local review without asking the same questions again.

Activation is `tack enable` locally or `tack enable --shared` for a shared `.tack` marker. When file scaffolding is requested, use `tack enable --scaffold` (optionally `--shared`). It creates only missing AGENTS.md, CLAUDE.md, the configured architecture document (default docs/architecture.md) and docs-map.txt. It does not overwrite existing instructions, grant execution trust, install dependencies or choose a workflow mode. For activation without `--scaffold`, include any missing base files in the proposal before adding them.

## Offer a concrete selection

Explain the observed project in a few sentences. Then offer a short, project-specific selection of optional additions, naming the exact paths, purpose and reason they fit. Ask which the user wants to create or adapt; offer the recommended set, a smaller set and deferral when useful. Let the user select individual items. Existing explicit instructions or an approved plan already authorizing an item count as the answer; ask only about undecided additions and continue independent authorized work while waiting.

For team setup, reuse or agree on coding/testing/Git conventions, context entrypoints, where necessary decisions/plans/handoffs belong, and verification commands. Index the agreed locations in AGENTS.md instead of duplicating context for each tool. Save every selected shared preference explicitly, including values that match defaults: an omitted setting can inherit a teammate's different personal preference. Local overrides win over shared values, then personal defaults; trust stays local.

For several selected settings, use a temporary version-1 profile with `mode` and `config`, then `tack config --shared --apply FILE --dry-run` and `tack config --shared --apply FILE`. This merges only selected values and reports effective origins; remove the temporary input afterwards. For one choice, `tack config NAME VALUE --shared` or `tack mode auto --shared` remains sufficient. Do not export ambient personal settings as team policy. Configure context paths before scaffolding, then confirm selected values have shared origins or explain intentional local overrides. Group unresolved choices and reuse recorded answers.

Examples to consider only when evidence supports them:

| Addition | Evidence and benefit |
| --- | --- |
| Tests and a fast-check command | Missing coverage for real behavior; inspect current tooling before adding a framework. |
| `checks-map.json` | Different changed paths require existing checks. Inspect what commands cover: a small project may need only its canonical suite; avoid selecting both focused tests and a full suite that repeats them. Keep manual documentation review visible instead of mapping prose to unrelated tests. |
| CI | Repository host is known and reproducible checks exist; reuse current workflows. |
| `.github/pull_request_template.md` | Team uses PRs and has no suitable project or organization template; adapt validation to actual commands. |
| README or a development guide | Setup knowledge is missing; link existing docs instead of copying them. |
| `.env.example` | Code consumes configuration variables; use placeholders, never copy real secrets. |
| Docker or deployment docs | Local services or a specified deployment target make them useful. |
| Release automation or dependency updates | Distribution and maintenance requirements justify them. |
| Selected external skills | A demonstrated gap remains after checking existing capabilities; propose individual skills from sources such as Addy Osmani or Matt Pocock using `lessons/references/external-skills.md`. Download only selected additions. |
| A local skill or agent definition | Repeated project-specific procedure or a distinct bounded role is useful; reuse current capabilities first. |
| ADRs, runbooks or domain glossary | Concrete decisions, operational procedures or terminology need recording. |

Do not present this table as a mandatory checklist. Do not create a license, release workflow, Docker setup, issue forms or broad docs tree by default. Plans, handoffs and AI logs are created when actual work and the selected workflow require them, not as empty onboarding templates. Selecting a PR template alone does not select issue forms.

## Implement and remember

Fill the base from evidence: actual commands with sources and verification status, real components, relevant conventions and valid doc links. Unknowns stay explicit until the user or code resolves them. For an empty repository a documented decision that the stack is not chosen yet is valid; no invented architecture is needed. Remove `<!-- tack:review-needed -->` only after reviewing that file. Refine docs-map rules to real source paths and existing docs; any one listed document changing satisfies a rule. Reuse an established documentation location and link it from the base rather than duplicate it.

Create only selected additions. Reuse existing PR templates through dev-workflow's Git/PR reference. For capabilities, follow `lessons` → `references/project-capabilities.md`, keep definitions in the project first, validate and index them in AGENTS.md; creating an agent definition does not authorize delegation or global promotion. For selected external skills, also follow `lessons/references/external-skills.md`: review conflicts, preserve dependencies and licenses, and record source, revision and local adaptations.

Record a concise `Setup choices` section in AGENTS.md: accepted additions, explicit declines/deferrals, material assumptions and verified commands. Avoid personal or secret data. Check `tack setup --check`, resolve relevant findings, and verify any executable configuration with appropriate local checks. The readiness check is structural; the assistant must verify factual accuracy. Set `tack config setup-review done` when the review is complete, including when the user chooses no optional additions. Set `deferred` when the user postpones; reset to `pending` when they ask to revisit. Do not mark unresolved work complete. Report created/reused files, verification and remaining unknowns.

If the user wants no repository files and AGENTS.md is absent, do not create it just to record a refusal. Keep the review state in local configuration instead. Report any deliberately declined base/readiness findings as such; do not claim that the structural check passed.
