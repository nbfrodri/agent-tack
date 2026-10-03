#!/usr/bin/env bash
# Runs one behaviour eval: a real `claude -p` (or `codex exec`) session on a throwaway repo.
# Uses real model tokens.
#
# Usage: evals/run.sh <scenario> [harness|baseline] [repetition]
#   scenarios:  new-project | bug-fix | release | codex-new-project
#   harness:    the full setup, with the project enabled (default)
#   baseline:   Claude Code as shipped: no user settings, skills or instructions, and git
#               without the global hooks (same repo and prompt)
# Results go to $EVALS_OUT (default: $TMPDIR/agent-harness-evals)/<scenario>/<condition>-<rep>;
# grade them with evals/grade.py and summarise them with evals/report.py.
set -uo pipefail

HARNESS_REPO="$(cd "$(dirname "$0")/.." && pwd)"
EVALS="${EVALS_OUT:-${TMPDIR:-/tmp}/agent-harness-evals}"
name="${1:?scenario name required}"
condition="${2:-harness}"
rep="${3:-1}"
case "$name" in
  new-project | bug-fix | release | codex-new-project) ;;
  *)
    echo "unknown scenario '$name' (new-project | bug-fix | release | codex-new-project)" >&2
    exit 2
    ;;
esac
case "$condition" in
  harness | baseline) ;;
  *) echo "unknown condition '$condition' (harness | baseline)" >&2; exit 2 ;;
esac
case "$rep" in *[!0-9]* | '') echo "repetition must be a number" >&2; exit 2 ;; esac

out="$EVALS/$name/$condition-$rep"
dir="$out/repo"
rm -rf "$out"
mkdir -p "$dir"

if [ "$condition" = baseline ]; then
  # A git config without the harness hooks, keeping only the user's identity
  export GIT_CONFIG_GLOBAL="$out/gitconfig"
  git config --file "$GIT_CONFIG_GLOBAL" user.name "$(git config --global --get user.name 2>/dev/null || echo Eval)"
  git config --file "$GIT_CONFIG_GLOBAL" user.email "$(git config --global --get user.email 2>/dev/null || echo eval@example.com)"
  git config --file "$GIT_CONFIG_GLOBAL" init.defaultBranch main
fi

NEW_PROJECT_PROMPT='Crea una pequeña librería en Python (usa uv) para calcular el total de un carrito de compra: precio por cantidad, 10% de descuento por volumen a partir de 10 unidades del mismo producto, e IVA del 21% sobre el total. Es un proyecto nuevo en esta carpeta. No hace falta que me preguntes nada, decide tú lo razonable.'

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

case "$name" in
  new-project | codex-new-project) (cd "$dir" && git init -q -b main) ;;
  bug-fix) seed_bug_repo ;;
  release) seed_release_repo ;;
esac
cd "$dir" || exit 1
[ "$condition" = harness ] && "$HARNESS_REPO/bin/harness" enable >/dev/null

case "$name" in
  new-project | codex-new-project) prompt="$NEW_PROJECT_PROMPT" ;;
  bug-fix) prompt='Cuando el carrito está vacío, average_price peta con ZeroDivisionError. Debería devolver 0. Arréglalo.' ;;
  release) prompt='Prepara la siguiente release del proyecto. No hay remoto configurado todavía.' ;;
esac
printf '%s\n' "$prompt" > "$out/prompt.txt"

baseline_flags=()
[ "$condition" = baseline ] && baseline_flags=(--setting-sources "project,local" --disable-slash-commands)

start=$(date +%s)
case "$name" in
  codex-new-project)
    codex exec --json -s workspace-write -c sandbox_workspace_write.network_access=true \
      --skip-git-repo-check -C "$dir" "$prompt" > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
  *)
    claude -p "$prompt" --output-format stream-json --verbose \
      "${baseline_flags[@]+"${baseline_flags[@]}"}" \
      --permission-mode acceptEdits \
      --allowedTools "Bash(git *)" "Bash(uv *)" "Bash(python3 *)" "Bash(ls *)" "Bash(cat *)" \
        "Bash(mkdir *)" "Bash(pytest *)" "Bash(harness *)" "Bash(find *)" "Bash(grep *)" "Bash(head *)" "Bash(sed -n *)" \
        Read Write Edit Glob Grep Skill Agent TodoWrite \
      > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
esac
echo "exit=$? seconds=$(( $(date +%s) - start ))" > "$out/run.txt"
