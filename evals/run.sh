#!/usr/bin/env bash
# Runs a behaviour eval: a real `claude -p` / `codex exec` session in a throwaway repo,
# with the installed skills, instructions and hooks. Uses real model tokens.
# Usage: evals/run.sh <scenario>   (s1-claude-new | s2-claude-bug | s3-claude-release | s4-codex-new)
# Results go to $EVALS_OUT (default: $TMPDIR/agent-harness-evals); grade them with evals/grade.py.
set -uo pipefail

EVALS="${EVALS_OUT:-${TMPDIR:-/tmp}/agent-harness-evals}"
name="${1:?scenario name required}"
case "$name" in
  s1-claude-new | s2-claude-bug | s3-claude-release | s4-codex-new) ;;
  *)
    echo "unknown scenario '$name' (s1-claude-new | s2-claude-bug | s3-claude-release | s4-codex-new)" >&2
    exit 2
    ;;
esac
dir="$EVALS/$name/repo"
out="$EVALS/$name"
rm -rf "$out"
mkdir -p "$dir"

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
  s1-claude-new|s4-codex-new) ;;
  s2-claude-bug) seed_bug_repo ;;
  s3-claude-release) seed_release_repo ;;
esac
cd "$dir" || exit 1

case "$name" in
  s1-claude-new) prompt="$NEW_PROJECT_PROMPT" ;;
  s4-codex-new) prompt="$NEW_PROJECT_PROMPT" ;;
  s2-claude-bug) prompt='Cuando el carrito está vacío, average_price peta con ZeroDivisionError. Debería devolver 0. Arréglalo.' ;;
  s3-claude-release) prompt='Prepara la siguiente release del proyecto. No hay remoto configurado todavía.' ;;
esac
printf '%s\n' "$prompt" > "$out/prompt.txt"

start=$(date +%s)
case "$name" in
  s4-codex-new)
    codex exec --json -s workspace-write -c sandbox_workspace_write.network_access=true \
      --skip-git-repo-check -C "$dir" "$prompt" > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
  *)
    claude -p "$prompt" --output-format stream-json --verbose \
      --permission-mode acceptEdits \
      --allowedTools "Bash(git *)" "Bash(uv *)" "Bash(python3 *)" "Bash(ls *)" "Bash(cat *)" \
        "Bash(mkdir *)" "Bash(pytest *)" "Bash(find *)" "Bash(grep *)" "Bash(head *)" "Bash(sed -n *)" \
        Read Write Edit Glob Grep Skill Agent TodoWrite \
      > "$out/transcript.jsonl" 2> "$out/stderr.log"
    ;;
esac
echo "exit=$? seconds=$(( $(date +%s) - start ))" > "$out/run.txt"
