## Context

See proposal.md — Why for the measurements. What matters for the approach: the built-in footer is fixed at one row (`height: 1`, `layout: horizontal` in its own default styling) and has no wrapping mode. Three CSS-only routes were tried against the real board and each failed in its own way:

- `Footer { height: 2 }` — no effect at all; the row stays one line and still truncates.
- `Footer { layout: vertical }` — one entry per row, so sixteen rows of which two are visible.
- `Footer { height: 2; layout: grid; grid-size: 8 2 }` — all sixteen entries appear, but the cells are equal width, so every label is clipped to fit the narrowest: `q Qu`, `h Pre`, `l Nex`.

The grid route is the interesting failure: it proves the entries can be placed on two rows, and that equal-width cells are the wrong distribution. Entries vary from 5 cells (`a Add`) to 11 (`. Did today`), so the rows have to be packed by measured width.

## Goals / Non-Goals

**Goals:**

- Every binding visible in full, at the widths this board is actually used at.
- The bar derived from the board's own bindings, so it cannot drift from what the keys do.
- No change to how any key behaves — this is a display, and bindings stay on the app where they already are.

**Non-Goals:**

- Anything about refresh. `r` already reloads and was verified against the live API; see proposal.md.
- Configurable layout, a fixed number of rows, or a way to hide the bar. It wraps to what it needs and that is all.
- Replacing the help overlay. The overlay stays the fuller reference, with its grouping and its explanatory notes; the bar is the at-a-glance reminder.

## Decisions

**A small custom widget, because CSS cannot express this.** Not a preference — the three routes above are the evidence. The widget reads the app's shown bindings, measures each entry, packs them greedily into rows that fit the available width, and re-packs on resize.

**Derive the entries from the bindings rather than writing them out.** The spec requires the bar and the board to agree about which keys exist, and the only way to guarantee that is to have one source. A hand-written list would be correct on the day it was written and wrong at the next change — which is exactly how the help overlay and the footer could have drifted before now.

**Keep the command-palette hint.** It is a working route into Textual's palette and nothing about this change argues for removing it; it simply becomes one more entry the packing has to fit.

**Pack greedily, left to right, rather than balancing the rows.** Balancing would look tidier but reorders entries relative to the bindings list, which is the order a person learns them in. Reading order matters more than an even right edge here.

**Re-pack on resize rather than measuring once.** A bar packed for the width at startup would clip again the moment the terminal narrowed, which is the bug being fixed.

## Risks / Trade-offs

- **Clicking an entry to invoke it is lost.** The built-in footer supports it; a widget that draws its own text does not, unless click handling is added. Accepted: this is a keyboard-driven board and every entry is reachable by its key. Recorded because it is a real capability being given up, not an oversight — adding click handling later is a small, separate change.
- **The bar takes a second row, so the task list loses a line.** Intended, and specified. At 80 columns it takes three rows and the list loses two.
- **A very narrow terminal wraps further still.** At 40 columns the bar would need five or six rows and crowd the list badly. No cap is imposed, because capping means either clipping or omitting, and both are the thing being fixed. A terminal that narrow cannot usefully show the task table anyway.
- **The widget must not swallow key events.** It is a display; if it took focus, the keys it advertises would stop reaching the app. Something to verify rather than assume, and the tasks call for it explicitly.
