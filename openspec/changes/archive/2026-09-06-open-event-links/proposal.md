## Why

The board now shows the day's calendar events, but shows only when each starts
and what it is called. For a meeting, the thing a person actually needs at the
moment it begins is the address that joins it — and that address is in the
event, sitting one keystroke away from being useful and currently unreachable.

Measured on this machine over a 42-day window: of 128 events from the
configured accounts, 47 carry a description, and every one of those 47 carries
exactly one web address. Reaching it today means leaving the board and opening
the calendar application to copy it out.

The board already opens a task's link and a tracker issue's page with the same
key. An event's link is the third case of a pattern that exists, not a new
idea.

## What Changes

- An event's row carries the web address found in the event, and the key that
  opens a task's link opens it.
- The address is taken from the event's location, or from its description when
  the location holds none. Both are read because a calendar system may fill
  either; where both were filled here, they always named the same address.
- An event's description is shown in the same place a task's note is shown,
  so a person can read what a meeting is for without leaving the board.
- An event with no address says so when the key is pressed, in words that
  name it an event rather than a task.
- Not a breaking change: nothing a task or a tracker row does today is
  altered, and no key gains a new meaning.

## Capabilities

### New Capabilities

None. This extends the board's existing behaviour rather than introducing a
capability of its own.

### Modified Capabilities

- `task-board`: two requirements added — opening an event's link, and showing
  an event's description in the detail area. Two modified — the requirement
  that an event cannot be changed gains the statement that opening it is not a
  change and remains available, and the requirement restricting which schemes
  are opened is widened from a task's title to the event text this change
  begins reading.

## Impact

- `ical.py` — the event record gains its description and the address found in
  it; the read gains two more fields from the framework.
- `main.py` — the event row carries the address and the description; the
  action that opens a link learns the event case, beside the tracker case it
  already has; the help overlay gains a line.
- No new dependency, no change to what is configured, no change to what is
  written anywhere. The calendar stays read-only.
- An event's description is personal content and now sits in the row's data
  and on the screen. It is never written to disk, never sent anywhere, and
  must not appear in a test fixture, a captured board state, or a commit.
