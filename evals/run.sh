#!/usr/bin/env bash
# Runs one behaviour eval: a real `claude -p` (or `codex exec`) session on a throwaway repo.
# Uses real model tokens.
#
# Usage: evals/run.sh <scenario> [condition] [repetition]
#   scenarios:  new-project | bug-fix | release | codex-new-project | vague-requirement | conventions
#   conditions: auto | lite | lean | standard | strict: the full setup, with the project enabled at
#               that workflow mode; harness (default) is an alias for auto
#   baseline:   Claude Code as shipped: no user settings, skills or instructions, and git
#               without the global hooks (same repo and prompt)
# Results go to $EVALS_OUT (default: $TMPDIR/agent-tack-evals)/<scenario>/<condition>-<rep>;
# grade them with evals/grade.py and summarise them with evals/report.py.
set -eEuo pipefail

HARNESS_REPO="$(cd "$(dirname "$0")/.." && pwd)"
EVALS="${EVALS_OUT:-${TMPDIR:-/tmp}/agent-tack-evals}"
name="${1:?scenario name required}"
condition="${2:-harness}"
rep="${3:-1}"
case "$name" in
  new-project | bug-fix | release | codex-new-project | vague-requirement | conventions) ;;
  *)
    echo "unknown scenario '$name' (new-project | bug-fix | release | codex-new-project | vague-requirement | conventions)" >&2
    exit 2
    ;;
esac
case "$condition" in
  baseline) mode='' ;;
  harness) mode=auto ;;
  auto | lite | lean | standard | strict) mode="$condition" ;;
  *) echo "unknown condition '$condition' (baseline | harness | auto | lite | lean | standard | strict)" >&2; exit 2 ;;
esac
case "$rep" in *[!0-9]* | '') echo "repetition must be a number" >&2; exit 2 ;; esac

