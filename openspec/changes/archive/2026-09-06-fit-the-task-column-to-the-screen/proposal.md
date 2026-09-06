## Why

The column holding a task's title has no width, so it grows to fit the
longest title in the view and the table grows with it. A single long title
pushes the project column off the right-hand edge, and reading it means
scrolling sideways — on a full-screen terminal, not a cramped one. Measured
with a 124-character title on a 120-column terminal, the table wants 170
cells and 50 of them are off-screen.

The board has the room. It is simply giving all of it to one column.

## What Changes

- The title takes the width left over once the other columns have had
  theirs, so the table fits the terminal instead of overflowing it.
- A title too long for that width is shortened and **shown** to be
  shortened. Today a fixed width would cut it silently, with nothing to say
  the rest exists.
- The project column narrows from 22 cells to 11, which is what its names
  need and which gives the title 11 more cells at every width.
- A project name too long for 11 is shortened the same way, so that no
  column on the board cuts text without saying so.
- The title never shrinks below a readable minimum. Where the terminal is
  too narrow to give it that, the table scrolls as it does today rather than
  squeezing the title into nothing.
- The widths follow the terminal: making the window wider gives the title
  the new room, and narrower takes it back.

Shortening is by ellipsis, not by wrapping onto a second line. A wrapped row
would mean rows of differing height, a selection highlight spanning lines,
and the past-due colour and the strike-through of a finished task surviving
the wrap — a great deal of machinery for the same end.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: gains a requirement that the board fits its columns to the
  terminal it is in, marks any text it had to shorten, keeps the title
  readable at a minimum width, and scrolls rather than shrinking past it.

## Impact

- `main.py`: the column widths, the cell the title is built into, and a
  redraw when the terminal is resized.
- No change to `singularity.py` or `tracker.py`, to the ordering, to any
  write, or to any key.
- The focus view already promises the whole title "unlike the row it was
  opened from", so it is unaffected and its promise becomes more useful
  rather than less.
