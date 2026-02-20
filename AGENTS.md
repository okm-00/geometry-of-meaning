# AGENTS.md — Table of Contents

This file is the entry point for any agent working in this repository.
It is intentionally short. Follow the pointers below to find deeper context.
Do not expand this file into a monolith — add new knowledge to the docs/ system of record instead.

## Project overview

An interactive story app: a locally-served web application that generates short stories via a local LLM
(LM Studio), with two alternative endings the user can toggle using arrow keys.

## Commands

```bash
make install   # first-time setup
make run       # start the server (http://localhost:8000)
make test      # run the test suite
make verify    # test + health check — run after any change or restart
make triage    # recent errors + open TD items — run after verify
make health    # check server and LM Studio status
make logs      # tail logs/app.log
```

LM Studio must be running locally with a model loaded and the local server enabled.
First time: `cp .env.example .env` and fill in `LM_STUDIO_MODEL`.

## Key pointers

| What you need                        | Where to find it                                  |
|--------------------------------------|---------------------------------------------------|
| Architecture and layer rules         | [ARCHITECTURE.md](ARCHITECTURE.md)                |
| Product goals and user intuition     | [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)    |
| Visual/UX design principles          | [docs/DESIGN.md](docs/DESIGN.md)                  |
| Frontend conventions                 | [docs/FRONTEND.md](docs/FRONTEND.md)              |
| Agent-first operating principles     | [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md) |
| Design decisions index               | [docs/design-docs/index.md](docs/design-docs/index.md) |
| Product spec (acceptance criteria)   | [docs/product-specs/story-app.md](docs/product-specs/story-app.md) |
| Execution plans (active + completed) | [docs/PLANS.md](docs/PLANS.md)                    |
| Known technical debt                 | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) |
| Quality grades by domain             | [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md)    |
| Reliability requirements             | [docs/RELIABILITY.md](docs/RELIABILITY.md)        |
| Security model                       | [docs/SECURITY.md](docs/SECURITY.md)              |
| Testing philosophy and conventions   | [docs/TESTING.md](docs/TESTING.md)                |
| LM Studio API reference              | [docs/references/lmstudio-api-llms.txt](docs/references/lmstudio-api-llms.txt) |
| FastAPI patterns reference           | [docs/references/fastapi-llms.txt](docs/references/fastapi-llms.txt) |
| uv reference                         | [docs/references/uv-llms.txt](docs/references/uv-llms.txt) |

## Core rules (non-negotiable)

1. All configuration lives in environment variables. Never hardcode URLs, model names, or secrets.
2. Prompt construction lives in `app/story.py`. Routes in `app/main.py` must not build prompts.
3. All deps are managed via `pyproject.toml` with uv. Do not add deps any other way.
4. The `docs/` directory is the system of record. If a decision is made, it must be documented here.
5. When adding a new feature, create an execution plan in `docs/exec-plans/active/` first.
6. Read `docs/design-docs/core-beliefs.md` before making any architectural decision.
7. Every non-trivial feature must include tests. A feature is not complete until `make verify` passes. Read `docs/TESTING.md` before writing any test.
8. Execution plans must include a `## Tests` section (acceptance criteria before implementation) and a `## Verification` section ending with a TD-tracker checkbox (see `docs/TESTING.md`).

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
