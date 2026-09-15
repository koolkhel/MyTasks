Instruments used below:

- **Stub tier** — `python tests/run.py`, no credentials, no network, no
  mailbox. Mail suites build their mailbox per run in a throwaway directory;
  `tests/stub/t_mail.py` already has a helper that builds a message with an
  HTML part, which is what these checks need. Where a suite reads the committed
  fixture instead it takes `mailfixture.copy()`, a private copy per run,
  because the code under test can move messages.
- **By hand, against the real account** — group 6. Not a suite, not part of any
  tier, and read separately: it fails for reasons no suite can have.
- Nothing here talks to the task store or the tracker, so no suite spends the
  account's quota and the question of which token it uses does not arise.

Every fixture is synthetic: invented project keys, `.invalid` hosts, generated
subjects. The markup *shape* is copied from a real notification; none of its
content is, because this repository is public.

Where a task says a suite passes, passing means the runner prints
`<suite> N/N checks passed` with no `[FAIL]` line **and exits 0** — the exit
status read, not just the output, because a suite that crashes before
constructing anything prints no `[FAIL]` line and has been misread as success
on this board before.

## 1. Reading the marker

- [x] 1.1 Add a field to `mail.Message` saying whether the notification presents its own issue as done, read from the message's HTML part. *(Amended during apply: this said "while the HTML is already being parsed rather than in a second pass", which was wrong. `_body` prefers a message's plain part and a notification carries both, so the HTML of exactly these messages is never parsed today. The marker needs its own pass, which the design now records along with what it costs.)* Verify in `tests/stub/t_mail.py`, against a built message whose header names an issue and whose HTML links that issue with a struck style, that the field is true; and against the same message with the style absent, that it is false.
- [x] 1.2 Verify in `tests/stub/t_mail.py` that the header decides which issue is looked at, not the links: a message about issue A whose HTML also links a struck issue B is not marked, because B is somebody else's issue mentioned in passing.
- [x] 1.3 Verify in `tests/stub/t_mail.py` that any link to the message's own issue carrying the mark is enough: a message carrying two such links, one struck and one plain — the shape every real notification has, the key struck and the summary not — is marked.
- [x] 1.4 Verify in `tests/stub/t_mail.py` that a message whose HTML links its issue with no mark at all is not marked, and that one whose HTML links no issue at all is not marked and raises nothing.
- [x] 1.5 Verify in `tests/stub/t_mail.py` that a message with no HTML part is not marked and raises nothing, that being every message from the folders that are not tracker mail.

## 2. What the row says

- [x] 2.1 Verify in `tests/stub/t_mailflat.py` that the row's newest message decides: a thread whose older messages are unmarked and whose newest is marked reads as done, and the reverse reads as not done.
- [x] 2.2 Draw a marked row's title the way the board already draws a finished task. Verify in `tests/stub/t_mailview.py` that a marked row is drawn that way and that an unmarked row is drawn exactly as it was.
- [x] 2.3 Verify in `tests/stub/t_mailview.py` that the mark is still legible when the row is the selected one. The board's own notes record that the cursor replaces a colour while dim survives; this is a measurement of which the strike does, and if it does not survive, stop and say so rather than changing the requirement — the leftmost cell is the recorded fallback.
- [x] 2.4 Verify in `tests/stub/t_promote.py` that promoting a marked row makes an ordinary task carrying no mark, the mark belonging to the mail row alone.

## 3. Nothing is asked of the tracker

- [x] 3.1 Verify in `tests/stub/t_mailview.py` that rows are marked identically with a tracker configured, with one configured that cannot be reached, and with none configured at all — three boards, the same rows.
- [x] 3.2 Verify in `tests/stub/t_mail.py` that reading a mailbox makes no network call: the existing check that reading writes nothing is the model, and this adds that nothing is fetched. If the suite cannot show that directly, say so in the task rather than checking it off — an unverifiable claim is worse than an absent one. **Result: shown directly rather than asserted — `socket.socket`, `create_connection` and `getaddrinfo` are replaced with functions that raise, and the mailbox is read anyway. A read that touched the network would fail there instead of answering.**

## 4. The canary

- [x] 4.1 Add a check that the shape the detector looks for is the shape a notification actually has, so that a tracker template change shows up as a failing check rather than as an inbox that quietly stops marking anything. Verify in `tests/stub/t_mail.py` that the fixture's marked message is marked, and record in the check why it exists — it is the only warning the board will get.
- [x] 4.2 Record in the change what the detector cannot catch: the shape changing on the real server. The suite checks the fixture, and the fixture is what this repository believes the shape to be. Nothing here notices the day the belief goes stale, and saying so is the honest half of 4.1. **Recorded: the canary checks the shape this repository believes a notification has, which is the shape written into `tests/stub/t_mail.py`. It cannot notice the day the real server starts sending a different one — the suite never reaches the account, by design. So what it catches is somebody changing the detector without changing the fixture, or the reverse; what it cannot catch is the tracker being upgraded. The symptom of that would be an inbox that quietly stops marking anything, and the way to notice it is task 6.2's comparison against the real mailbox, re-run when something looks wrong.**

