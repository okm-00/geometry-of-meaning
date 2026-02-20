# PRODUCT_SENSE.md — Product Goals and User Intuition

## What this product is

An experimental storytelling application that explores AI-assisted interactive narrative.
The experience should feel like reading a book where you can nudge the ending.

## Who uses it

Currently: the developer / researcher experimenting with AI storytelling scaffolding.
Target: anyone curious about branching narrative experiences powered by local LLMs.

## What success looks like

- A user opens the app, reads a generated story, and wants to read another one.
- The two endings feel meaningfully different — not just paraphrases of each other.
- The transition between endings is instant and frictionless.
- The whole experience feels polished despite being a local prototype.

## What to optimize for

1. **Story quality**: Endings must feel distinct and narratively satisfying.
2. **Simplicity**: The interface should not require explanation.
3. **Speed**: Generation should feel fast enough not to break immersion.
4. **Reliability**: The app should not crash or produce broken output silently.

## What not to optimize for (yet)

- Feature breadth — resist adding features until the core experience is excellent.
- Mobile or multi-user support.
- Persistence or sharing.

## Product intuitions

- The "two endings" mechanic is the core value. Everything else serves it.
- Users will want to re-read the body before toggling the ending — don't clear it too fast.
- A loading state that is too slow will break the experience. Consider streaming in a future iteration.
- The story genre/tone should vary across generations — sameness kills replayability.
