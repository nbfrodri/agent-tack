# 0001. Candidate lessons with a repeat count

- **Date:** 2026-10-05
- **Status:** Accepted (taken autonomously while the owner was away; review welcome)

## Context
`lessons` turns a correction into a versioned rule only when the assistant judges it lasting. A correction made once, or one the user declines to save, is forgotten, so the same correction can repeat across sessions without anyone noticing (issue #43). Learning automatically from transcripts would be opaque and could save rules nobody approved.

## Decision
- The assistant records candidate lessons explicitly with `tack lesson note KEY "rule"` (a short kebab-case key it reuses for the same correction), per project or user-wide (`--global`). A repeat increases its count; `tack lesson contradict KEY` records evidence against it.
- Confidence is a plain score: times seen minus twice the times contradicted. At three sightings with a score of three or more, `tack lesson list` marks it ready; `lessons` then asks the user whether to save it as a rule and, once saved or declined, forgets it (`tack lesson forget KEY`).
- At session start, up to three candidates with a score of at least two, for this project or user-wide, are shown as unconfirmed, lowest priority within the context cap. Nothing becomes a rule without the user.
- Storage is `${XDG_STATE_HOME:-~/.local/state}/agent-tack/lessons.tsv`, private to the user (mode 600), never committed or sent anywhere. The CLI works the same from any assistant.

## Consequences
- Repeated corrections become visible and promotable with one question, in every tool.
- Counting depends on the assistant noting corrections; nothing is inferred from transcripts, so a missed note is a missed count. The `lessons` skill carries the rule to note them.
- Keys are chosen by the assistant; two keys for the same correction split the count. `tack lesson list` shows them side by side so they can be merged by forgetting one.
- Candidates are per machine; a promoted rule is what travels, through the config repository.
