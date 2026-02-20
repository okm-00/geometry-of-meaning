# Product Spec: Story App

## Purpose

A locally-served web application that generates short interactive stories using a local LLM.
The primary goal is to explore and build scaffolding for AI-assisted storytelling experiences.

## User experience

1. User opens `http://localhost:8000` in their browser.
2. A story is automatically generated (3–4 body paragraphs).
3. Two alternative final paragraphs ("endings") are generated alongside the body.
4. The first ending is displayed by default.
5. The user presses the **left arrow** or **right arrow** key to toggle between endings.
6. A visual indicator shows which ending is active (e.g. "← A | B →").
7. A "New Story" button triggers regeneration of the entire story including both endings.
8. A loading state is shown while generation is in progress.

## Acceptance criteria

- [ ] Page loads and auto-triggers story generation without user action.
- [ ] Story body (3–4 paragraphs) renders before the ending.
- [ ] Exactly two endings are generated and stored client-side.
- [ ] Left/right arrow keys switch between ending A and ending B.
- [ ] Active ending is visually distinguished (indicator shows A or B).
- [ ] "New Story" button clears current story and generates a new one.
- [ ] Loading state is shown during API call; UI is not interactive while loading.
- [ ] Errors from the API surface a user-readable message (not a raw stack trace).
- [ ] App works fully offline (only LM Studio needs to be running).

## Out of scope (v1)

- Story genre/theme selection by user
- Saving or sharing stories
- More than two endings
- Streaming text output
- Mobile layout optimization
- Authentication or multi-user support

## Future directions

- User-selectable story theme or seed prompt
- More than two branching endings (left/right + up/down)
- Paragraph-level branching (not just the final paragraph)
- Streaming generation for progressive display
- Story history / session persistence