out="$EVALS/$name/$condition-$rep"
dir="$out/repo"
rm -rf "$out"
mkdir -p "$dir"
exec 2> "$out/stderr.log"
start=$(date +%s)
isolated_home=""
# shellcheck disable=SC2317,SC2329 # Invoked indirectly by the EXIT trap.
finish() {
  status=$?
  printf 'exit=%s seconds=%s\n' "$status" "$(( $(date +%s) - start ))" > "$out/run.txt"
  python3 "$HARNESS_REPO/evals/metadata.py" finish "$out" || true
  if [ -n "$isolated_home" ]; then rm -rf "$isolated_home"; fi
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'status=$?; echo "Scenario setup failed (exit=$status)" >> "$out/stderr.log"; exit "$status"' ERR

if [ "$condition" = baseline ]; then
  # A git config without the harness hooks, keeping only the user's identity
  eval_user=$(git config --global --get user.name 2>/dev/null || echo Eval)
  eval_email=$(git config --global --get user.email 2>/dev/null || echo eval@example.com)
  export GIT_CONFIG_GLOBAL="$out/gitconfig"
  git config --file "$GIT_CONFIG_GLOBAL" user.name "$eval_user"
  git config --file "$GIT_CONFIG_GLOBAL" user.email "$eval_email"
  git config --file "$GIT_CONFIG_GLOBAL" init.defaultBranch main
fi

# Sessions are non-interactive: a question would end them, so every prompt waives questions.
NO_QUESTIONS='You do not need to ask me questions; choose reasonable defaults.'
NEW_PROJECT_PROMPT='Create a small Python library (use uv) to calculate a shopping cart total: price times quantity, a 10% volume discount for 10 or more units of the same product, and 21% VAT on the total. Name the package cart and expose cart_total(items), where items is a list of (unit_price, quantity) pairs, returning the total with VAT. This is a new project in this directory. '"$NO_QUESTIONS"

seed_bug_repo() {
  cd "$dir" || exit 1
  git init -q -b main
  mkdir -p src/cart tests
  cat > pyproject.toml <<'EOF'
[project]
name = "cart"
version = "0.1.0"
requires-python = ">=3.10"

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["src"]
EOF
  cat > src/cart/__init__.py <<'EOF'
from decimal import Decimal


def total(items: list[tuple[Decimal, int]]) -> Decimal:
    """Sum of unit price x quantity for each line."""
    return sum((price * qty for price, qty in items), Decimal("0"))


def average_price(items: list[tuple[Decimal, int]]) -> Decimal:
    """Average unit price across lines."""
    return sum((price for price, _ in items), Decimal("0")) / len(items)
EOF
  cat > tests/test_cart.py <<'EOF'
from decimal import Decimal

from cart import average_price, total


def test_total_multiplies_price_by_quantity():
    assert total([(Decimal("2.50"), 2), (Decimal("1.00"), 3)]) == Decimal("8.00")


def test_average_price():
    assert average_price([(Decimal("2"), 1), (Decimal("4"), 5)]) == Decimal("3")
EOF
  cat > README.md <<'EOF'
# cart

Shopping cart helpers.

## Development

```bash
uv run pytest
```
EOF
  printf '.venv/\n__pycache__/\n' > .gitignore
  git add -A && git commit -q -m "feat: add cart total and average price"
}

seed_release_repo() {
  seed_bug_repo
  git tag -a v0.1.0 -m "v0.1.0"
  cat > CHANGELOG.md <<'EOF'
# Changelog

## [Unreleased]

## [0.1.0] - 2026-09-01
### Added
- Cart total and average price.
EOF
  git add CHANGELOG.md && git commit -q -m "docs: add changelog"
  cat >> src/cart/__init__.py <<'EOF'


def item_count(items: list[tuple[Decimal, int]]) -> int:
    """Total number of units in the cart."""
    return sum(qty for _, qty in items)
EOF
  git commit -qam "feat: add item count"
  python3 - <<'PY'
from pathlib import Path
p = Path("src/cart/__init__.py")
p.write_text(p.read_text().replace("/ len(items)", '/ len(items) if items else Decimal("0")'))
PY
  git commit -qam "fix: return zero average for an empty cart"
  git commit -q --allow-empty -m "chore: tidy up"
}

# A feature in a project whose AGENTS.md sets conventions the prompt does not repeat: the hidden
# tests check the feature and those conventions (rounding, input validation, errors).
seed_conventions_repo() {
  cd "$dir" || exit 1
  git init -q -b main
  mkdir -p src/cart tests
  cat > pyproject.toml <<'EOF'
[project]
name = "cart"
version = "0.1.0"
requires-python = ">=3.10"

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["src"]
EOF
  cat > AGENTS.md <<'EOF'
# AGENTS.md

## Conventions
- Money is `Decimal`, never `float`. Every public function returns amounts rounded to cents with
  `ROUND_HALF_UP` (`.quantize(CENT, ROUND_HALF_UP)`), applied once, to the final result.
- Every public function validates its items with `_check`: a negative price or quantity raises
  `ValueError`.
- Invalid arguments raise `ValueError` with a message; never return `None` or ignore them.

## Commands
- Tests: `uv run pytest -q`
EOF
  cat > src/cart/__init__.py <<'EOF'
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def _check(items: list[tuple[Decimal, int]]) -> None:
    for price, quantity in items:
        if price < 0 or quantity < 0:
            raise ValueError("price and quantity must not be negative")


def subtotal(items: list[tuple[Decimal, int]]) -> Decimal:
    """Sum of unit price x quantity."""
    _check(items)
    return sum((price * quantity for price, quantity in items), Decimal("0")).quantize(CENT, ROUND_HALF_UP)
EOF
  cat > tests/test_cart.py <<'EOF'
from decimal import Decimal

import pytest

from cart import subtotal


def test_subtotal_multiplies_price_by_quantity():
    assert subtotal([(Decimal("2.50"), 2), (Decimal("1.00"), 3)]) == Decimal("8.00")


def test_subtotal_rejects_negative_quantities():
    with pytest.raises(ValueError):
        subtotal([(Decimal("1.00"), -1)])
EOF
  printf '# cart\n\nShopping cart helpers. Conventions and commands: AGENTS.md.\n' > README.md
  printf '.venv/\n__pycache__/\n' > .gitignore
  git add -A && git commit -q -m "feat: add cart subtotal"
}

case "$name" in
  new-project | codex-new-project) (cd "$dir" && git init -q -b main) ;;
  bug-fix | vague-requirement) seed_bug_repo ;;
  release) seed_release_repo ;;
  conventions) seed_conventions_repo ;;
