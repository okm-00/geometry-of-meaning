# Execution Plan: Session DB & Compare UI

**Status**: completed (schema superseded — see `docs/exec-plans/active/per-generation-api.md`)
**Started**: 2026-02-20
**Completed**: 2026-02-20

## Goal

Collapse the UI to a single always-on compare view, introduce a SQLite database that
stores every generation (with full prompt snapshots) and every feedback event, and replace
the old feedback bar with per-condition star ratings and a tag field.

## Steps

- [x] Create this execution plan
- [x] Add `DB_PATH` to `app/config.py`
- [x] Create `app/db.py`: schema, `init_db()`, `save_generation()`, `save_session()`, `save_feedback()`
- [x] Update `app/story.py`: add `system_prompt`/`user_prompt` to `StoryResult`, remove `_log_experiment()` and JSONL logging
- [x] Update `app/main.py`: replace `/api/story` with `POST /api/session` (concurrent), update `POST /api/feedback`
- [x] Update `static/index.html`: remove mode selector, always compare, star ratings + tag feedback panel
- [x] Create `tests/test_db.py`
- [x] Update `tests/test_main.py`
- [x] Update `tests/test_story.py`
- [x] Update `.env.example`, `ARCHITECTURE.md`, add `data/` to `.gitignore`

## Key design decisions

- **SQLite via stdlib `sqlite3`** — no new dependencies; zero-config; queryable with any SQLite client.
- **`POST /api/session`** runs both conditions concurrently via `asyncio.gather` +
  `loop.run_in_executor`, halving wall-clock latency for the compare view.
- **Prompt snapshots** stored in `generation.system_prompt` / `generation.user_prompt` so
  future schema/prompt changes don't lose the record of what actually ran.
- **JSONL logging removed** — DB is the single source of truth for experiment data.
- **Ratings and tag are optional** — Save is always enabled; partial feedback is better than none.

## DB schema (as initially implemented — superseded)

The `session` and `feedback` tables below were initially implemented with hardcoded
`baseline_generation_id` / `harness_generation_id` columns and a per-session feedback row.
This schema was replaced by `per-generation-api.md` to support N variants. See that plan
for the current schema.

```sql
CREATE TABLE generation (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    condition     TEXT NOT NULL,
    model         TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt   TEXT NOT NULL,
    temperature   REAL NOT NULL,
    body          TEXT NOT NULL,   -- JSON array
    endings       TEXT NOT NULL,   -- JSON array
    timing_ms     INTEGER NOT NULL,
    candidates    TEXT,            -- NULL until Phase 2
    scores        TEXT             -- NULL until Phase 2
);

-- SUPERSEDED: replaced with generation_ids JSON array in per-generation-api.md
CREATE TABLE session (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                     TEXT NOT NULL,
    baseline_generation_id INTEGER NOT NULL REFERENCES generation(id),
    harness_generation_id  INTEGER NOT NULL REFERENCES generation(id)
);

-- SUPERSEDED: replaced with per-generation feedback in per-generation-api.md
CREATE TABLE feedback (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ts               TEXT NOT NULL,
    session_id       INTEGER NOT NULL REFERENCES session(id),
    baseline_rating  INTEGER,       -- 1–5, nullable
    harness_rating   INTEGER,       -- 1–5, nullable
    tag              TEXT           -- max 120 chars, nullable
);
```

## Phase 2 insertion points

When the KDE harness is ready:
1. `_generate_harness()` in `app/story.py` — replace single LLM call with N-candidate reranking
2. Populate `generation.candidates` and `generation.scores` (columns already exist)
3. Add `HARNESS_NUM_CANDIDATES`, `HARNESS_LAMBDA`, `HARNESS_KDE_PATH` to `app/config.py`
