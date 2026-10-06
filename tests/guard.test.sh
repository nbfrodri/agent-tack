#!/usr/bin/env bash
# Analyses command strings as JSON; none of the command payloads are executed.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-guard.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_STATE_HOME="$WORK/home/.local/state" GIT_CONFIG_NOSYSTEM=1
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
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys

repo, work = map(Path, sys.argv[1:])
guard = repo / "hooks/claude/guard-bash.sh"
failed = 0
passed = 0

def expect(expected, command, name=None, path=None, reason=None, script=None, cwd=None, args=(), home=None, env=None):
    global failed, passed
    environment = dict(os.environ)
    if path is not None:
        environment["PATH"] = str(path)
    if home is not None:
        environment["HOME"] = str(home)
    environment.update(env or {})
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
user_policy = Path(os.environ["XDG_CONFIG_HOME"]) / "agent-tack/guard-policy.txt"
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
# The lessons skill shows the rule it proposes for a prohibition; that exact line must work.
lesson_rules = [line for line in (repo / "skills/lessons/SKILL.md").read_text().splitlines() if line.startswith("command | ")]
user_policy.write_text("\n".join(lesson_rules) + "\n")
expect("deny", "npm publish --access public", "the lessons skill's example rule is a working deny rule", reason="publish")
expect("allow", "npm pack", "the lessons skill's example rule matches only its command")
user_policy.unlink()
legacy_policy = Path(os.environ["XDG_CONFIG_HOME"]) / "agent-harness/guard-policy.txt"
legacy_policy.parent.mkdir(parents=True, exist_ok=True)
legacy_policy.write_text("command | ask | pulumi destroy | Legacy rule.\n")
expect("ask", "pulumi destroy", "user rules in the former config directory still apply", reason="legacy")
legacy_policy.unlink()

# rm -r targets are resolved against the working directory before they are judged, so ".." cannot
# climb out unnoticed. The project lives under HOME because temp paths are allowed on purpose.
inside = Path(os.environ["HOME"]) / "work" / "proj"
(inside / "sub").mkdir(parents=True)
expect("ask", "rm -rf ../other", "rm: a sibling of the project asks", cwd=inside, reason="outside the project")
expect("deny", "rm -rf ../../..", "rm: climbing to an ancestor of HOME is denied", cwd=inside)
expect("deny", "rm -rf ../..", "rm: climbing to HOME itself is denied", cwd=inside)
expect("ask", f"rm -rf {inside}/../other", "rm: an absolute path that climbs out asks", cwd=inside, reason="outside the project")
expect("allow", "rm -rf sub/../build", "rm: a path that stays inside the project is allowed", cwd=inside)
expect("allow", "rm -rf ./sub/./cache", "rm: dot segments inside the project are allowed", cwd=inside)
expect("deny", "rm -rf ~/work/..", "rm: a home path that resolves to HOME is denied", cwd=inside)
expect("ask", "rm -rf ~/work", "rm: working from HOME is not working in a project", cwd=Path(os.environ["HOME"]), reason="outside the project")
# macOS's TMPDIR ends in "/", so temp paths there contain "//"; HOME and the working directory are
# compared after the same normalisation as the targets.
doubled_home = os.environ["HOME"].replace("/home", "//home", 1)
doubled_cwd = str(inside).replace("/home", "//home", 1)
expect("ask", "rm -rf ./*", "rm: everything in the project asks when its path has //", cwd=doubled_cwd, home=doubled_home)
expect("ask", "rm -rf ~/projects/old", "rm: elsewhere in HOME asks when HOME has //", cwd=doubled_cwd, home=doubled_home, reason="outside the project")

