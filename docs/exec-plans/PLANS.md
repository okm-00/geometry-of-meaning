# Execution Plans (ExecPlans) — Format and Requirements

This document describes the requirements for an execution plan ("ExecPlan"), a design
document that a coding agent can follow to deliver a working feature or system change.
Treat the reader as a complete beginner to this repository: they have only the current
working tree and the single ExecPlan file you provide. There is no memory of prior plans
and no external context.

## How to use ExecPlans and this file

When **authoring** an ExecPlan, follow this file to the letter. If it is not in your
context, refresh your memory by reading it in full before writing a single line. Be
thorough in reading source material to produce an accurate specification. Start from the
skeleton below and flesh it out as you research.

When **implementing** an ExecPlan, do not prompt the user for next steps — proceed to
the next milestone. Keep all sections up to date. Add or split entries in Progress at
every stopping point to record what was done and what comes next. Resolve ambiguities
autonomously. Commit frequently.

When **discussing** an ExecPlan, record decisions in the Decision Log for posterity.
It must be unambiguously clear why any change to the specification was made. ExecPlans
are living documents: it must always be possible to restart from only the ExecPlan and
no other context.

## Requirements

NON-NEGOTIABLE:

- Every ExecPlan must be fully self-contained. Self-contained means it contains all
  knowledge and instructions a novice needs to succeed, with no references to external
  documents for essential facts.
- Every ExecPlan is a living document. Revise it as progress is made, discoveries occur,
  and design decisions are finalized. Each revision must remain fully self-contained.
- Every ExecPlan must produce demonstrably working behavior, not merely code changes that
  "meet a definition". Proof is a human observing the system do something.
- Every ExecPlan must define every term of art in plain language.

Purpose and intent come first. Begin by explaining, in a few sentences, why the work
matters: what someone can do after this change that they could not do before, and how to
see it working. Then guide the reader through the exact steps, what to edit, what to run,
and what to observe.

The agent executing your plan can read files, search, run the project, and run tests. It
does not know prior context. Repeat any assumption you rely on. Do not point to external
documents for essential facts — embed the knowledge here.

## Formatting

Write in plain prose. Prefer sentences over lists. Avoid checklists, tables, and long
enumerations unless brevity would obscure meaning. Checklists are permitted only in the
Progress section, where they are mandatory. Narrative sections must remain prose-first.

When showing commands, transcripts, diffs, or code, use indented blocks (four spaces),
not code fences — code fences inside a plan file cause formatting problems.

## Guidelines

Self-containment and plain language are paramount. Define every non-ordinary term
immediately when you first use it ("database layer" means `app/db.py`, for example).
Do not say "as defined previously" or "see ARCHITECTURE.md" — include the needed
explanation here, even if you repeat yourself.

Anchor the plan with observable outcomes. State what the user can do after implementation,
the commands to run, and the outputs they should see. Phrase acceptance as behavior a
human can verify, not internal attributes. "After starting the server, navigating to
http://localhost:8000/health returns HTTP 200 with status: ok" is acceptable. "Added a
health check handler" is not.

Specify repository context explicitly. Name files with full repository-relative paths,
name functions and modules precisely. When running commands, state the working directory.
When outcomes depend on environment, state the assumptions.

Be idempotent and safe. Write steps that can be repeated without causing damage. If a
step can fail halfway, include how to retry or adapt. Prefer additive, testable changes.

Validation is not optional. Include instructions to run tests, start the system, and
observe it doing something useful. State exact test commands and expected outputs.
Include expected error messages so a novice can tell success from failure.

Capture evidence. When steps produce terminal output, include concise excerpts that
prove success.

## Milestones

Milestones are narrative, not bureaucracy. Introduce each with a paragraph describing
the scope, what will exist at the end that did not before, the commands to run, and the
acceptance to observe. Keep it readable as a story: goal, work, result, proof. Never
abbreviate a milestone for brevity — details that seem obvious now may be crucial later.

Each milestone must be independently verifiable and incrementally implement the overall
goal.

## Living plans and design decisions

ExecPlans must contain and maintain a Progress section, a Surprises & Discoveries
section, a Decision Log, and an Outcomes & Retrospective section. These are not optional.
When you discover unexpected behavior, performance tradeoffs, or bugs that shaped your
approach, capture them in Surprises & Discoveries with short evidence snippets. If you
change course mid-implementation, document why in the Decision Log. At completion, write
an Outcomes & Retrospective entry summarizing what was achieved, what remains, and
lessons learned.

