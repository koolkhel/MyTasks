## Why

The tracker block is ordered by state and then by key, and the specification
says so -- twice, once to promise it and once to say that the priority letter
on each row changes nothing about the order. That was right when the letter
arrived: it was a label, and the block was short. It is wrong for how the
block is read now. A person looking at what is in progress wants the most
urgent thing at the top, and a block ordered by key puts a show-stopper below
a minor issue because its number is larger.

## What Changes

- The block is ordered by priority, most urgent first; within one priority by
  the configured order of states, as before; within one state by key, as
  before. An issue the tracker holds no priority for goes after every issue
  that has one.
- The order comes from the tracker, not from the board. The tracker lists its
  priorities in an order of its own and hands each value's position -- its
  ordinal -- alongside its name. The board asks for that position on the
  request it already makes and sorts by it. It keeps no list of priority
  names, exactly as it keeps none for the letter on the row: a priority the
  tracker renames, adds or reorders needs no change here.
- The letter on the row does not change, and neither does anything else the
  row shows.

Recorded assumptions, settled while exploring against the tracker:

- Every priority value the tracker hands an issue carries an integer
  position, ascending from most urgent. Confirmed on this tracker for all
  three priority bundles it defines, including one starting at -1 and one
  with two levels named in another language.
- Different projects may use different bundles, so the same word can sit at
  neighbouring positions in two of them. Within one bundle the order is
  exact; across bundles it is the tracker's, and the board does not try to
  reconcile it. The secondary keys -- state, then key -- are what keep two
  issues of like urgency in a stable, predictable place.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: "The tracker block sits below the day's unfinished tasks and
  is not ordered" -- the order within the block; "A tracker row says how
  urgent the tracker calls it" -- the priority now orders the block; and one
  requirement added for how urgency is read as the tracker's own order.

## Impact

- `tracker.py` -- `ordinal` on the value fields asked for; `priority_rank` on
  `Issue`; the sort in `parse()`.
- `tests/stub/t_version.py` (which builds raw issues by hand) and
  `tests/stub/t_track2.py` (the block's order).
- `docs/screenshots.py` -- the two invented issues at different priorities,
  the more urgent listed first.
- No change to `board.py` or `main.py`: the block is handed over already
  ordered, and the board draws it as it always has.
