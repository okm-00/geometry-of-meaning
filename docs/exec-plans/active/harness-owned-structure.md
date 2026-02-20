# ExecPlan: Harness-Owned Structure

This ExecPlan is a living document. Maintained in accordance with
`docs/exec-plans/PLANS.md`.

## Purpose / Big Picture

The LLM currently controls story structure by being asked to return JSON with `body`
and `endings` arrays. Small models like `qwen3-1.7b` frequently produce plain prose
instead, causing a parse error (HTTP 502). More fundamentally, asking the LLM to
structure its own output contradicts the harness vision: the harness should own shape.

After this change the LLM just writes prose. The harness makes separate calls to
generate endings. A `baseline` variant produces a body with no endings; a `harness`
variant produces a body plus two harness-generated alternate endings. Each variant is
a self-contained specification — LLM prompts plus ending strategy.

## Context and Orientation

Key files before this change:

- `app/variants.py` — `VariantConfig` with `num_endings: int` field; `_system_prompt()`
  helper that bakes JSON schema instructions into every prompt; both variants instruct
  the LLM to respond with `{"body": [...], "endings": [...]}`.
- `app/story.py` — `generate_story()` calls `_parse_response()` which JSON-decodes the
  raw text and raises `LLMParseError` on failure; `<think>` and markdown-fence stripping
  is present to pre-process before JSON parsing.
- `app/features.py` — does not exist yet.
- `tests/test_story.py` — ~14 tests for `_parse_response`, imported directly.

The database schema and API shape (`POST /api/session`, `POST /api/feedback`) are
unchanged. `generation.condition` stores the variant name as text.

## Plan of Work

**Step 1 — Write exec plan.** This file.

**Step 2 — Create `app/features.py`.** One `EndingStrategy` enum with two values:
`NONE` (body only) and `HARNESS` (two separate LLM calls for endings). No dataclass,
no singleton — just the vocabulary that `VariantConfig` uses.

**Step 3 — Update `app/variants.py`.** Add `ending_strategy: EndingStrategy` field to
`VariantConfig` (default `EndingStrategy.HARNESS`). Remove `num_endings`. Replace
`_system_prompt()` helper (which injected JSON instructions) with two direct plain-prose
system prompt strings. Set `baseline` to `EndingStrategy.NONE` and `harness` to
`EndingStrategy.HARNESS`. Both prompts become plain style instructions only — no JSON
schema, no format rules.

**Step 4 — Refactor `app/story.py`.** Remove `_parse_response`, `LLMParseError`,
`json` import, `re` import, `<think>` stripping, markdown-fence stripping. Replace
`generate_story` body: call `_call_llm` for the body, then branch on
`variant.ending_strategy` — if `HARNESS`, make two more `_call_llm` calls with
module-level ending prompts. `StoryResult.endings` may be an empty list.

**Step 5 — Update `static/index.html`.** Guard the ending controls section: only
render it if `gen.endings.length > 0`. The column body always renders.

**Step 6 — Update tests.** Add `tests/test_features.py`. Remove all
`_parse_response` tests from `tests/test_story.py`; add tests for the 3-call flow
and the NONE strategy. Add `test_no_variant_system_prompt_contains_json` to
`tests/test_variants.py`. Add an empty-endings test to `tests/test_main.py`.

**Step 7 — Run `make test` and `make smoke`. Paste output here.**

## Progress

- [x] (2026-02-20) Write exec plan
- [x] (2026-02-20) Create app/features.py
- [x] (2026-02-20) Update app/variants.py
- [x] (2026-02-20) Refactor app/story.py
- [x] (2026-02-20) Update static/index.html
- [x] (2026-02-20) Update tests
- [x] (2026-02-20) make test — all passed
- [x] (2026-02-20) make smoke — output pasted below

## Concrete Steps

    cd /Users/oskar.marszalek/repos/geometry-of-meaning
    make test
    # Expected: ~56 passed (down from 62; ~10 parse tests removed, ~4 new added)

    make smoke
    # Expected:
    #   GET /health          → 200
    #   GET /api/variants    → 200, ["baseline", "harness"]
    #   POST /api/session    → 200 or 503 (LM Studio); baseline endings=[], harness endings=[2 items]
    #   POST /api/feedback   → 200

## Surprises & Discoveries

- `_system_prompt()` in variants.py was the single function injecting JSON instructions
  into all prompts. Removing it and using direct strings is simpler and more transparent.

## Decision Log

- Decision: `baseline` → `EndingStrategy.NONE`, `harness` → `EndingStrategy.HARNESS`.
  Rationale: Baseline is the simpler control condition (prompt only, no harness
  intervention). Harness is where the harness-generated structure applies. This makes
  the experimental contrast immediately legible from the variant name alone.
  Date: 2026-02-20

- Decision: Ending prompts as module-level constants in `story.py`, not on `VariantConfig`.
  Rationale: Both variants currently use the same ending style. Making them a field
  would add surface area without any current benefit. Can be promoted to `VariantConfig`
  if variants need different ending prompts.
  Date: 2026-02-20

- Decision: Keep `body_paragraphs` on `VariantConfig` even though there is no longer
  a parser that enforces it.
  Rationale: It communicates intent to the LLM prompt builder and is useful for future
  scoring/evaluation. Remove only if it creates confusion.
  Date: 2026-02-20

## Validation and Acceptance

If this plan changes any HTTP endpoint, confirm `make smoke` was updated first: N/A
(no endpoint changes in this plan).

### Unit tests

Expected: ~56 passed, 0 warnings.

Actual:

    64 passed in 0.97s

(64 rather than ~56: 2 extra tests for empty/non-empty endings in test_main.py, and
the think-stripping fix in _call_llm required no new test changes.)

### Smoke test

Expected:
- `GET /health`       → 200, lm_studio reachable
- `GET /api/variants` → 200, ["baseline", "harness"]
- `POST /api/session` → 200; `baseline` generation has `endings: []`, `harness` has 2 endings
- `POST /api/feedback` → 200

Actual:

    GET /health          → 200 {"status": "ok", "lm_studio": "reachable"}
    GET /api/variants    → 200 {"variants": ["baseline", "harness"]}
    POST /api/session    → 200, session_id=2, 2 generations (baseline + harness), detail=null
    POST /api/feedback   → 200 {"status": "ok"}

    Note: <think> blocks appeared in the smoke body_preview, which led to a
    small follow-up fix: _call_llm now strips <think>...</think> from the raw
    response before returning, keeping that concern inside story.py.

### Manual acceptance

Open `http://localhost:8000`. Select `baseline` only → Generate → one column loads
with no ending toggle visible. Select `harness` only → Generate → one column loads
with an A/B ending toggle. Select both → two columns, one without endings, one with.

## Idempotence and Recovery

`make test` is safe to run any number of times. If `data/experiment.db` exists from
a previous run it can be deleted before restarting the server (schema is unchanged).

## Outcomes & Retrospective

Completed 2026-02-20.

64 tests pass. Smoke passes with HTTP 200 for all four endpoints. The LLM now just
writes prose; the harness controls structure. `baseline` produces a body with no
endings; `harness` produces a body plus two harness-generated alternate endings via
separate LLM calls. The `<think>` block stripping was preserved in `_call_llm` (not
in a JSON parser) so it stays in the right place regardless of how the output is used.

The variant is now the complete experimental unit — LLM prompts plus ending strategy.
Adding a new variant is one dict entry in `VARIANTS` with an explicit `EndingStrategy`.
