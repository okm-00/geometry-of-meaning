# Core Beliefs

Agent-first operating principles for this repository.
These are not suggestions — they are constraints that keep the codebase legible for future agent runs.

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

## 8. Error messages are agent context

When writing custom error messages (exceptions, HTTP responses, log lines),
write them as if they will be read by an agent that has no other context.
Include: what failed, where it failed, and what the expected state was.

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

## 9. Tests define correct behavior — write them before the code

A test suite is not documentation added after the fact. The `## Tests` section of an
execution plan defines acceptance criteria before a line of implementation is written.
If you cannot write the test cases first, the feature is not well-enough understood to implement.
A failing test is a better signal than a bug report. A green CI run is the definition of done.
