## Why

The note pane below the list is `height: auto` with `max-height: 40%`, so it is
as tall as whatever the selected row happens to carry: nothing for a task with
no note, a single line for a short one, seventeen rows for a YouTrack message.
The list resizes every time the cursor moves, which means the rows move under
the hand that is moving through them — worst exactly where the volume now is,
stepping down a queue of 564 mail rows whose bodies differ wildly in length.

And because the pane is capped at 40%, a long message is cut with no way to
read the rest of it in place. Mail arrived in this board a change ago; a
notification body is the one thing on screen that routinely does not fit.

## What Changes

- The note pane keeps a fixed height — eight rows — whatever the selected row
  carries, and whether or not anything is selected. On a window too short for
  eight to be reasonable it falls back to 40% of the height, as now.
- The pane scrolls. `[` and `]` move it up and down a page at a time, keeping
  one line of overlap, while the cursor stays on its row. Both keys get their
  Cyrillic twins, as every key on this board does.
- The pane shows a scrollbar when its content overflows and none when it fits,
  so "there is more below" is visible rather than guessed.
- Moving the cursor to another row returns the pane to the top of that row's
  note, so a note always starts where it starts.
- The help overlay and the key bar say so.
- Adjacent, and small: the focus card (`enter`) shows a note without escaping
  it, so a note containing `[bold]` is drawn as styling there while the pane
  below the list draws it as characters. The two places that show a note
  should agree. **Strike this from the change if you would rather it stood
  alone** — it is a defect of its own, not part of holding the pane still.

## Capabilities

### New Capabilities

None. This changes how an existing region behaves, not what the board can do.

### Modified Capabilities

- `task-board`: "Detail of the selected task" gains the pane's fixed height,
  its scrolling and the keys that do it, and the rule that the pane returns to
  the top when the selection changes. "Actions available on the selected task"
  gains the two scrolling keys. "Focus view of the selected task" gains the
  rule that it shows a note as the characters it contains, which is what the
  pane below the list already promises.

## Impact

- `main.py`: the CSS for `#detail`; `compose` (the pane becomes a scrollable
  container holding the same `Static`, so `#detail` goes on naming the widget
  the text is written to and no suite that queries it changes); two new
  bindings and their actions; `update_detail` resets the offset; the help text
  and the key bar; `TaskFocus.compose` escapes its note.
- `tests/`: a suite for the pane — its height with an empty note, a short one
  and one far longer than it; that the list keeps the same number of rows as
  the cursor moves; that the keys scroll it and do not move the cursor; that
  the offset returns to the top on a new selection; that a scrollbar appears
  only when there is more. Plus the existing suites that read `#detail`
  (`t_mailview`, `t_note`) and the key-twin suites.
- Nothing outside the board: no store, no mailbox, no gateway, no network.
