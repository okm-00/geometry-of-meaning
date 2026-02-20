# RELIABILITY.md — Reliability Requirements and Patterns

## Current reliability posture (v1)

This is a local development prototype. Reliability requirements are minimal but explicit.

## Requirements

| Requirement                                      | Status       | Notes                                       |
|--------------------------------------------------|--------------|---------------------------------------------|
| App starts cleanly with `make run`               | met          | Must not error on startup                   |
| LM Studio unavailable → graceful error response  | met          | Returns 503 with structured message         |
| Malformed LLM JSON → graceful error response     | met          | Returns 502 with diagnostic message         |
| App recovers after LM Studio restarts            | met          | No persistent state, so automatic           |
| Request timeout on LLM calls                     | met          | `LM_STUDIO_TIMEOUT_SECONDS` (default 60s)   |
| Health endpoint for connectivity probing         | met          | `GET /health` — LM Studio models-list call  |

## Patterns

### Error responses

All errors must return structured JSON: `{ "detail": "human-readable message" }`.
Never let Python exceptions propagate as raw 500 responses.

### Health check

`GET /health` probes LM Studio with a models-list call and returns structured JSON.
Always HTTP 200; callers inspect the `status` field (`"ok"` or `"degraded"`).

### Graceful shutdown

Not implemented in v1. FastAPI + uvicorn handle SIGTERM adequately for local use.

## Known gaps (see tech-debt-tracker.md)

- TD-1: No retry on malformed LLM JSON — a single bad response surfaces as an error to the user.
