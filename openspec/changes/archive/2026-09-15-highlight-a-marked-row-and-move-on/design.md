## Context

See proposal.md — Why. What follows is only what the framework and the board's
own drawing force on the approach.

The table draws a cell in two layers. The framework renders each cell as
`Styled(cell, pre_style=..., post_style=...)`: the pre-style sits under the
cell's own markup, and the post-style goes over it. A row's background comes
from a hook that feeds the pre-style, so the cell's markup paints on top of
it. The selected row's colours come from the post-style, which is why they
replace whatever the cell asked for.

That second half is not new knowledge here. The board already records it, in
the note beside the colour it draws a past-due title in: the cursor style
replaces a cell's colour outright on the selected row, for every row, so a
past-due row that is selected is told apart by its age label instead.

The post-style is built from the cursor and hover flags and from nothing else.
There is no hook that puts an arbitrary row's style there.

The relevant colours, measured rather than assumed. The selected row draws
bold `#ddf3f3` on `#00aaaa`; an ordinary row draws `#feff55` on the ground.
Against that bar: the ordinary colour is 2.68 to 1, the selected row's own
text is 2.48 to 1, a past-due title is 1.30 to 1 and a dimmed one 1.23 to 1.
The bar against the ground is 7.33 to 1 in the dark theme and 4.64 to 1 in the
blue one.

## Goals / Non-Goals

**Goals:**

- A bar that covers the row's whole width, the padding between columns
  included, so it reads as a bar rather than as highlighted words.
- A marked row and the selected row that stay tellable apart.
- A framework hook whose loss is noticed by a failing check rather than by a
  feature that quietly stops drawing.

**Non-Goals:**

- Changing what marking means, what it writes, how long it lasts or which
  rows accept it. Only how it is drawn and where the cursor goes.
- Reworking the table's rendering. One hook is overridden and nothing else.
- Making the bar accessible in a general sense. This board draws a selected
  row at 2.48 to 1 and has committed to that palette; the aim here is to be
  no worse than the row beside it, which the ordinary colour already is.

## Decisions

### The background comes from the row-style hook, the legibility from the cell

Two pieces, because neither does the whole job.

The row-style hook gives a background across the full width. It cannot give
legibility: it feeds the pre-style, so the cell's own markup still paints its
colour on top, and the measurements above say a past-due or dimmed title on
the bar is unreadable.

So the cell stops asking. Where a row is marked, the title is built without
the past-due colour and without the dimming, and falls back to the ordinary
text colour. The result is the same as the selected row's — the row loses its
title colour — reached from the other end, because the post-style that does it
for the selected row is not available for any other.

Alternative considered and rejected: overriding the cell-rendering method so
that a marked row's style could go in the post-style, exactly as the cursor's
does. That is a long method with two caches and a private signature, and
taking it over to change one style would put the whole of the table's
rendering in this board's keeping.

### The table is subclassed, which costs the suites nothing

The hook is a method, so reaching it means a `DataTable` subclass. Querying by
type finds a subclass, so every suite that reaches the table by its type or
its id goes on finding it — checked rather than assumed, because about fifteen
suites do exactly that.

### The marked style is the selected row's background with ordinary text

Not a colour of its own. The board's themes declare the DOS sixteen colours
and nothing else, and a dimmed or blended cyan would be a value neither theme
holds. Using the bar the board already has keeps that rule and gives the two
states the relationship a Turbo palette draws between a selection and an
active selection: the same bar, the active one brighter.

### The mark's own character stays

It costs no width — the column it sits in is two cells and every row draws one
— and on the row under the cursor it is the only thing left saying the row is
marked, since the cursor's bar covers the mark's. Without it, pressing the key
on the last row, where the cursor does not move, would give no visible answer
at all.

### The cursor moves before the repaint, not after

Redrawing puts the cursor back on the row the board has recorded as selected,
so moving the table's cursor and then redrawing would undo the move. The
selection is set to the next row first and the redraw follows, which is how
ticking already moves the selection on.

## Risks / Trade-offs

**The row-style hook is private** → A framework upgrade could rename or remove
it, and marks would silently stop being drawn: no error, no failing import,
just no bar. Mitigated by a check that asserts the hook exists on the
framework's own class, so an upgrade breaks a suite rather than the feature.
The board already pins framework behaviour this way elsewhere.

**A marked row loses its own title colour** → A past-due row that is marked no
longer shows the past-due colour. Accepted because it is what the selected row
already does, and because the age label still says the row is past due. The
alternative is a title at 1.3 to 1, which is not a trade-off but a defect.

**A run of marks reads as one long bar** → With several adjacent rows marked
the screen shows a block of bar rather than separate rows. The cursor is still
findable inside it, being the bold one, and the mark characters run down the
column. Watched rather than designed around: it is the look the change is for.

**Moving on when a mark comes off** → Correcting a mark walks the cursor away
from the row just corrected. Taken deliberately as the simpler rule, and it is
what the same key does elsewhere in the tools this borrows from.

## Open Questions

None. The colours are measured, the hook is identified, and the two behaviours
are settled.