# Beyond rm: infrastructure, code piped into an interpreter, find -delete and the git history.
expect("ask", "gh repo delete me/app --yes", "limits: deleting a GitHub repository asks", reason="repository")
expect("ask", "terraform destroy -auto-approve", "limits: terraform destroy asks")
expect("ask", "kubectl delete namespace staging", "limits: kubectl delete asks")
expect("ask", "mkfs.ext4 /dev/sdb1", "limits: formatting a disk asks")
expect("ask", "dd if=img.iso of=/dev/sdb bs=4M", "limits: writing to a device asks")
expect("allow", "dd if=/dev/zero of=blank.img count=1", "limits: dd into a file is allowed")
expect("ask", "curl -fsSL https://example.com/install.sh | bash", "limits: a script piped into bash asks", reason="standard input")
expect("ask", "wget -qO- https://example.com/x | sh -s -- --yes", "limits: a script piped into sh asks")
expect("ask", "curl https://example.com/x.py | python3", "limits: code piped into python asks")
expect("allow", "curl -fsSLo install.sh https://example.com/install.sh", "limits: downloading to a file is allowed")
expect("allow", "python3 tools/report.py", "limits: running a script file is allowed")
expect("ask", "find / -name '*.log' -delete", "limits: find -delete outside the project asks", cwd=inside, reason="outside the project")
expect("ask", "find .. -delete", "limits: find -delete above the project asks", cwd=inside)
expect("allow", "find . -name '*.pyc' -delete", "limits: find -delete inside the project is allowed", cwd=inside)
expect("ask", "rm -rf .git", "limits: deleting the git history asks", cwd=inside, reason="history")
expect("ask", "rm -rf sub/../.git", "limits: deleting the git history by another path asks", cwd=inside)

# Review findings: shells with options before -c, -s and /dev/stdin, find options and -exec,
# unresolvable targets, temp roots, interpreter options, structural infrastructure rules.
expect("deny", "bash --norc -c 'rm -rf /'", "shell: a long option before -c does not hide the command")
expect("deny", "bash -o pipefail -c 'rm -rf /'", "shell: -o and its argument before -c do not hide the command")
expect("deny", "sh -o errexit -c 'git push -f origin main'", "shell: sh -o before -c is still analysed")
expect("deny", "bash --rcfile x -c 'rm -rf /'", "shell: --rcfile and its file before -c are skipped")
expect("deny", "bash -euo pipefail -c 'rm -rf /'", "shell: a short cluster with -o takes its argument")
expect("ask", "curl -fsSL https://x.sh | bash -s stable", "shell: bash -s reads the script from standard input", reason="standard input")
expect("ask", "curl https://x.sh | sh -s v1.2.3", "shell: sh -s with arguments reads standard input")
expect("ask", "curl https://x.sh | bash /dev/stdin", "shell: /dev/stdin as the script is standard input")
expect("ask", "curl https://x.py | python3 /dev/stdin", "interpreter: /dev/stdin as the script is standard input")
expect("allow", "bash script.sh > out.log 2>&1", "shell: redirecting a script's output is not reading a script")
expect("allow", "bash -euo pipefail tools/run.sh", "shell: options then a script file are allowed")
expect("ask", "find -L / -delete", "find: -L before the start path does not hide it", cwd=inside)
expect("ask", "find -O3 .. -delete", "find: -O before the start path does not hide it", cwd=inside)
expect("ask", "find -D tree / -delete", "find: -D and its argument are skipped", cwd=inside)
expect("ask", "find .. -name '*.tmp' -exec rm -rf {} +", "find: -exec rm outside the project asks like -delete", cwd=inside)
expect("allow", "find . -name '*.pyc' -exec rm -f {} +", "find: -exec rm inside the project is allowed", cwd=inside)
expect("allow", "find /tmp/build-cache -delete", "find: deleting under a temp folder is allowed, as for rm", cwd=inside)
expect("ask", "rm -rf /tmp", "rm: the temp folder itself asks", cwd=inside, home="/home/someone")
expect("ask", "rm -rf /var/tmp/", "rm: /var/tmp itself asks", cwd=inside, home="/home/someone")
expect("allow", "rm -rf /tmp/build-cache", "rm: a folder inside temp is allowed", cwd=inside, home="/home/someone")
expect("allow", "rm -rf /var/folders/ab/T/tmp.x1", "rm: inside a TMPDIR with a trailing slash is allowed", cwd=inside, home="/home/someone", env={"TMPDIR": "/var/folders/ab/T/"})
expect("ask", "rm -rf $(dirname \"$PWD\")", "rm: a target from a substitution cannot be judged and asks", cwd=inside, reason="cannot")
expect("ask", "rm -rf {..,x}", "rm: brace expansion cannot be judged and asks", cwd=inside)
expect("ask", "rm -rf ~root", "rm: another user's home cannot be judged and asks", cwd=inside)
expect("allow", "rm -rf build/*", "rm: a glob inside the project is allowed", cwd=inside)
expect("deny", "rm -rf ../*", "rm: every sibling of the project is too broad", cwd=inside)
expect("ask", "rm -rf *", "rm: everything in the project still asks", cwd=inside)
expect("ask", "rm -rf .git/objects", "rm: part of the git history asks", cwd=inside, reason="history")
expect("ask", "find .git -delete", "find: the git history asks", cwd=inside, reason="history")
expect("allow", "node -v", "interpreter: node -v is a version check")
expect("allow", "ruby -v", "interpreter: ruby -v is a version check")
expect("allow", "node --test", "interpreter: node --test runs the project's tests")
expect("allow", "python3 -m pytest -q", "interpreter: python3 -m runs a module")
expect("ask", "curl x | python3 -X dev", "interpreter: -X and its value before standard input still ask")
expect("ask", "curl x | perl -I lib", "interpreter: perl -I and its path before standard input still ask")
expect("ask", "curl x | ruby -r json", "interpreter: ruby -r is require, not inline code")
expect("ask", "curl x | perl -p", "interpreter: perl -p without -e reads its script from standard input")
expect("allow", "node -e 'console.log(1)'", "interpreter: inline node code is visible")
expect("ask", "curl x | source /dev/stdin", "shell: sourcing standard input asks")
expect("allow", "dd if=/dev/zero of=/dev/null count=1", "dd: writing to /dev/null is allowed")
expect("ask", "dd if=img of=//dev/sdb", "dd: a doubled slash still names a device")
expect("allow", "grep -r mkfs docs", "mkfs: naming mkfs in an argument is allowed")
expect("allow", "git commit -m 'docs: explain terraform destroy and kubectl delete'", "infra: words in a commit message are allowed")
expect("ask", "kubectl -n prod delete pod web", "kubectl: delete after global flags asks")
expect("ask", "kubectl --context prod delete deployment web", "kubectl: delete after --context asks")
expect("allow", "kubectl -n prod get pods", "kubectl: reading is allowed")
expect("ask", "terraform -chdir=infra destroy", "terraform: destroy after -chdir asks")
expect("ask", "terraform apply -destroy -auto-approve", "terraform: apply -destroy asks")
expect("allow", "terraform plan", "terraform: plan is allowed")

