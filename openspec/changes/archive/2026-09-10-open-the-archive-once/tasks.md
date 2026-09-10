## 1. Open the archive once to confirm

- [x] 1.1 Give `Server.numbers` an optional way to give up, asked between
      searches, so the give-up the confirmation relies on survives the loop it
      replaces. Verify in `tests/stub/t_gateway.py` (stub) that a `numbers`
      call whose stop answers yes after the first search raises rather than
      finishing, and that one with no stop behaves exactly as now — the
      existing `numbers` cases passing unchanged.
- [x] 1.2 Replace the confirmation loops in `archive` with one `numbers` call
      against the archive covering both groups — the messages just moved and
      those already elsewhere — and partition the result: a moved message
      absent from the archive is the failure that brings the row back, an
      already-elsewhere message present is reported as already done, absent is
      reported as in neither place. Verify in `tests/stub/t_gateway.py` (stub)
      that all four outcomes are reported exactly as they are now, by the
      existing confirmation cases passing unchanged.
- [x] 1.3 Assert the new shape: the archive is opened twice for a row of any
      size — once to confirm, once to mark read. Verify in
      `tests/stub/t_gateway.py` (stub) for rows of 1, 2, 3 and 7 against the
      recording server; passing means the count is 2 for every one of them,
      where it is 2, 3, 4 and 8 today.
- [x] 1.4 Confirm the searches are unchanged — one per message, never an OR of
      the row, this gateway answering an OR of eight with two matches. Verify
      by the existing search-count cases in `tests/stub/t_gateway.py` (stub)
      passing unchanged, including the one that refuses an OR outright.

## 1a. Fixed in passing

- [x] 1a.1 `t_gateway`'s check that no tracked file names a credential command
      was failing before this change began. `tests/stub/t_trace.py`, added by
      the previous change, constructs one precisely to prove a password cannot
      reach the trace — the same reason the other three named files are
      allowed — and was not on the list. Added, with the reason recorded.
      Verified: `t_gateway` passes, and the check now also asserts that what
      each allowed file names is plainly a marker rather than a secret, so the
      allowance cannot become a licence.
- [x] 1a.2 Record why the tier looked green when that change shipped: the
      check reads git's index, so it sees a file only once tracked. The suite
      was run before committing, when `git grep` could not see it. A comment
      at the check now says to run it again after committing — the one check
      here whose answer changes at the commit.

## 2. Open it three times to put a row back

- [x] 2.1 Rewrite `restore` to find every message in one `numbers` call, mark
      them all unread in one request, and move them back with one request per
      folder they came from. Verify in `tests/stub/t_gateway.py` (stub) that a
      row of several is reported restored exactly as now, and that a message
      not in the archive is still reported missing rather than invented.
- [x] 2.2 Assert the new shape: three archive openings for a row of any size.
      Verify in `tests/stub/t_gateway.py` (stub) for rows of 1, 2, 3 and 7;
      passing means the count is 3 for each, where it is 3, 6, 9 and 21 today,
      and that the moves are one per source folder rather than one per
      message.
- [x] 2.3 Make the undo all or nothing, in the order find, mark, move — the
      marking before the move because a move changes the message's number.
      Verify in `tests/stub/t_gateway.py` (stub) with a server that refuses
      the move: passing means no message reached its folder, all are still in
      the archive, and the failure is reported.
- [x] 2.4 Confirm nothing about a restored message's state changed: it comes
      back unread, to the folder it came from. Verify by the existing restore
      cases in `tests/stub/t_gateway.py` (stub) passing unchanged.

## 3. Move the check that describes the old shape

- [x] 3.1 Move the shape assertions in `tests/stub/t_trace.py` (stub) from the
      old counts to the new: a row of seven made eleven folder openings, eight
      of them the archive, six of those repetition. It now makes five
      openings, two of them the archive, none repeated. Passing means the
      suite asserts the new counts and no longer describes the repetition as
      present.
- [x] 3.2 Confirm the trace itself still records every request with its
      duration and outcome, there being fewer of them. One more assertion had
      to move than the plan named: the "costs nothing" case hard-coded the
      totals — 12, 18 and 30 requests — so it was also a check on the request
      shape and drifted the moment the shape changed. Rewritten to state the
      invariant instead: the trace holds every request but login and logout,
      and holds nothing the account never saw. That is what "costs nothing"
      means, and it does not move when the shape does — the rule the previous
      change added about deriving an expectation rather than restating it.

## 4. Verification against a stub

- [x] 4.1 Run the gateway and review suites together: `.venv/bin/python
      tests/run.py t_gateway t_trace t_review t_promote t_busy t_crash`.
      Passing means each reports all of its checks passed at its new count,
      and the four confirmation outcomes, the refusals and the crash paths are
      unchanged.
- [x] 4.2 Run the full stub tier with `.venv/bin/python tests/run.py`. Passing
      means every suite passes, as it does now, with any failure shown
      pre-existing by running that suite against a git worktree at HEAD —
      `t_undo1` is recorded in `tests/known_failures.py` under `FLAKY`, is
      deliberately not excused, and is judged by re-running it alone.

## 5. Verification against the live account

- [x] 5.1 Run `tests/gateway/t_gwlive.py` against the real account. Result:
      39/39, every check, count unchanged. This is the tier that exercises the
      one genuinely new behaviour — a search of the archive after an opening
      that was not its own — and it holds against this gateway, including for
      messages moved in moments earlier.
- [x] 5.2 Confirm from a trace that a folded row's confirmation opened the
      archive twice rather than once per message, and that every message was
      still found. The suite's own folded-row halves trace into the harness's
      throwaway directory, so this was measured by archiving and restoring the
      smallest folded row directly, with the trace in a known place and the
      restore in a `finally`. Result on the real account, a row of two
      messages: the archive half made 12 requests with **2 archive openings**
      (6.89 s and 7.36 s) and 2 archive searches, both messages confirmed —
      3 openings before this change. Counts and durations only.
- [x] 5.3 Record what the change bought, in the account's own numbers. On a
      row of two: archive openings 3 → 2 on the confirmation and 6 → 3 on the
      undo, about 28 s off a review-and-undo at the ~7 s an opening measured
      in that run. Openings have measured between 6.9 s and 16.6 s across
      runs, so the figure moves with the gateway's mood rather than being one
      number. The shape is what is fixed: two openings to confirm and three to
      put a row back, whatever the row's size, where it was n+1 and 3n — so a
      sixteen-message row goes from 17 and 48 openings to 2 and 3. The spec's
      corrected per-message figures follow from that shape, not from one
      run's timing.
