# Shared preferences

Project instructions take precedence. Reply in the user's language; follow the project's language for code and documentation. Lead with the outcome, relevant verification and unresolved limits; default to a brief response.

Never add AI attribution or AI coauthor trailers to commits, PRs, issues or changelogs. Respect existing authorization for publication and Git operations; otherwise prepare the result before asking. Do not bypass a rejected hook. Read-only requests stay read-only.

## In enabled projects

Use supplied startup context; if it is absent, query `tack context` once. Reuse project instructions already loaded by the tool. Read canonical contracts and affected callers when needed, not every document at startup.

Apply KISS/YAGNI and pragmatic SOLID: the smallest complete change, useful responsibilities and no speculative abstractions. Work on a branch, preserve unrelated edits, use meaningful tests and Conventional Commits, and update documentation made inaccurate. Use red/green for behavioral changes; existing checks may suffice for a trivial edit. Never weaken behavior to satisfy outdated tests.

Run the project's relevant checks. `tack verify --plan` selects declared commands without running them; execution requires local trust. For integration, `tack team` inspects locally known branches; a clean Git merge is not proof of compatible behavior. Report failures and unverified areas.

For implementation needing a plan or risk-specific review, use `dev-workflow` and only its relevant references. Task modes control effort, not the number of artifacts to create. Reuse settled decisions and check results while their inputs remain valid; ask about genuine unresolved choices. Specialist skills and agents are optional; their absence does not block ordinary work.

For requested initialization, use `new-project`: inspect existing conventions, propose useful additions and apply approved choices. Keep shared project preferences separate from local trust and personal overrides. Create project-local skills or roles only for a demonstrated reusable need; global promotion needs separate authorization.
