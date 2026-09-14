Instruments used below, and what each needs:

- **Stub tier** — `python tests/run.py`, no credentials, no network, no
  mailbox. Mail suites read a mailbox built per run by `tests/mailfixture.py`;
  `build()` makes one in a fresh temporary directory and takes a `seen` header
  per message, so a folder holding both read and unread mail is buildable
  without a real account. Where a suite reads the *committed* fixture instead,
  it takes `mailfixture.copy()` — a private copy per run — because the code
  under test moves messages and would otherwise edit the fixture in the
  repository.
- **Gateway tier** — `python tests/run.py --gateway`, which moves a real
  message on the real mail account. Run separately from the stub tier and read
  separately: it fails for reasons the stub tier cannot have.
- Nothing in this change talks to the task store, so no suite here spends the
  account's task quota and the question of which token it uses does not arise.

Where a task says a suite passes, passing means the runner prints
`<suite> N/N checks passed` with no `[FAIL]` line **and exits 0** — the exit
status read, not just the output, because a suite that crashes before
constructing anything prints no `[FAIL]` line and has been misread as success
on this board before.

## 1. What the queue holds

- [x] 1.1 Remove the read/unread skip from `mail._messages` and rewrite the two docstrings that state the old rule (`read` and `_messages`), so the file no longer says a read message has been dealt with. Verify in `tests/stub/t_mail.py` against a mailbox built per run holding, in one watched folder, a read message and an unread one: both are returned.
- [x] 1.2 Verify in `tests/stub/t_mail.py` that a message in a folder the board does not watch is not returned, and that a message moved out of a watched folder into the archive is not returned — the queue leaving by the folder and not by the flag.
- [x] 1.3 Verify in `tests/stub/t_mail.py` that a message whose flags cannot be read is returned like any other, the existing behaviour when a flag is unreadable being to decline to infer that anything was dealt with.
- [x] 1.4 Verify in `tests/stub/t_mailflat.py` and `tests/stub/t_mailview.py` that folding and the detail pane are unaffected by the new population: a thread holding both read and unread messages folds into one row whose count is all of them, and the newest message is what the row shows. *(Marked done in a batch before it was run, which was wrong: both suites were failing. `t_mailflat` asserted the removed behaviour outright — "a message flagged read by another program is gone" — and `t_mailview` carried six counts of the old population. Both corrected, and the mixed-thread folding checks this task asks for were added.)*

## 2. A message carries its read state

- [x] 2.1 Add a field to `mail.Message` saying whether the message was marked read, taken from the maildir flags that `_messages` already reads. Verify in `tests/stub/t_mail.py` that it is true for a message built with the `seen` header and false for one without.
- [x] 2.2 Verify in `tests/stub/t_mail.py` that a message whose flags cannot be read reports not-read, matching what 1.3 shows about it still being in the queue: unreadable is treated as undealt-with in both places.

## 3. Undo restores what was there

- [x] 3.1 Carry each message's prior read state in the undo entry a review creates, in `main.py`. Verify in `tests/stub/t_review.py`, with the suite's recording gateway, that reviewing a thread of three messages — two read, one not — records all three states.
- [x] 3.2 Make undo restore those states instead of marking every message unread, issuing at most two flag requests, one per group, through the existing `gateway.mark_seen(folder, items, seen)`. Verify in `tests/stub/t_review.py` that undoing that thread asks for the two read messages to be marked read and the one unread message to be marked unread, and asks nothing else.
- [x] 3.3 Verify in `tests/stub/t_review.py` that a thread whose messages were all unread before the review is restored with one request, not two, an empty group costing no call.
- [x] 3.4 Verify in `tests/stub/t_review.py` that a review still marks every message read in the archive after the move — the half of today's behaviour this change does not touch — and that undo still moves the messages back to the folder they came from.
- [x] 3.5 Verify in `tests/stub/t_review.py` that an undo that fails leaves the row whole, as the existing requirement already demands, with the flag restoration taking part in the same all-or-nothing.

## 4. The trace names the messages

- [x] 4.1 Put the identities of the messages acted on into what each successful gateway operation passes to the trace. Verify in `tests/stub/t_trace.py` that after a stubbed review the trace holds the identity of every message moved, and that a grep of the trace for a Message-ID pattern is no longer empty — which it is today, across a full day of real use.
- [x] 4.2 Verify in `tests/stub/t_trace.py` that the trace still holds no subject, no sender and no part of any body, the existing requirement being unchanged by adding identities beside them.

## 5. What it costs

- [x] 5.1 Change the mailbox `tests/stub/t_mailperf.py` builds so that it holds the read and unread mix a real account has — about 60% already read — rather than unread messages only, so the suite measures the population the board now reads instead of the one it used to. Verify the suite passes with its existing bound, and record the measured read and fold times in the change, as its docstring already does for the numbers it was written against.
- [x] 5.2 Verify in `tests/stub/t_mailperf.py` that the row count the mixed mailbox folds to is asserted, so that a future change to folding cannot quietly turn 385 rows into several thousand.

## 6. Verification of the whole

- [x] 6.1 Run each mail suite alone: `python tests/run.py t_mail t_mailflat t_mailview t_review t_promote t_trace t_mailperf`. Passing is every suite passing and exit 0. **Result: 7 passed, 0 failed, exit 0.**
- [x] 6.2 Run the whole stub tier: `python tests/run.py`. Passing is every suite passing with no new failure against the 47 that pass today, and exit 0. **Result: 47 passed, 0 failed, exit 0.** Two earlier attempts each reported one failure — `t_review` once, `t_keys2` once, each passing alone, the second producing no output at all. Both runs overlapped with other work in the same repository (file writes, mailbox scans, `openspec` calls), and a run taken with nothing else touching the repo passed clean. The failures were the instrument, not the code; a tier run is only evidence when it has the repository to itself.
- [x] 6.3 Vacuity check: put the read/unread skip back in `mail._messages`, re-run the mail suites, and confirm they fail, reading the exit status rather than grepping the output. Restore and confirm they pass again. **Result: all five suites failed, 36 checks in total, exit 1 — t_mail 44/50, t_mailflat 16/21, t_mailview 90/97, t_review 116/132, t_promote 72/74. Restored; `shasum mail.py` back to `22d85d1e302b`.**
- [x] 6.4 Second vacuity check, for the undo: make undo mark everything unread as it does today, re-run `tests/stub/t_review.py`, and confirm the group 3 checks fail. Restore and re-run. **Result: 128/132, exit 1. The two group 3 checks failed by name — "each message is read exactly as it was before the review" and "two flag requests, one per group, both on the archive" — with two further failures as knock-on. Restored; `shasum gateway.py` back to `d21012ee5bd4`.**
- [x] 6.5 Freeze the product code for the verification runs and confirm with `shasum` afterwards that it did not change during them. Un-check any task whose verification predates a later edit to the code it verified. **Result: the clean tier run took the checksums before and diffed them after — identical. Frozen at `d1ff32fc4f9c` main.py, `5a252bc1b1ed` mail.py, `d21012ee5bd4` gateway.py. `mail.py` moved from `22d85d1e302b` after the earlier runs because its module docstring still opened with the old rule; that edit predates this run, so nothing needed un-checking.**

## 7. Against the real account

- [x] 7.1 Run the gateway tier: `python tests/run.py --gateway`. It moves a real message on the real account; its own fixtures name what they create so it can be recognised, and it deletes what it made in a `finally`. Passing is every check passing and exit 0. Re-run a single failure once before believing it — these suites contend over one account. **Result: `t_gwlive` 43/43 checks passed, exit 0, against the real account.** It moves one message and one folded row to the archive and back, which exercised the new undo path against a real service rather than a substitute.
- [x] 7.2 Check the account afterwards for anything the suite left behind, a crashed run leaving messages in place that would surface later as a phantom failure. **Result: nothing left behind. No file matching the suite's naming in any watched folder, and the mailbox log's entries for the day are the board's own reviews, each confirmed with nothing in neither place.**
- [ ] 7.3 Open the board by hand and confirm the inbox holds the read mail as well as the unread. State it as a comparison rather than a number: the folder is being worked down while this change is in flight, so an absolute row count written here is wrong by the time it is checked — it read 890 messages and 386 rows when this was planned and 444 and 120 a few hours later. Passing is that a message read in the mail client and not archived is on the board, and that the row count is above what the unread messages alone would give (`mail.read` filtered on the read flag answers that at any moment). This is not a suite and is not part of any tier.
- [ ] 7.4 Tick one message on the board, confirm it leaves the view, and confirm in the mail client that it is in the archive and marked read. Then undo, and confirm the row returns and the message is back in the watched folder with the read state it had before. Passing is all four observed.
- [ ] 7.5 Archive a message by hand in the mail client, reload the board, and confirm the row goes once the mirror catches up — the other half of what "leaves the queue by leaving the folder" promises.
