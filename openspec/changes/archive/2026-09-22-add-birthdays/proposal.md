## Why

The board selects calendars by **source account** only. A person who wants one
particular calendar on the board — a calendar of contact birthdays, kept by the
system from the address book — has no way to say so: naming that calendar in the
configuration matches nothing, and because an entry that matches nothing is
treated as the calendar being unreadable, the attempt removes *every* event from
the board and replaces them with a message. The natural thing to try is both
ineffective and destructive, and it reads as the feature being broken.

The account is also the wrong grain for the request. A birthday calendar
typically sits in a source that a person does not otherwise want on their board,
so "read the whole account" is not an answer either.

## What Changes

- An entry in the calendar configuration matches a **source account title or a
  calendar title**. Naming an account reads every calendar in it, as now; naming
  a calendar reads that calendar. No new variable and no new syntax — the
  existing two entries simply accept one more kind of name.
- Which entry counts as **work** follows the same rule, so naming a calendar as
  the work one keeps the key that hides work working on its events.
- An entry that matches nothing on the machine no longer blanks the calendar.
  The calendars that did match are still shown, and the entry that matched
  nothing is reported in a message that stands until it is put right — the way
  the board already treats a source that is reporting trouble.
- Not in this change: any notion of showing an event before the day it falls on.
  An event still appears on its own day and nowhere else.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *Which calendar accounts are read is configured, not built in* —
  a configured entry names an account **or** a calendar, and an entry matching
  nothing is reported without withdrawing the calendars that matched.
- `task-board`: *Work events are hidden with the rest of the work* — an event
  counts as work when the work entry names either its account or its calendar.

## Impact

- `ical.py` — `Config` gains the account-or-calendar match and a work test that
  reads both; `fetch` selects on either title, and reports unmatched entries
  alongside the events it did read instead of raising for them.
- `main.py` — the calendar worker takes events and unmatched entries together,
  so a partial reading both draws its events and leaves a standing message.
- `board.py` — the work test for an event row is given the event's calendar as
  well as its account.
- `README.md` — the configuration table describes the two entries as naming
  accounts or calendars.
- `docs/screenshots.py` — substitutes `ical.fetch` to draw the README's
  pictures from invented data, so it follows the new return type.
- `tests/stub/` — a new self-contained suite for the matching rules and the
  partial-reading path; `tests/config/t_ical.py` extended where it already
  covers account filtering.
- Seventeen places across the suites and `docs/` replace `ical.fetch` with a
  stand-in returning a bare list, and each follows the new return type. They
  are mechanical, but they are not optional: three of them were missed on a
  first pass and the tier reported three crashes rather than three failures.
- No change to what the board writes, to the task store, or to any other source.
  Reading stays read-only, and no account or calendar name enters the source.
