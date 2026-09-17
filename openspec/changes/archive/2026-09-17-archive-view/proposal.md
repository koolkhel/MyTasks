## Why

A task the board finishes leaves it. The store keeps it -- the account this was
built against holds about 9,000 archived tasks against 541 live ones, seventeen
times what the board can reach -- but nothing in the terminal can show one
again. Looking up what was done, and when, means picking up the phone.

The store carries an archive date on every archived task and can filter on it,
so the material is there. What it cannot do is search titles or sort, which is
why this is a change rather than a query.

## What Changes

- A fourth view, reached by its own key, listing the tasks the store has
  archived: completed and cancelled, newest first by the date the store
  archived them.
- The archive is fetched whole the first time it is asked for, on a worker, and
  held for as long as the board is open. Nothing is written to disk, and a
  session that never opens the view fetches nothing.
- The search key narrows the whole held archive rather than only the rows on
  screen -- the store offers no text search, so the board is the only thing that
  can answer one.
- The view draws a bounded number of rows and reports what it is holding back.
  Drawing all of them costs about 150 ms a repaint, which is paid again on every
  mark, so the archive holds everything and draws the newest few hundred.
- Two keys write from the archive: `space` brings a task back (the store
  un-archives it and it returns to its own day), and `d` dates it, so a task
  brought back can be sent to today in the next press. A row written to stays
  on screen until the archive is re-read, so the second key has something to
  act on. Every other write is refused by name, before anything is announced.
  Marking, copying, the focus card and opening a link work as everywhere.
- Day movement, adding a task and reordering are inert in the archive, as they
  already are in the dateless views.

Recorded assumptions, settled while exploring:

- Cancelled tasks are in the archive, drawn with the mark and strike they
  already carry. They are a fifth of it.
- Tasks the store archived without their ever being ticked are not: the view is
  the finished ones.
- The date column and the view's name say **archived**, not completed. The store
  archives most tasks the moment they are ticked but sweeps the rest at
  midnight, so for a recent row the two differ by a day, and naming it
  completion would state as fact something the store does not know.
- Bringing a task back is in scope after all. The first draft made the view
  read-only and called that a default; it was a decision, and the wrong one --
  restoring a task from the archive is one of the two things a person opens an
  archive to do. Settled with the user: un-tick and date, nothing else.

## Capabilities

### New Capabilities

None. The archive is the board showing a different view, and every requirement
it needs sits beside the ones for the inbox and the someday view.

### Modified Capabilities

- `task-board`: a fourth view with its own key, its own contents and its own
  ordering; the view-naming, day-movement, task-adding and available-actions
  requirements extended to account for it; the search extended to reach a
  history larger than the view; and what a view withholds extended to cover a
  drawn-row bound.

## Impact

- `singularity.py` -- a query for the archived tasks, paged, and the archive
  date on the task model.
- `board.py` -- the archive as a position, its rows, their order, the bound on
  how many are drawn, and what the status line says about it.
- `main.py` -- the key, the worker that fetches, the held history, the day bar,
  and the refusals.
- `tests/stub/` -- a new suite for the view, and whatever existing suites
  enumerate the board's views.
- `README.md` -- the archive belongs in the feature list and in the key table.

No dependency is added. No file is written. The store is read with the same
client and the same token as every other fetch.
