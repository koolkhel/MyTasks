## 1. The log

- [x] 1.1 Add a module that writes one line per entry — an ISO-8601 UTC stamp, a level, a message — to `logs/mytasks.log` resolved against the board's own files rather than the working directory; verify with a new self-contained suite (`tests/stub/t_busy.py`, a stubbed store, no mailbox, no network) that a line written from a temporary directory lands in the expected file and parses back into stamp, level and message
- [x] 1.2 Verify in `t_busy` that writing is best-effort: with the log path pointed at a directory that cannot be created, every call returns normally, nothing is raised, and nothing is reported to the person
- [x] 1.3 Add `logs/` to `.gitignore` with the reason beside it, and verify in `t_busy` that `git check-ignore` reports the log path ignored and that `git status --porcelain` does not list it after a line has been written
- [x] 1.4 Verify in `t_busy` that an entry holds no subject, sender or body: log a review of synthetic messages whose subjects and bodies carry a recognisable marker, and confirm the marker is absent from the file while the identity, folder, count and duration are present

## 2. Counting what is in flight

- [x] 2.0 Rename the flag that says the board is leaving off `_closing`, which is Textual's own: its message loop reads `while not (self._closed or self._closing)`, so the board had been overwriting the framework's shutdown flag since the change that fixed the five-minute quit hang. Verify in `t_busy` that setting the board's own flag leaves it able to draw and to answer a key — the pause that never returned before this. Found while building this change, because nothing after it in the suite could run

- [x] 2.1 Count mailbox operations in flight on the board, raised where a review or an undo is launched; verify in `t_busy` against a substituted gateway that ticking a mail row raises it to one and a second tick to two
- [x] 2.2 Lower the count on every path where an operation ends, and verify in `t_busy` that it returns to zero after each of the six separately: confirmed, unconfirmed, already archived, in neither place, gateway unreachable, and given up because the board is closing
- [x] 2.3 Verify in `t_busy` that the count returns to zero after an undo, both when the messages are put back and when they are not found in the archive
- [x] 2.4 Verify in `t_busy` that the count is zero on a board that has done nothing, and on a board with no gateway configured after a tick that is refused for want of one

## 3. The indicator

- [x] 3.1 Draw one cell at the right of the day bar in every view, showing rest, in-flight and failed states with the glyphs the design names; verify in `t_busy` that the day bar's rendered text ends with the rest glyph on a board that has done nothing, in a day view, the inbox and the someday view
- [x] 3.2 Verify in `t_busy` that the cell shows the in-flight state while a review is held open by a substituted gateway, and the rest state once it completes
- [x] 3.3 Animate the in-flight state from a timer started when the count leaves zero and stopped when it returns; verify in `t_busy` that the glyph changes between frames while work is in flight, that it is one of the four named frames, and that no timer is running once the count is zero
- [x] 3.4 Verify in `t_busy` that animating redraws no row: with a review held open, the table's row count, the selected id and the view's scroll position are unchanged across several frames
- [x] 3.5 Verify in `t_busy` that every glyph the cell can show is one terminal cell wide by measuring it, so the bar's right edge cannot jitter between frames
- [x] 3.6 Set the failed state on any operation that fails, and verify in `t_busy` that it shows after a failure, still shows after a later review succeeds, and is cleared by asking for a reload

## 4. Quitting

- [x] 4.1 Ask before quitting while the count is above zero, through the board's existing confirmation, naming how much is outstanding; verify in `t_busy` that the confirmation appears with a review held open and that its text names the count
- [x] 4.2 Verify in `t_busy` that declining leaves the board running, showing the same view and the same selected row, with the operation still in flight
- [x] 4.3 Verify in `t_busy` that confirming ends the board
- [x] 4.4 Verify in `t_busy` that quitting with nothing in flight asks nothing and ends the board at once
- [x] 4.5 Verify in `t_busy` that a board ended without being asked still gives up a running confirmation cleanly, as it does today — the behaviour the existing suites cover must not change

## 5. Saying so

- [x] 5.1 Describe the cell and its three states in the help overlay, and that quitting asks while the mailbox is busy; verify in `t_busy` that the overlay names all three states and mentions the log's path, and that it names no Cyrillic key
- [x] 5.2 Verify in `t_busy` that the shipped wording does not claim the board writes nothing to disk, which the log makes false — grep the overlay and the module docstrings for such a claim

## 6. Nothing else moved

- [x] 6.0 Record the name-collision lesson in the project's apply guidance, since two landed in one change; verify `openspec instructions apply --json` still returns every entry it did before, the new one among them — the first attempt indented the entry at eight spaces where the list uses twelve, which folded the other fifteen into its own text and left one entry where there had been fifteen
- [x] 6.1 Run the self-contained tier (`python tests/run.py`) against frozen code, confirmed with `shasum` afterwards, and verify the whole tier is green apart from suites already recorded as failing — naming `t_review` and `t_gateway`, which drive the same paths the count now hooks, and `t_still`, which asserts on the day bar's position and the view. Result: 40 passed, 0 failed, `main.py` and `journal.py` unchanged through the run. Three suites needed updating first: `t_mailview` crashed on the shadowed method, `t_twins2` named the quit action, and `t_undo3` counted `Confirm(` call sites — that last one now names which functions may confirm rather than how many places do, so it cannot be satisfied by bumping a number
- [x] 6.2 Run the configuration tier (`python tests/run.py --config`, which needs the board's own `.env`) and verify `t_noleak` still passes, since a log in the repository is exactly what it exists to catch
- [x] 6.3 Take a fresh day-guarded baseline before any edit, then run the store tier with the suites' token (`python tests/run.py --store`) and verify the only failures are those the tier is recorded as failing, re-running any other once before believing it; where the baseline no longer describes the account, settle it by comparing a capture from a worktree at HEAD with one from the working tree. Result: 11 passed, 4 known to fail, plus `t_order1`, `t_reg2` and `t_regress` against a baseline the board had outrun — the account moved in both directions while the board was in use (today 22 against 19, the inbox 33 against 35, tomorrow 9 against 7). Settled by the capture comparison: HEAD and the working tree agreed on all 19 keys. With a refreshed baseline all three pass, 29/29, 19/19 and 21/21
- [x] 6.4 Verify against the real gateway that one review writes the entries the log should hold and that the indicator returns to rest — reporting counts, durations and outcomes only, no subject, sender or address. Driven through the board's own review worker rather than through `gateway.archive`, which is where the counting, the mark and the log live: a board with a **stubbed task store** and the real gateway, ticking one real row and putting it back. Nothing live about the half that need not be. The real configuration is captured before the harness is imported, so the harness goes on withholding the mailbox, the gateway and the log from every other suite. Result on the account: 26/26, one message archived and confirmed in 101.5 s, the count 1 then 0, the mark from rest to turning to rest, and two log entries carrying the folder, the count and the duration with no subject or sender
