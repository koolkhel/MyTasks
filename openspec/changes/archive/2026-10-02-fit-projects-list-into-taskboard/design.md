## Context

See proposal.md for why. What shapes the approach is what the board actually
draws, which turned out not to be what it computes.

The list has five columns. Four cost a fixed amount and the title takes the
remainder, worked out as the application's width minus a constant naming what
the other four cost including the two cells of padding the table puts around
each. At 104 columns that gives the title 69, and the five columns with their
padding come to exactly 104.

The table cannot draw in 104. It keeps two cells for a vertical scrollbar,
whether or not it is scrolling, so it draws in 102. Measured by rendering the
screen and reading the strips back rather than by trusting the arithmetic:

| | cells |
|---|---|
| application width | 104 |
| columns plus their padding | 104 |
| what the row actually draws as | 102 |

An eleven-cell project name comes out as ten. The same at three rows and at
sixty, so this is not the scrollbar appearing under a long list.

The names themselves, measured on the account as display widths rather than
character counts, since each begins with an emoji that costs two cells:

| | display width |
|---|---|
| three project names | 9, 9, 22 |
| the calendar names seen beside them | 8 and 11 |

So two of the three are being clipped by the arithmetic alone and nothing else.
One needs 24 cells, and no fix to the arithmetic reaches it.

## Goals / Non-Goals

**Goals:**

- Stop drawing more cells than the list can show, at every width and whatever
  the list holds.
- Give the project column the room its names need, once, and say in the spec
  which column pays for it.
- Leave the published pictures showing what the board now draws.

**Non-Goals:**

- An elastic project column. Weighed, measured and declined; the decision below
  records what would make it worth revisiting.
- Any change to how a title is shortened, which column holds what, or what any
  row says. Only the widths move.
- Anything about the emoji that opens each project name. They are two cells of
  the nine or the twenty-two, and they are the person's own data.

## Decisions

### The fit is computed against what the list can draw in

The constant that names what the other columns cost gains the two cells the
table reserves. The honest form is to take the number from the table rather
than to write two down, because two is this widget's answer today and not a
fact about terminals.

Against that: the width is needed before the table exists, at the moment the
columns are declared, and the board already measures from the application for
a reason it has written down — a resize reaches the application first, and
asking the table during one returns the width it is about to stop having.

Asking the table was tried first and does not work. It answers 0 until its
scrollbar is actually shown, and the columns are fitted before that, so the
first fit came out two cells too wide and only a later one was right. A width
that depends on when it is asked is this very fault wearing a different hat.

So the room is a constant, and a check pins it against what the widget reserves
in its own styles. The number cannot then drift away from the framework
unnoticed, which is the failure this whole change is an instance of.

Rejected: letting the table scroll sideways and calling it the person's
problem. The requirement already forbids it in so many words.

### The project column is fixed at 24, and the title pays

24 is what the widest name on the account needs. The title gives up the room
because it is the only column whose content has no natural length, because it
has the most to spare at any usable width, and because a shortened title still
reads where a shortened label does not.

The cost, stated plainly: thirteen cells off every title at every width, and
two more from the fix above. At 120 columns the title goes from 83 to 70, which
is ample. At 80 it reaches its minimum of 30 and the list begins scrolling
sooner than it did. That was measured and chosen rather than discovered later.

Rejected, with the measurement that would reopen it: an elastic column, taking
what the widest name on screen needs up to a cap. It costs nothing on a day
holding only the short names, which is most days. It was declined because the
title column would then change width as a person walks between days, and the
rows would shift under the hand moving through them — the same objection the
detail pane's fixed height is built on. If the project column ever has to hold
names long enough that a fixed width wastes real room on most days, this is
where to start.

### The width is one constant, used by every kind of row

A task's project, a tracker row's project, an event's calendar and a mail row's
correspondent all shorten to the same width and sit in the same column. One
constant for all four, as now, so the column cannot come to mean two widths
depending on which source a row came from.

## Risks / Trade-offs

- **Thirteen cells off every title, forever.** → Accepted and named in the
  proposal. It buys one project name, which was the ask. The elastic
  alternative and its price are recorded above.
- **The two reserved cells are this widget's number, not a law.** → Taken from
  the table where it can be, and pinned by a check against what the widget
  reports, so a framework that changes it fails a suite rather than silently
  clipping rows again.
- **A narrow terminal scrolls sooner.** → It scrolled before, at a narrower
  width. The minimum title width is unchanged, so what a person sees at the
  narrow end is the same list behaving the same way, reached a little earlier.
- **The published pictures go stale the moment the widths move.** → Remade in
  the same change, by the one command that makes them.

## Migration Plan

Nothing to migrate. The widths are computed on every layout and every resize,
nothing about them is stored, and no configuration changes. A person who
upgrades sees the new widths on the next draw.

Rolling back is restoring two constants.

## Open Questions

- Whether the other fixed column, the one holding the time or the tracker
  state, is also wider than it needs. It was not measured here because it was
  not in the way, and nothing in this change depends on the answer.
