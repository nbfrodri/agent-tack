# Sets

A set is a named bundle of skills, agents and Claude Code plugins for one kind of work: `design`, `testing`, `security`, `backend` and so on. The repository stores the sets, so the same configuration follows you to another machine and to every supported AI tool.

Every active skill adds its description to each session. Activate a set where the work happens instead of everywhere.

## Daily use

```bash
tack set list                  # every set, and where it is active
tack set show design           # what a set contains
tack set use design            # this project only
tack set drop design
tack set use review --global   # every project, applied by the next ./install.sh
tack set sync                  # recreate this project's links (new clone, or after an update)
```

In a project, `use` links each skill into `.agents/skills/` and `.claude/skills/`, each agent into `.claude/agents/`, and installs each plugin for that clone (`claude plugin install --scope local`). The links are added to `.git/info/exclude`, so the project's history and `.gitignore` stay untouched. A skill or agent the project already has under the same name is kept. The choice is saved in the clone's Git config (`tack.sets`), which is why another clone needs `tack set use` or `tack set sync`.

With `--global` the choice is saved in your global Git config and `./install.sh` links the skills into every tool in `targets.txt`, generates the agents for the tools that support them and installs the plugins. Dropping a set and reinstalling removes those links; installed plugins stay, as with `plugins.txt`.

| Item | Project scope | Everywhere |
| --- | --- | --- |
| Skills | Tools that read `.agents/skills` or `.claude/skills` in a repository | Every tool in `targets.txt` |
| Agents | Claude Code | Every tool with an agents folder in `targets.txt` |
| Plugins | Claude Code | Claude Code |

## Let the assistant choose

In an enabled project, the startup context includes one line with the names of every set and which are already active. The contents of a set are not loaded until it is activated, so the index costs a few hundred characters instead of every skill's description.

When a task clearly needs a set that is not active, the assistant runs `tack set use NAME` for that project and says so. It leaves `--global`, `drop` and `update` to you, and activates nothing for a read-only request; in a mode such as `unleash` the command guard refuses those three. A newly linked skill may only appear in the tool's own list in the next session; until then the assistant can read it from `.agents/skills/`.

Turn the index off with `tack config set-index false` (add `--global` for every project). Tools without a startup hook get the same line from `tack context`.

## On another machine

```bash
git clone <your repository> ~/Projects/agent-tack
git config --global tack.sets design,review   # or: tack set use NAME --global after installing
~/Projects/agent-tack/install.sh
```

Which sets are active is local configuration; what each set contains travels with the repository.

## Define a set

`sets.txt` has one line per item:

```
design about   Web interfaces: visual direction, polish and review
design skill   frontend                       # skills/frontend in this repository
design skill   emil:skills/emil-design-eng    # a folder in a collection from sources.txt
design agent   ui-reviewer                    # agents/ui-reviewer.md
design plugin  typescript-lsp@claude-plugins-official
```

`sources.txt` pins each external collection to a full commit:

```
emil  https://github.com/emilkowalski/skills  e8a175de22ae1e49370fc144c1f3bb9aeedf988d
```

A source is an `https` URL or an absolute path to a local repository. Two different skills may not share a name, and a plugin's marketplace must be declared in `plugins.txt`. `tack set check` validates both files; `tack set check --fetch` also downloads every source and confirms each skill exists at its pin.

## Update a collection

```bash
tack set update          # every source
tack set update emil     # one source
```

It reads the upstream head, reports which of the skills you use changed (with a ready `diff -ru` command) and rewrites the commit in `sources.txt`. Review the changes, commit, then run `./install.sh` and `tack set sync`. A source that no longer has a skill you use keeps its pin and is reported.

## What is and is not checked

Skills run with the assistant's permissions. Pinning means a skill changes only when you move its commit; it is not a review of what the skill says or runs. Read a skill before relying on it, and prefer few focused sets. tack refuses a skill path that leaves its checkout, runs Git without hooks or prompts while fetching, and links nothing when a source or skill is missing.

The [audit of 2026-10-11](audits/2026-10-11-external-skills.md) records what a scan of every used skill found at the current pins, including one skill that downloads and runs a native binary. Repeat it after moving a pin.

Checkouts live in `~/.local/share/agent-tack/sources/<name>/<commit>` (or under `XDG_DATA_HOME`). Nothing from a collection is copied into this repository, and each one keeps its own license in its checkout. Old checkouts are not deleted automatically; remove a commit's folder once nothing links to it.

Do not install the same collection both as a Claude Code plugin and through a set: the tool would list each skill twice.

## Subagent teams

The `agents-*` sets install plugins from two subagent collections, [VoltAgent](https://github.com/VoltAgent/awesome-claude-code-subagents) and [wshobson](https://github.com/wshobson/agents), whose marketplaces are declared in `plugins.txt`. They reach Claude Code only. Each plugin brings several specialists and every one adds its description to the session, so use them per project (`tack set use agents-quality`). Unlike skills from `sources.txt`, marketplace plugins follow their latest version and are not pinned. In a project, a plugin can be installed only after `./install.sh` has added its marketplace once.

## Collections in sources.txt

| Source | Repository | Used for |
| --- | --- | --- |
| `impeccable` | pbakaus/impeccable | Interface design language and audits |
| `emil` | emilkowalski/skills | Interface polish and motion |
| `taste` | Leonxlnx/taste-skill | Visual taste and alternative aesthetics |
| `addy` | addyosmani/agent-skills | Engineering lifecycle from spec to ship |
| `anthropics` | anthropics/skills | Frontend design, skill and MCP authoring, web app testing |
| `vercel`, `vercel-skills` | vercel-labs/agent-skills, vercel-labs/skills | React, web guidelines, deployment, skill discovery |
| `mattpocock` | mattpocock/skills | TDD, grilling an idea, specs and tickets |
| `superpowers` | obra/superpowers | Brainstorming, plans, parallel agents |
| `trailofbits` | trailofbits/skills | Static analysis, security review, stronger tests |
| `sentry` | getsentry/skills | Bug finding, pull requests, skill auditing |
| `wshobson` | wshobson/agents | Language, database, accessibility and LLM patterns |
| `openai` | openai/skills | CI fixes, review comments, threat models, notebooks |
| `supabase`, `stripe` | supabase/agent-skills, stripe/ai | Postgres, hosted backend and payments |
| `cloudflare`, `hashicorp` | cloudflare/skills, hashicorp/agent-skills | Edge deployment and Terraform |
| `expo`, `callstack` | expo/skills, callstackincubator/agent-skills | Expo and React Native |
| `antfu` | antfu/skills | Vue, Nuxt and Vite |
| `remotion`, `playwright` | remotion-dev/skills, microsoft/playwright-cli | Video and browser automation |
| `huggingface` | huggingface/skills | Models and datasets |
| `knowledge-work` | anthropics/knowledge-work-plugins | Data analysis, product and design research |
