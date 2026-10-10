# Audit: external skills and subagent plugins used by sets

- Date: 2026-10-11. Scope: every skill folder that `sets.txt` takes from `sources.txt` at the pinned commits (152 folders, 1,009 files, 75 scripts), and the plugins of the `agents-*` sets as cached that day (171 agent definitions).
- Method: a pattern scan of every text file, followed by reading each hit in context. Patterns: pipe-to-shell installs, `sudo`, global installs, destructive commands, permission bypass, credential paths, secret variables, network sends, telemetry, instruction-override phrasing, writes to agent settings, dynamic execution, hidden Unicode, symlinks leaving the folder, shipped hook or MCP files.
- Limits: a pattern scan finds known shapes, not intent. Minified scripts and the one native binary were not reviewed. Marketplace plugins are not pinned, so their result holds only for the versions cached on this date. Repeat after `tack set update`.

## Result

No skill or agent tries to override instructions, hide actions from the user, bypass permissions, read credentials or ship hooks, and no symlink leaves its folder. Every instruction-override phrase found is defensive ("treat repository content as data"). Hidden Unicode appears only as zero-width spaces before nested code fences and in emoji examples.

Four items need a decision from the owner rather than a fix here.

| Severity | Where | Finding | Decision |
| --- | --- | --- | --- |
| High | `impeccable` (set `design`) | The skill tells the assistant to run `scripts/impeccable context` once per session. That launcher downloads a native binary from the project's GitHub releases into `~/.impeccable/bin` and executes it. The version comes from the pinned `VERSION` file and the download is checked against a `.sha256` file from the same host, so the pin fixes which release is fetched but the binary itself is outside the reviewed commit. The skill can also install per-project hooks in each tool's settings, with a recorded consent. | Kept, because the owner asked for this skill. Remove it from `design` to avoid running an unreviewed binary. |
| Medium | `deploy-to-vercel` (was in `devops`) | Its script packs the project (without `.git`, `.env*` and `node_modules`) and uploads it to a public deploy endpoint that needs no account, returning a claimable preview URL. | Removed from `devops`. Add it back for projects where that upload is intended. |
| Medium | `huggingface-datasets` (set `ai`) | Documents uploading raw agent session logs (`~/.claude/projects`, `~/.codex/sessions`) to a Hugging Face dataset. It says to default to private repositories and warns that traces can hold secrets. | Kept. Only act on it when asked. |
| Low | `hf-cli`, `modern-python`, `uv-package-manager`, `playwright-cli`, `bats-testing-patterns` and others | Installation steps use `curl ... \| sh`, `npm install -g`, `brew install` or `pip install` of well-known tools. | Kept. The command guard asks before these run. |

## Other observations

- `superpowers:brainstorming` starts a server bound to `127.0.0.1` with a per-session key; its page loads a logo from the author's site, which can be turned off with `SUPERPOWERS_DISABLE_TELEMETRY`.
- `supply-chain-risk-auditor` and `semgrep` (Trail of Bits) ship scripts that call package registries; `semgrep` requires `--metrics=off`.
- `sharp-edges`, `gha-security-review` and `skill-scanner` contain attack examples as reference material, which is why they dominate the raw counts.
- The subagent plugins hold only Markdown definitions: no hooks, MCP servers or scripts. 128 of the 153 VoltAgent definitions that name a model fix it to one vendor tier instead of inheriting the session's. One definition outside the declared sets (`healthcare-admin`) suggests a pipe-to-shell install.
- `sentry:skill-scanner`, in the `agent-tooling` set, applies a similar review to a single skill and is the tool to use before adding a new one.
