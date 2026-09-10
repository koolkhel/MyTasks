## 1. Take the expectation from the fixture

- [x] 1.1 Keep a reference to the *over* event `positions` builds, and assert
      the start-time cell against that event's own start rather than against
      `(h-2)%24`. Not against the literal `00:00` either — that is right today
      and would strand again the moment the fixture moves. Verify in
      `tests/stub/t_elapsed.py` (stub) at the hour of the run; passing means
      the case runs and its five "nothing else about the row changed" checks
      all pass.
- [x] 1.2 Confirm no other assertion in the file recomputes the fixture's
      arithmetic. Verify by searching `tests/stub/t_elapsed.py` for arithmetic
      on the hour and confirming every remaining occurrence is fixture
      construction — `spans_now`, `after_now`, `before_now` and `ev` — rather
      than an expected value.

## 2. Make the sweep cover what the suite asserts

- [x] 2.1 Gather what `positions` claims about a row — the mark, the start
      label taken from the event, the title, the calendar, and the absence of a
      strike — into one helper, so the claim exists once rather than in two
      lists that can drift the way the expectation and the fixture did.
      Verify in `tests/stub/t_elapsed.py` (stub) that `positions` still passes
      using it.
- [x] 2.2 Have the hour sweep judge that helper for every position it builds,
      at every hour, in addition to the shading it already judges. Verify in
      `tests/stub/t_elapsed.py` (stub); passing means the sweep reports no
      fixture lying and no row drawn wrongly across all twenty-four hours,
      with the same two skips as before.
- [x] 2.3 Prove the widened sweep would have caught this: run it with the
      start-time expectation recomputed from the hour instead of read from the
      event, confirm it fails, then restore the fix and confirm it passes.
      Result: the widened sweep reports **69** wrong fixture-hours, naming the
      cell and the hour for each, where the sweep as it stood passed at all
      twenty-four. Restored and confirmed by checksum. The defect was
      reproduced in its shape rather than byte-for-byte, the original line
      having lived in the case that now asserts through the shared helper.

## 3. Verification against a stub

- [x] 3.1 Run the suite directly at the hour of the run: `.venv/bin/python
      tests/run.py t_elapsed`. Passing means every check passes, at a count
      raised by the assertions the sweep gained.
- [x] 3.2 Prove it at the hours that used to skip or break the case, rather
      than waiting for the clock: the sweep presents each hour to the board as
      the present, so a single run covers midnight, one o'clock and the last
      hour. Passing means the case is exercised at every hour it can be, and
      reported as skipped only at midnight, where nothing has ended today.
- [x] 3.3 Run the full stub tier with `.venv/bin/python tests/run.py`. Result:
      41 passed, 0 failed, 0 known to fail. Passing means every suite passes
      and nothing is reported as known to fail —
      `t_elapsed` was the tier's only failure, and `tests/known_failures.py` is
      deliberately not touched, so a green run is the check that it needed no
      entry.
- [x] 3.4 No live tier is run and none is needed: `t_elapsed` is
      self-contained, needs no credentials and touches no account. Verify by
      confirming the diff touches no file outside `tests/stub/`.
