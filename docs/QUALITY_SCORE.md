# QUALITY_SCORE.md — Per-Domain Quality Grades

Quality grades as of initial build (2026-02-19).
Update this file after any significant change. A recurring doc-gardening task should review it.

Scoring: A (excellent) → B (good) → C (acceptable) → D (needs work) → F (broken/missing)

## Domain scores

| Domain              | Score | Notes                                                                          |
|---------------------|-------|--------------------------------------------------------------------------------|
| LLM integration     | B     | Works; timeout added; no retry logic, no streaming                             |
| API routes          | B     | Simple and correct; typed error responses; no input validation needed yet      |
| Frontend UI         | B     | Functional; minimal styling; arrow key UX works                                |
| Error handling      | B     | Typed exceptions; correct HTTP status codes (503/502); persistent log file     |
| Documentation       | A     | Full harness in place; testing contract documented                             |
| Test coverage       | B     | 21 tests covering all error paths and parse edge cases; CI gate on every PR    |
| Configuration       | A     | All env-var driven; config.py is single source of truth                        |
| Security            | C     | Local-only app; acceptable for now (see SECURITY.md)                           |
| Reliability         | B     | Timeout added; health endpoint added; no retries yet (TD-1)                    |

## Improvement priorities

1. Error handling: retry on malformed LLM JSON (TD-1)
2. Frontend: UI growth may require splitting index.html (TD-3)
