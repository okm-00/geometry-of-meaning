# FRONTEND.md — Frontend Conventions and Patterns

## Stack

- Single `static/index.html` file. No build step, no framework, no node_modules.
- Vanilla JavaScript (ES2020+), inline in the HTML file.
- CSS is inline in a `<style>` block in the same file.

## State model

All UI state lives in a single plain JS object:

```js
const state = {
  status: 'idle' | 'loading' | 'ready' | 'error',
  body: [],       // array of paragraph strings
  endings: [],    // array of exactly 2 ending strings
  activeEnding: 0 // 0 or 1
};
```

State is mutated only via a `setState(patch)` function that merges the patch and calls `render()`.
Direct DOM manipulation outside of `render()` is not allowed.

## Render cycle

`render()` is a pure function of `state`. It:
1. Clears the story container.
2. Renders based on `state.status`.
3. Does not hold any state itself.

## API calls

- All API calls go through a single `fetchStory()` async function.
- On call start: `setState({ status: 'loading' })`.
- On success: `setState({ status: 'ready', body: ..., endings: ..., activeEnding: 0 })`.
- On error: `setState({ status: 'error' })`.

## Keyboard handling

- Arrow keys are handled by a single `keydown` listener on `document`.
- Only active when `state.status === 'ready'`.
- Left arrow: `setState({ activeEnding: 0 })`.
- Right arrow: `setState({ activeEnding: 1 })`.

## Do not

- Do not add external JS dependencies (no jQuery, no Alpine, no HTMX) without a design decision.
- Do not add a build step without a design decision.
- Do not split into multiple files without a design decision.
- Do not use `innerHTML` for user-generated text — use `textContent` or `createElement`.
