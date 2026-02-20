# Exec Plan: Per-Variant Feature Toggles in Setup Screen

**Status:** In Progress
**Branch:** feature/ui-customisation

## Goal

Allow users to configure features (currently: `ending_strategy`) per selected
variant directly on the setup screen — not just pick a named bundle. When a
variant checkbox is checked, a small feature selector appears beneath it.

## Motivation

Variant names (`baseline`, `harness`) capture default prompt + harness
combinations. Letting users override individual features (e.g. run baseline
*with* harness-style endings) makes experiments more flexible without requiring
new named variants to be added to `variants.py`.

## Design

### API changes

**`GET /api/variants`** — richer response:
```json
{
  "variants": {
    "baseline": { "ending_strategy": "none" },
    "harness":  { "ending_strategy": "harness" }
  },
  "ending_strategies": ["none", "harness"]
}
```

**`POST /api/session`** — new request shape:
```json
{
  "selections": [
    { "name": "baseline", "ending_strategy": "none" },
    { "name": "harness",  "ending_strategy": "harness" }
  ]
}
```
Server applies the override via `dataclasses.replace(VARIANTS[name], ending_strategy=EndingStrategy(value))`.

### Frontend changes

- `state.variantMeta`: stores per-variant metadata from `/api/variants`
- `state.availableEndingStrategies`: list of valid strategy strings
- `state.selectedFeatures`: `{ [name]: { ending_strategy } }` — feature overrides, initialised from variant defaults when a checkbox is first checked
- Setup screen shows a feature selector row beneath each checked variant
- `fetchSession()` sends `selections` (list of `{name, ending_strategy}`)

## Files to change

| File | Change |
|---|---|
| `app/main.py` | `GET /api/variants` richer response; `SessionRequest` → `selections`; apply overrides via `dc_replace` |
| `static/index.html` | state additions; CSS for feature row; `buildSetupScreen` restructured; `fetchVariants`/`fetchSession` updated |
| `tests/test_main.py` | update all session tests for new shape; update variants test |
| `Makefile` | update smoke payload |

## Validation and Acceptance

### Pre-coding expected results

**`make test` (64 tests):** all pass

**`make smoke`:**
```
GET /api/variants   → HTTP 200, variants is a dict, ending_strategies is a list
POST /api/session   → HTTP 200, generations array with correct endings per selection
POST /api/feedback  → HTTP 200 {"status":"ok"}
```

### Post-coding actual results

**`make test`:** 68 passed in 0.86s

**`make smoke`:**
```
GET /health         → {"status":"ok","lm_studio":"reachable"}
GET /api/variants   → variants dict with ending_strategy per variant + ending_strategies list
POST /api/session   → HTTP 200, 2 generations, no <think> blocks in body_preview
POST /api/feedback  → {"status":"ok"}
```

**Status:** Complete ✓
