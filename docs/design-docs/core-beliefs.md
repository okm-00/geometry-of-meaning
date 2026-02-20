# Core Beliefs

Agent-first operating principles for this repository.
These are not suggestions — they are design requirements that shape how the system is built.
The goal is autonomous agent operation: humans steer intent, agents execute and self-validate.

## 1. The repository is the system of record

Any decision, convention, or constraint that is not in this repository effectively does not exist.
Slack discussions, mental models, and verbal agreements must be translated into docs/ artifacts
before they can influence agent behavior.

## 2. Configuration is never hardcoded

URLs, model names, timeouts, feature flags — all via environment variables.
`app/config.py` is the single place where env vars are read.
No other file may call `os.environ` or `os.getenv` directly.

## 3. Prompt construction is co-located with LLM logic

All prompt templates live in `app/story.py`.
Routes (`app/main.py`) must not build or modify prompts.
This keeps prompts testable and discoverable in one place.

## 4. Parse at the boundary

LLM responses are untrusted strings. `app/story.py` is responsible for parsing and validating
the JSON structure before returning a typed result to the route layer.
If parsing fails, raise a clear exception with enough context to debug the prompt.

## 5. Flat is better than clever

The architecture has one domain and three layers. This is intentional.
Do not introduce new abstraction layers without a documented design decision in `docs/design-docs/`.
The goal is that any agent can understand the full codebase by reading three files.

## 6. Boring technology compounds

Prefer dependencies that are stable, widely documented, and well-represented in LLM training data.
Avoid dependencies that require reading obscure changelogs or have unstable APIs.
Current stack (FastAPI, openai SDK, uv) was chosen for this reason.

## 7. Docs are first-class artifacts

Before implementing a non-trivial change, write an execution plan in `docs/exec-plans/active/`.
After completing it, move it to `docs/exec-plans/completed/` and update relevant docs.
Technical debt is logged in `docs/exec-plans/tech-debt-tracker.md` immediately when identified.

## 8. All runtime state is directly agent-accessible

Every runtime signal must be machine-readable and reachable in-context — no human relay.

- **Errors**: typed exception classes carry structured context (what failed, where, expected state).
  HTTP error responses are always `{ "detail": "..." }` JSON, never raw tracebacks.
- **Logs**: persistent, structured, tailable via `make logs`. `make triage` surfaces recent errors
  and open TD items in a single command.
- **Health**: `GET /health` returns structured JSON. `make health` wraps it for agent invocation.
- **Validation**: `make verify` runs the full test + health loop and exits non-zero on failure.

If an agent needs a human to copy-paste a terminal output into a prompt, that is a design failure.
When adding a new failure mode, ask: can an agent read this signal directly and act on it?

## 9. The feedback loop closes without human relay

`make verify` is the canonical feedback loop. After any change, an agent must be able to run it,
interpret the output, and either confirm correctness or diagnose and fix the failure — without
escalating to a human for context.

This is not a convenience. It is a design requirement. Every new feature must satisfy it:

- The test suite must cover its correctness (`make test`).
- The health endpoint must remain green after the change (`make health`).
- Any new failure mode must produce output that is actionable without human interpretation.

If `make verify` passes, the change is correct. If it fails, the agent has everything it needs.
If an agent cannot self-validate, the system is incomplete — fix the system, not the agent.

## 10. Encode constraints in tooling, not in documentation

If an operational rule can be expressed as a command, it must be a command — not a rule
that an agent reads and is expected to remember. Documentation that says "always do X"
is a smell; a tool that does X automatically is the fix.

Examples of this principle applied:
- "Tests must pass before merging" → CI blocks the merge (not a rule in AGENTS.md)
- "Verify health after restart" → `make verify` runs it (not a checklist to follow)
- "Use the right command flags" → `make run` encodes them (not prose to memorize)

When you find yourself writing "always remember to..." in a doc, stop and ask whether
a Makefile target, a CI step, or a startup check can enforce it instead.

## 11. Tests define correct behavior — write them before the code

A test suite is not documentation added after the fact. The `## Tests` section of an
execution plan defines acceptance criteria before a line of implementation is written.
If you cannot write the test cases first, the feature is not well-enough understood to implement.
A failing test is a better signal than a bug report. A green CI run is the definition of done.
