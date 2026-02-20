# ARCHITECTURE.md

## Overview

This is an intentionally flat, single-domain application. The architecture prioritizes legibility
for agents over clever abstraction. Every layer has one job.

## Domain: Story

The single business domain is `story`: generating and serving interactive narrative content.

## Layer map

```
Browser (static/index.html)
    │
    │  HTTP GET /          → serves index.html
    │  HTTP POST /api/story → returns StoryResponse JSON
    ▼
app/main.py  [Routes layer]
    │  Receives HTTP requests, validates input, delegates to story layer, returns responses.
    │  Must not contain business logic or prompt construction.
    ▼
app/story.py  [Service layer]
    │  Owns all LLM interaction: builds prompts, calls LM Studio, parses and validates response.
    │  Must not import from main.py. Must not know about HTTP.
    ▼
app/config.py  [Config layer]
    │  Reads environment variables. Single source of truth for runtime configuration.
    │  No logic — only settings.
    ▼
LM Studio  [External: local LLM server]
    OpenAI-compatible API at http://localhost:1234/v1 (default).
    Accessed via the openai Python SDK with a custom base_url.
```

## Dependency rules

- Routes → Service: allowed
- Routes → Config: allowed
- Service → Config: allowed
- Service → Routes: FORBIDDEN
- Config → anything else in app/: FORBIDDEN

## Error taxonomy

Three typed exception classes are defined in `app/story.py` and handled in `app/main.py`:

| Exception            | Meaning                              | HTTP status |
|----------------------|--------------------------------------|-------------|
| `LLMConnectionError` | Cannot reach LM Studio               | 503         |
| `LLMResponseError`   | LM Studio returned HTTP error        | 502         |
| `LLMParseError`      | Response was not parseable/valid JSON| 502         |

503 = our dependency is down (caller may retry later).
502 = dependency responded but with bad data (do not retry blindly).

## Logging

ERROR-level logs are written to `logs/app.log` via a `RotatingFileHandler` configured at
startup in `app/main.py`. This file persists across terminal sessions and is readable by
agents or humans when investigating runtime issues. `logs/` is in `.gitignore`.

## Health endpoint

`GET /health` returns structured JSON indicating LM Studio reachability.
It uses a lightweight models-list call (no token cost).

```
{ "status": "ok",       "lm_studio": "reachable" }
{ "status": "degraded", "lm_studio": "unreachable", "detail": "..." }
```

## Response schema

```
POST /api/story

Response 200:
{
  "body": ["paragraph 1", "paragraph 2", ..., "paragraph N"],  // 3-4 paragraphs
  "endings": ["ending A text", "ending B text"]                 // exactly 2
}

Response 500:
{
  "detail": "human-readable error message"
}
```

## Static files

`static/index.html` is served directly by FastAPI's StaticFiles mount.
There is no build step. No bundler. No node_modules.
All JS is vanilla, inline in the HTML file.

## Configuration surface

All configuration is via environment variables (see `.env.example`):

| Variable              | Default                      | Description                        |
|-----------------------|------------------------------|------------------------------------|
| `LM_STUDIO_BASE_URL`  | `http://localhost:1234/v1`   | LM Studio local server URL         |
| `LM_STUDIO_MODEL`     | (required)                   | Model identifier as shown in LM Studio |
| `LM_STUDIO_API_KEY`   | `lm-studio`                  | Placeholder — LM Studio ignores this |
