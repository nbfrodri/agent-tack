# Sets

A set is a named bundle of skills, agents and Claude Code plugins for one kind of work: `design`, `testing`, `security`, `backend` and so on. The repository stores the sets, so the same configuration follows you to another machine and to every supported AI tool.

Sets are the only way a skill or an agent gets installed. One set, `core`, is always active: it holds the workflow and project setup skills that the global instructions name. Everything else, including this repository's own skills and agent roles, arrives with a set you activate. `tack-skills` and `tack-agents` bring every skill or every role of this repository at once, without the external collections or the subagent plugins. They are compatibility sets for a former full-catalog choice: they group by origin, not by the work at hand, so the startup index does not offer them to the assistant. `engineering-lifecycle`, Addy Osmani's complete method, is kept there too: it is an alternative to this repository's workflow for a whole project, which is yours to choose.

Every active skill adds its description to each session. Activate a set where the work happens instead of everywhere.

## Daily use

```bash
tack set list                  # every set, and where it is active
tack set show design           # what a set contains
tack set use design            # this project only
tack set drop design
tack set use review --global   # every project, applied by the next ./install.sh
tack set sync                  # recreate this project's links (new clone, or after an update)
tack set suggest               # sets that fit this project's files; --apply activates, --skip declines
tack set skip NAME             # stop suggesting one set in this project
```

In a project, `use` links each skill into `.agents/skills/` and `.claude/skills/`, each agent into `.claude/agents/`, and installs each plugin for that clone (`claude plugin install --scope local`). The links are added to `.git/info/exclude`, so the project's history and `.gitignore` stay untouched. A skill or agent the project already has under the same name is kept. The choice is saved in the clone's Git config (`tack.sets`), which is why another clone needs `tack set use` or `tack set sync`.

With `--global` the choice is saved in your global Git config and `./install.sh` links the skills into every tool in `targets.txt`, generates the agents for the tools that support them and installs the plugins. Dropping a set and reinstalling removes those links; installed plugins stay, as with `plugins.txt`.

| Item | Project scope | Everywhere |
| --- | --- | --- |
| Skills | Tools that read `.agents/skills` or `.claude/skills` in a repository | Every tool in `targets.txt` |
| Agents | Claude Code | Every tool with an agents folder in `targets.txt` |
| Plugins | Claude Code | Claude Code |

## How a set reaches the work

Three steps, measured on small real tasks with a small and a larger model (2026-10-12):

1. **tack finds the sets that fit.** A set can declare the files that give a project away (`python match pyproject.toml`, `react match package.json:react`). `tack set suggest` lists the sets whose rules this project satisfies, with the evidence; `tack enable` prints the same list.
   A set for a kind of task leaves no trace in the files, so it declares what a request for it says instead (`security ask threat+model* owasp modelo+de+amenazas`). A term is a word, `word*` for the words that start with it, or `word+word` for a phrase; a request is compared whole word by whole word, in lowercase and without accents, so `review` never matches "preview". The terms are English and Spanish, and deliberately narrow: a phrase such as `review+this+branch` rather than a word ordinary requests also use.
2. **You say yes once.** With each message, tack tells the assistant which fitting sets are not active, and the assistant ends its reply with one line naming them. Answer yes and it runs `tack set suggest --apply`; `tack set suggest --skip` declines them for this project and ends the reminder. A set whose rules start to match later is offered again. A set the request asks for is named the same way, only with the messages that say one of its terms: `tack set use NAME` activates it and `tack set skip NAME` stops the suggestion in this project.
3. **The assistant loads the matching skills.** With each message, tack names the skills of the project's active sets and asks the assistant to load the ones whose name matches the task before doing anything else.

What the trials showed, and why the steps are split this way:

| Left to the assistant | Result |
| --- | --- |
| Activating a set because the startup context lists it, or orders it | Never (0 of 18) |
| Activating a set when the user asks | Yes (2 of 2) |
| Using the skills of an active set, with no reminder | Small model never (0 of 10); larger one on a specialised task only (1 of 3) |
| Using them with the reminder next to the message | Yes (6 of 6 with the small model) |
| Telling the user which sets fit | Yes (3 of 3) |
| Telling the user which set a request asks for, in English and Spanish | Yes (4 of 4), and nothing on requests that ask for none (2 of 2) |

