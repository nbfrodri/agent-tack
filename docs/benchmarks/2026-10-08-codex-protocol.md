# Codex subscription comparison protocol

Status: environment qualification; outcome results pending.

The owner authorized real Codex evaluations through their ChatGPT subscription on 2026-10-08, replacing the earlier local-only restriction. No API billing credentials are used. Subscription usage is reported as observed tokens and elapsed time, not as a dollar charge or a claim about remaining plan allowance.

## Fixed comparison

- Manifest: [`evals/batches/codex-subscription.json`](../../evals/batches/codex-subscription.json).
- Primary models: `gpt-6-luna` and `gpt-6.1-sol`, both at medium reasoning effort. This is independent of the owner's interactive model selection.
- Conditions: baseline and tack auto; two repetitions of bug-fix, attachments and search for each model, 24 runs total. A fixed seed shuffles the order, with at most two concurrent runs and 600 seconds per run.
- Codex CLI: `0.160.1`. Both conditions use the same [launcher](support/codex-subscription.py), which fixes effort, closes stdin and trusts reviewed installed hook definitions for the invocation. Its permissions profile extends `:workspace` and grants writes to the fixture's `.git` directory, so temporary commits are possible. A command-only probe verified that `.git` writes succeed and writes outside the fixture remain blocked. It records non-secret model/effort observations before the temporary home disappears.
- Environment: a disposable Linux container with no host mounts. Its seccomp configuration permits user namespaces so Codex's bubblewrap sandbox can run; no change is made to the host or interactive Codex configuration. Temporary homes live under `/home/dev/eval-tmp`, outside `/tmp`, where this Codex version refuses to create helper aliases.
- Each session receives a separate HOME/XDG/Codex configuration and the same seeded task. Only subscription authentication crosses into the temporary home. Credentials and full private session records are excluded from published artifacts.

## Interpretation

Hidden acceptance tests are the primary outcome. Report each model/scenario separately, all attempts including timeouts, uncertainty from the small sample, tokens including cache counters, wall-clock time, and process changes separately from correctness. Do not pool the pilot, historical Claude runs, models or incompatible source/configuration fingerprints.

Runtime observations describe the model configuration seen in local Codex sessions, not independent server-side model identification. Keep an unknown cost as unknown; API list prices do not measure subscription consumption. A larger token count can include cached input and should not be presented as the same ratio of paid cost.

An environmental qualification pair failed before commands could run because Docker's default seccomp profile prevented bubblewrap namespaces. Both transcripts and their token consumption are retained as infrastructure attempts; their unchanged fixtures are not evidence for or against tack. A second qualification pair fixed the code in both conditions but exposed two environment gaps: pytest was not preinstalled and default workspace permissions prevented temporary Git commits. The comparison supplies pytest and the scoped Git permission above to both conditions. Qualification attempts are kept separate. Any further setup failures or protocol changes must be recorded before interpreting the final batch.

The target in #100 is evidence-dependent. Publish null or adverse results as such; running a benchmark does not by itself justify increasing the project's score.

## Sources

- [Codex non-interactive execution and JSON usage events](https://learn.chatgpt.com/docs/non-interactive-mode).
- [Subscription pricing and usage: separate from API prices](https://learn.chatgpt.com/docs/pricing).
- [Named filesystem permissions](https://learn.chatgpt.com/docs/config-file/config-reference).
