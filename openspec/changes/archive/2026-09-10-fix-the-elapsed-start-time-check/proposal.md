## Why

`t_elapsed` fails from one o'clock every day, on a check that reads:

    check("it keeps its start time", cell(app, "over", 2), f"{(h-2)%24:02d}:00")

The change that took the suites off the clock widened the *over* fixture from
`h-2 .. h-1` to `0 .. h`, so it now starts at midnight. This expectation was
left computing the old arithmetic beside it. The fixture moved; the assertion
did not; nothing connected them, so nothing complained.

It escaped two checks that were built to catch exactly this, and how it did is
the more useful half.

The change was verified at half past midnight, where the case is skipped
outright — nothing has ended today at that hour, so the whole *over* branch
never ran. A clock fix hidden by the clock.

The twenty-four-hour check written in that change judges the three positions by
whether the board recedes them. `positions` asserts five more things about the
same row — its mark, its start time, its name, its calendar, and that it is not
struck out — and none of those was covered. So the hour sweep passed while an
assertion about the very fixture it was sweeping had been wrong since the
fixture changed.

The rule that would have prevented it is not written down anywhere. The
requirement about suites and the clock governs what a fixture must mean and
that a limit must be shown to hold away from now, but nothing says an
expectation about a fixture SHALL be taken from that fixture rather than
recomputed alongside it. Two expressions of one value, kept in step by hand,
is the whole defect — and it is not specific to the clock.

## What Changes

- The start-time expectation is taken from the event the case built, so the
  two cannot drift again. Any later change to the fixture moves both.
- The hour sweep widens from the one property it judged to every assertion
  `positions` makes about the row, so a fixture that stops matching what is
  said about it fails at whichever hour it is wrong, rather than at whichever
  hour someone happens to run.
- A requirement recording the rule: an expectation about a fixture is derived
  from that fixture. Written for fixtures in general rather than for clocks,
  because nothing about the failure was particular to time.

## Capabilities

### Modified Capabilities

- `test-suite`: one new requirement, that a suite derives an expectation from
  the fixture it is about instead of recomputing it. Added beside the
  requirement about the clock rather than folded into it: that requirement's
  own rules are unchanged and correct, and this one is broader — it would hold
  for a mailbox or a task fixture with no clock involved.

### New Capabilities

None.

## Impact

- `tests/stub/t_elapsed.py` — one expectation, and the hour sweep's coverage.
- No product code. The board is right; the suite was wrong about it.
- `tests/known_failures.py` is not touched. The suite stops failing.
- No live tier. `t_elapsed` is self-contained and needs no credentials.
