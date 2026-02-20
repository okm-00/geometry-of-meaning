# Execution Plan: Error Handling Guardrails

**Status**: completed
**Started**: 2026-02-20

## Goal

Replace the reactive, undifferentiated error handling with a systematic quality gate:
typed exceptions, HTTP status codes that reflect failure mode, a test suite that gates merges,
CI on GitHub Actions, and persistent error-level logging for post-deploy observability.

## Background

The `<think>` block bug (Qwen3 reasoning mode) exposed that the app had no
systematic way to surface runtime errors. The bug was only discovered because a human
reported it, and only diagnosed by manually reading a live terminal. This plan closes
that gap at every layer.

## Steps

- [x] Write `docs/exec-plans/active/error-handling.md` (this file)
- [x] Update agentic instruction layer: `AGENTS.md`, `docs/design-docs/core-beliefs.md`, create `docs/TESTING.md`
- [x] Add typed exceptions to `app/story.py`; add `LM_STUDIO_TIMEOUT_SECONDS` to config
- [x] Update `app/main.py`: HTTP status mapping, `GET /health`, logging to `logs/app.log`
- [x] Write `tests/test_story.py` and `tests/test_main.py`; add `pytest`+`httpx` to `pyproject.toml`
- [x] Add `.github/workflows/ci.yml`
- [x] Update `ARCHITECTURE.md`, `QUALITY_SCORE.md`, `RELIABILITY.md`, `tech-debt-tracker.md`, `.gitignore`

## Tests (acceptance criteria as test cases)

### `tests/test_story.py` — unit, no network

`_parse_response`:
- valid JSON → returns `StoryResult` with correct fields
- `<think>...</think>` block present → stripped, JSON parsed correctly
- markdown fences present → stripped, JSON parsed correctly
- missing `body` field → raises `LLMParseError`
- missing `endings` field → raises `LLMParseError`
- `body` with fewer than 2 items → raises `LLMParseError`
- `endings` with ≠ 2 items → raises `LLMParseError`
- non-string paragraph in `body` → raises `LLMParseError`
- completely invalid JSON → raises `LLMParseError`

`generate_story` (mocked OpenAI client):
- `APIConnectionError` raised → `LLMConnectionError` raised with LM Studio URL in message
- `APIStatusError` raised → `LLMResponseError` raised with status code and model name
- valid response → returns `StoryResult`

### `tests/test_main.py` — FastAPI integration, mocked `generate_story`

- `POST /api/story` success → HTTP 200, body matches `StoryResponse` schema
- `POST /api/story` + `LLMConnectionError` → HTTP 503, `detail` non-empty
- `POST /api/story` + `LLMResponseError` → HTTP 502, `detail` non-empty
- `POST /api/story` + `LLMParseError` → HTTP 502, `detail` non-empty
- `GET /health` when LM Studio reachable → HTTP 200, `{"status": "ok"}`
- `GET /health` when LM Studio unreachable → HTTP 200, `{"status": "degraded", "detail": ...}`

## Verification

```bash
make verify
make triage
```

- `make test` — all 21 tests pass
- `make health` — returns `{"status": "ok", "lm_studio": "reachable"}`
- [x] New observations logged to tech-debt-tracker.md — TD-4 added (test runs write to logs/app.log)

## Decisions made

- TD-2 (no timeout) resolved by `LM_STUDIO_TIMEOUT_SECONDS` config var (default 60s)
- HTTP 503 vs 502: 503 = our dependency is down (caller should retry later);
  502 = dependency responded but badly (caller should not retry blindly)
- Log file at `logs/app.log`, ERROR level only — keeps logs scannable; DEBUG available via
  `--log-level debug` flag at startup
- Health endpoint uses LM Studio models-list call (zero token cost, verifies connectivity)