## 4b. What it costs

- [x] 4b.1 Give `tests/stub/t_mailperf.py` notifications with an HTML part, so that the suite measures the read path the board now takes. Its fixture builds plain-text messages only, so the new parse never runs in it and the suite would go on reporting a read that skips a third of the work. Verify the suite passes with its existing bound and record the measured read time in the change. *(Added during apply. The design claimed a cost of 0.06 ms a message, quoted from a docstring about a different operation; measured against real notifications it was 0.316 ms, and 0.106 ms after skipping the parse where the styling is absent from the document. A cost that is stated and unmeasured is the same gap this project has been bitten by before.)* **Result: 1,233 messages read in 0.17s against 0.11s before the HTML parts existed, folded in 0.00s, 453 rows, drawn in 0.02s — the existing bound holds. The fixture had to be fixed twice before it measured anything: first it built plain-text messages so there was no HTML to parse, then it carried the markup but not the header naming the issue, so the detector answered from the header alone. Both times the suite reported a believable number for work it was not doing. It now asserts that some of its issues are recognised as finished — 182 of 1,233 — so a measurement taken over a short-circuited path fails instead of flattering the change.**

## 5. Verification of the whole

- [x] 5.1 Run each mail suite alone: `python tests/run.py t_mail t_mailflat t_mailview t_review t_promote t_trace t_mailperf`. Passing is every suite passing and exit 0. **Result: 7 suites, 0 failed, exit 0.**
- [x] 5.2 Run the whole stub tier: `python tests/run.py`. Passing is every suite passing and exit 0, with no new failure against what passes when this change begins. **Result: 47 passed, 0 failed, exit 0, with the repository to itself.**
- [x] 5.3 Vacuity check: make the detector always answer false, re-run the mail suites, and confirm they fail, reading the exit status rather than grepping the output. Restore and confirm they pass again. **Result: all five suites failed, 11 checks, exit 1 — t_mail 58/62, t_mailflat 23/25, t_mailview 104/107, t_promote 77/78, t_mailperf 8/9. The perf suite failing is the new guard doing its job: without it, a read that never parses anything would still have reported a believable time. Restored; `shasum mail.py` back to `7a95a708f4f1`.**
- [x] 5.4 Second vacuity check, for the drawing: draw a marked row exactly like an unmarked one, re-run `tests/stub/t_mailview.py`, and confirm the group 2 checks fail. Restore and re-run. **Result: 105/107, exit 1, the two drawing checks failing by name — "the finished row is struck through" and "and it is still struck while selected". `t_promote` passed, its check being that a promoted task is not struck, which stays true when nothing is; it does not guard the drawing and is not meant to. Restored; `shasum main.py` back to `e8d9c33322425`.**
- [x] 5.5 Freeze the product code for the verification runs and confirm with `shasum` afterwards that it did not change during them. Un-check any task whose verification predates a later edit to the code it verified. **Result: the clean tier run took the checksums before and diffed them after — identical. Frozen at `e8d9c33322425` main.py, `7a95a708f4f1` mail.py, and the fixture helper alongside. Nothing needed un-checking.**

## 6. Against the real account

- [x] 6.1 Open the board by hand with the real mailbox and confirm that rows about finished issues are drawn as finished and rows about unfinished ones are not. Passing is both observed on rows whose state is known independently. **Result: observed and confirmed at the board. With the real mailbox the inbox drew 25 mail rows, exactly one of them struck through -- the row about the one issue known independently to be finished -- and the other 24 plain. The mark survived the cursor: the row stayed struck while selected.**
- [x] 6.2 Count how many rows the board marks, and compare it with the number of issues whose newest notification carries the mark, read straight off the mailbox. Passing is the two agreeing. State it as a comparison rather than a number: the folder is worked down continuously — it held 571 notifications when this was explored and 100 a few hours later — so a number written here is wrong by the time it is checked. **Result: the two agree. The watched folders held enough for a live comparison once a notification about a finished issue came back into them. The board's count of marked rows and an independent count read straight off the maildir -- a regex over each message's HTML alternative, scoping the styling to the anchor that links to the issue the header names, rather than the parser the board uses -- came out the same, and the agreement is on a non-zero count rather than nothing against nothing. The rows the board does not mark also match: every unmarked one is unmarked by both methods.**