# Unleash relaxes only explicit local asks; deny rules and opaque or outside-project asks stay.
project = work / "unleashed"
subprocess.run(["git", "init", "-q", str(project)], check=True)
subprocess.run(["git", "-C", str(project), "config", "tack.enabled", "true"], check=True)
subprocess.run(["git", "-C", str(project), "config", "tack.mode", "unleash"], check=True)
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
expect("deny", "tack config unleash-max-tool-calls 999999", "unleash: the agent cannot raise its own limit", cwd=project)
expect("deny", "tack config unleash-max-tool-calls --unset", "unleash: the agent cannot remove its own limit", cwd=project)
expect("deny", "tack mode standard", "unleash: the agent cannot change its own mode", cwd=project)
expect("deny", "tack trust", "unleash: the agent cannot grant itself formatter trust", cwd=project)
expect("deny", "tack migrate", "unleash: the agent cannot migrate tack settings", cwd=project)
expect("deny", "git config tack.unleashMaxToolCalls 999999", "unleash: raw git config writes to tack keys are refused", cwd=project)
expect("deny", "tack config unleash-max-tool-calls 999999", "unleash: the renamed CLI cannot raise the limit either", cwd=project)
expect("deny", "tack mode standard", "unleash: the renamed CLI cannot change the mode", cwd=project)
expect("deny", "git config tack.unleashMaxToolCalls 999999", "unleash: raw git config writes to tack keys are refused", cwd=project)
expect("allow", "tack config unleash-max-tool-calls", "unleash: reading a setting is allowed", cwd=project)
expect("allow", "tack status", "unleash: status is allowed", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "tack.mode", "lite"], check=True)
expect("ask", "git reset --hard HEAD~1", "other modes keep asking about local discards", cwd=project)
expect("allow", "tack config delegation off", "other modes let the assistant change settings", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "tack.mode", "no-such-mode"], check=True)
expect("ask", "git reset --hard HEAD~1", "an invalid mode keeps asking", cwd=project)
subprocess.run(["git", "-C", str(project), "config", "tack.enabled", "false"], check=True)
subprocess.run(["git", "-C", str(project), "config", "tack.mode", "unleash"], check=True)
expect("ask", "git reset --hard HEAD~1", "unleash needs the workflow enabled", cwd=project)
# Codex runs a command when a hook answers "ask", so under --codex every ask becomes a deny.
expect("deny", "git reset --hard HEAD~1", "codex: an ask becomes a deny", reason="confirmation", args=("--codex",))
expect("deny", "cat <<'EOF' | python3\nprint(1)\nEOF", "codex: opaque commands are refused", args=("--codex",))
expect("deny", "git commit --no-verify -m 'fix: x'", "codex: deny rules stay deny", args=("--codex",))
expect("allow", "git status", "codex: safe commands pass", args=("--codex",))

