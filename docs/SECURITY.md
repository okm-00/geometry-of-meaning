# SECURITY.md — Security Model and Constraints

## Threat model (v1)

This is a local-only application. It binds to `localhost` and is not intended to be
exposed to a network. The threat model is accordingly minimal.

## Constraints

| Constraint                                          | Status     |
|-----------------------------------------------------|------------|
| App binds to localhost only                         | enforced   |
| No user authentication required                     | accepted   |
| No secrets stored in the repository                 | enforced   |
| API keys never hardcoded                            | enforced   |
| LM Studio API key is a placeholder (`lm-studio`)   | accepted   |
| No external network calls at runtime                | enforced   |

## Environment variables

- `.env` is gitignored. Never commit `.env` to version control.
- `.env.example` contains only placeholder values — safe to commit.

## User-generated input

- v1 has no user text input fields. The only user input is arrow key presses (integer index toggle).
- Story text from the LLM is rendered via `textContent`, not `innerHTML` — no XSS risk.

## Future concerns (not in scope for v1)

- If the app is ever exposed beyond localhost, authentication must be added.
- If user input is accepted (e.g. story prompts), sanitization must be implemented.
- If stories are persisted, a data retention policy is needed.
