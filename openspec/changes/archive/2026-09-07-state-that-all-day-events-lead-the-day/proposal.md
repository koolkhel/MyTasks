## Why

An all-day calendar event leads the day, above every other row — above the
past-due tasks, above the day's own untimed tasks, and above the tracker
block. That is what the board does and what is wanted.

The requirement says less than that. It says an all-day event sits "above the
rows that happen at a time", which is true but silent about every row that
does not happen at a time. A reader could satisfy the requirement while
putting an all-day event below the past-due tasks, or among the day's own
all-day tasks, and be within the letter of it.

The placement was also recorded as provisional — accepted "for now" while the
calendar block was being built. It is not provisional any more, and a
requirement that states a decision weakly is the kind that gets reversed by
accident later.

## What Changes

- The requirement states that an all-day event leads the day, above every
  other row, with the reason: it describes the whole day, so nothing that
  happens within the day outranks it.
- Scenarios are added pinning it against the rows the old wording did not
  reach — a past-due task, the day's own all-day tasks, and the tracker block.
- **No behaviour changes.** The board already does this; the requirement is
  being brought up to what it does and what was decided.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement modified — how an event is ordered among the
  day's rows, whose sentence about all-day events is widened from "above the
  rows that happen at a time" to "above every other row", with scenarios for
  the rows it did not previously mention.

## Impact

- No source change. This is a requirement catching up with the board.
- The suite gains checks for the cases the requirement now states, which is
  where the value is: the old wording was satisfied by behaviour that would
  have looked wrong, so nothing was stopping it from drifting there.
