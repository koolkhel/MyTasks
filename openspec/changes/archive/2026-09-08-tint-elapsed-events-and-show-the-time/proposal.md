## Why

The day now holds calendar events, and every one of them looks the same
whether it is over or still to come. A day read at four in the afternoon
presents the nine o'clock stand-up exactly as it presents the five o'clock
call, so the eye has to check each row's hour against a clock it does not
have.

There is no clock. The board shows a date and no time, so the one number
needed to read the day's events is the one number missing from the screen.

## What Changes

- An event whose end has passed is drawn receded, so the day reads as what is
  still ahead. The boundary is the event's **end**, not its start: a call that
  has begun and not finished is one there is still a chance of joining, and
  dimming it would say otherwise.
- The board shows the current time, at the right of its own header.
- The drawing keeps up with the clock. A tint defined against the current time
  is a promise the board has to keep as the hour passes, so it redraws when
  the set of ended events changes — and stays still when it does not.
- Receded means dim, not a hue. Measured: the row cursor replaces a cell's
  colour outright, so a hue disappears on the selected row — the reason a
  past-due task carries its age label as well as its colour. Dim survives the
  cursor, so it needs no second signal to fall back on.
- Not in scope: how far past due a *task* is. Those labels are computed from
  the instant the day was fetched, and go stale in a long sitting. A clock
  makes that visible but does not cause it, and putting it right means
  reconciling with counts the store itself computed — its own change, with its
  own evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: two requirements added — the board showing the current time,
  and an event that has ended being shown as past. Nothing existing changes:
  the rule that an event's row is told from a task's without relying on colour
  is untouched, because the mark that distinguishes them is untouched.

## Impact

- `ical.py` — whether an event has ended, asked of the event, which already
  carries the instant it ends.
- `main.py` — the header gains its clock, an event's row is drawn receded when
  it has ended, and a quiet timer redraws when that set changes.
- No new dependency and no new configuration. The clock is the one the UI
  framework already ships, which refreshes itself and does not redraw the list
  to do it.
