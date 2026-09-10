## 1. Decide when the answer is knowable

- [x] 1.1 Add a way to ask how many of an action's writes are still in flight,
      counted from the queues that hold them rather than kept as a number of
      its own — the board already derives its in-flight total this way for the
      status line, and its own note about the count it does keep warns that a
      missed decrement lasts the session. Verify in `tests/stub/t_undo1.py`
      (stub) that the count is what the queues hold: the action's writes before
      any settles, and none once they all have.
- [x] 1.2 In the refusal path, after the queue is taken back, decide only where
      nothing of the action is left in flight: drop the entry if nothing was
      applied, keep it otherwise, and where writes remain outstanding decide
      nothing at all. Verify in `tests/stub/t_undo1.py` (stub) that the
      existing case — four writes, one refused — keeps its entry, which is the
      check that has been failing about one run in five.
- [x] 1.3 Confirm the confirmed-write path is untouched, a write that has just
      applied something being unable to cause a drop. I did touch it first —
      added a call from the success path on the reasoning that a deferred
      decision needed taking there — then worked the cases through and found
      it could only ever be a no-op: it returns early while writes remain and
      keeps the entry once they do not, a success having just made `applied`
      non-zero. Removed, and `forget` now says why the success path leaves it
      alone, that being the first thing a reader will wonder. Verified: one
      call site by grep, and the existing undo cases pass unchanged.
- [x] 1.4 Confirm the writes abandoned behind a refusal cannot leave an action
      waiting on writes that will never be sent: they are taken out of the
      queues by the same pop. Verify in `tests/stub/t_undo1.py` (stub) with an
      action whose writes are all on one task's queue and whose first is
      refused; passing means the entry is dropped there and then, nothing
      being left outstanding.

## 2. Prove it by forcing both orderings

- [x] 2.1 Move the forced-ordering cases out of `tests/probes/t_race.py` and
      into `tests/stub/t_undo1.py` (stub), beside the check they explain: the
      same action run twice, with the refusal paced to settle before the
      other writes and then after them. Passing means the entry survives both
      times.
- [x] 2.2 Assert the two orderings agree, which is the defect stated directly:
      the same action, answered in either order, leaves the undo key reaching
      the same thing. Verify in `tests/stub/t_undo1.py` (stub); passing means
      the two runs report the same number of entries, where today they report
      one and none.
- [x] 2.3 Make the guarded check unconditional. The existing case ends with
      `if app._undo:` because the entry might be missing, which is why a
      failing run reported 46 checks rather than 47 — a varying count being
      part of the recorded signature. With the entry always surviving, the
      guard has nothing to protect. Verify in `tests/stub/t_undo1.py` (stub)
      that the suite reports the same number of checks on every run.
- [x] 2.4 Assert an action that landed nothing still leaves nothing: every
      write refused, and the undo key reaching past it. Verify in
      `tests/stub/t_undo1.py` (stub); passing means no entry survives and the
      existing lone-refusal case is unchanged.

## 3. Tidy what recorded the race

- [x] 3.1 Remove `tests/probes/t_race.py`. Its own docstring says it is not a
      suite because there was no right answer to assert; there is one now, and
      it is asserted in 2.1 and 2.2. Verify that nothing live refers to it —
      the only reference outside archived change records is the known-failure
      entry removed next.
- [x] 3.2 Remove `t_undo1`'s entry from `tests/known_failures.py`. It records
      this race. Verify that the suite passes without it and that the runner
      reports no known failures for the tier.

## 4. Verification against a stub

- [x] 4.1 Run the undo and write suites together: `.venv/bin/python
      tests/run.py t_undo1 t_undo3 t_undo6 t_writes t_move t_work3`. Result:
      5 passed, 0 failed, 1 known to fail — `t_undo1` 55/55 (was 47 at best
      and 46 when the race bit), `t_undo3` 41/41, `t_writes` 55/55, `t_move`
      36/36, `t_work3` 36/36, and `t_undo6` reported as its own recorded
      known failure, unrelated. That run uses the suites' token, which it
      announced.
- [x] 4.2 Run `t_undo1` alone five times and under the full tier five times.
      Result: ten runs, all green — 55/55 in each of the five alone, and
      42 passed / 0 failed / 0 known to fail in each of the five tier runs,
      with the code frozen at one checksum throughout and the check count
      identical every time.
      Worth recording that these ten runs are the weaker half of the
      evidence. The stronger half is that the two orderings are now forced
      and asserted to agree, which turns a one-in-five race into a
      deterministic check that runs in every tier pass. This criterion was
      written before those cases existed; it was met rather than argued
      down.
- [x] 4.3 Run the full stub tier with `.venv/bin/python tests/run.py`. Result:
      42 passed, 0 failed, 0 known to fail, five times over. The
      git-index-reading check is unaffected: this change adds no file and
      removes one, the set that check sees is unchanged at three files — all
      of them already allow-listed — and `t_gateway` passes 209/209. The
      task said "removes two"; it removes one, the probe. The known-failure
      entry is an edit, not a deletion.
