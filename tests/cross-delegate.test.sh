#!/usr/bin/env bash
# Protects the cross-delegate report contract. Usage: tests/cross-delegate.test.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tack-cross-delegate.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_STATE_HOME="$HOME/.local/state"
export GIT_CONFIG_NOSYSTEM=1
mkdir -p "$XDG_CONFIG_HOME" "$XDG_STATE_HOME"

python3 - "$REPO" <<'PY'
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(sys.argv.pop())
SKILL = ROOT / "skills/cross-delegate"


class ReportSchemaTests(unittest.TestCase):
    def schema(self):
        return json.loads(
            (SKILL / "references/report-schema.json").read_text(encoding="utf-8")
        )

    def test_schema_is_valid_json(self):
        self.schema()

    def test_every_property_is_required(self):
        schema = self.schema()
        missing = set(schema["properties"]) - set(schema["required"])
        self.assertFalse(missing, f"Properties missing from required: {sorted(missing)}")

    def test_additional_properties_are_forbidden(self):
        self.assertIs(self.schema()["additionalProperties"], False)

    def test_verdict_enum(self):
        self.assertCountEqual(
            self.schema()["properties"]["verdict"]["enum"],
            ["done", "partial", "blocked"],
        )

    def test_skill_mentions_report_schema(self):
        self.assertIn(
            "references/report-schema.json",
            (SKILL / "SKILL.md").read_text(encoding="utf-8"),
        )


unittest.main(verbosity=2)
PY
