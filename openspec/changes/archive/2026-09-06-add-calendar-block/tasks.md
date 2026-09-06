## 1. Reading the calendar

- [x] 1.1 Add `ical.py` in the shape `tracker.py` established — its own configuration read from the environment, one failure type, and a plain event record — and verify the source names no account and no calendar
- [x] 1.2 Read the accounts named in the environment and nothing else, and verify against the machine that only their events come back and the other accounts' do not
- [x] 1.3 Ask for a day's events and verify against the machine that a repeating event appears on a day it falls on but did not begin — the thing that ruled out the scripting interface
- [x] 1.4 Verify a day query answers in a few milliseconds, so that changing day can simply ask again with nothing cached
- [x] 1.5 Turn every failure into the one type — permission refused, granted only in part, or the framework unavailable — and verify partial permission is treated as unreadable rather than as an empty day
- [x] 1.6 Add the dependency to `requirements.txt`, and verify a fresh environment built from it can read a day

## 2. Events in the day

- [x] 2.1 Build a row for each event carrying when it starts and what it is called, marked apart from a task without colour, and verify a mixed day shows both distinguishably
- [x] 2.2 Place events among the day's rows by when they start, with all-day events above the timed rows, and verify an event before a timed task is listed above it and a later one below
- [x] 2.3 Verify the tasks' own order is untouched: with every event disregarded, the day is exactly the order it would have been alone
- [x] 2.4 Fetch for the day being viewed and refetch when the day changes, and verify moving to another day shows that day's events and not the previous day's
- [x] 2.5 Verify the day's tasks appear without waiting for the calendar, and that a slow or failing calendar never keeps them off the screen

## 3. What the board may not do to an event

- [x] 3.1 Refuse every writing key on an event through the funnel every write already passes, and verify each of them writes nothing and says why
- [x] 3.2 Verify an event is not counted among the day's tasks in what the board reports
- [x] 3.3 Verify reordering does not move an event and does not carry a task across one

## 4. Work events and the work filter

- [x] 4.1 Treat events from the work account as work, and verify hiding work removes them while leaving the other account's events
- [x] 4.2 Verify the hidden count includes the work events it removed
- [x] 4.3 Verify pressing the key again brings them back, and that nothing was written either way

## 5. When the calendar cannot be read

- [x] 5.1 Say so once when the calendar is unreadable and otherwise leave the day exactly as it is, and verify with permission refused and with it granted only in part
- [x] 5.2 Verify an unconfigured calendar shows no events and reports no failure, while a configured account that does not exist is reported
- [x] 5.3 Verify the board recovers when the calendar becomes readable again and the view is refreshed, without a restart, and that the message goes

## 6. Verification

- [x] 6.1 Write a suite covering the ordering with events present, the write refusals, the work filter, the configuration cases and the unreadable cases against synthetic events, and verify it passes
- [x] 6.2 Verify against the real calendar, reading counts only and never an event's title, that the configured accounts' events appear on the right days and the excluded accounts' do not
- [x] 6.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand
