## Why

A task list is sometimes better thought about somewhere else. Breaking a piece
of work into its parts wants a free-form outliner, not a board with one task
per row -- and today the only way to get a row into such an editor is to
retype it, and the only way to get the parts back is to press the add key once
per line.

The board is also the one place in this workflow with no way out. Mail can be
promoted into it, the tracker and the calendar are read into it, but nothing
leaves it as text. That makes it a destination rather than a stage.

## What Changes

- A person can mark rows on the board and copy them to the system clipboard as
  markdown: `- [ ] title` for an unfinished task, `- [x] title` for a finished
  one, and `- [x] ~~title~~` for a cancelled one, which is a third state
  markdown has no box for.
- Marking is offered on every row the board draws, the mailbox's, the
  calendar's and the tracker's included. Copying reads a row; it does not
  change one, and the rows this board does not own are as readable as the ones
  it does. They carry no tick state of their own and copy as `- [ ]`.
- Marks are a set of rows rather than a range of lines: they survive a redraw
  and follow the person between views, so rows gathered from three different
  days can be copied together. The board says how many are marked where it
  already says what a view is not showing.
- Pasting several lines into the board adds one task per line to the view on
  screen -- undated in the inbox, deferred in someday, on the shown day
  otherwise -- by the same rules the add key already follows.
- A pasted line is read as a task description with its list decoration
  removed: a leading `-`, `*`, `+` or `1.`, a markdown checkbox, and the
  indentation in front of them. A line that carries no decoration is a task
  too. `- [x]` is read rather than merely stripped, so rows copied out and
  pasted back come back as they left.
- A paste is one action and one undo, however many tasks it made. This is the
  second action on the board that reverses a creation by deleting it, after
  promoting a mail thread.
- Pasting several lines while the add prompt is open stops silently discarding
  all but the first. That is today's behaviour and it loses work without
  saying so.

## Capabilities

### New Capabilities

None. This is the board's own behaviour.

### Modified Capabilities

- `task-board`: adds marking rows, copying them out as markdown, and pasting
  lines in as tasks. Modifies the enumeration of the actions a person may
  take; what escape clears; what cannot be undone, which today says no undo
  ever deletes a task while the promotion requirement already has one that
  does; and where several tasks added at once land in a day's order.

## Impact

- `main.py`: the key table and its two-layout twins, the marked set and how a
  marked row is drawn, the status line, a paste handler on the app, the
  markdown reader and writer, the clipboard write, and the prompt's own paste.
- No change to `singularity.py`'s surface. Creating a finished task is a
  creation followed by the completion endpoint, which the existing write queue
  already carries across the identifier it is given back.
- Two hazards to measure rather than assume, both recorded in the design: how
  many requests a paste of many lines sends at once, and whether tasks created
  in one action can tie for position in a day.
