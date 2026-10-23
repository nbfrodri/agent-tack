# tack and Everything Claude Code (ECC)

[ECC](https://github.com/affaan-m/ECC) is the best-known public collection of AI coding configuration. This page says how tack differs, so you can pick one or borrow from both. It makes no claim that either produces better code: [ADR 0004](adr/0004-personal-configuration-with-sets.md) records that tack's own evaluations did not show a general quality gain.

Figures for ECC were read from its repository on 2026-10-23 and change often; check the repository before quoting them.

## At a glance

| | ECC | tack |
| --- | --- | --- |
| What it is | A large, public collection presented as a product, with its own site and packages | One person's configuration, public to read or fork; defaults follow that person's preferences |
| Size | 311 skill folders, 71 agent entries and 97 command entries; about 287,000 stars and 42,500 forks; MIT | 20 skills and 11 agent roles of its own; 53 sets that list 223 distinct skills, most of them pinned from 26 third-party collections |
| How you get it | Install the plugin or packages | `git clone`, then `./install.sh`; it links the checkout into each tool and records what it changed so `./uninstall.sh` can restore it |
| What loads | A catalog installed together | Only the sets you activate, per project or everywhere; `tack set suggest` proposes sets from the project's files and never activates them. Every active skill adds its description to each session |
| Effort per task | Not assessed here | Modes (`lite`, `standard`, `strict`, plus opt-in `unleash`) chosen by risk, not by size |
| Verification | Hooks and scanners | `tack verify` selects the project's own checks from the changed paths; a completion hook asks for a commit or a stated reason; nothing runs without local trust |
| Safety | Hooks and a security scanner | A command guard that parses git, file, exec and infrastructure commands; Git hooks against staged secrets, AI attribution and pushes to `main` |
| Tools | Claude Code, Cursor, Codex and OpenCode, according to its documentation | Claude Code, Codex, Gemini CLI, Copilot CLI, OpenCode, Crush and Cursor, through `targets.txt` and thin adapters; the guard and hooks reach the tools with native hooks |
| Skill sources | Written in the repository | Written here or pinned to a full commit of another repository, checked out outside this one |

## Where they differ in practice

- **Breadth against a small footprint.** ECC covers many languages, industries and workflows. tack keeps few skills of its own and lets you pull in the ones a project needs, so the standing context cost stays low.
- **Product against personal setup.** ECC is built for many users. tack changes without a migration path for other people; a fork is the supported way to diverge.
- **Choosing a level of ceremony.** tack's central idea is that a typo and a payment change need different amounts of process. This review did not check whether ECC has an equivalent.
- **Deterministic checks.** tack's most reusable parts are not prompts: selecting a project's checks from a diff, comparing agreed settings, testing a prospective merge and parsing commands before they run.
- **Questioning the model's work.** tack asks the assistant to offer two or three options for an open design choice, has a read-only `critic` challenge a plan before code at strict level, and treats a model reviewing its own change as weak evidence. ECC has related ideas, for example `santa-method` and `council`; tack ported what it lacked into its own files instead of pinning them.

## When ECC is the better fit

You want a large ready-made catalog, language and framework packs that tack does not carry, or a project maintained for many users with support behind it. tack will not match that breadth and does not try to.

## Borrowing from ECC

tack reviewed ECC twice. The first review produced issues #41 to #53; the second compared seven skills with tack's own and ported only the missing parts. The method, for any collection: read the whole skill, compare it with what you have, keep the difference, and pin a collection in [`sources.txt`](../sources.txt) only when you would use most of it. See [external skills](external-skills.md).
