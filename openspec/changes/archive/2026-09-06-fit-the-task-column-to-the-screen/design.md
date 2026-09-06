## Context

See proposal.md — Why.

Every number below was measured against a running board or a stand-in for
one, not reasoned about.

The row is built in one place, and the columns are declared in one place.
The title cell is assembled from layered markup — a link injected inside the
text, then a strike for a finished task, then a colour for a past-due one —
which is what makes shortening it more delicate than cutting a string.

## Goals / Non-Goals

**Goals:**

- Every column of a row visible without scrolling sideways.
- A shortened title that admits it was shortened.

**Non-Goals:**

- Wrapping a title onto further lines. Rows of differing height, a selection
  highlight spanning lines, and colour and strike surviving a wrap — a great
  deal of machinery for the same end, and rejected before this was planned.
- Shortening anything but what does not fit. A title that fits is untouched.

## Decisions

**The title takes what is left, not a share of the screen.**

The other columns and the table's own padding cost a fixed amount whatever
the terminal:

```
   mark(1) + checkbox(2) + when(11) + project(11)  = 25
   padding, 2 per column across 5 columns          = 10
                                            total  = 35
```

A share of the screen was considered first and does not work, because the
fixed cost is added to it rather than taken out of it:

```
   terminal   "80% of it"  fits?      what is left  fits?
      80            64       NO                 34    yes
     100            80       NO                 54    yes
     120            96       NO                 74    yes
     160           128       NO                114    yes
```

So the width is `max(minimum, terminal - 35)`.

**The project column narrows from 22 to 11.** Its names are 8, 8 and 21
cells; 11 holds the common ones and gives the title 11 more cells at every
width. The 21-cell name no longer fits, which is why it too must show that
it was shortened — otherwise this change would create, one column over, the
very silent cutting it exists to remove.

**The minimum is 30 cells, and below it the list scrolls.** Measured with
the widths above:

```
   terminal   title gets   table wants   viewport   verdict
       50           30            65         50     scrolls 15
       60           30            65         60     scrolls 5
       65           30            65         65     fits          <- the threshold
       80           45            80         80     fits
      120           85           120        120     fits
      160          125           160        160     fits
```

At 65 columns and above nothing scrolls. Below it the minimum holds and the
list scrolls as it does today, which is no worse than the present behaviour
and better than an unreadable title.

**Shortening is done by the text, not by the column.** Giving a column a
width makes the terminal library cut the text with nothing to show for it:

```
   |a linked bit and then a great deal more   |   <- a column of width 40
   |a linked bit and then a great deal more...|   <- shortened as text
```

The first is what a width alone produces. So the cell is built as text that
knows its own styling and is shortened by it, which was measured to keep the
link intact across the cut — the span survived at its original offsets — and
to add the ellipsis the column would not. Cutting the markup *string*
instead would sooner or later cut inside a link and corrupt it.

**Widths follow the terminal.** They are computed from the current width
rather than fixed at startup, and recomputed when the terminal is resized;
the board already answers resize elsewhere, so there is a place for it.

## Risks / Trade-offs

**A shortened title hides its end** → Accepted, and already answered: the
focus view shows the whole title, and its requirement already says "unlike
the row it was opened from". This change makes that promise more useful
rather than contradicting it.

**The project column loses 11 cells** → Accepted on the user's judgement,
with the ellipsis added so the one name that no longer fits still reads as
deliberately shortened.

**Recomputing on resize is state that can go stale** → The width is derived
from the terminal at draw time rather than stored and updated, so there is
nothing to fall out of step; a resize simply redraws.

**A terminal narrower than 65 columns still scrolls** → Accepted and
specified. It is the present behaviour, kept deliberately for the case where
the alternative is a title too short to recognise.
