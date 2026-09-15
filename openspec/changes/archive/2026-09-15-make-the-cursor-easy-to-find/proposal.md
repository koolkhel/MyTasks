## Why

The selected row is the hardest row on the board to see, and once several rows
are marked it cannot reliably be found at all.

Measured against the bar it is drawn on, the selected row's own text comes out
at 2.48 to 1. A marked row's text on the same bar is 2.68 to 1. The row that
says where a person is is less legible than the rows around it — and since
marking gave a marked row that same bar, a cursor sitting in a run of marked
rows is one bar among several, told apart only by the weight of its text.

This is not a new want. The board already requires that the selected row's
background differ from the surrounding rows and that its text be legible
against it. Drawing marked rows on the selected row's own bar made the first
of those false whenever anything is marked, and nothing checked it.

The cause of the second is older than marking. The selected row's text colour
is asked of the theme as "whatever contrasts", and against a mid-tone bar that
resolves to a light colour — light text on a mid-tone ground, which is the
worst of the three choices available.

## What Changes

- The selected row is drawn on a brighter bar than a marked row, so the two
  are told apart by colour rather than by the weight of their text. Colour can
  be seen at a glance and from the corner of the eye; weight has to be read.
- Its text comes out dark rather than light, because the bar it sits on is a
  light one and the theme resolves it that way. This takes the selected row
  from 2.48 to 1 to 13.67 to 1 and makes it the most legible row on the board
  rather than the least. The text colour is not stated: stating it was tried
  and measured worse under one of the two themes.
- A marked row keeps the bar it has. Nothing about marking, copying or the
  cursor's movement changes.
- Both colours are ones the themes already declare. No new value is
  introduced, and the brighter one is currently used nowhere.
- The selected row becomes findable when nothing is marked as well, which it
  was not before: its bar now differs from the ground by much more than it
  did.

## Capabilities

### New Capabilities

None. This is how an existing row is drawn.

### Modified Capabilities

- `task-board`: what the selected row is drawn in, and how it is told apart
  from a marked row. Also the requirement that a theme keeps the board's
  distinctions visible, which already demands the selected row differ from the
  rows around it and gains the case that made it false — being surrounded by
  marked rows.

## Impact

- `main.py`: the stylesheet rule for the selected row, and the row-style hook
  that gives a marked row its bar — which reads the selected row's background
  today and must stop doing so once the two differ.
- No change to any module that talks to the store, the mailbox, the calendar
  or the tracker, and nothing here writes anything.
- The board's palette rule is unaffected: both themes already declare both
  colours, so "looks like Turbo C++" stays checkable rather than becoming a
  matter of taste.
