# Design Decisions Index

A catalogue of all significant design decisions made in this project.
Each entry links to the decision record or inline documents the rationale.

| ID   | Decision                                         | Status    | Rationale summary                                              |
|------|--------------------------------------------------|-----------|----------------------------------------------------------------|
| DD-1 | Use LM Studio + openai SDK for LLM calls         | accepted  | OpenAI-compatible API; SDK is stable and widely documented     |
| DD-2 | Single `index.html`, no build step               | accepted  | Minimizes tooling surface; agent can read/modify the entire UI |
| DD-3 | FastAPI serves both HTML and API from one process| accepted  | Single process = simpler local dev; no CORS complexity         |
| DD-4 | Prompt requests structured JSON output           | accepted  | Avoids brittle text parsing; LLMs handle JSON well             |
| DD-5 | Two endings generated in a single LLM call       | accepted  | Fewer round-trips; both endings share narrative context        |
| DD-6 | uv for package management                        | accepted  | Fast, reproducible, single pyproject.toml source of truth      |

## How to add a new entry

1. Assign the next `DD-N` ID.
2. Add a row to the table above.
3. If the decision is complex (trade-offs, rejected alternatives), create a dedicated file
   at `docs/design-docs/DD-N-short-title.md` and link it from the table.
