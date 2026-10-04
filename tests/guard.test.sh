#!/usr/bin/env bash
# Analyses command strings as JSON; none of the command payloads are executed.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-guard.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME" "$WORK/no-python" "$WORK/no-jq"
for tool in bash cat dirname tr jq; do
  executable="$(command -v "$tool" || true)"
  [ -z "$executable" ] || ln -s "$executable" "$WORK/no-python/$tool"
done
for tool in bash cat dirname tr python3 git; do
  executable="$(command -v "$tool" || true)"
  [ -z "$executable" ] || ln -s "$executable" "$WORK/no-jq/$tool"
done
python3 - "$REPO" "$WORK" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys

repo, work = map(Path, sys.argv[1:])
guard = repo / "hooks/claude/guard-bash.sh"
failed = 0
passed = 0

def expect(expected, command, name=None, path=None, reason=None, script=None, cwd=None, args=()):
    global failed, passed
    environment = dict(os.environ)
    if path is not None:
        environment["PATH"] = str(path)
    try:
        result = subprocess.run(
            ["bash", str(script or guard), *args],
            input=json.dumps({"tool_input": {"command": command}, "cwd": str(cwd or work)}),
            text=True, capture_output=True, env=environment, timeout=8,
        )
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)["hookSpecificOutput"] if result.stdout else {}
        actual = output.get("permissionDecision", "allow")
        assert actual == expected, f"expected {expected}, got {actual}: {result.stdout}"
        if reason:
            assert reason.lower() in output["permissionDecisionReason"].lower(), output
        passed += 1
        print(f"  PASS {name or command[:90]}")
    except (AssertionError, ValueError, subprocess.TimeoutExpired) as error:
        failed += 1
        print(f"  FAIL {name or command[:90]}: {error}")

