# Conventions

Portable guidance and selectable defaults. **A project's existing conventions win**: follow its linter, formatter and style first, and use these where it has none (and in new projects).

## Git

| Topic | Convention |
| --- | --- |
| Commit messages | [Conventional Commits 1.0](https://www.conventionalcommits.org): `type(scope): description`, English, imperative, ≤ 72 chars. Enforced in enabled projects by the `commit-msg` hook (which only rejects over 100). Details in `git-github.md`. |
| Branches | `type/short-description`, or `type/123-short-description` when there's an issue. Short-lived. |
| Merging PRs | Recommend merge commit for coherent verified milestones, or squash for one change with temporary intermediate commits. Offer available methods in the integration confirmation; preserve commits unless the user explicitly chooses squash. The PR title and every commit follow Conventional Commits. |
| Commits inside a PR branch | Commit coherent verified milestones while working. A passing test and its implementation usually share a commit. Resolve temporary fixup commits before publication, without rewriting published history unless authorised. |
| After merge | Delete the merged branch locally and on the remote right away; repos enable automatic deletion on merge. Unmerged branches are deleted only with the user's approval. |
| Attribution | No AI attribution anywhere (see `git-github.md`). |

Repository settings to match (new repos, or existing ones with the user's permission):
```bash
gh repo edit --enable-merge-commit --enable-squash-merge \
  --enable-rebase-merge=false --delete-branch-on-merge
```

## Releases and tags

| Topic | Convention |
| --- | --- |
| Versioning | [SemVer](https://semver.org) for distributed packages with a defined public API; retain an existing version policy. If deriving versions from Conventional Commits: `fix`/`perf` → patch, `feat` → minor, breaking change → major. Start at `0.1.0`; release `1.0.0` when the project reaches production or has a stable public API. |
| Tags | `vMAJOR.MINOR.PATCH` (e.g. `v1.4.2`), **annotated**, on `main`. Pre-releases: `v2.0.0-alpha.1`, `-beta.N`, `-rc.N`. No other tag names. Published tags are never moved or deleted. Enforced by the `pre-push` hook in enabled projects. |
| How releases happen | For projects that need GitHub release automation, **release-please** is one option: a GitHub Action keeps a release PR open with the next version and the CHANGELOG computed from the commits on `main`; merging it creates the tag and the GitHub Release. Manual releases (`release` skill) only where release-please isn't set up. |
| Changelog | `CHANGELOG.md` in the repo (Keep a Changelog sections) **and** the same notes in the GitHub Release. |
| Release commit | `chore(main): release X.Y.Z` (release-please) or `chore(release): vX.Y.Z` (manual). |
| Hotfixes | A `fix` commit on `main` and a patch release; branch from the tag (`hotfix/X.Y.Z`) only when `main` holds unreleasable work. |

Details and setup: `release` skill.

## All languages
- **English** for all identifiers, comments, docstrings, logs and error messages (user-facing UI text follows the product's language, through i18n where there is more than one). Business terms are translated consistently; when the translation isn't obvious, add it to the project glossary (`docs/glossary.md`) with the original term in the business's language.
- Names say what something is or does: no abbreviations except universal ones (`id`, `url`, `db`). Booleans read as questions (`isActive`, `has_access`, `canEdit`). Functions are verbs, classes and types nouns.
- Comments explain *why*, never restate *what*. No commented-out code; git has the history.
- Money: decimal types (`Decimal`, `decimal.js`/`big.js`, `brick/money`) or integer minor units, never floats. Dates and times: UTC, ISO 8601 at the boundaries.
- Small functions with one level of abstraction; early returns over nested `if`s; no magic numbers (use named constants).
- Errors: explicit and typed (domain error classes); never swallow them.

## Code style (how code is written)

### Formatting: the tools decide
Reuse the project formatter and its configuration. Add formatting automation only when it serves the project, and run it through the available editor, trusted hook or CI. For a new project, these are possible choices to agree during setup:
- TypeScript/JavaScript (Prettier or Biome): 2-space indentation, **double quotes, semicolons**, trailing commas, 80 columns.
- Python (Ruff format): 4 spaces, double quotes, 88 columns.
- PHP (Pint, Laravel preset): 4 spaces, PSR-12.
- An `.editorconfig` can share editor defaults (UTF-8, LF line endings, final newline, trimmed trailing whitespace) when editor settings otherwise disagree with the formatters.

### Writing style
- **Functional first.** Pure functions and immutable data by default; side effects (I/O, DB, network, time, randomness) pushed to the edges and injected. Use classes where they add something: DDD entities and aggregates that protect invariants, value objects, and services or repositories with injected dependencies (and wherever a framework expects them, as NestJS or Laravel do).
- **Flat control flow.** Use guard clauses and early returns instead of nesting; split deeply nested logic when it improves readability; avoid nested ternaries that obscure behavior.
- **Small and focused.** A function does one thing at one level of abstraction; if it needs a comment to separate "parts", those parts are functions. Use a parameter object when several arguments form a coherent concept or are easy to confuse.
- **Explicit over clever.** Use descriptive names rather than short ones, and readable steps rather than dense one-liners. Prefer `map`/`filter`/comprehensions for simple transformations and a plain loop when the logic gets complex.
- **Immutability.** `const` by default (`let` only when reassigned); never mutate arguments; return new objects/arrays. In Python, no mutable default arguments; prefer tuples or frozen dataclasses for fixed data.
- **Async.** Use `async`/`await` rather than `.then()` chains; run independent work in parallel (`Promise.all`, `asyncio.gather`); never leave a promise unhandled.
- **Types as documentation.** Declare explicit return types on exported functions; model states with union or discriminated types and enums instead of loose strings and booleans; make illegal states unrepresentable when it's cheap.
- **Errors.** Throw or raise domain-specific errors with context; catch only where you can handle or translate them (usually at the boundary).

### Comments and docs in code
**Default: no comments.** Well-named functions, variables and types make most comments unnecessary, and AI-written code tends to over-comment. Before writing a comment, try to make it unnecessary: rename, extract a well-named function, or introduce a named constant or type.

Write a comment only when the code cannot say it:
- **why** something non-obvious is done: a business rule, a constraint, a workaround with a link to its issue, a security or performance reason;
- a warning about a non-obvious consequence ("order matters: X must run before Y because…");
- `TODO(#123): …`, always with an issue reference.

Never write:
- comments that restate the code (`// increment counter`, `# loop over items`, `// return the result`);
- step-by-step narration or section banners inside a function (`// 1. validate input`, `# --- helpers ---`); if a function has "parts", they should be separate functions;
- comments about the change itself or the conversation (`// added`, `// fixed bug`, `// new implementation`, `// as requested`, `// updated to use X`); that belongs in the commit message;
- commented-out code;
- docstrings that repeat the signature (`"""Gets the user. Args: user_id: the user id. Returns: the user."""`).

**Docstrings / JSDoc** go only on the public API (exported functions, classes and modules of libraries and shared code) when the purpose, behaviour or errors aren't obvious from the name and types. Keep them to one or two lines plus whatever is non-obvious.

When editing existing code, don't add comments to explain your change, and remove comments that your change made wrong.

## Language and stack specifics
Read only the file for the stack you are touching: `languages/typescript.md` (TypeScript, JavaScript, React, Next.js, Node), `languages/python.md`, `languages/php.md` (Laravel) or `languages/sql.md` (SQL and data).
