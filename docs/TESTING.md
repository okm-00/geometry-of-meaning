# TESTING.md — Testing Philosophy and Conventions

## Principle

Tests are the primary guardrail. They run before code lands in `main` and define what correct
behavior looks like. Logs are the fallback for issues that tests didn't anticipate.

Read this file before writing any test.

## Stack

- **pytest** — test runner
- **httpx** — async HTTP client used by FastAPI's `TestClient`
- Both are dev dependencies in `pyproject.toml`

## Running tests

```bash
make test      # run the full suite
make verify    # test + health check (run after any change or restart)
```

CI runs `make test` on every push and pull request.

## Test layout

```
tests/
├── __init__.py
├── test_story.py    ← unit tests for app/story.py (no network)
└── test_main.py     ← integration tests for app/main.py (mocked generate_story)
```

## What to test at each layer

### Service layer (`tests/test_story.py`)

Unit tests. No network calls — mock the OpenAI client.

Test `_parse_response` (the pure parsing function) exhaustively:
- Happy path: valid JSON → correct `StoryResult`
- Edge cases the LLM may produce: `<think>` blocks, markdown fences
- Every validation rule: missing fields, wrong types, wrong counts

Test `generate_story` for each exception mapping:
- `APIConnectionError` → `LLMConnectionError`
- `APIStatusError` → `LLMResponseError`
- Malformed response → `LLMParseError`

### Route layer (`tests/test_main.py`)

Integration tests using FastAPI's `TestClient`. Mock `generate_story` at the import boundary —
do not call the real LLM.

Test HTTP status codes:
- Success → 200 with schema-valid body
- `LLMConnectionError` → 503
- `LLMResponseError` → 502
- `LLMParseError` → 502

Test the health endpoint:
- Reachable LM Studio → `{"status": "ok"}`
- Unreachable → `{"status": "degraded", "detail": "..."}`

### What not to test here

- Do not write tests that call the real LLM. Those are slow, non-deterministic, and require
  LM Studio to be running. They are not CI-safe.
- Do not test the frontend (`static/index.html`) with pytest. UI behavior is verified manually
  or with a dedicated browser test tool.

## Error taxonomy (what the tests verify)

| Exception class      | Cause                              | HTTP status |
|----------------------|------------------------------------|-------------|
| `LLMConnectionError` | Cannot reach LM Studio             | 503         |
| `LLMResponseError`   | LM Studio returned HTTP error      | 502         |
| `LLMParseError`      | Response not valid/expected JSON   | 502         |

## When to write tests

Per core-belief #9 and AGENTS.md rule #8: test cases are written in the execution plan's
`## Tests` section before implementation begins. If you are implementing a feature without
a `## Tests` section in its exec plan, stop and write one first.

## Verification

After any code change or server restart, run:

```bash
make verify
```

This runs the test suite and hits `GET /health`. A feature is not complete until
`make verify` passes. This is a command, not a checklist — encode verification in
tooling, not in prose (core-belief #10).

After `make verify`, `make triage` shows recent errors and all open TD items together —
use it to decide if anything new needs logging before moving on.

Every exec plan's `## Verification` section must end with this checkbox:

```
- [ ] New observations logged to tech-debt-tracker.md (or nothing to log)
```

This makes the triage step visible and accountable in every plan. An unchecked box
is a signal to the reviewer that the step was skipped.
