## Why

The tracker block leads today, above every task the board manages. It was put
there because an issue in progress is what is being worked on now, and because
the foot of a list — past the finished tasks — is where a person stops looking.

The first half of that has not held up in use. An issue has no time and no
date; it is far more like an all-day task than like the past-due work and the
morning appointments it currently sits above. Reading the day means reading
past seven rows that describe no particular hour before reaching the hours.

The second half still holds, and it decides where the block goes rather than
whether it moves. Measured on this account earlier today: 13 of 23 tasks were
finished by the evening. A block placed at the true foot of the list would
spend every evening buried under more completed rows than there are live ones.

So the block moves down to sit with the day's untimed work — after the tasks
still to do, and before the finished ones.

## What Changes

- The tracker block sits after every unfinished task the board manages and
  before the first finished or cancelled one, rather than above them all.
  Where a day has no finished tasks it ends the list; where every task is
  finished it leads them.
- The block stays a block: still not interleaved with tasks, still ordered by
  configured state and then by key within a state, still keeping that sequence
  whatever the day does.
- Ticking a task now moves it *past* the block rather than within the tasks
  above it, because the block is where the day's unfinished work ends. The
  requirement that the block "stays where it was, before the tasks" when
  something is ticked is restated in those terms; what it protects — the
  block's own sequence, and its not being reordered by the day — is unchanged.
- Nothing else about a tracker row changes: not what it shows, not that it
  counts as work, not that only opening acts on it, not the counts it appears
  in, not that it shows on today alone.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: two requirements modified — the one placing the block, which
  is also renamed because its name states the position being changed, and the
  one describing what today shows, whose first scenario says the rows appear
  above the day's tasks.

## Impact

- `main.py` — where the block joins the day's rows. One line becomes a small
  placement, beside the one that places events.
- No change to reading the tracker, to configuration, to what a row draws, or
  to any refusal. Only where the rows sit.
- The work filter, the hidden count and the tracked count are all computed
  before placement and are unaffected.
