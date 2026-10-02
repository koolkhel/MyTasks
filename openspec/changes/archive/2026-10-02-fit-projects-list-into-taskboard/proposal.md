## Why

Every row on the board loses its last two cells, and has done at every width
since the columns were first fitted to the terminal. The title column is sized
as the terminal's width minus what the other columns cost, and that cost never
counted the two cells the table reserves for its own vertical scrollbar. So the
board lays out 104 cells of columns into a 102-cell space and the right edge is
cut.

It is the project column that pays, being last. Measured by rendering the
screen rather than by reading the arithmetic: at 104 columns the drawn line
comes out 102 cells, and an eleven-cell project name arrives as ten. It happens
with three rows as readily as sixty, so it is not the scrollbar appearing when a
list grows long; the table reserves the room either way.

That alone is a defect, and the existing requirement already forbids it in so
many words: a person is to see every column of a row without scrolling
sideways. Two of the three project names on this account fit in eleven cells
and are being clipped by this and nothing else.

The third does not fit at eleven however the arithmetic is fixed. It is 22
cells wide, and a project name shortened to ten is not a name a person can
read: unlike a title, which carries its own words and reads sensibly when cut,
a project name is a label from a small fixed set and a cut one has to be
guessed at.

## What Changes

- The width the columns are fitted into SHALL be the width the table can
  actually draw in, not the width of the application. Whatever the table keeps
  for its own furniture comes off before the title takes what is left, so no
  column is cut by it.
- The project column grows from eleven cells to twenty-four, which is what the
  widest name on this account needs. The title column gives up the room, being
  the column with the most to spare and the one that shortens gracefully.
- **BREAKING** nothing in behaviour, but every title is thirteen cells shorter
  at every width, and two cells shorter again from the fix above. On a terminal
  too narrow to leave the title its minimum, the list begins scrolling sooner
  than it did. That is the trade, it was measured before being chosen, and it
  buys one project name.

Not in scope: making the project column elastic, so that it takes what the
widest name on screen needs and no more. It was weighed and declined because
the title column would then change width as a person walks between days, and
this board has been careful elsewhere that nothing moves under the hand that is
moving through it. The design records the measurement that would make it worth
revisiting.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `task-board`: the requirement that fits the columns to the terminal gains the
  rule that the room the table keeps for itself is counted, so that its promise
  of every column being visible is actually kept. A new requirement states how
  wide the column naming a project is chosen to be, and which column yields the
  room.

## Impact

- `main.py`: the constant that says what the columns other than the title cost,
  and where the title's width is worked out from the application's size.
- `board.py`: the project column's width, which the task row, the tracker row,
  the event row and the mail row all shorten to.
- `tests/`: the suites that pin the fitted widths, and a new part that holds the
  drawn line to the width the table can show rather than to the arithmetic.
- `README.md` and `docs/screenshots.py`: the published pictures show the
  columns, so they are taken again.
- No configuration, no new dependency, and nothing a person must do after
  upgrading.
