## Why

Marking rows was built to copy them. Copying a set of tasks into another
program is half of moving them there; the other half is taking them off this
board, and that still has to be done one row at a time.

The same is true of everything else a person does to several rows at once.
Finishing a batch, cancelling a batch, pushing a batch to tomorrow: each is
one decision and seven keypresses per row, and the board already knows which
rows were meant — it is drawing them as a bar and counting them on the status
line.

## What Changes

- Every key that writes to a task acts on the marked rows when there are any:
  deleting, ticking and unticking, cancelling, dating, filing into a project,
  recording a day's work, and the green mark. With nothing marked, every one
  of them behaves exactly as it does today.
- The row under the cursor takes no part in the operation when rows are
  marked. A mark is a deliberate choice and the cursor is merely where
  somebody happens to be standing.
- The two keys that toggle — ticking and the green mark — drive the whole set
  to one state rather than flipping each row on its own. Where any marked row
  lacks the state, every marked row is given it; where every one has it, every
  one loses it. Flipping each row separately would answer a question nobody
  asked.
- Rows the board does not own are passed over rather than refused: a marked
  set holding mail, calendar or tracker rows has the board's own tasks written
  and the rest left alone, and the board says how many it passed over.
- Deleting a marked set asks once, and the question names how many rows will
  go. It also says when they come from more than the view on screen, because
  marks follow a person between views and a set can hold rows that cannot be
  seen.
- The rows stay marked after the write. The set is not consumed by being acted
  on: a batch can be ticked and then copied, or copied and then deleted.
- A marked set's writes are one action: one entry to undo, one report of what
  happened, and one confirmation where one is called for.

## Capabilities

### New Capabilities

None. Every key here already exists.

### Modified Capabilities

- `task-board`: which rows a write key acts on, what the two toggling keys do
  to a set that does not agree, what is confirmed before a set is deleted, and
  what happens to rows the board does not own. Two requirements are renamed
  because their names would otherwise say something untrue — actions are no
  longer offered only on the selected task, and marks are no longer only for
  copying.

## Impact

- `main.py`: the seven write actions, which each read one task today; the
  confirmation for deleting; and the report each action leaves behind.
- Nothing new is needed to keep the store happy. Sending many writes at once
  already has a queue and a measured width, built for pasting and reused here
  unchanged.
- No change to any module that talks to the store, the mailbox, the calendar
  or the tracker.
- One risk carried deliberately: a marked set stays marked after a write and
  can hold rows that are not on screen, so the status line's count and the
  confirmation before a deletion are what stand between a person and doing the
  same thing twice.
