## Why

Pressing the key that starts a workspace is the one moment the board knows
that work on something has begun. It throws that away: the program is
launched, a line appears in the status bar, and the board goes back to looking
exactly as it did — the list gives no sign of which issue is being worked on,
and nothing anywhere says for how long.

So the two questions a person asks of their own board mid-afternoon — *what am
I on?* and *how long have I been on it?* — have no answer on it.

## What Changes

- Starting a workspace ends by showing that issue's card, rather than leaving
  the person looking at the list they were looking at before.
- The board remembers the one thing being worked on, and when that began.
- The card shows when work started and how long ago that was, whenever the row
  it is showing is the one being worked on — whether the card was opened by
  starting a workspace or by the key that opens a card on any row.
- Starting work on something else replaces what is remembered. One thing at a
  time, because a person is working on one thing at a time and a board that
  claimed otherwise would be describing a wish.
- Nothing is written down. The board forgets when it stops, and a restarted
  board shows no count even for work still going on. That is the whole of what
  this change promises, deliberately: an accumulated record of time worked is
  a different thing, wanted or not, and would be a different change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *Starting a workspace from an issue* gains its last step —
  the card opens on the issue just started. Beside it, one added requirement
  says what the board remembers about work in progress and what the card shows
  of it. The requirement that describes the focus view is untouched: it says
  what the card shows of a *task*, and this adds a line about something else.

## Impact

- `main.py` only: the tail of `action_start_workspace`, one field on the app,
  `TaskFocus`, and the key that opens a card passing what it knows.
- `tests/stub/t_workspace.py` (406 lines) gains the checks for the card
  opening and the clock.
- `tests/stub/t_star2.py` builds a `TaskFocus` directly, so the new
  information SHALL reach it as an optional argument and that suite SHALL keep
  passing unchanged.
- No new dependency, no configuration, nothing stored, no API call.
