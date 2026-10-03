# Conventions

Defaults for every project. **A project's existing conventions win**: follow its linter, formatter and style first, and use these where it has none (and in new projects).

## Git

| Topic | Convention |
| --- | --- |
| Commit messages | [Conventional Commits 1.0](https://www.conventionalcommits.org): `type(scope): description`, English, imperative, ≤ 72 chars. Enforced in enabled projects by the `commit-msg` hook (which only rejects over 100). Details in `git-github.md`. |
| Branches | `type/short-description`, or `type/123-short-description` when there's an issue. Short-lived. |
| Merging PRs | **Merge commit.** Preserve the verified commits from the branch in `main`; squash only when explicitly requested by the user. The PR title and every commit follow Conventional Commits. |
| Commits inside a PR branch | Commit coherent verified milestones while working. A passing test and its implementation usually share a commit. Resolve temporary fixup commits before publication, without rewriting published history unless authorised. |
| After merge | Delete branches only when authorised by the user. |
| Attribution | No AI attribution anywhere (see `git-github.md`). |

Repository settings to match (new repos, or existing ones with the user's permission):
```bash
gh repo edit --enable-merge-commit --enable-squash-merge=false \
  --enable-rebase-merge=false --delete-branch-on-merge=false
```

## Releases and tags

| Topic | Convention |
| --- | --- |
| Versioning | [SemVer](https://semver.org) for every project, computed from Conventional Commits: `fix`/`perf` → patch, `feat` → minor, breaking change → major. Start at `0.1.0`; release `1.0.0` when the project reaches production or has a stable public API. |
| Tags | `vMAJOR.MINOR.PATCH` (e.g. `v1.4.2`), **annotated**, on `main`. Pre-releases: `v2.0.0-alpha.1`, `-beta.N`, `-rc.N`. No other tag names. Published tags are never moved or deleted. Enforced by the `pre-push` hook in enabled projects. |
| How releases happen | **release-please** by default: a GitHub Action keeps a release PR open with the next version and the CHANGELOG computed from the commits on `main`; merging it creates the tag and the GitHub Release. Manual releases (`release` skill) only where release-please isn't set up. |
| Changelog | `CHANGELOG.md` in the repo (Keep a Changelog sections) **and** the same notes in the GitHub Release. |
| Release commit | `chore(main): release X.Y.Z` (release-please) or `chore(release): vX.Y.Z` (manual). |
| Hotfixes | A `fix` commit on `main` and a patch release; branch from the tag (`hotfix/X.Y.Z`) only when `main` holds unreleasable work. |

Details and setup: `release` skill.

## All languages
- **English** for all identifiers, comments, docstrings, logs and error messages (user-facing UI text follows the product's language, through i18n where there is more than one). Business terms are translated consistently; when the translation isn't obvious, add it to the project glossary (`docs/glossary.md`) with the original Spanish term.
- Names say what something is or does: no abbreviations except universal ones (`id`, `url`, `db`). Booleans read as questions (`isActive`, `has_access`, `canEdit`). Functions are verbs, classes and types nouns.
- Comments explain *why*, never restate *what*. No commented-out code; git has the history.
- Money: decimal types (`Decimal`, `decimal.js`/`big.js`, `brick/money`) or integer minor units, never floats. Dates and times: UTC, ISO 8601 at the boundaries.
- Small functions with one level of abstraction; early returns over nested `if`s; no magic numbers (use named constants).
- Errors: explicit and typed (domain error classes); never swallow them.

## Code style (how code is written)

### Formatting: the tools decide
Formatting is never discussed or done by hand: the formatter runs on save, in the Claude hook after every edit, and in CI. Use each tool's **defaults** and don't add config that overrides them:
- TypeScript/JavaScript (Prettier or Biome): 2-space indentation, **double quotes, semicolons**, trailing commas, 80 columns.
- Python (Ruff format): 4 spaces, double quotes, 88 columns.
- PHP (Pint, Laravel preset): 4 spaces, PSR-12.
- Every repo has an `.editorconfig` (UTF-8, LF line endings, final newline, trimmed trailing whitespace) so editors agree with the formatters.

### Writing style
- **Functional first.** Pure functions and immutable data by default; side effects (I/O, DB, network, time, randomness) pushed to the edges and injected. Use classes where they add something: DDD entities and aggregates that protect invariants, value objects, and services or repositories with injected dependencies (and wherever a framework expects them, as NestJS or Laravel do).
- **Flat control flow.** Use guard clauses and early returns instead of nesting; at most two levels of indentation inside a function; no nested ternaries.
- **Small and focused.** A function does one thing at one level of abstraction; if it needs a comment to separate "parts", those parts are functions. Use an options object or a parameter object beyond three parameters.
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

## TypeScript / JavaScript (React, Next.js, Node)
| Topic | Convention |
| --- | --- |
| Package manager | **pnpm** for new projects (`pnpm-lock.yaml`, `packageManager` field in `package.json` via Corepack). In existing projects, the one its lockfile says. |
| Language | TypeScript with `"strict": true`; no `any` (use `unknown` and narrow it); `import type` for type-only imports. |
| Formatting and linting | The project's tool. New projects: Biome, or ESLint + Prettier when a framework preset needs ESLint (e.g. `eslint-config-next`). |
| File names | **kebab-case** for every file: `user-profile.tsx`, `use-cart.ts`, `order-service.ts`. Next.js special files keep their names (`page.tsx`, `layout.tsx`, `route.ts`). |
| Identifiers | `PascalCase` components, classes, types and interfaces (no `I` prefix); `camelCase` variables and functions; `useSomething` hooks; `UPPER_SNAKE_CASE` true constants. |
| Exports | Named exports. Default exports only where the framework requires them (Next.js `page`, `layout`, `route`, config files). |
| Imports | Path alias `@/` for project files instead of long `../../..` chains. |
| Components | Function components; props type named `<Component>Props`; one exported component per file (small private helpers may live alongside). |

## Python (FastAPI, Django, scripts)
| Topic | Convention |
| --- | --- |
| Tooling | **uv** (dependencies, virtualenv, running); **Ruff** for lint and format (PEP 8); **mypy** or **pyright** (strict in new projects). |
| Layout | `src/<package>/` with `tests/` alongside (Django: the standard project/app layout). |
| Identifiers | `snake_case` modules, functions and variables; `PascalCase` classes; `UPPER_SNAKE_CASE` constants; leading `_` for private. |
| Types | Type hints on every public function and method; `X \| None` rather than `Optional[X]`; Pydantic models or dataclasses rather than bare dicts for structured data. |
| Docstrings | Google style, on public modules, classes and functions whose purpose isn't obvious from the name and types. |
| Idioms | `pathlib` over `os.path`; f-strings; context managers for resources; `logging`, not `print`, in application code. |

## PHP (Laravel)
| Topic | Convention |
| --- | --- |
| Tooling | **Composer**; **Laravel Pint** (PSR-12 plus the Laravel preset); **Larastan** at the highest level the project can sustain; Pest for tests. |
| Laravel naming | Models singular `PascalCase` (`Order`); tables plural `snake_case` (`order_items`); controllers singular plus `Controller` (`OrderController`); Form Requests `StoreOrderRequest`/`UpdateOrderRequest`; Actions as verb + noun (`CreateOrder`); Resources `OrderResource`; route URIs plural kebab-case (`/order-items`); route names dotted (`orders.show`). |
| Code | `declare(strict_types=1);` in domain and application classes; typed properties, parameters and return types everywhere; constructor property promotion; backed enums instead of string constants. |

## SQL and data
Tables plural `snake_case`; columns `snake_case`; foreign keys `<singular>_id`; timestamps `created_at`/`updated_at`; indexes `idx_<table>_<columns>`. See the `database` skill.
