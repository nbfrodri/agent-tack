---
name: debugging
description: Systematic debugging method - reproduce, isolate, form hypotheses, verify with evidence, fix the root cause and lock it in with a regression test. Use whenever something is broken, failing, crashing, slow, flaky or behaving unexpectedly - a bug report, a stack trace, a failing test or CI job, "no funciona", "da error", "a veces falla" - even if the user only pastes an error message.
---

# Debugging

The goal is to fix the root cause, not the symptom, and to prove it. Guessing and patching until the error disappears usually hides the bug somewhere else, so work from evidence.

## 1. Reproduce
Get a reliable reproduction before changing anything: the exact command, input, environment and the actual vs. expected result. If it can't be reproduced, gather more data (logs, versions, config, recent changes) instead of guessing. For flaky failures, run it in a loop and look for what varies: timing, ordering, shared state, randomness, the clock, the network.

## 2. Write the failing test
Turn the reproduction into an automated test that fails now. It becomes the definition of "fixed" and protects against regressions (this is the TDD red step).

## 3. Isolate
Shrink the problem until the cause is obvious:
- Read the full error and stack trace: the first frame in the project's own code is usually where to look.
- Check what changed recently: `git log -p`, `git diff`, dependency updates. `git bisect` finds the breaking commit fast when there is a known good version.
- Cut the input or code path in half until the failure disappears.
- Add temporary logging or use a debugger to compare the real values with your assumptions.

## 4. Hypothesise and verify
Write the hypothesis down ("X is null because Y runs before Z") and design a check that would prove it wrong. Change one thing at a time. If the evidence contradicts the hypothesis, drop it rather than bending the evidence.

## 5. Fix the root cause
Fix where the defect originates, not where it surfaces. Ask whether the same mistake exists elsewhere (search for the pattern). Avoid broad try/catch, retries or sleeps that only mask the problem, unless the root cause really is external and you say so.

## 6. Verify and clean up
- The new test passes, and so does the full suite.
- Remove temporary logging and debug code.
- Commit as `fix(<scope>): <what was wrong>`, with a body explaining the root cause and how it was found.
- Tell the user the cause, the fix, how you verified it, and any related risks you noticed.
