#!/usr/bin/env python3
"""Export public per-run facts without publishing prompts, credentials or full transcripts.

Usage: python3 summarize-codex.py EVIDENCE_ROOT OUTPUT.json
Keeps qualification batches separate and never edits original metrics.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def summarize(root):
    records = []
    for path in sorted(root.rglob("metrics.json")):
        metrics = json.loads(path.read_text(encoding="utf-8"))
        meta = metrics.get("metadata", {})
        runtime_path = path.with_name("runtime-observation.json")
        runtime = json.loads(runtime_path.read_text(encoding="utf-8")) if runtime_path.exists() else None
        record = {key: metrics.get(key) for key in (
            "scenario", "condition", "rep", "exit_code", "completed", "timed_out", "hidden_passed",
            "hidden_total", "hidden_pass", "tests_pass", "tests_count", "commits", "worked_on_branch",
            "conventional_commits_pct", "ai_attribution_in_history", "duration_s", "setup_s", "input_tokens",
            "output_tokens", "cost_usd", "regression_test", "fix_commit")}
        record["identity"] = {key: meta.get(key) for key in (
            "batch_id", "run_id", "provider", "requested_model", "resolved_model", "cli_version",
            "harness_revision", "source_sha256", "configuration_sha256", "fixture_sha256", "hidden_sha256",
            "prompt_sha256", "source_dirty", "source_changed", "timeout_seconds", "metrics_version")}
        record["runtime"] = runtime
        usage, files, failed_commands = [], {}, []
        for transcript in sorted(path.parent.glob("transcript*.jsonl")):
            files[transcript.name] = hashlib.sha256(transcript.read_bytes()).hexdigest()
            for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                    usage.append(event["usage"])
                item = event.get("item", {})
                if event.get("type") == "item.completed" and item.get("type") == "command_execution" and item.get("exit_code"):
                    failed_commands.append(item["exit_code"])
        record["transcript_sha256"] = files
        record["reported_usage"] = {key: sum(item[key] for item in usage if isinstance(item.get(key), int))
                                    if usage and all(isinstance(item.get(key), int) for item in usage) else None
                                    for key in ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                                                "output_tokens", "reasoning_output_tokens")}
        # A command can fail intentionally (e.g. a red test); this is not an acceptance verdict.
        record["nonzero_command_exits"] = failed_commands
        repo = path.parent / "repo"
        if repo.is_dir():
            def git(*args):
                return subprocess.run(["git", "-C", str(repo), *args], check=True,
                                      capture_output=True, text=True).stdout
            initial = git("rev-list", "--max-parents=0", "HEAD").strip()
            record["artifacts"] = {
                "diff_stat": git("diff", "--stat", initial),
                "production_test_diff": git("diff", initial, "--", "*.py"),
                "documentation_diff": git("diff", initial, "--", "*.md"),
                "untracked_files": git("ls-files", "--others", "--exclude-standard").splitlines(),
            }
        records.append(record)
    return {"schema": 1, "runs": records,
            "notes": ["Subscription token usage is not a USD charge.",
                      "Infrastructure qualification attempts must be interpreted separately.",
                      "Runtime model/effort observations are local configuration evidence.",
                      "Reasoning output is reported separately and must not be added twice to output tokens."]}


if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:3])
    output.write_text(json.dumps(summarize(source), indent=2) + "\n", encoding="utf-8")