expect("deny", "git -ccore.hooksPath=/dev/null commit -m 'fix: x'")
expect("deny", "git -cCoRe.HoOkSpAtH=/dev/null status")
expect("deny", "git --config-env core.hooksPath=HOOKS status")
expect("deny", "sudo -n git commit --no-verify -m 'fix: x'")
expect("deny", "sudo -u root -n rm -rf /")
expect("deny", "/usr/bin/sudo --user=root /usr/bin/git push -f origin main")
expect("deny", "env -S 'git commit --no-verify'")
expect("deny", "env --split-string='rm -rf /'")
expect("deny", "env -Sgit\\ commit\\ --no-verify")
expect("allow", "sudo -n git status")
expect("allow", "env -S 'git status'")
expect("deny", "env -S '-i rm -rf /'", "env split options retain executable")
expect("deny", "env -S '-- git commit --no-verify'", "env split option terminator retains executable")
expect("ask", "git commit $'--no-verify'", "unsupported ANSI quote requires review")
expect("allow", "echo 'sudo -n rm -rf /; git -ccore.hooksPath=/dev/null'")
expect("allow", "cat <<'EOF'\n$(rm -rf /)\nEOF", "quoted heredoc stays data")
expect("ask", "cat <<'EOF' | python3\nimport os; os.system('rm -rf /')\nEOF", "piped interpreter heredoc requires review")
expect("ask", "awk -f - <<'EOF'\nBEGIN { system(\"rm -rf /\") }\nEOF", "awk script heredoc requires review")
expect("allow", "cat > sh <<'EOF'\nrm -rf /\nEOF", "shell-named data target stays data")
expect("allow", "printf '%s' '\v'", "control byte inside quoted data completes")
expect("allow", "echo \v", "non-shell whitespace completes")
expect("allow", "git -cmessage=core.hooksPath status", "hooksPath text in other config value stays data")
expect("allow", "cat <<EOF\nNever run rm -rf /\nEOF", "plain heredoc stays data")
expect("allow", "cat <<EOF\n\\$(rm -rf /)\nEOF", "escaped heredoc substitution stays data")
expect("deny", "cat <<EOF\n$(rm -rf /)\nEOF", "unquoted heredoc substitution executes")
expect("deny", "cat <<EOF\n`git commit --no-verify`\nEOF", "unquoted heredoc backtick executes")
expect("ask", "bash <<'EOF'\nrm -rf /\nEOF", "shell heredoc requires review", reason="heredoc")
expect("ask", "sudo -n sh <<EOF\ngit commit --no-verify\nEOF", "wrapped shell heredoc requires review")
expect("ask", "cat <<'EOF' | sh\nrm -rf /\nEOF", "piped executable heredoc requires review")
expect("allow", "cat <<'A' <<'B'\n$(rm -rf /)\nA\nrm -rf /\nB", "multiple quoted heredocs stay data")
expect("deny", "cat <<'A' <<B\ndata\nA\n$(rm -rf /)\nB", "multiple heredocs retain expansion rules")
expect("deny", "cat <<-EOF\n\tdata\n\tEOF\nrm -rf /", "tab-stripped heredoc retains following command")
expect("deny", "cat <<EOF\nEOFnot_the_delimiter\nEOF\nrm -rf /", "delimiter must match complete line")
expect("ask", "! rm -rf /", "unsupported shell negation requires review")
expect("ask", "\\\nif true; then rm -rf /; fi", "line continuation retains command position")
expect("ask", "bash <<< 'rm -rf /'", "shell here-string requires review")
expect("ask", "bash < script.sh", "shell stdin script requires review")
expect("ask", "if true; then rm -rf /; fi", "unsupported conditional requires review")
expect("ask", "for item in x; do git commit --no-verify; done", "unsupported loop requires review")
expect("ask", "case x in x) rm -rf /;; esac", "unsupported case requires review")
expect("ask", "function cleanup { rm -rf /; }", "unsupported function requires review")
expect("allow", "echo 'if true; then rm -rf /; fi'", "quoted control flow stays data")
expect("allow", "echo \"$(printf ')')\"", "parentheses inside quoted substitution stay quoted")
expect("deny", "echo \"$(printf ')'; rm -rf /)\"", "substitution matching respects quotes")
expect("deny", "echo $(cat <<'EOF'\n)\nEOF\nrm -rf /\n)", "substitution matching respects heredocs")
expect("ask", "echo $(echo $(echo $(echo $(echo $(rm -rf /))))))", "deep nesting requires review", reason="depth")
expect("allow", "printf '%s' '" + "x" * 50000 + "'", "50k quoted data completes within hook budget")
expect("deny", "printf '%s' '" + "x" * 50000 + "'; rm -rf /", "long command retains trailing safety check")
expect("ask", "printf '%s' '" + "x" * 70000 + "'; rm -rf /", "oversized command asks explicitly", reason="size")
expect("ask", "git commit -" + "a" * 50000 + "n", "long compact option does not exceed hook budget")
expect("ask", 'echo "' + '$(true)' * 100 + '"', "many substitutions require bounded review", reason="limit")
expect("ask", ";".join(["git status"] * 1500), "too many commands ask explicitly", reason="limit")
expect("deny", "git commit --no-verify", "Python JSON fallback", path=work / "no-jq")
if (work / "no-python/jq").exists():
    expect("deny", "sudo -n rm -rf /", "jq-only fallback still denies", path=work / "no-python")
    expect("ask", "cat <<EOF\n$(rm -rf /)\nEOF", "jq-only unsupported syntax asks", path=work / "no-python")
    expect("ask", "printf '%s' '" + "x" * 50000 + "'", "jq-only long input asks promptly", path=work / "no-python", reason="size")

# Policy as data: the shipped table keeps the database rules; a user file can only add rules.
expect("ask", "psql -c 'drop table orders'", "shipped policy: destructive SQL is case-insensitive", reason="database")
expect("ask", "mongosh --eval 'db.dropDatabase()'", "shipped policy: data deletion in a database client")
expect("ask", "bin/rails db:drop", "shipped policy: database reset commands")
user_policy = Path(os.environ["XDG_CONFIG_HOME"]) / "agent-harness/guard-policy.txt"
user_policy.parent.mkdir(parents=True, exist_ok=True)
user_policy.write_text(
    "# user rules\n"
    "command | ask | terraform destroy | Terraform destroy deletes infrastructure.\n"
    "command | deny | kubectl delete namespace prod | Never delete the production namespace.\n"
    "command | allow | git commit --no-verify | users cannot relax the guard\n"
    "sql | allow | DROP TABLE | users cannot relax shipped asks\n"
    "nowhere | deny | echo hi | unknown scopes are skipped\n"
    "this line is malformed\n"
)
expect("ask", "psql -c 'DROP TABLE orders'", "user policy cannot relax a shipped ask")
expect("ask", "terraform destroy -auto-approve", "user policy adds an ask rule", reason="infrastructure")
expect("deny", "kubectl delete namespace prod", "user policy adds a deny rule", reason="production")
expect("allow", "terraform plan", "user rules match only their pattern")
expect("deny", "git commit --no-verify", "user policy cannot allow what the guard denies")
expect("allow", "echo hi", "malformed user lines are ignored")
user_policy.unlink()

