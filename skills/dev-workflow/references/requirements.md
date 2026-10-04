# Requirements that can be checked

At standard and strict, every task has acceptance criteria, and they are written so a test can prove each one. Do this before any code, in the plan or the issue.

## Number them
Give each criterion an ID that never changes: `R1`, `R2`… One observable behaviour per ID.

```markdown
## Acceptance criteria
- R1: a wrong password is rejected with 401 and no session cookie
- R2: five failures within 15 minutes lock the account for 15 minutes
- R3: a locked account's error says when it unlocks
```

## Check them before coding
Run this checklist on the list and ask the user about anything that fails (one round of questions, each with a proposed answer):

| Property | Ask | Fails when |
| --- | --- | --- |
| **Verifiable** | Can a test pass or fail on it? | "fast", "user-friendly", "robust", "secure" without a measure; propose one ("p95 under 200 ms on the seed data") |
| **Consistent** | Does it contradict another criterion, the current behaviour or the docs? | Two criteria cannot both hold, or one silently changes documented behaviour |
| **Complete** | Are the unhappy paths covered? | No criterion for errors, empty or boundary input, permissions, concurrency, or the performance and security limits that apply |
| **Traceable** | Does each criterion come from the request, an issue or a decision you can point to? | A criterion nobody asked for (scope creep) or a request with no criterion |

## Trace them
- Each test names the requirement it proves, in its name or a comment: `test_lockout_after_five_failures_R2`, `// R2`.
- The pull request lists requirement → tests → commit:

  | Requirement | Tests | Commit |
  | --- | --- | --- |
  | R1 | `test_wrong_password_R1` | `a1b2c3d` |

- `tack trace` checks it: every requirement in the newest plan has a test that names it, and no test names a requirement that was dropped. Run it before offering to push.

A requirement that changes keeps its ID and its tests change with it; a dropped requirement's tests are removed or re-pointed in the same change.
