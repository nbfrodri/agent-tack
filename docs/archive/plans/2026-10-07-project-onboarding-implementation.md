# Project onboarding and native integrations

Status: done

The user approved minimal, evidence-based scaffolding, a common initialization flow for new and existing repositories, and a project-specific conversation before optional additions. Existing authorization also covers native integrations for Gemini, Copilot, OpenCode, Crush and Cursor, concrete Codex model tiers, reply styles and PR templates. Use local tests only; no paid model benchmarks or global installation.

## Acceptance criteria

- Activation remains separate from file creation. `enable --scaffold` creates only missing AGENTS.md, CLAUDE.md, architecture and docs-map files, grounded in repository evidence. No fabricated services, dangling template links or empty working-document trees.
- `tack setup` reports detected stack, declared commands, existing foundations, local capabilities and useful missing additions without executing project code. `--check` diagnoses unfinished guidance, broken links and invalid map targets.
- Startup context routes pending setup to one shared new-project workflow. The assistant inspects the repository, incorporates user intent, asks about concrete optional files, respects existing authorization and records accepted, declined or deferred choices. A completed/deferred review is not asked again each session.
- New projects and existing repositories use the same base and optional selection policy. Plans, handoffs, AI logs, CI, releases, Docker and capabilities are added when justified and authorized.
- Native tool installation preserves foreign/edited files, supports reinstall and uninstall, and documents the distinction between supported native adapters and instruction-only behavior.

## Implementation

1. Add a bounded read-only project analysis and readiness helper in `lib/project_setup.py`; call it from scaffolding and a `tack setup` command. Add the setup-review toggle and startup hint. Test empty/existing repos, monorepos, unsafe paths, idempotency and deferred/completed reviews.
2. Replace stack-specific templates with neutral guidance. Update `new-project`, `project-docs`, global instructions and a focused onboarding reference to implement analysis, proposals, user choices and verification. Keep the global entrypoint short.
3. Finish native agent rendering/ownership, Gemini/Copilot hook adapters and tool registry/model mappings. Exercise protocols and install/reinstall/uninstall in temporary HOME directories.
4. Update usage, editor support, architecture and docs-map. Run focused suites, pinned lint and the full local suite in Linux; record actual outcomes. Leave real-model evaluations prepared but unrun.

## Preservation and limits

Scaffolding never overwrites existing files or follows symlink parents. Commands are evidence, not automatically trusted execution. Optional additions require the user's selection; prior explicit choices count as authorization. Tool API fixtures cannot establish compatibility with every installed live version. `.tack` remains a shared activation marker, not a configuration directory.

## Verification performed

- All 21 suites passed in a disposable Linux container (`tests/run-all.sh -j 4`, 211 seconds), including installer, ownership, doctor, hooks, guard, CLI, offline eval fixtures and JavaScript mod tests.
- Final focused verification passed after the last adapter changes: 6 native installation/format tests, 8 protocol/shared-hook tests and 7 project setup tests. `tests/lint.sh` passed at CI-pinned versions; catalog validation and skill-creator validation of the edited skills passed.
- Regressions covered empty projects, monorepos, detected commands without execution, existing files/templates/capabilities, symlink destinations, repeated scaffolding, invalid doc links/map targets, setup-review state, native user hooks, edited agents, reinstall, opt-out and uninstall.
- The first full pass identified the new onboarding skill's required core membership and a Gemini fixture that needed its native skills directory; both were fixed and the full pass repeated. A container missing Node was replaced with the existing local evaluation image.
- The interactive conversation protocol is prepared in `evals/project-onboarding.md`; no model evaluations, paid calls, global installation or publication were performed.