# Unleash relaxes only explicit local asks; deny rules and opaque or outside-project asks stay.
project = work / "unleashed"
subprocess.run(["git", "init", "-q", str(project)], check=True)
subprocess.run(["git", "-C", str(project), "config", "harness.enabled", "true"], check=True)
subprocess.run(["git", "-C", str(project), "config", "harness.mode", "unleash"], check=True)
expect("allow", "git reset --hard HEAD~1", "unleash: local discard is allowed", cwd=project)
expect("allow", "git branch -D old-idea", "unleash: branch force-delete is allowed", cwd=project)
expect("allow", "git stash drop", "unleash: stash drop is allowed", cwd=project)
expect("allow", "rm -rf .", "unleash: deleting inside the project is allowed", cwd=project)
expect("ask", "rm -rf /etc/app", "unleash: deleting outside the project still asks", cwd=project)
expect("ask", "git push --force origin feat/x", "unleash: rewriting the remote still asks", cwd=project)
expect("ask", "psql -c 'DROP TABLE orders'", "unleash: database rules still ask", cwd=project)
expect("ask", "cat <<'EOF' | python3\nprint(1)\nEOF", "unleash: opaque commands still ask", cwd=project)
expect("deny", "git commit --no-verify -m 'fix: x'", "unleash: deny rules stay", cwd=project)
expect("deny", "git push origin main --force", "unleash: force-push to main stays denied", cwd=project)
expect("ask", "cd ~ && rm -rf *", "unleash: a directory change before a local discard still asks", cwd=project)
expect("ask", "cd / && rm -rf ./*", "unleash: deleting after cd to root still asks", cwd=project)
expect("ask", "pushd /tmp && git clean -fdx", "unleash: pushd counts as a directory change", cwd=project)
expect("ask", "git -C /home/someone/other reset --hard", "unleash: git -C targets another repository", cwd=project)
expect("ask", "git --git-dir=/x --work-tree=/y clean -fdx", "unleash: git-dir and work-tree target another repository", cwd=project)
expect("ask", "git branch -D main", "unleash: deleting the main branch still asks", cwd=project)
expect("deny", "harness config unleash-max-tool-calls 999999", "unleash: the agent cannot raise its own limit", cwd=project)
expect("deny", "harness config unleash-max-tool-calls --unset", "unleash: the agent cannot remove its own limit", cwd=project)
expect("deny", "harness mode standard", "unleash: the agent cannot change its own mode", cwd=project)
expect("deny", "harness trust", "unleash: the agent cannot grant itself formatter trust", cwd=project)
expect("deny", "git config harness.unleashMaxToolCalls 999999", "unleash: raw git config writes to harness keys are refused", cwd=project)
expect("allow", "harness config unleash-max-tool-calls", "unleash: reading a setting is allowed", cwd=project)
expect("allow", "harness status", "unleash: status is allowed", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "harness.mode", "lite"], check=True)
expect("ask", "git reset --hard HEAD~1", "other modes keep asking about local discards", cwd=project)
expect("allow", "harness config delegation off", "other modes let the assistant change settings", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "harness.mode", "no-such-mode"], check=True)
expect("ask", "git reset --hard HEAD~1", "an invalid mode keeps asking", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "harness.enabled", "false"], check=True)
subprocess.run(["git", "-C", str(project), "config", "harness.mode", "unleash"], check=True)
expect("ask", "git reset --hard HEAD~1", "unleash needs the workflow enabled", cwd=project)
# Codex runs a command when a hook answers "ask", so under --codex every ask becomes a deny.
expect("deny", "git reset --hard HEAD~1", "codex: an ask becomes a deny", reason="confirmation", args=("--codex",))
expect("deny", "cat <<'EOF' | python3\nprint(1)\nEOF", "codex: opaque commands are refused", args=("--codex",))
expect("deny", "git commit --no-verify -m 'fix: x'", "codex: deny rules stay deny", args=("--codex",))
expect("allow", "git status", "codex: safe commands pass", args=("--codex",))
bare = work / "bare-guard"
(bare / "lib").mkdir(parents=True)
(bare / "guard-bash.sh").write_text(guard.read_text())
for name in ("shell-parse.sh", "shell-parse.py"):
    source = repo / "hooks/claude/lib" / name
    if source.exists():
        (bare / "lib" / name).write_text(source.read_text())
expect("ask", "echo hi", "missing shipped policy asks for review", reason="policy", script=bare / "guard-bash.sh")
print(f"\n{passed} passed, {failed} failed")
sys.exit(bool(failed))
PY
