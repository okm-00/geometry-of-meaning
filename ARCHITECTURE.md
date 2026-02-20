# ARCHITECTURE.md

## Overview

This is an intentionally flat, single-domain application. The architecture prioritizes legibility
for agents over clever abstraction. Every layer has one job.

## Domain: Story

The single business domain is `story`: generating and serving interactive narrative content
across two experimental conditions (baseline and harness), with user feedback persisted to a
local SQLite database.

## Layer map

```
Browser (static/index.html)
    │
    │  HTTP GET /              → serves index.html
    │  HTTP POST /api/session  → generates N variants concurrently, returns generations array
    │  HTTP POST /api/feedback → records a star rating + tag for a single generation
    ▼
app/main.py  [Routes layer]
    │  Receives HTTP requests, validates input, delegates to story and db layers.
    │  Must not contain business logic or prompt construction.
    ▼
app/story.py  [Service layer]
    │  Owns all LLM interaction: builds prompts, calls LM Studio, parses and validates response.
    │  Routes generation to _generate_baseline() or _generate_harness() based on condition.
    │  Returns StoryResult with full prompt snapshots (for DB storage by the route layer).
    │  Must not import from main.py. Must not know about HTTP.
    ▼
app/db.py  [Database layer]
    │  SQLite via stdlib sqlite3. Owns schema creation and all CRUD operations.
    │  init_db() called once at startup. save_generation(), save_session(), save_feedback().
    │  Must not import from main.py or story.py.
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
- Routes → DB: allowed
- Routes → Config: allowed
- Service → Config: allowed
- DB → Config: allowed
- Service → Routes: FORBIDDEN
- DB → Routes or Service: FORBIDDEN
- Config → anything else in app/: FORBIDDEN

## Error taxonomy

Three typed exception classes are defined in `app/story.py` and handled in `app/main.py`:

| Exception            | Meaning                               | HTTP status |
|----------------------|---------------------------------------|-------------|
| `LLMConnectionError` | Cannot reach LM Studio                | 503         |
| `LLMResponseError`   | LM Studio returned HTTP error         | 502         |
| `LLMParseError`      | Response was not parseable/valid JSON | 502         |

503 = our dependency is down (caller may retry later).
502 = dependency responded but with bad data (do not retry blindly).

## Logging

ERROR-level logs are written to `logs/app.log` via a `RotatingFileHandler` configured at
startup in `app/main.py`. This file persists across terminal sessions and is readable by
agents or humans when investigating runtime issues. `logs/` is in `.gitignore`.

Experiment data (generations and feedback) is persisted to the SQLite database — see
the Database section below.

## Health endpoint

`GET /health` returns structured JSON indicating LM Studio reachability.
It uses a lightweight models-list call (no token cost).

```
{ "status": "ok",       "lm_studio": "reachable" }
{ "status": "degraded", "lm_studio": "unreachable", "detail": "..." }
```

## API schema

```
POST /api/session
No request body.

Response 200:
{
  "session_id": 7,
  "generations": [
    { "generation_id": 13, "condition": "baseline", "body": [...], "endings": [...] },
    { "generation_id": 14, "condition": "harness",  "body": [...], "endings": [...] }
  ]
}

The generations array is ordered but not named — adding a third variant only requires
returning a third element. The frontend iterates the array; "baseline" and "harness"
are condition labels, not field names.

Response 4xx/5xx:
{ "detail": "human-readable error message" }

POST /api/feedback
Request body (one call per generation):
{
  "generation_id": 13,
  "rating": 4,          // optional, 1–5
  "tag": "melancholy"   // optional, max 120 chars
}

Response 200: { "status": "ok" }

To rate all generations in a session, submit one POST /api/feedback per generation_id.
The frontend does this concurrently via Promise.all.
```

## Database

SQLite file at `config.DB_PATH` (default: `data/experiment.db`). Three tables:

```sql
generation  — one row per LLM call; stores full prompt snapshots, body, endings, timing
session     — groups N generation IDs shown together (stored as JSON array)
feedback    — one row per generation rated; stores a single rating (1–5) and optional tag
```

Schema detail:

```sql
-- session stores any number of generation IDs, not just two
CREATE TABLE session (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT    NOT NULL,
    generation_ids TEXT    NOT NULL   -- JSON array, e.g. [1, 2] or [1, 2, 3]
);

-- feedback is keyed by generation_id, not session_id
CREATE TABLE feedback (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT    NOT NULL,
    generation_id INTEGER NOT NULL REFERENCES generation(id),
    rating        INTEGER,            -- 1–5, nullable
    tag           TEXT                -- max 120 chars, nullable
);
```

Key queries:

```sql
-- Average rating per condition
SELECT g.condition, AVG(f.rating)
FROM feedback f
JOIN generation g ON f.generation_id = g.id
GROUP BY g.condition;

-- All feedback joined to the prompt that produced it
SELECT f.rating, f.tag, g.condition, g.system_prompt, g.timing_ms
FROM feedback f
JOIN generation g ON f.generation_id = g.id
ORDER BY f.ts DESC;
```

`data/` is in `.gitignore`.

## Static files

`static/index.html` is served directly by FastAPI's StaticFiles mount.
There is no build step. No bundler. No node_modules.
All JS is vanilla, inline in the HTML file.

## Configuration surface

All configuration is via environment variables (see `.env.example`):

| Variable                | Default                    | Description                             |
|-------------------------|----------------------------|-----------------------------------------|
| `LM_STUDIO_BASE_URL`    | `http://localhost:1234/v1` | LM Studio local server URL              |
| `LM_STUDIO_MODEL`       | (required)                 | Model identifier as shown in LM Studio  |
| `LM_STUDIO_API_KEY`     | `lm-studio`                | Placeholder — LM Studio ignores this    |
| `LM_STUDIO_TIMEOUT_SECONDS` | `60`                   | Request timeout in seconds              |
| `DB_PATH`               | `data/experiment.db`       | Path to SQLite database file            |
