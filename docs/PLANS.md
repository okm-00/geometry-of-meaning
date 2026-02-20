# PLANS.md — Execution Plan Guide & Index

## What is an execution plan?

An execution plan (ExecPlan) is a living document that records intent, design decisions,
and verification evidence for a non-trivial change. It is written before work starts and
updated continuously as work proceeds.

A plan is not a ticket or a to-do list. It is a self-contained document: a future agent
or human must be able to read it alone, reproduce the work, and verify the result.

## When to write one

Write a plan before starting any change that:
- touches more than three files, or
- introduces a new concept (new dependency, new DB table, new endpoint), or
- takes more than a few minutes to reason about.

Prompt changes, single-line fixes, and documentation edits do not need plans.

## How to create a plan

1. Read [`docs/exec-plans/PLANS.md`](exec-plans/PLANS.md) in full.
2. Copy the skeleton at the bottom of that file into `docs/exec-plans/active/<slug>.md`.
3. Fill in the `Validation and Acceptance` section (expected values) before touching any code.
4. Work through the plan, updating `Progress`, `Decision Log`, and `Surprises` as you go.
5. Fill in actual `make test` and `make smoke` output in `Validation and Acceptance`.
6. Only when both pass with actual output recorded: move the file to
   `docs/exec-plans/completed/` and update the index below.

## The Validation and Acceptance section is the exit gate

A plan is not complete until `Validation and Acceptance` contains:
- actual `make test` output (all passed, 0 warnings)
- actual `make smoke` output (all endpoints behaving as expected)
- a completed manual acceptance step

No exceptions.

---

## Active plans

| Plan | File | Started |
|------|------|---------|
| A/B Scaffold | [active/ab-scaffold.md](exec-plans/active/ab-scaffold.md) | 2026-02-20 |
| Session DB & Compare UI | [active/session-db.md](exec-plans/active/session-db.md) | 2026-02-20 |

## Completed plans

| Plan | File | Completed |
|------|------|-----------|
| Initial build | [completed/initial-build.md](exec-plans/completed/initial-build.md) | 2026-02-19 |
| Error handling guardrails | [completed/error-handling.md](exec-plans/completed/error-handling.md) | 2026-02-20 |