esac
cd "$dir" || exit 1
if [ -n "$mode" ]; then
  "$HARNESS_REPO/bin/tack" enable >/dev/null
  # Set locally so the user's global default mode cannot leak into the comparison.
  "$HARNESS_REPO/bin/tack" mode "$mode" >/dev/null
fi

case "$name" in
  new-project | codex-new-project) prompt="$NEW_PROJECT_PROMPT" ;;
  bug-fix) prompt="When the cart is empty, average_price raises ZeroDivisionError. It should return 0. Fix it. $NO_QUESTIONS" ;;
  release) prompt="Prepare the next release of the project. No remote is configured yet. $NO_QUESTIONS" ;;
  # Deliberately vague: the workflow should turn it into measurable criteria before any code.
  vague-requirement) prompt="Make the cart faster and more robust. $NO_QUESTIONS" ;;
  conventions) prompt="Add discount codes: a public function total(items, code=None) in the cart package that applies an optional code to the subtotal. SAVE10 takes 10% off; FLAT5 takes 5.00 off, never going below zero. Codes are case-insensitive. $NO_QUESTIONS" ;;
esac
printf '%s\n' "$prompt" > "$out/prompt.txt"

allowed_tools=("Bash(git *)" "Bash(uv *)" "Bash(python3 *)" "Bash(python *)" "Bash(PYTHONPATH=*)" "Bash(ls *)" "Bash(cat *)"
  "Bash(mkdir *)" "Bash(pytest *)" "Bash(tail *)" "Bash(tack *)" "Bash(harness *)" "Bash(find *)" "Bash(grep *)" "Bash(head *)" "Bash(sed -n *)"
  Read Write Edit Glob Grep Skill Agent TodoWrite)
provider=claude
[ "$name" = codex-new-project ] && provider=codex
cli_version=$("$provider" --version 2>/dev/null || true)
harness_revision=$(git -C "$HARNESS_REPO" rev-parse HEAD)
python3 "$HARNESS_REPO/evals/metadata.py" start "$out" "$name" "$condition" "$rep" "$provider" \
  "${EVALS_MODEL:-}" "$cli_version" "$harness_revision" "${allowed_tools[@]}"
model_flags=()
[ -z "${EVALS_MODEL:-}" ] || model_flags=(--model "$EVALS_MODEL")

baseline_flags=()
[ "$condition" = baseline ] && baseline_flags=(--setting-sources "project,local" --disable-slash-commands)

if [ "$condition" = baseline ] && [ "$name" = codex-new-project ]; then
  auth_source="${CODEX_HOME:-$HOME/.codex}/auth.json"
  isolated_home=$(mktemp -d "${TMPDIR:-/tmp}/harness-eval-home.XXXXXX")
  chmod 700 "$isolated_home"
  mkdir -m 700 "$isolated_home/.codex" "$isolated_home/.config"
  if [ -f "$auth_source" ]; then
    (umask 077; cat "$auth_source" > "$isolated_home/.codex/auth.json")
  fi
  export HOME="$isolated_home" CODEX_HOME="$isolated_home/.codex" XDG_CONFIG_HOME="$isolated_home/.config"
fi

start=$(date +%s)
trap - ERR
set +e
case "$name" in
  codex-new-project)
    codex exec --json "${model_flags[@]+"${model_flags[@]}"}" -s workspace-write -c sandbox_workspace_write.network_access=true \
      --skip-git-repo-check -C "$dir" "$prompt" > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
  *)
    claude -p "$prompt" "${model_flags[@]+"${model_flags[@]}"}" --output-format stream-json --verbose \
      "${baseline_flags[@]+"${baseline_flags[@]}"}" \
      --permission-mode acceptEdits \
      --allowedTools "${allowed_tools[@]}" \
      > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
esac
status=$?
exit "$status"
