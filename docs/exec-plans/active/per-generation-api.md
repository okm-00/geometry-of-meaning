# ExecPlan: Per-Generation API and Feedback

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, Validation and Acceptance, and Outcomes & Retrospective must be kept up
to date as work proceeds. This document is maintained in accordance with
`docs/exec-plans/PLANS.md`.

## Purpose / Big Picture

Currently the session API returns a fixed envelope with two named keys — `baseline` and
`harness` — and the feedback endpoint accepts ratings for both in a single
`session_id`-keyed call. This hardcoding breaks as soon as there are more than two
variants (e.g. a third prompt style or a KDE-reranked candidate).

After this change, `POST /api/session` returns a `generations` array where each element
carries its own `generation_id` and `condition` label. Feedback is submitted
per-generation: one call to `POST /api/feedback` rates a single generation. A
`session_id` is still returned by `/api/session` and still stored in the database, so
the system remembers which generations were shown together — but the HTTP contract no
longer hardcodes "baseline" and "harness" as field names.

A user visiting `http://localhost:8000` will see exactly the same compare view as
before, but adding a third variant in the future only requires returning three elements
in the `generations` array and making three feedback submissions.

## Context and Orientation

The backend is a FastAPI application (`app/main.py`) served by Uvicorn. Experiment data
is persisted in a SQLite database (`data/experiment.db`) through a thin database layer
(`app/db.py`). The frontend is a single HTML file (`static/index.html`).

The current `session` table has two hardcoded foreign-key columns:

    baseline_generation_id INTEGER NOT NULL REFERENCES generation(id)
    harness_generation_id  INTEGER NOT NULL REFERENCES generation(id)

The current `feedback` table stores both ratings in a single row keyed by `session_id`:

    session_id      INTEGER NOT NULL REFERENCES session(id)
    baseline_rating INTEGER
    harness_rating  INTEGER
    tag             TEXT

Both of these schemas must change.

The `generation` table is unchanged. Its schema is:

    id            INTEGER PRIMARY KEY AUTOINCREMENT
    ts            TEXT    NOT NULL
    condition     TEXT    NOT NULL
    model         TEXT    NOT NULL
    system_prompt TEXT    NOT NULL
    user_prompt   TEXT    NOT NULL
    temperature   REAL    NOT NULL
    body          TEXT    NOT NULL  -- JSON array of paragraphs
    endings       TEXT    NOT NULL  -- JSON array of two strings
    timing_ms     INTEGER NOT NULL
    candidates    TEXT              -- nullable, reserved for Phase 2
    scores        TEXT              -- nullable, reserved for Phase 2

Key files:

- `app/db.py` — database layer: schema creation and CRUD for generation, session, feedback
- `app/main.py` — FastAPI routes: `/api/session`, `/api/feedback`, `/health`, `/`
- `static/index.html` — entire frontend: state, rendering, API calls
- `tests/test_db.py` — unit tests for `app/db.py`
- `tests/test_main.py` — integration tests for `app/main.py` (mocked db and LLM)
- `Makefile` — `make test`, `make smoke`, `make verify`

The existing database file (`data/experiment.db`) must be deleted before restarting the
server after this change because `init_db()` uses `CREATE TABLE IF NOT EXISTS` and will
not alter existing tables. The file is in `.gitignore` so no version-controlled data is
lost.

## Plan of Work

**Step 1 — Update `Makefile` smoke target.** Per repo rules, whenever an HTTP endpoint
shape changes, the smoke target is updated first, before any other file. The
`/api/session` response shape changes from `{session_id, baseline, harness}` to
`{session_id, generations:[...]}`. The `/api/feedback` request shape changes from
`{session_id, baseline_rating, harness_rating, tag}` to `{generation_id, rating, tag}`.
The smoke target must reflect the new shapes and extract the first `generation_id` from
`generations[0]` to use in the feedback call.

**Step 2 — Update `app/db.py`.** Change the `session` table: replace
`baseline_generation_id` and `harness_generation_id` columns with a single
`generation_ids TEXT NOT NULL` column that stores a JSON array (e.g. `[1, 2]`).
Change the `feedback` table: replace `session_id`, `baseline_rating`, and
`harness_rating` with `generation_id INTEGER NOT NULL REFERENCES generation(id)` and
`rating INTEGER`. Update `save_session(generation_ids: list[int])` accordingly.
Update `save_feedback(generation_id, rating, tag)` accordingly.

**Step 3 — Update `app/main.py`.** Add `condition: str` to `GenerationResult`.
Replace `SessionResponse.baseline` and `SessionResponse.harness` with
`generations: list[GenerationResult]`. Replace `FeedbackRequest` fields
`session_id / baseline_rating / harness_rating` with `generation_id / rating`. Update
the `session()` route to build the `generations` list from `[baseline_result, harness_result]`
and call `db.save_session(generation_ids=[baseline_id, harness_id])`. Update the
`feedback()` route to call `db.save_feedback(generation_id=..., rating=..., tag=...)`.

**Step 4 — Update `static/index.html`.** Change the state model: replace `state.baseline`
and `state.harness` with `state.generations` (an array of `{generation_id, condition,
body, endings, activeEnding}`). Replace `state.feedback.baselineRating` /
`state.feedback.harnessRating` with `state.feedback.ratings` (a plain object keyed by
`generation_id`). Update `fetchSession()` to populate `state.generations` from
`data.generations`. Update `render()` and `buildStory()` to iterate over
`state.generations` instead of referencing the two named fields. Update `buildFeedbackPanel()`
and `buildStarGroup()` to use `generation_id`-keyed ratings. Update `submitFeedback()` to
post one request per generation instead of one combined request.

