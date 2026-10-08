# Conventions

Project instructions and existing tools take precedence over tack's fallback guidance. Choose conventions during setup and save the relevant ones in project `AGENTS.md`. A fork can change cross-project defaults.

For tack's own contributors, [AGENTS.md](../AGENTS.md), [development](development.md) and the [PR template](../.github/pull_request_template.md) define the repository contract: English content, Bash 3.2 compatibility, isolated tests and meaningful installer/hook regressions.

Tack's default Git hooks enforce Conventional Commits in enabled projects, protect selected operations and remove AI attribution. Existing projects can turn off Conventional Commit enforcement with `tack config conventional-commits false`, including as an allowed shared preference. See [hook behavior and limits](how-it-works.md#enforced-rules-hooks).

Language tools, formatter settings and release automation should match the project. A Python service need not adopt frontend tools, and a local script need not acquire a release pipeline. [Engineering practices](engineering-practices.md) explains the useful principles; [customization](customization.md) shows where the fallback instructions live.
