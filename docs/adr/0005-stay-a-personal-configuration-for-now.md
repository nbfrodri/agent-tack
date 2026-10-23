# 0005: Promote tack as a personal setup, and decide on a product later

- Status: accepted (2026-10-23). Builds on [0004](0004-personal-configuration-with-sets.md); it does not supersede it.

## Context

After v0.2.0 the owner prepared to promote the repository: a comparison with Everything Claude Code ([`docs/comparison.md`](../comparison.md)), a README demo, a longer post and texts for several channels, and an improved GitHub description and preview image. The owner asked what presenting tack as a product, rather than as a personal setup, would change.

The evidence behind 0004 has not changed: six comparisons between 2026-10-03 and 2026-10-09 did not show better code than a short project `AGENTS.md`, and the last measured 5% to 62% more time and 25% to 68% more input tokens. Nothing measured since contradicts it. Promoting a setup that others may read or fork is consistent with that; claiming general quality or adoption is not.

## Decision

- Keep 0004 in force. Promote tack as one person's configuration, public to read or fork, and say so in every text. The honest part of the evidence, what did not work, belongs in the promotion.
- Do not present tack as a product for now. The owner will decide later ("it will be seen"); this record exists so that decision starts from a known list instead of from scratch.
- First review point: about four weeks after the first public post. Look at stars, forks, clones and traffic (`gh api repos/nbfrodri/agent-tack/traffic/views` and `.../traffic/clones`) and at issues or pull requests opened by people other than the owner. No threshold is set; the owner judges whether there is real interest.

## What presenting tack as a product would change

None of this is started. It is the list to start from, ordered by how much each item blocks the claim.

1. **Evidence of value.** A new, reproducible evaluation of what does seem to work (the command guard, check selection from a diff, the critic role), published with its method and its costs. Without it a product claim contradicts this repository's own measurements.
2. **A new ADR superseding 0004**, naming who tack is for and what is a stable interface: the `tack` command, `tack.json` and `sets.txt`.
3. **Stability for other people.** A deprecation and migration policy instead of "a fork is the supported way to diverge"; neutral defaults in place of the owner's (modes, reply style, active sets: not yet audited, so unknown which are personal). Each contract change, such as the exit code of a timed-out check in v0.2.0, would need notice.
4. **Consent before downloads.** 0004 let the installer download the external collections of an active set, because the owner chose them. For others the earlier rule would have to return: nothing from third parties is downloaded unless the user chose it. Each pinned collection also remains a supply-chain surface to review, with its own license.
5. **Onboarding.** A one-command install, a `tack init` that needs no reading, and a replacement for the collaborator bootstrap that was removed on 2026-10-12.
6. **Operation and support.** Seven tools whose versions change (a weekly compatibility check exists but someone has to act on it), native Windows still experimental, a full suite of about 22 minutes in CI, issue and discussion templates, triage and a roadmap. `SECURITY.md` already exists.
7. **Identity.** A stable name, a landing page and a release rhythm. Whether the name clashes with other projects has not been checked.

Not changing in any case: the design that keeps tack independent of a model or editor, and rules living in `AGENTS.md` and skills.

## Consequences

- Texts, the README and channel submissions describe a personal configuration and make no claim about code quality or adoption. A submission that asks for proven community use (for example `VoltAgent/awesome-agent-skills`) waits until outside users exist.
- The product decision costs nothing until it is taken, but the longer the repository carries no outside users, the less there is to base it on. The four-week review is the first chance to see.
- If the owner decides yes, step 1 comes first and the rest follow in the order above; the ADR that supersedes 0004 is written before any product claim is published.
