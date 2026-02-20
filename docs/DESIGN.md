# DESIGN.md — Visual and UX Design Principles

## Aesthetic

- Dark background, high-contrast text — reading comfort for long-form text.
- Serif or readable sans-serif font for story body — prioritize legibility.
- Minimal chrome: no sidebars, no navigation, no distractions.
- The story is the interface.

## Layout

- Single centered column, max-width ~680px — optimal reading line length.
- Body paragraphs have generous line-height (1.7–1.8) and paragraph spacing.
- The active ending is visually separated from the body (e.g. a subtle divider or different treatment).

## Interaction

- Arrow key affordance is indicated clearly — user should not have to discover it.
- The A/B toggle indicator is always visible when a story is loaded.
- Loading state uses a simple, non-intrusive animation (e.g. pulsing text, not a spinner).
- Errors use a calm, readable inline message — not modal alerts.

## Color palette (v1)

- Background: `#0f0f0f` or similar near-black
- Body text: `#e8e6e3` warm off-white
- Ending text: slightly different treatment to signal "this is the ending"
- Accent: a single muted tone for interactive elements (buttons, indicators)

## Typography

- Body: system serif or a clean sans-serif (e.g. Georgia, or system-ui)
- UI chrome (buttons, labels): system-ui, small size

## Responsive

v1 targets desktop only. No mobile optimization required.
