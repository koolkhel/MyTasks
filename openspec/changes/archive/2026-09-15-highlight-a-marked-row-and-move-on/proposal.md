## Why

Marking rows to copy them works, and it is hard to see and slow to do.

A mark is drawn as one character in a two-cell column. Against a screenful of
rows that character is easy to miss, and there is nothing to tell at a glance
how much of the list is chosen. The board already has a way of saying "this
row", and it is the selection bar.

Marking a run of rows takes two presses each, `v` then a movement key, because
the cursor stays where it is. The rows a person marks are usually next to each
other -- the part of a day being broken down, a stretch of the inbox -- so the
movement is nearly always the same one.

## What Changes

- A marked row is drawn as a bar across the whole row, in the colour the
  selection bar already uses, rather than as a character in one column.
- The cursor stays distinguishable from a mark: it keeps its own bold, pale
  text on that bar, where a marked row carries the ordinary one. Both are
  bars; the cursor is the bold one. A row that is both is drawn as the cursor,
  because where a person is outranks what they chose.
- While a row is marked its title is drawn in the ordinary colour: the
  past-due colour and the dimming of a finished row are left off. This is not
  new behaviour but the existing behaviour of the selected row, applied to a
  second kind of row -- those colours are unreadable on the bar, and a
  past-due row is already told apart by its age label when it is selected.
- The mark character stays where it is, beside the row's own mark. It costs no
  width, and it is the only thing that reports a mark on the row the cursor is
  sitting on, where the bar says nothing.
- Pressing the marking key moves the cursor to the next row, so a run can be
  marked by pressing one key repeatedly. It moves on taking a mark off as well
  as putting one on: one rule rather than two.
- On the last row the cursor stays where it is, and the mark is still made.

## Capabilities

### New Capabilities

None. This is how an existing key draws and behaves.

### Modified Capabilities

- `task-board`: how a marked row is drawn, and where the cursor goes when a
  row is marked. The requirement that a mark and the cursor are told apart
  stands; what changes is that both are now bars and the difference is weight
  and colour rather than a glyph against no glyph.

## Impact

- `main.py`: a `DataTable` subclass supplying the row's background, the title
  drawing in `row_for`, and the marking action.
- A private framework hook is the only way to give a row that is not the
  cursor a background across its whole width. The risk that a framework
  upgrade removes it silently is recorded in the design and covered by a task.
- No change to any module that talks to the store, the mailbox, the calendar
  or the tracker. Nothing here writes anything.