# merge-requires-green: a stub gh reports the PR's check buckets; red or pending CI blocks the merge.
def gh_stub(name, body):
    stub = work / "gh" / name
    stub.mkdir(parents=True)
    (stub / "gh").write_text("#!/usr/bin/env bash\n" + body + "\n")
    (stub / "gh").chmod(0o755)
    return f"{stub}:{os.environ['PATH']}"

def bin_without(name, missing, extra=None):
    """A PATH holding the usual tools except `missing`, plus an optional gh stub body."""
    folder = work / name
    folder.mkdir()
    for tool in ("bash", "env", "cat", "dirname", "tr", "jq", "python3", "git", "awk", "grep", "sed",
                 "head", "readlink", "basename", "sleep", "mktemp", "rm", "wc", "cut", "timeout", "kill"):
        executable = shutil.which(tool)
        if tool not in missing and executable:
            (folder / tool).symlink_to(executable)
    if extra is not None:
        (folder / "gh").write_text("#!/usr/bin/env bash\n" + extra + "\n")
        (folder / "gh").chmod(0o755)
    return str(folder)

# The rule is part of the workflow, so it applies only in enabled projects.
merging = work / "merging"
subprocess.run(["git", "init", "-q", str(merging)], check=True)
subprocess.run(["git", "-C", str(merging), "config", "tack.enabled", "true"], check=True)
green = gh_stub("green", "printf 'pass\\nskipping\\npass\\n'")
red = gh_stub("red", "printf 'pass\\nfail\\n'")
pending = gh_stub("pending", "printf 'pass\\npending\\n'; exit 8")
unknown = gh_stub("unknown", "echo 'no checks reported' >&2; exit 1")
selector = gh_stub("selector", '[ "$*" = "pr checks 42 --repo o/r --json bucket --jq .[].bucket" ] || exit 1; echo pass')
expect("allow", "gh pr merge --merge --delete-branch", "merge: green checks allow the merge", path=green, cwd=merging)
expect("deny", "gh pr merge 42 --squash", "merge: failing checks deny the merge", path=red, reason="failing", cwd=merging)
expect("deny", "gh pr merge --merge", "merge: pending checks deny until CI finishes", path=pending, reason="still running", cwd=merging)
expect("ask", "gh pr merge --merge", "merge: checks gh cannot report ask", path=unknown, reason="cannot confirm", cwd=merging)
expect("deny", "gh pr merge --merge", "merge: a guard started by a relative path still finds tack", path=red, reason="failing",
       cwd=merging, script=os.path.relpath(guard))