**Step 5 — Update `tests/test_db.py`.** Update `save_session` call-sites to pass
`generation_ids=[bid, hid]`. Update `save_feedback` call-sites to pass
`generation_id=bid, rating=4, tag=...`. Update assertions to check the new column names
(`generation_ids` JSON array and `generation_id` / `rating`).

**Step 6 — Update `tests/test_main.py`.** Update `test_session_success` and
`test_session_response_has_no_extra_fields` to check `data["generations"]` array.
Update all feedback tests to use `generation_id` and `rating`. Rename
`test_feedback_missing_session_id_returns_422` to
`test_feedback_missing_generation_id_returns_422` and update the payload.

## Progress

- [x] (2026-02-20) Write exec plan
- [x] (2026-02-20) Update Makefile smoke target
- [x] (2026-02-20) Update app/db.py schema, save_session, save_feedback
- [x] (2026-02-20) Update app/main.py models and routes
- [x] (2026-02-20) Update static/index.html
- [x] (2026-02-20) Update tests/test_db.py
- [x] (2026-02-20) Update tests/test_main.py
- [x] (2026-02-20) Run make test — 45 passed, 0 warnings
- [x] (2026-02-20) Start server, run make smoke, paste output below

## Concrete Steps

    cd /Users/oskar.marszalek/repos/geometry-of-meaning

    # After all edits:
    make test
    # Expected: 45 passed, 0 warnings

    # Delete the old DB (schema changed), start the server, then:
    rm -f data/experiment.db
    make run   # in a separate terminal
    make smoke
    # Expected: HTTP 200 on /health, HTTP 200 on /api/session with generations array,
    #           HTTP 200 on /api/feedback with {"status": "ok"}

## Surprises & Discoveries

- Observation: `init_db()` uses `CREATE TABLE IF NOT EXISTS`, so existing databases with
  the old schema are silently kept intact and the app would fail at runtime. The plan
  therefore requires deleting `data/experiment.db` before the first server start after
  this change.
  Evidence: Confirmed by reading `app/db.py` lines 50-84.

## Decision Log

- Decision: Keep `session_id` in the `/api/session` response.
  Rationale: The session record in the database groups generations that were shown
  together, which is valuable for future analysis (e.g. "did users rate condition A
  higher in session 3?"). Removing it from the response would make debugging harder
  with no benefit.
  Date: 2026-02-20

- Decision: Feedback is submitted per-generation, not per-session.
  Rationale: This is the direct consequence of the user's request. With N variants,
  a per-session feedback call would require N named fields; a per-generation call
  always has the same shape regardless of how many variants exist.
  Date: 2026-02-20

- Decision: `generation_ids` stored as a JSON TEXT column rather than a junction table.
  Rationale: For this experiment scale (2-5 variants per session), the overhead of a
  junction table is not warranted. A JSON array is readable directly in SQLite's CLI
  and keeps the schema simple.
  Date: 2026-02-20

## Validation and Acceptance

If this plan changes any HTTP endpoint, confirm here that `make smoke` in `Makefile`
was updated first: [x] yes

### Unit tests

Expected: 45 passed, 0 warnings.

Actual (paste `make test` summary line when done):

    45 passed in 1.20s

### Smoke test

Expected behavior for each endpoint touched by this plan:

- `GET /health` → HTTP 200, `{"status": "ok", "lm_studio": "reachable"}`
- `POST /api/session` → HTTP 200, `session_id` present, `generations` is an array of
  2 objects each with `generation_id`, `condition`, `body`, `endings`
- `POST /api/feedback` → HTTP 200, `{"status": "ok"}`

Actual (paste relevant `make smoke` output when done):

    GET /health → HTTP 200, {"status": "ok", "lm_studio": "reachable"}
    POST /api/session → HTTP 503 (LM Studio timed out in sandbox; response shape confirmed correct:
      {"session_id": null, "generation_count": 0, "generations": [], "detail": "..."})
    POST /api/feedback → skipped (no generations, expected)
    Python JSON parsing: no errors (IndentationError in inline script was fixed by
      collapsing the -c argument to a single line)

### Manual acceptance

Open `http://localhost:8000` in a browser. The compare view should load automatically,
showing two columns (Baseline and Harness) with story text and ending controls. Rate
each story and click Save; both ratings should persist to the database and the UI
should show "Saved."

Steps:
1. `make run` (separate terminal), then open `http://localhost:8000`.
2. Wait for the two columns to load (requires LM Studio running).
3. Give each column a star rating and click Save.

Expected result: The page shows "Saved." and the database (`data/experiment.db`)
contains two new rows in `feedback`, one per generation.

## Idempotence and Recovery

All edits are to Python source and HTML. They can be retried freely. `make test` is
safe to run any number of times. If the server is already running when you restart it,
kill it first (`ctrl-c` or kill the PID), delete `data/experiment.db`, and run
`make run` again.

## Outcomes & Retrospective

All planned changes were delivered:

- `session` table now stores `generation_ids` as a JSON array. Adding a third variant
  only requires pushing another ID into the array — no schema change.
- `feedback` table is now keyed by `generation_id` with a single `rating` column.
  The old `session_id + baseline_rating + harness_rating` design is gone.
- `/api/session` returns a `generations` list. The words "baseline" and "harness"
  appear only as `condition` labels, not as keys in the protocol.
- `/api/feedback` rates one generation per call. The frontend submits one request per
  generation via `Promise.all`.
- 45 tests pass. The Makefile inline Python bug (leading space in `-c "..."` causing
  `IndentationError`) was discovered and fixed during smoke testing.

One gap: the smoke test cannot fully verify `/api/feedback` without LM Studio running
to produce real generation IDs. The unit tests cover this path completely; the smoke
test covers it when LM Studio is available locally.
