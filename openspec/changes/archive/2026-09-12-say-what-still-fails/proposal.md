## Why

The list of known failures says four suites crash and one thing about the
calendar suite says nothing at all, and neither is true.

`t_place`, `t_perf`, `t_undo6` and `t_work6` are recorded as crashing with
`RuntimeError` -- "a task it created is not found on the board; not
diagnosed". All four pass now, twice each, run the way the runner runs them:
20/20, 5/5, 11/11, 16/16. The list's own rule is that an entry which starts
passing gets reported so it can be removed rather than accumulate; four
entries are now excusing nothing and hiding any real crash of those suites
behind a matching signature.

`t_ical` fails two of its fifteen checks on this machine and is in no list at
all. The two are the last block, the one that asks whether an account named
in the configuration but absent from the machine is reported rather than
passed over. They fail because the calendar permission has not been granted
to the shell the suites run in: `_status()` returns "not determined", the
access request is never answered, and `fetch` refuses at the store before it
ever reaches the account-matching code under test. Nothing is wrong with the
code those two checks cover. A suite that cannot tell "this machine will not
let me look" from "the board got this wrong" reports the wrong one.

## What Changes

- Remove the four entries from the known-failure list, and record in the file
  -- the way it already records resolutions -- that they were removed for
  passing, with what they used to do and when.
- Make `t_ical` ask the system what it is allowed to do before running the
  two checks that need a real calendar. Without the permission it says so,
  does not run them, counts only what it ran, and still succeeds.
- Do not list `t_ical` as a known failure. An entry excusing two failures
  would excuse a real break of those two checks just as readily, which is
  precisely what the list forbids.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite`: **A suite declares what it needs to run** -- being in the
  right group does not settle whether a suite can run here. A check that
  needs a permission the machine grants SHALL find out before asserting, skip
  itself and name what is missing when the answer is no, and count only what
  it ran.
- `test-suite`: **A suite known to fail is recorded with the reason** -- when
  an entry is removed because the suite passes, the record of what it used to
  do stays, so that removal is a fact on file and not a gap.

Pruning the four entries themselves needs no new requirement: "a listed suite
that starts passing SHALL be reported, so that the list is pruned rather than
accumulating entries nobody has revisited" already says to do it. This change
does it.

## Impact

- `tests/known_failures.py` -- four entries out of `KNOWN`, one resolution
  record in.
- `tests/config/t_ical.py` -- a permission check before its final block.
- No product code. `ical.py` is read for its access constants and is not
  changed; the behaviour the two checks cover is already correct.
- `tests/run.py` is not changed. A suite that exits 0 having printed its
  count is already reported as passing, and four `KNOWN` names simply stop
  being looked up.
