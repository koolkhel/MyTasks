## Context

See proposal.md -- Why. Two facts settle the approach, both measured rather
than recalled.

**Where the calendar suite actually stops.** `ical._status()` is a plain query
of the system's authorization for calendar events. In the shell the suites run
in it returns `_NOT_DETERMINED` (0). `_store()` then builds a store, asks for
access, and spins a run loop for up to `ACCESS_TIMEOUT_SECONDS` (30) waiting
for an answer that never comes; status is still 0 afterwards, 0 is not a key in
the access-trouble table, so the fallback message is raised: "the calendar
could not be read". `fetch` therefore refuses inside `_store()` -- before the
account-matching code the last two checks are about is reached at all. Those
two checks are not failing; they never ran.

**What the runner can express.** `run.py` skips whole tiers when the
environment lacks what they need, and has no notion of skipping one check. It
reads a suite's verdict from its exit status and shows the first line matching
`N/M checks passed`. So a suite that cannot run part of itself has to say so
itself, in its own output, and still exit 0.

## Goals / Non-Goals

**Goals:**

- The four entries go, and the file still records that they existed and why
  they went.
- `t_ical` gives the same verdict on a machine that grants the calendar
  permission and one that does not -- passing -- while asserting more on the
  first.
- The permission probe costs nothing and surprises nobody: no 30-second wait,
  no permission dialog raised at whoever is running the suites.

**Non-Goals:**

- Changing `ical.py`. The behaviour the two checks cover is correct; only the
  suite's ability to reach it is in question.
- Changing `run.py`, including its summary pattern.
- Granting the permission, or telling anyone to. A machine that withholds it
  is a legitimate machine to run the suites on -- that is the whole point.

## Decisions

**Probe with `_status()`, not by attempting the read.** The guard asks
`ical._status() == ical._FULL_ACCESS` and skips on anything else.

- *Alternative: call `ical._store()` and catch `CalendarUnreadable`.* Rejected.
  On a not-yet-decided machine that is the 30-second path, every run, and it is
  the call that raises a permission dialog. A suite must not stop for half a
  minute to discover it has nothing to do, and must not put a system prompt in
  front of someone who only ran the tests.
- *Alternative: read the exception message.* Rejected. It would tie the suite
  to wording the module is free to change.

`_WRITE_ONLY` (4) is handled by the same comparison: a calendar that may be
written but not read cannot serve these checks either, and "not full access"
is one condition rather than a list of bad ones.

**Skip the two checks, not the suite.** Thirteen of the fifteen substitute
`_status` for a fixed value and need no permission at all; they are the checks
that cover how access trouble is reported, which is most of the suite's value.
Refusing to start would throw them away on every machine that has not granted
the permission.

**Do not add a known-failure entry.** An entry excusing two failures cannot
tell "the machine would not let me look" from "the board got this wrong", and
absorbing the second into the first is the exact failure the list's own rules
are written against. The suite knowing why it cannot run a check is strictly
better information than a list saying it is expected to fail.

**Place the guard after the suite restores the real `_status`.** The earlier
blocks replace `ical._status` with fixed values and restore it; the guard has
to read the restored one, so it belongs with the final block and not at the top
of the file. `ical._STORE` is already `None` at that point, so nothing cached
from a substituted status survives into the probe.

**Record the removals the way the file already records them.** `known_failures.py`
keeps `REPAIRED`, `REWRITTEN`, `LOST` and a trailing "Resolved:" note beside
`KNOWN`. The four entries move into a record of that kind, carrying what they
used to say. Deleting the lines outright would leave the next person to
rediscover a crash that has already been chased once.

## Risks / Trade-offs

- **The four suites pass today and crash again tomorrow** -> Each was run twice,
  and they are live suites against the task store, which is exactly the class
  that fails once and passes clean after. The entries said they *crash* with
  `RuntimeError`; a return of that crash now reports as a new failure, which is
  the outcome we want -- an entry that stays would hide it. The removals are
  reversible in one commit if the crash returns.
- **A green run shows `13/13` and does not say two were skipped** -> The
  runner prints only the matched summary line, so the reason lives in the
  suite's own output. `13/13 checks passed` is true; nothing claims fifteen ran.
  Widening the runner's summary pattern to carry a skip count would touch a
  pattern every suite shares, and belongs in its own change if the omission
  proves to matter.
- **The guard hides a real break of those two checks on an ungranted machine**
  -> It does, and it must: on such a machine there is no way to test them. On a
  granted machine -- the one where the board itself reads the calendar -- both
  run as before. That is where the verification for this change is done.
- **A future reader adds a check needing the permission below the guard** ->
  The guard covers the final block, which is the whole of what needs the
  calendar; the block header says so.

## Migration Plan

None. Two test files change, no product code, no data. Rollback is reverting
the commit; the removed entries are recoverable from the same file's record of
them as well as from history.
