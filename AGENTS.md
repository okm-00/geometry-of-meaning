# AGENTS.md — Table of Contents

This file is a map, not a manual.
It is the entry point for any agent working in this repository — intentionally short.
Follow the pointers below to find deeper context. Do not expand this file into a monolith.

## Project overview

An interactive story app: a locally-served web application that generates short stories via a local LLM
(LM Studio). The UI always shows both conditions side-by-side (compare view). Generations and
user feedback (star ratings + tag) are persisted to a SQLite database (`data/experiment.db`).

The app runs A/B experiments: `POST /api/session` generates baseline and harness variants
concurrently and returns them as a `generations` array. Feedback is submitted per-generation
via `POST /api/feedback`. The design is N-variant-ready — adding a third condition requires
no API or schema changes. The harness path (`_generate_harness()` in `app/story.py`) is
the single insertion point for Phase 2 (KDE reranking).

## Commands

```bash
make install   # first-time setup
make run       # start the server (http://localhost:8000)
make test      # run the test suite (no server or LM Studio needed)
make smoke     # live endpoint smoke test (requires server + LM Studio running)
make verify    # test + smoke — run after any change before declaring done
make triage    # recent errors + open TD items — run after verify
make health    # check server and LM Studio status
make logs      # tail logs/app.log
```

LM Studio must be running locally with a model loaded and the local server enabled.
First time: `cp .env.example .env` and fill in `LM_STUDIO_MODEL`.

**Agent rule: always run `make verify` as the final step after completing any implementation.**
If the server is not running, start it first (`make run`), then verify.
If smoke hits an endpoint that doesn't exist or returns unexpected errors, fix before declaring done.
Update `make smoke` whenever API endpoints change — a stale smoke test is the same as no smoke test.

## Orientation — read these first

| What you need                    | Where to find it                                                      |
|----------------------------------|-----------------------------------------------------------------------|
| Agent-first operating principles | [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md) |
| Architecture and layer rules     | [ARCHITECTURE.md](ARCHITECTURE.md)                                    |
| Product goals and user intuition | [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)                       |

## Reference — look up when needed

| What you need                        | Where to find it                                                                  |
|--------------------------------------|-----------------------------------------------------------------------------------|
| Visual/UX design principles          | [docs/DESIGN.md](docs/DESIGN.md)                                                  |
| Frontend conventions                 | [docs/FRONTEND.md](docs/FRONTEND.md)                                              |
| Design decisions index               | [docs/design-docs/index.md](docs/design-docs/index.md)                            |
| Product spec (acceptance criteria)   | [docs/product-specs/story-app.md](docs/product-specs/story-app.md)                |
| Execution plans (active + completed) | [docs/PLANS.md](docs/PLANS.md)                                                    |
| Known technical debt                 | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md)      |
| Testing philosophy and conventions   | [docs/TESTING.md](docs/TESTING.md)                                                |
| Quality grades by domain             | [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md)                                    |
| Reliability requirements             | [docs/RELIABILITY.md](docs/RELIABILITY.md)                                        |
| Security model                       | [docs/SECURITY.md](docs/SECURITY.md)                                              |
| LM Studio API reference              | [docs/references/lmstudio-api-llms.txt](docs/references/lmstudio-api-llms.txt)   |
| FastAPI patterns reference           | [docs/references/fastapi-llms.txt](docs/references/fastapi-llms.txt)              |
| uv reference                         | [docs/references/uv-llms.txt](docs/references/uv-llms.txt)                       |

## Non-negotiable constraints

Four rules whose violation silently breaks the system. Everything else is in
[docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md).

1. All configuration lives in environment variables. `app/config.py` is the only place that reads them.
2. Prompt construction lives in `app/story.py`. Routes in `app/main.py` must not build prompts.
3. Before starting non-trivial work, read [`docs/exec-plans/PLANS.md`](docs/exec-plans/PLANS.md)
   in full, then create an ExecPlan in `docs/exec-plans/active/` using its skeleton. Fill in
   the **Validation and Acceptance** section (expected values) before writing any code.
4. Run `make verify` (tests + live smoke) as the final step of every implementation. Paste the
   actual output into the plan's Verification section. If an API endpoint changes, update
   `make smoke` in the Makefile first — a stale smoke test is the same as no smoke test.

CI runs `make test` automatically on every push and PR. Do not merge a PR with failing tests.

## Repository layout (top-level)

```
story-app/
├── AGENTS.md           ← you are here
├── ARCHITECTURE.md     ← domain/layer map
├── Makefile            ← all commands (run, test, verify, health, logs)
├── docs/               ← system of record
├── app/                ← Python backend (FastAPI)
├── tests/              ← pytest test suite
├── static/             ← frontend (single HTML file)
├── pyproject.toml      ← deps and project metadata
└── .env.example        ← config template
```