An assistant loads a skill readily but does not change the project's configuration on its own, so activation stays a choice it reports and you make. The samples are small: one run per case, simple tasks.

Claude Code gets the reminder with every message, through a hook. Tools without such a hook get it once, in the startup context from `tack context`; a real Codex session read the matching skills first. Turn the reminder off with `tack config disabled-hooks skill-reminder`, and the startup index with `tack config set-index false`. In a mode such as `unleash`, where nobody confirms each step, the command guard lets the assistant read sets and suggestions but not change them.

Sets for a kind of task rather than a stack (`review`, `planning`, `security`) have no files to detect: their `ask` terms name them when a request says one, and `tack set use NAME` activates one at any time. The terms are narrow on purpose, so a request worded another way names nothing; widen a set's `ask` line when that happens to you. Tools without a per-message hook get no request suggestions, because the startup context is written before any request.

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
design about     Web interfaces: visual direction, polish and review
design category  interfaces                     # groups the list and the startup index
design skill   frontend                       # skills/frontend in this repository
design skill   emil:skills/emil-design-eng    # a folder in a collection from sources.txt
design agent   ui-reviewer                    # agents/ui-reviewer.md
python match   pyproject.toml                 # the set fits a project that has this file
react  match   package.json:react             # ...or whose manifest names this dependency
shell  match   *.sh 3                         # ...or that has at least three such files
design plugin  typescript-lsp@claude-plugins-official
```

`sources.txt` pins each external collection to a full commit:

```
emil  https://github.com/emilkowalski/skills  e8a175de22ae1e49370fc144c1f3bb9aeedf988d
```

Names are lowercase letters, digits and hyphens; choose one that tells an assistant when the set applies. A source is an `https` URL or an absolute path to a local repository. Two different skills may not share a name, and a plugin's marketplace must be declared in `plugins.txt`. `tack set check` validates both files; `tack set check --fetch` also downloads every source and confirms each skill exists at its pin.

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

Within a set, one voice per job. An external skill that prescribes how to work (its own TDD cycle, planning ritual, review procedure or completion check) competes with this repository's workflow, so the sets leave those out and keep external skills that add knowledge or a tool. Reference material that two collections cover is listed once, from the more complete one.

A skill belongs in a set only if its instructions are in the pinned checkout. One that tells the assistant to download its rules when it runs follows whatever that address serves that day, so the pin no longer says what the skill does.

## Subagent teams

The `agents-*` sets install plugins from two subagent collections, [VoltAgent](https://github.com/VoltAgent/awesome-claude-code-subagents) and [wshobson](https://github.com/wshobson/agents), whose marketplaces are declared in `plugins.txt`. They reach Claude Code only. Each plugin brings several specialists and every one adds its description to the session, so use them per project (`tack set use agents-quality`). Unlike skills from `sources.txt`, marketplace plugins follow their latest version and are not pinned. In a project, a plugin can be installed only after `./install.sh` has added its marketplace once.

## Collections in sources.txt

| Source | Repository | Used for |
| --- | --- | --- |
| `impeccable` | pbakaus/impeccable | Interface design language and audits; its own set, because it runs a downloaded binary |
| `emil` | emilkowalski/skills | Interface polish and motion |
| `taste` | Leonxlnx/taste-skill | Visual taste and alternative aesthetics |
| `addy` | addyosmani/agent-skills | Engineering lifecycle from spec to ship |
| `anthropics` | anthropics/skills | Frontend design, skill and MCP authoring |
| `vercel`, `vercel-skills` | vercel-labs/agent-skills, vercel-labs/skills | React rules and composition, React Native, view transitions, skill discovery |
| `mattpocock` | mattpocock/skills | Grilling an idea, specs, tickets and writing for agents |
| `superpowers` | obra/superpowers | Dispatching parallel agents |
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
