# Execution Plan: A/B Comparison Scaffold

**Status**: completed
**Started**: 2026-02-20
**Completed**: 2026-02-20

## Goal

Add A/B comparison infrastructure to the story app: a `condition` parameter on the API,
stub implementations for "baseline" and "harness" generation modes, and a UI that can
show either mode alone or both side-by-side with a preference feedback button.

No corpus or KDE yet. The harness path calls the same LLM as baseline — the branching
code, logging, and insertion point are real, ready for Phase 2.

## Steps

- [x] Create this execution plan
- [x] Extend `app/story.py`: `condition` param, `_generate_baseline()` / `_generate_harness()` stubs, `_log_experiment()` helper
- [x] Extend `app/main.py`: `StoryRequest` model, condition passthrough, `POST /api/feedback` endpoint
- [x] Extend `static/index.html`: mode selector (Baseline / Harness / Compare), side-by-side compare layout, feedback bar
- [x] Update/add tests for condition param and feedback endpoint
- [x] Update `.env.example`, `ARCHITECTURE.md`, `AGENTS.md` to document new experiment concepts

## Key design decisions

- **Condition is per-request**, not global config — the frontend controls it each call.
- **Harness stub** calls `_generate_baseline()` internally; `_generate_harness()` is the
  single insertion point for KDE reranking in Phase 2.
- **Logging** writes one JSONL line per generation and per feedback event to
  `logs/experiment_log.jsonl`; the schema includes null `candidates`/`scores` fields
  so Phase 2 can fill them in without a schema change.
- **Compare mode** fires two concurrent `fetch` calls from the frontend — no new
  combined endpoint needed.

## Phase 2 insertion points

When the KDE harness is ready:
1. Replace the body of `_generate_harness()` in `app/story.py`
2. Add `sentence-transformers` and `scikit-learn` to `pyproject.toml`
3. Add `HARNESS_KDE_PATH`, `HARNESS_NUM_CANDIDATES`, `HARNESS_LAMBDA` to `app/config.py`
