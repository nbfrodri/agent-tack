# Optional tools: adoption decisions

The aim is useful feedback at a justified cost, not a larger default installation. Source inspection and the following local probe do not establish productivity gains.

## Aislop 0.18.1

Tested the pinned npm package with lifecycle scripts disabled in a disposable Node 22 container (`sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392`). No credentials, AI calls, auto-fixes or installed hooks were used. The selected upstream package manifest requires Node >=20. The source revision inspected was `ec7589f9a97ef6905c0930fcad6e1eeeecd7efb5`; npm version pinning is distinct from building those exact source bytes.

A Python fixture retained a public `parse_setting(value)` entrypoint. Its defective implementation swallowed ValueError and returned None; its corrected implementation returned int(value), letting invalid input raise. Ruff 0.14.0 with its default checks reported no findings for either fixture.

| Input | Aislop result | Assessment |
| --- | --- | --- |
| Swallowed ValueError | `ai-slop/swallowed-exception`, error; score 73; exit 1 | Useful additional finding for the intended contract |
| Correct public wrapper | `ai-slop/thin-wrapper`, warning; score 89; exit 0 | A pattern match, but removing this public entrypoint would violate the intended API |

Three complete scans of each one-file fixture, including docker exec/process startup, took 798–837 ms each. This says nothing about a large repository. Format/lint engines were explicitly skipped because Ruff was absent inside the scanner container; the independent Ruff comparison ran in the existing test image. Missing engines must stay visible.

Decision: offer a pinned, project-selected scan and inspect diagnostics; no automatic installation, score threshold, per-edit hook or repair agent. Calibrate individual rules before making them blocking. A score threshold of 90 would reject the correct public wrapper in this tiny example. Raw outputs/timings remain in ignored `evals/out/aislop-*.json`.

## Skills and workflow tools

- **Ponytail:** much of the inspected skill duplicates tack's existing KISS/YAGNI and minimal-change guidance, and adds persistent levels/reply rules. Keep optional selective installation; do not stack it by default. Its speed claims have not been reproduced with tack.
- **Superpowers:** reuse the idea of clarifying consequential requirements and comparing meaningful alternatives. Its approval stages are an explicit behavior choice, not a default tack requirement. Offer selected skills through the existing installer.
- **Addy Osmani / Matt Pocock:** retain the current project-scoped selection/provenance workflow. No blanket collection install.
- **pre-commit / reviewdog:** reuse a project's chosen hook runner and optional reporting. No new hook manager or issue-creation service.
- **Worktrunk:** optional convenience; native Git worktrees cover the current need.
- **Spec Kit:** an alternative lifecycle to compare, not another mandatory layer.

The [external tools guide](../external-skills.md) links primary sources. No third-party source was copied into tack in this change. Existing guard/secret/history hooks remain; no extra mandatory Git hook earned inclusion from this experiment. More hooks remain a project-specific choice with measured latency and false-positive checks.
