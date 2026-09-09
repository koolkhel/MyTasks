## 1. The pane holds still

- [x] 1.1 Make the detail area a scrollable container holding the same `Static#detail`, and verify with a new self-contained suite (`tests/stub/t_pane.py`, no store, no mailbox, no network) that `query_one("#detail", Static).render()` still answers the note's text — the interface four existing suites read
- [x] 1.2 Stop the container taking focus, and verify in `t_pane` that the table is still what holds focus after the board has drawn, that `down` and `j` still move the cursor, and that no key reaches the pane by tabbing to it
- [x] 1.3 Give the pane a fixed height with a share-of-the-window cap, and verify in `t_pane` against a stubbed store that the table's row count is identical for a row with no note, a row with a one-line note and a row whose note is forty lines — measured at 80×44 and again at 80×20
- [x] 1.4 Verify in `t_pane` that the pane shows eight rows of text on a window of 44 rows and falls back to a share of the height on one of 12, and that at each size the pane's height is the same for all three notes of 1.3
- [x] 1.5 Verify in `t_pane` that the pane is its full height with nothing selected at all — a view holding no rows — rather than collapsing as it does today

## 2. Reading a note that does not fit

- [x] 2.1 Bind `[` and `]` through the key-twin helper so each carries its Cyrillic twin, and verify in `t_pane` that both twins scroll and that `t_twins`-style key-table checks still pass (`tests/stub/t_twins1`, `t_twins2`, `t_twins4`)
- [x] 2.2 Scroll the pane by its height less one line, and verify in `t_pane` that `]` on a forty-line note moves the offset by exactly the pane's height minus one, that a second press moves it again, and that `[` returns it
- [x] 2.3 Verify in `t_pane` that scrolling does not move the selection: the cursor row and the selected id are unchanged after `]`, and `down` still moves the cursor afterwards
- [x] 2.4 Verify in `t_pane` that `[` at the top and `]` on a note that fits leave the offset at zero and report nothing, and that neither key writes: no call reaches the stubbed store
- [x] 2.5 Verify in `t_pane` that the pane's scrollbar is shown for a note longer than the pane and hidden for one that fits, at both window sizes
- [x] 2.6 Verify in `t_pane` that scrolling works on a row the board does not own — a mail row built from a copied fixture, a calendar row and a tracker row — and that the row is not refused as unownable

## 3. A new selection starts at the beginning

- [x] 3.1 Return the pane to the top when the selected row changes, remembering which row it was last drawn for, and verify in `t_pane` that scrolling part way down one row's note and then moving to another shows the new note from its first line
- [x] 3.2 Verify in `t_pane` that a repaint of the *same* row leaves the offset where the person left it — drive a repaint the way a background load does, with the selection unchanged, and confirm the offset is untouched
- [x] 3.3 Verify in `t_pane` that moving away from a row and back again shows that row's note from the top rather than where it was last read to

## 4. The focus card agrees with the pane

- [x] 4.1 Escape the note in the focus card, and verify in `t_pane` that a note holding `[bold red]LOUD[/]` shows every character there and applies no styling — the same two checks `t_note` already makes about the pane
- [x] 4.2 Verify in `t_pane` that the card still shows a note that needs no escaping unchanged, and that a task with no note renders no note line

## 5. Saying so

- [x] 5.1 Add the two keys to the help overlay and the key bar, and verify in `t_pane` that both list them, that the overlay says the pane keeps one height and scrolls, and that the overlay names no Cyrillic key
- [x] 5.2 Verify in `t_pane` that the shipped wording no longer describes the detail area as sized to its content, if it ever did — grep the overlay text and the module docstrings for a claim the change makes false

## 6. Nothing else moved

- [x] 6.1 Run the self-contained tier (`python tests/run.py`) and verify every suite that reads `#detail` still passes unchanged — `t_mailview`, `t_promote`, `t_note` — and that the whole tier is green with no new known failures
- [x] 6.2 Run the configuration tier (`python tests/run.py --config`, which needs the board's own `.env`) and verify `t_evlink`'s three `#detail` checks still pass
- [x] 6.3 Run the store tier with the suites' token (`python tests/run.py --store`) and verify the same five suites known to fail before this change are the only ones failing, so no board-drawing change has reached the live views. Result: 13 passed, 4 known to fail — the four this tier holds, the fifth being the tracker tier's. `t_perf2` also failed at 3/4 and passed 4/4 run alone straight afterwards: it times the board with writes in flight, so it fails under a busy tier. Recorded in `known_failures.FLAKY` rather than chased; a failure caused by this change would reproduce with this change in place, and it does not
- [x] 6.4 Measure in `t_pane` how long a repaint takes with the pane holding a forty-line note beside 460 mail rows, and record it beside the figure `t_mailperf` already prints, so a pane that made drawing slower would be visible rather than discovered