expect("ask", "gh pr merge --merge", "merge: without gh the guard asks", path=bin_without("no-gh", ("gh",)), reason="cannot confirm", cwd=merging)
expect("allow", "gh pr merge 42 -R o/r --merge --body 'x y'", "merge: the PR and repository are forwarded", path=selector, cwd=merging)
expect("ask", "gh pr merge $(gh pr list -q .[0].number) --merge", "merge: a dynamic PR selector asks", path=green, cwd=merging)
expect("ask", "cd ../other && gh pr merge --merge", "merge: after a directory change the checks cannot be read here", path=green, reason="cannot confirm", cwd=merging)
expect("ask", "GH_REPO=o/r gh pr merge 5", "merge: a repository chosen through the environment asks", path=green, reason="cannot confirm", cwd=merging)
expect("allow", "gh pr merge 5 --auto --squash", "merge: --auto may wait for pending checks", path=pending, cwd=merging)
expect("deny", "gh pr merge 5 --auto --squash", "merge: --auto still refuses failing checks", path=red, reason="failing", cwd=merging)
expect("allow", "gh pr merge 5 --disable-auto", "merge: turning auto-merge off needs no checks", path=red, cwd=merging)
slow = bin_without("no-timeout", ("timeout",), "exec sleep 30")
expect("ask", "gh pr merge --merge", "merge: without timeout a slow gh is cut off and asks", path=slow, reason="cannot confirm", cwd=merging)
expect("allow", "gh pr view 42", "merge: other gh commands pass", path=red, cwd=merging)
expect("allow", "echo 'gh pr merge 42'", "merge: quoted text stays data", path=red, cwd=merging)
expect("deny", "gh pr merge --merge", "codex: pending checks deny", path=pending, reason="still running", args=("--codex",), cwd=merging)
expect("deny", "gh pr merge --merge", "codex: unknown checks deny and leave it to the user", path=unknown, reason="confirmation", args=("--codex",), cwd=merging)
expect("allow", "gh pr merge --merge", "merge: projects without tack enabled are left alone", path=red)
subprocess.run(["git", "-C", str(merging), "config", "tack.mergeRequiresGreen", "false"], check=True)
expect("allow", "gh pr merge --merge", "merge: the toggle off skips the check", path=red, cwd=merging)
# Environment assignments are skipped by their name, whatever their value holds.
expect("deny", "X=a/b git commit --no-verify -m x", "an assignment with a slash still reaches the command")
expect("deny", "/usr/bin/env X=a/b git commit --no-verify -m x", "env with a slash assignment still reaches the command")
# Latency budget: the guard runs before every shell command, so a typical one must stay quick.
import time
budget_ms = float(os.environ.get("TACK_GUARD_BUDGET_MS", "200"))  # CI sets a wider budget for slower runners
payload = json.dumps({"tool_input": {"command": 'git add -A && git commit -m "fix: x" && git push'}, "cwd": str(work)})
# One warm-up run, then the median of five, so a single slow run on a busy machine does not fail it.
timings = []
try:
    for run in range(6):
        started = time.monotonic()
        subprocess.run(["bash", str(guard)], input=payload, text=True, capture_output=True, timeout=8)
        if run:
            timings.append((time.monotonic() - started) * 1000)
    median_ms = sorted(timings)[2]
except subprocess.TimeoutExpired:
    median_ms = float("inf")
if median_ms <= budget_ms:
    passed += 1
    print(f"  PASS latency: a compound command takes {median_ms:.0f} ms (budget {budget_ms:.0f} ms)")
else:
    failed += 1
    print(f"  FAIL latency: a compound command takes {median_ms:.0f} ms (budget {budget_ms:.0f} ms)")
bare = work / "bare-guard"
(bare / "lib").mkdir(parents=True)
(bare / "guard-bash.sh").write_text(guard.read_text())
for name in ("shell-parse.sh", "shell-parse.py"):
    source = repo / "hooks/claude/lib" / name
    if source.exists():
        (bare / "lib" / name).write_text(source.read_text())
expect("ask", "echo hi", "missing shipped policy asks for review", reason="policy", script=bare / "guard-bash.sh")
# With its policy but without its rule libraries, the guard asks instead of allowing.
(bare / "guard-policy.txt").write_text((repo / "hooks/claude/guard-policy.txt").read_text())
expect("ask", "echo hi", "a missing rule library asks for review", reason="The guard library lib/guard-", script=bare / "guard-bash.sh")
# The guard stays readable: no function longer than 60 lines in the dispatcher or its libraries.
long_functions = []
for path in [guard, *sorted((repo / "hooks/claude/lib").glob("guard-*.sh"))]:
    start = name = None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\(\) *\{", line)
        if match:
            # A one-line function closes on its own line.
            name, start = (None, None) if line.rstrip().endswith("}") else (match.group(1), number)
        elif line == "}" and name:
            if number - start + 1 > 60:
                long_functions.append(f"{path.name}:{name} ({number - start + 1} lines)")
            name = None
if long_functions:
    failed += 1
    print("  FAIL functions longer than 60 lines: " + ", ".join(long_functions))
else:
    passed += 1
    print("  PASS no guard function is longer than 60 lines")
print(f"\n{passed} passed, {failed} failed")
sys.exit(bool(failed))
PY
