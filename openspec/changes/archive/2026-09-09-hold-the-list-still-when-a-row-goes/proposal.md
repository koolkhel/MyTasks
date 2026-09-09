## Why

Ticking a row scrolls the list. Measured from two screenshots of the real
inbox, one space press apart: the cursor was on line 7 of a 20-row viewport
with the next fifteen mail rows below it; afterwards the view had scrolled
thirteen rows *up* into the task list and the cursor sat on the last line,
with nothing below it at all.

The board never asks for that. `repaint` rebuilds the table from scratch, and
`DataTable.clear()` sets `scroll_y = 0`; `move_cursor(row=N)` then scrolls the
minimum needed to reveal row N, and from the top the minimum is "put N on the
last visible line". The arithmetic matches the screenshots exactly: the
offset went from `N-6` to `N-19`, and `N-19` is `N - 20 + 1`.

A repaint happens on every write confirming, every mail, calendar or tracker
load, and every tick — of a task as much as a mail row. It is only visible
now because the inbox is 600 rows long, so scroll position finally means
something.

## What Changes

- Ticking a row, or any other repaint, leaves the list where it was. The
  reviewed row vanishes and the rows below slide up one; nothing else on
  screen moves, and the cursor stays on the line it was on.
- Where a repaint would leave the selected row outside the visible area, the
  board still reveals it — centred, rather than pinned to the last line. This
  is the case ticking a *task* creates: the ticked task re-sorts down among
  the finished ones while the selection moves to the next unfinished one.
- Changing view starts the new view at its beginning. It carries the old
  view's *row number* today, so entering a sixty-row day from row 300 of the
  inbox lands on its last row, and coming back carries that into the inbox as
  row twenty. That number means nothing across views. **Noticed from use
  while this change was being built**, and it is the same complaint one step
  along: the list arriving somewhere nobody asked for.
- The key bar names the note-scrolling keys `[` and `]`. It shows
  `left_square_bracket` and `right_square_bracket` today: the bar has its own
  table for turning Textual's key names into keys a person presses, and those
  two were never added to it when the keys were.

## Capabilities

### New Capabilities

None. This is about where an existing view puts an existing selection.

### Modified Capabilities

- `task-board`: a new requirement for where the selection sits on screen
  after a redraw — the spec covers *which* row is selected in detail and says
  nothing about where it lands, which is why this went unnoticed. Plus the
  requirement about the key bar, which promises the bar names the keys a
  person presses.

## Impact

- `main.py`: `repaint` saves and restores the table's offset and stops
  `move_cursor` scrolling; two entries in the key bar's name table.
- `tests/`: a suite for the offset — that a tick leaves it unchanged, that
  the next row lands on the line the ticked one occupied, that a selection
  which would fall off-screen is still revealed, and that a shrinking list
  clamps rather than stranding the view. Plus the existing suites that read
  the key bar (`t_move`, `t_work3`, `t_work5`, `t_undo3`) and those that move
  the cursor (`t_top`, `t_move`, `t_writes`, `t_review`).
- Nothing outside the board: no store, no mailbox, no gateway, no network.
  Every row in the new suite is generated, so nothing from a real account
  reaches a fixture.
