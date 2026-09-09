## 1. Unclamp the fixtures in t_elapsed

- [x] 1.1 Replace the clamped *under way* fixture in the three-positions block
      and the *crosses* fixture in the keeping-up block with the current hour
      to the next, letting the helper roll an end of 24 to the next day's
      midnight rather than clipping it to 23. Verify in
      `tests/stub/t_elapsed.py` (stub) that both blocks pass at the hour of the
      run; passing means the event they call under way is reported as not
      receded, which at hour 23 it was not before.
- [x] 1.2 Replace the three clamped *to come* fixtures — in the no-reference
      block, the selected-row block and the keeping-up block — with the next
      hour to the one after, and guard each with the condition under which
      such an hour exists (`h <= 22`) rather than the wider margins in place.
      Verify in `tests/stub/t_elapsed.py` (stub); passing means each block
      either asserts against an event that really is still to come, or says it
      skipped the case.
- [x] 1.3 Widen the *over* fixture to the start of the day up to the current
      hour, and its guard to `h >= 1`, so the case is testable from one o'clock
      rather than two. Verify in `tests/stub/t_elapsed.py` (stub) that the
      receded-event checks run and pass at the hour of the run.
- [x] 1.4 Comment the remaining guards with what they protect: the helper takes
      the start hour modulo 24, so an unguarded *to come* at hour 23 asks for
      hour 24 and silently gets midnight **today** — in the past — and the
      check then passes for the opposite of its reason. Verify by reading the
      file; passing means each guard says which impossible position it is
      standing in for, not merely that a number would be out of range.
- [x] 1.5 Read the hour where each fixture is built rather than once at import,
      so a run crossing an hour boundary cannot assert against fixtures built
      for the previous hour. Verify by grep: no assertion in the file depends
      on a module-level reading of the clock.

## 2. Make the narrow-terminal case measure rather than assume

- [x] 2.1 Replace the three hard-coded widths in `tests/stub/t_busy.py` with a
      measurement and a bracket: render the day bar wide, measure its text,
      then assert the mailbox mark is shown four columns above that length and
      dropped three above it. Verify in `tests/stub/t_busy.py` (stub); passing
      means both sides of the boundary are asserted and neither depends on
      what today's date is called.
- [x] 2.2 Keep a wide case and a narrow case that are not near the boundary, so
      the check still says the ordinary things — the mark is there on a normal
      terminal and the bar keeps its text when the mark goes. Verify in
      `tests/stub/t_busy.py` (stub) that both pass at widths well away from the
      measured length.
- [x] 2.3 Record in the suite why the widths are measured: the bar is a date,
      the day and month names differ in length, and the case as written asked
      whether today's name was long enough rather than whether the mark is
      dropped when it will not fit. Verify by reading the file.

## 3. Show it holds away from the moment of the run

- [x] 3.1 Add a case to `tests/stub/t_elapsed.py` (stub) that builds the three
      positions for **every** hour of the day and presents each hour to the
      board as the present, using the clock-rebinding the suite already does in
      its keeping-up block. Judged twice: the fixture's own span against that
      instant, and the board's dimming. Both are needed — dimming answers only
      "has this ended", so it cannot tell an event under way from one still to
      come, and a clamped *to come* at hour 22 was under way and passed anyway.
      Passing means no fixture lies at any hour, the board draws each
      accordingly, and the only skips are the two positions that cannot exist.
- [x] 3.2 Confirm the day bar's bracket is already independent of the moment:
      both asserted widths are the measured text's length plus a constant, so
      the case names no width, hour or date of its own. One literal width
      remains and is not an assertion — the wide render the text is measured
      from. The equivalent of an away-from-now check is 4.3's, which applies
      the rule to two supplied texts of different lengths.

## 4. Verification against a stub

- [x] 4.1 Run both suites directly: `.venv/bin/python tests/run.py t_elapsed
      t_busy`. Passing means each reports all of its checks passed, at counts
      raised by the cases added above.
- [x] 4.2 Prove the fixtures at the hours that used to break them, rather than
      waiting for the clock. Done as `every_hour` in `tests/stub/t_elapsed.py`
      (stub), which builds all three positions for each of the twenty-four
      hours and presents each hour to the board as the present. Passing means
      no fixture lies at any hour, the board draws each accordingly, and the
      only skips are *before now* at midnight and *after now* in the last
      hour. The same enumeration run against the old clamped fixtures reports
      all five of them lying at hour 23 and the three *to come* ones lying at
      22 as well — where a check judging only by the board's dimming failed at
      23 alone, hour 22 having passed on a fixture that meant something else.
- [x] 4.3 Prove the bar's bracket against a date whose name is a different
      length, rather than waiting for another day of the week: assert the
      boundary against a bar text supplied to the rule rather than only against
      today's. Done as cases in `tests/stub/t_busy.py` (stub) rather than as a
      one-off run, so it stays checked. Passing means the boundary sits at the
      text's length plus four for both a 37-character bar and a 41-character
      one — measured at 41/40 and 45/44 columns respectively.
- [x] 4.4 Run the full stub tier with `.venv/bin/python tests/run.py`. Result:
      41 passed, 0 failed, 0 known to fail. Passing means every suite passes
      and nothing is reported as known to fail —
      `t_busy` and `t_elapsed` were the whole of the tier's redness, and
      `tests/known_failures.py` is deliberately not touched, so a green run is
      the check that neither needed to be listed.
- [x] 4.5 No live tier is run and none is needed: both suites are
      self-contained, need no credentials, and touch no account. Verify by
      confirming the diff touches no file outside `tests/stub/`.