## Validation and Acceptance — repo-specific requirements

This section exists in every ExecPlan for this repository. It has a fixed structure.
Fill in the "expected" fields before writing any code. Fill in the "actual" fields by
pasting real terminal output before marking the plan complete. A plan is not complete
until both fields are filled.

The repo's test and smoke commands are:

    cd /path/to/geometry-of-meaning

    make test     # unit tests — no server or LM Studio needed
    make smoke    # live endpoint tests — requires `make run` and LM Studio running
    make verify   # runs make test then make smoke

**Critical rule:** if this plan changes any HTTP endpoint (adds, removes, or renames a
route, or changes a request/response shape), update the `smoke` target in `Makefile`
**before touching any other file**. A stale smoke target is the same as no smoke target.

In the plan's Validation and Acceptance section, record:

1. The expected `make test` result (e.g. "45 passed, 0 warnings").
2. The actual `make test` output — pasted verbatim, trimmed to the summary line.
3. The expected `make smoke` result for each endpoint touched by this plan.
4. The actual `make smoke` output — pasted verbatim, trimmed to relevant lines.
5. A manual acceptance step: one sentence describing what a human does in the browser
   or terminal to confirm the feature works end-to-end, and what they should observe.

---

## Skeleton

Copy everything below this line into `docs/exec-plans/active/<slug>.md` and fill it in.

---

# ExecPlan: <Short, action-oriented title>

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, Validation and Acceptance, and Outcomes & Retrospective must be kept up
to date as work proceeds. This document is maintained in accordance with
`docs/exec-plans/PLANS.md`.

## Purpose / Big Picture

Explain in a few sentences what someone gains after this change and how they can see it
working. State the user-visible behavior you will enable.

## Context and Orientation

Describe the current state as if the reader knows nothing. Name the key files by full
repository-relative path. Define any non-obvious term you will use. Do not refer to
other documents for essential facts — include them here.

Key files relevant to this plan:

- `path/to/file.py` — what it does and why it matters here

## Plan of Work

Describe, in prose, the sequence of edits and additions. For each change, name the file,
the function or location, and what to insert or modify. Keep it concrete. Explain the
why for every non-obvious decision.

## Progress

Use checkboxes. Every stopping point must be recorded here, even if it requires splitting
a partially completed step. Use timestamps for longer tasks.

- [ ] (YYYY-MM-DD HH:MMZ) Step one
- [ ] Step two

## Concrete Steps

State the exact commands to run and the working directory. When a command produces
output, show a short expected transcript so the reader can compare. Update this section
as work proceeds.

    cd /Users/oskar.marszalek/repos/geometry-of-meaning
    make test
    # Expected: N passed, 0 warnings

## Surprises & Discoveries

Document unexpected behaviors, bugs, or insights discovered during implementation.

- Observation: ...
  Evidence: ...

## Decision Log

Record every non-obvious decision.

- Decision: ...
  Rationale: ...
  Date: YYYY-MM-DD

## Validation and Acceptance

This section must be filled before writing any code (expected) and before closing the
plan (actual). See `docs/exec-plans/PLANS.md` for the repo-specific requirements.

If this plan changes any HTTP endpoint, confirm here that `make smoke` in `Makefile`
was updated first: [ ] yes

### Unit tests

Expected: N passed, 0 warnings (state the expected count before starting).

Actual (paste `make test` summary line when done):

    [paste here]

### Smoke test

Expected behavior for each endpoint touched by this plan:

- `GET /health` → HTTP 200, `{"status": "ok", ...}`
- `POST /api/session` → HTTP 200, session_id present, baseline + harness bodies non-empty
- `POST /api/feedback` → HTTP 200, `{"status": "ok"}`

Actual (paste relevant `make smoke` output when done):

    [paste here]

### Manual acceptance

One sentence describing what a human does in the browser or terminal to confirm the
feature works end-to-end, and what they should observe.

Steps:
1. ...

Expected result: ...

## Idempotence and Recovery

State whether steps can be run multiple times safely. If any step is risky or
destructive, provide a safe retry or rollback path.

## Outcomes & Retrospective

Fill when the plan is complete. What was achieved vs. what was planned. What gaps remain.
What a future agent should know before touching this area again.
