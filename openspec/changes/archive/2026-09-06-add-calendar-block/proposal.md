## Why

The board knows everything a person put on a list and nothing about the time
they actually have. A day showing six tasks reads the same whether the hours
between nine and five are free or entirely spoken for. The meeting at two is
the reason the task at three will not happen, and the board cannot say so.

The calendar already holds that, on this machine, and it is only being read —
nothing about it needs to change for the board to show it.

## What Changes

- The day being viewed also shows the events in the calendar for that day,
  drawn from the machine's own calendar rather than fetched from anywhere.
- Events are **interleaved with the day's tasks by time**, not held apart in
  a block. A meeting at nine and a task at eleven read in the order they will
  happen, which is what makes the day legible. All-day events sit at the top,
  since they are the shape of the whole day rather than a moment in it.
- An event cannot be ticked, edited, rescheduled, reordered or deleted. It
  belongs to the calendar; showing it here does not make it the board's.
- Events from the work account are treated as work, so the key that hides
  work hides them along with the work tasks and the tracker's issues.
- Which accounts are shown is named in the environment. Two are: one whose
  events count as work and one whose do not.
- Where the calendar cannot be read — permission refused, withdrawn, or
  granted only in part — the board says so once and otherwise behaves exactly
  as it does today.

**BREAKING** for the ordering: a day's rows are no longer all tasks. The
requirements describing that order are being restated to say where an event
falls, which is a change to a contract other behaviour rests on.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: gains requirements for showing the day's events, for where
  they fall in the order, for refusing every change to them, for the work
  account being hidden by the work filter, for configuring which accounts are
  read, and for the board surviving a calendar it cannot read. The
  requirements that describe a day's ordering change, because they currently
  describe a list containing only tasks.

## Impact

- A new module, `ical.py`, read-only, in the shape `tracker.py` already
  established: its own configuration, its own single failure type, and rows
  the board joins without the rest of the board learning where they came from.
- `main.py`: the rows joining the day, the write refusal, the work filter, and
  the fetch when the shown day changes.
- `requirements.txt`: `pyobjc-framework-EventKit`, which brings `pyobjc-core`
  and `pyobjc-framework-Cocoa` with it. This is the board's first dependency
  that works on one operating system only, and the first that needs a
  permission granted outside the board.
- `.env`: two entries naming the accounts.
- No change to `singularity.py` or `tracker.py`, to any write, or to the
  existing keys.
