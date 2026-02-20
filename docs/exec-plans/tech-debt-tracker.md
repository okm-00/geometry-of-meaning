# Technical Debt Tracker

Log known technical debt here immediately when identified. Do not let it accumulate silently.
Each entry should have an ID, description, impact, and rough priority.

| ID    | Description                                              | Impact  | Priority | Added      | Resolved   |
|-------|----------------------------------------------------------|---------|----------|------------|------------|
| TD-1  | LLM response parsing has no retry on malformed JSON      | Low     | Low      | 2026-02-19 |            |
| ~~TD-2~~ | ~~No request timeout on LM Studio API calls~~        | Medium  | Medium   | 2026-02-19 | 2026-02-20 |
| TD-3  | Single HTML file will become unwieldy as UI grows        | Low     | Low      | 2026-02-19 |            |
| TD-4  | Test runs write to `logs/app.log` via the error handlers in `app/main.py`; log file mixes test noise with real runtime errors, making it harder to diagnose production issues by timestamp | Low | Low | 2026-02-20 | |

## How to use this tracker

- Add a row as soon as you identify debt — do not defer.
- When debt is resolved, mark it struck-through or remove it and note the resolution in the relevant exec-plan.
- Revisit this file at the start of any refactoring plan.
