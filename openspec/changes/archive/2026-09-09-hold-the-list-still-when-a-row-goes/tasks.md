## 1. The view stops moving on its own

- [x] 1.1 Save the table's scroll position before the rebuild and restore it after, and stop `move_cursor` scrolling; verify with a new self-contained suite (`tests/stub/t_still.py`, a stubbed store, no mailbox, no network, every row generated) that a redraw with the selection unchanged leaves the offset exactly as it was, on a list of 600 rows scrolled part way down
- [x] 1.2 Verify in `t_still` that ticking the selected row leaves the offset unchanged and that the row on the view's top line is the same row it was — the property the screenshots showed broken
- [x] 1.3 Verify in `t_still` that the row following the ticked one is selected on the same screen line the ticked row occupied, measured as `cursor_row - scroll_y` before and after
- [x] 1.4 Verify in `t_still` that ticking five rows in succession moves the selection's screen line not at all, and that each press removes exactly one row
- [x] 1.5 Verify in `t_still` that a redraw driven the way a background load drives one — rebuilding every row with the selection unchanged — leaves the offset alone, repeated three times

## 2. A row that would fall out of sight is still found

- [x] 2.1 Reveal the selected row when the restored view does not show it, and centre it rather than revealing it by the minimum; verify in `t_still` that a selection forced outside the visible band is brought into view
- [x] 2.2 Verify in `t_still` that the revealed row is not on the last visible line — the bottom-edge pin this change exists to remove — by comparing its screen line against the viewport's height
- [x] 2.3 Verify in `t_still` that ticking a task, whose completion re-sorts it among the finished rows while the selection moves to the next unfinished one, leaves that selection visible
- [x] 2.4 Verify in `t_still` that a view which loses most of its rows while scrolled far down shows the end of the shorter list, with the offset clamped rather than left past the end
- [x] 2.5 Start a new view at its beginning, remembering which view the table was last drawn for, and verify in `t_still` that pressing the today key from part way down a 600-row inbox opens a sixty-row day at its first row, that coming back opens the inbox at its first row, that stepping between days does the same, and that a redraw of the same view — or asking again for the view already shown — still holds its place. Needed code, not only a check: the design had measured this on a six-row day, where the carried-over row number clamps to zero and looks correct

## 3. The key bar names the keys a person presses

- [x] 3.1 Add the two bracket keys to the key bar's name table, and verify in `t_still` that `KeyBar.entries()` reports `[` and `]` for the note-scrolling actions and that no entry anywhere in the bar is a toolkit name — no entry containing an underscore
- [x] 3.2 Verify in `t_still` that the bar and the help overlay still agree: every key the bar names is described in the overlay, which is what the shipped requirement about the bar promises

## 4. Nothing else moved

- [x] 4.1 Run the self-contained tier (`python tests/run.py`) against frozen code, confirmed with `shasum` afterwards, and verify the whole tier is green with no new known failures — naming `t_top`, `t_move`, `t_writes`, `t_review` and `t_pane`, which move the cursor, and `t_move`, `t_work3`, `t_work5`, `t_undo3`, which read the key bar. Result: 39 passed, 0 failed, all of those green. **Not green every run**: `t_undo1` fails about 1 in 5 on a loaded machine, proved to be a product race this change makes lose more often rather than a fault of its own, recorded in `known_failures.FLAKY` with its signature and with `tests/probes/t_race.py` as the instrument. It passed in this run
- [x] 4.2 Run the configuration tier (`python tests/run.py --config`, which needs the board's own `.env`) and verify it is green
- [x] 4.3 Take a fresh day-guarded baseline before any edit, then run the store tier with the suites' token (`python tests/run.py --store`) and verify the only failures are the four this tier is recorded as failing, re-running any other failure once before believing it. Result: 11 passed, 4 known to fail, plus `t_order1`, `t_reg2` and `t_regress` failing the same three checks — today 18 tasks against the baseline's 21, ten past due against thirteen, eight inbox rows in a different order. The board was in use through this session, so the baseline no longer described the account. Settled with the instrument that can tell the two apart: a capture from a worktree at HEAD and one from the working tree, minutes apart, agreed on all 19 keys — the same rows, order and counts. With a refreshed baseline all three pass, 29/29, 19/19 and 21/21
- [x] 4.4 Measure in `t_still` how long a redraw takes with the offset saved and restored on a 600-row list, and confirm it is no slower than the 0.03 s already recorded for a redraw of that size. Measured 0.009-0.012 s a redraw of 600 rows, and the suite holds a one-second bound so a pane or a hold that made drawing slow would be visible
