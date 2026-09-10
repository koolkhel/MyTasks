## 1. Write the trace where the requests are

- [x] 1.1 Add a trace writer to `journal.py` beside the log and the crash
      file: one line, appended to `imap-<date>.log` in the directory
      `journal.PATH` names, on the same best-effort terms as the log — never
      raising, never reporting itself. Verify in `tests/stub/t_trace.py` (a new
      stub suite) that a line lands in a redirected directory, that two
      different dates make two files, and that a directory that cannot be
      created leaves no file, raises nothing, and returns.
- [x] 1.2 Time `call()` inside `Server._talk` and write one line for each
      request, whether it returned or raised, recording the command, how long
      it took, and how it ended. Verify in `tests/stub/t_trace.py` (stub)
      against the recording server that a review writes a line per request,
      that each carries a duration, and that a request made to fail is
      recorded as failed with what it failed with.
- [x] 1.3 Pass what each call site already holds — the folder, and either a
      count or the message identity — so a line says which folder and which or
      how many messages. Verify in `tests/stub/t_trace.py` (stub) with one
      case per verb: passing means each line names its folder, a search names
      the identity it searched for, and a fetch, move and store name a count.
- [x] 1.4 Confirm `login` and `logout` stay outside the traced path, which is
      what keeps a credential off it. Verify in `tests/stub/t_trace.py` (stub)
      that no line names either, and by grep that `gateway.py` calls them
      outside `_talk`.

## 2. Hold the promises the spec makes

- [x] 2.1 Assert no message text can reach the trace, structurally rather than
      by filtering: check in `tests/stub/t_trace.py` (stub) that the whole
      trace of a review holds no subject and no sender planted in the fake
      server's messages, and that no request the gateway issues names a header
      or a body — the verb set being what makes the promise hold.
- [x] 2.2 Assert no credential can reach it: a review against a substituted
      server whose password is a planted marker leaves that marker nowhere in
      the trace. Verify in `tests/stub/t_trace.py` (stub).
- [x] 2.3 Assert the trace costs the account nothing: the requests made with
      tracing are exactly those made without it. Verify in
      `tests/stub/t_trace.py` (stub) by comparing the recording server's list
      of commands for the same review against the counts already measured —
      12 for a row of one message, 18 for three, 30 for seven.
- [x] 2.4 Assert nothing reads it back: deleting the trace between two runs
      changes no row. Verify in `tests/stub/t_trace.py` (stub) by comparing a
      board's rows across a run with the trace removed in between.
- [x] 2.5 Assert it is not committable, by asking git rather than trusting the
      arrangement: a case in `tests/stub/t_trace.py` (stub) that
      `git check-ignore` reports a trace path in the real logs directory as
      ignored, naming the rule.
- [x] 2.6 Confirm no suite writes a trace into the real `logs/`. The premise
      was wrong and the check found it: `tests/stub/t_gateway.py` reaches
      `gateway.py` through `fakeimap` but never imported `harness`, so
      `journal.PATH` was never repointed there and tracing every request put
      708 synthetic lines into the board's own `logs/`. Fixed by importing
      `harness` for its side effect — not `from harness import *`, which
      shadows `time`. The stray file was entirely synthetic (invented folder
      names only) and was removed. Passing means the whole stub tier runs and
      `logs/` holds nothing but the journal, which it now does.

## 3. Make the repetition visible

- [x] 3.1 Record, as a check rather than a comment, the shape a folded row's
      conversation has. Corrected against what the trace actually shows: a row
      of seven messages makes eleven folder selects, **eight** of which open
      the archive — seven readonly, one per message, plus one writable for the
      flag store. So **six** are repetition, not seven; the writable one is
      needed. Asserted in `tests/stub/t_trace.py` (stub) against the recording
      server, so the separate change that removes the repetition has a check
      to move rather than a claim to re-establish.

## 4. Verification against a stub

- [x] 4.1 Run the new suite and the gateway suites together:
      `.venv/bin/python tests/run.py t_trace t_gateway t_review t_promote
      t_busy t_crash`. Passing means each reports all of its checks passed at
      its new count, and the review, promotion and crash paths are unchanged.
- [x] 4.2 Run the full stub tier with `.venv/bin/python tests/run.py`. Result:
      42 passed, 0 failed. A first run showed one failure, `t_undo1`'s "the
      entry survives the one refusal" — the product write race already recorded
      in `tests/known_failures.py` under `FLAKY`, which is deliberately not
      excused so that a real break is never absorbed. It passed 47/47 alone,
      as that entry says to check, and the suite names `gateway`, `fakeimap`
      and `journal` zero times, so this change cannot reach it.

## 5. Verification against the live account

- [x] 5.1 Run `tests/gateway/t_gwlive.py` against the real account. Result:
      39/39, its full count. Two runs first failed at 26/28 on the case that
      cuts the line mid-operation, identically both times: that case took its
      row from the mirror reading at the top of the suite, and by the time it
      runs three halves have each moved a real message and put it back, over
      four to six minutes, during which the mirror re-syncs on its timer.
      Fixed here rather than deferred — it blocked this change's own
      verification and the fix is reading the mirror where the row is used.
      The `finally` now also distinguishes "nothing moved, so nothing needed
      putting back" from a restore that lost something; the old wording
      reported 0 either way, which read like stranded mail and was not.
- [x] 5.2 Read the trace that live run produced and confirm it answers the
      four questions the crash could not. It does: thirteen requests in order,
      each with its duration, and the cut recorded as
      `EXAMINE 0.00s ABORT socket error: [Errno 32] Broken pipe` as the last
      request of that review. The wording here was loose and the spec was
      right: the failing request is the last of *that operation*, not the last
      in the file — the suite's own restore follows it and is traced too, as a
      separate operation. That distinction is asserted within one review by
      `tests/stub/t_trace.py`. Reported as commands, durations and outcomes
      only.
- [x] 5.3 Confirm on the real account what a conversation costs, in the
      account's own numbers rather than from comments. Measured over a live
      run of 20 requests totalling 88.9 s: opening folders is **81.9 s of it,
      92%** — EXAMINE 6 requests 42.8 s (median 6.89 s, worst 14.04 s) and
      SELECT 4 requests 39.1 s (median 11.93 s, worst 14.25 s) — against
      SEARCH 5 requests 5.2 s (median 1.10 s) and MOVE, STORE and FETCH
      1.9 s between them. A later run showed archive opens at 13.2 s, 13.8 s
      and 16.6 s. So the six redundant readonly archive opens in a
      seven-message row cost on the order of 80 s, which is the evidence the
      separate fix is argued from. Counts and durations only.
