## Why

Every message the board reads comes from three folders of one corporate
account. All of it is work. The key that hides work does not hide any of it.

The board's other two sources do get hidden. A tracker issue is stamped with
the work project, and a calendar event is stamped when its account is the work
one; both are filtered, both are counted in what was hidden, and both are
specified and covered by suites. Mail is stamped with nothing, so the filter
never claims it.

Mail also misses the filter a second, independent way. The rows are appended
after the filtering, which the comment directly above that filter warns about
in as many words: appending afterwards would carry the tracker rows — the most
work-like rows on screen — straight past the key that hides work. Mail was
appended afterwards anyway. So stamping the rows alone would not be enough.

What makes this worth fixing rather than noting: mail is inbox-only, and the
inbox is the one view where the key currently does nothing whatsoever. A task
with a project is by definition not in the inbox, so there is never work there
to hide — the board announces "work hidden", removes no row, and leaves the
mailbox's several hundred rows exactly where they were. The board's own note
about that announcement says a mode that hides nothing is indistinguishable
from a key that does not work, and in the inbox that is the state it is in.

Hiding work in the inbox should leave the unfiled personal tasks. On this
mailbox that means turning several hundred rows into the handful underneath
them, which is not reachable by any other key.

## What Changes

- Mail rows count as work. The key that hides work hides every mail row, and
  pressing it again brings them all back.
- The rows are filtered where the other sources are filtered, rather than
  appended past the filter afterwards. Without this the stamp alone changes
  nothing, and the ordering that puts mail last stays exactly as it is.
- The count of what was hidden includes the mail rows, so the inbox stops
  saying "work hidden" with no number.
- The status line's thread and message counts report what is on screen, so
  they drop out while mail is hidden — the same meaning `tracked` already has
  for the tracker's rows. The daybar's hidden count is then the one number
  that says how much went.
- **Every** mail row counts as work, unconditionally, the way a tracker issue
  does rather than the way an event does. There is one account and its folders
  are all corporate, so there is nothing today for a per-account rule to
  distinguish. Recorded as a choice: a second, personal mailbox would want the
  calendar's per-account treatment, and would be the reason to revisit it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one new requirement saying mail counts as work, beside the two
  that already say it of tracker issues and of work events. *Hiding the work
  tasks* changes too: its scenario promising the inbox is unaffected was true
  when the inbox held only tasks, and mail arriving there falsified it.

## Impact

- `main.py` — where a mail row is built, where the work filter runs, and where
  the two mail counts are taken. The repaint's ordering is untouched: mail
  still follows the day's tasks, still appended rather than sorted in.
- No change to what is written anywhere. The filter decides which of the rows
  a view already chose are painted, and hiding has never written anything.
- No change to the mailbox, the gateway or the log. This is a view filter.
- `tests/stub/` — the work-filter suites and the mail suites, which between
  them already cover the tracker's and the calendar's version of this.
