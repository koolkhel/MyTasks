## Why

Every timed event on a day is drawn in the wrong place as soon as that day
holds a past-due task. Observed on today's board: four events at 11:00, 12:00,
17:00 and 18:00, all stacked at the top, above a task at 08:00.

This contradicts a requirement the board already carries — *an event at nine
and a task at eleven appear in that order*. An event at eighteen appearing
above a task at eight is that same sentence, failing.

The cause is a wrong assumption in how an event is placed. A timed event is
inserted above the first row that happens later than it, and a row naming no
time was defined as later than any event — on the reasoning that untimed rows
sit at the end of a day. They do not. The day's order is banded, and untimed
rows occur in more than one band:

```
   assumed        [ timed ....... ][ untimed ]
   actual         [ green ][ past due ][ pinned ][ timed ][ untimed ][ done ]
                                ^                              ^
                          untimed, at the top             untimed again
```

A past-due task names no time, so it is the first row of the day, and every
timed event is inserted above it.

## What Changes

- An event takes its place by the same ordering the tasks use, rather than by
  the clock alone. It is ordered as what it is: unfinished, untagged, not past
  due, unpinned, and happening at its hour.
- A past-due task therefore stays above an event, a finished task stays below
  one, and an event lands beside the task that shares its hour.
- **The requirement that an event is not subject to the rules ordering tasks
  is replaced.** That sentence is what produced the defect: an event has no
  opinion about being finished or overdue, but it still has to be *placed*
  relative to rows that do.
- What does not change: events are still inserted into the tasks rather than
  sorted with them, so removing every event still leaves the tasks in exactly
  the order they would have had alone. That guarantee holds by construction,
  as it does today.
- An all-day event still leads the day. Unchanged and out of scope here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement modified — how an event is ordered among the
  day's rows, replacing the rule that placed it by clock time against every
  row with one that places it within the same bands the tasks are ordered by.

## Impact

- `main.py` — how an event's row is placed among the sorted tasks. One
  function.
- No change to what is read, written, configured, or drawn. An event's row is
  identical; only where it sits changes.
- The existing scenario covering this passed because the day it describes has
  no past-due row and no finished row in it. The cases that reproduce the
  defect are the ones this change must add.
