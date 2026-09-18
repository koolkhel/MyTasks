## Why

A tracker issue on today's board is a key, a summary, a state and a project.
What the issue is actually about -- its description -- is a click away in the
browser, and the version it is to be fixed in is nowhere at all: the board
reads it, keeps it on every issue's row, and hands it to the workspace program,
but never draws it. A person deciding what to pick up next has to leave the
board to find out either.

The board already has the place for both. A selected task shows its note in
the area under the list and on the focus card; a selected event shows its
description there, a selected message its body -- each by carrying its text as
the row's note. An issue can do exactly the same, and the line above the note,
which carries a task's flags, can carry an issue's facts.

## What Changes

- The tracker is asked for each issue's description, on the one request it
  already answers. No further call, no further page.
- A tracker row carries the description as its note, so the area under the
  list, the focus card and the note-scrolling keys show it with no change to
  any of them -- as text, escaped, exactly as an event's description is.
- For a tracker row, the first line of that area names the issue's facts: the
  state the tracker reports it in, its project, and the version or versions it
  is against, where a version field is configured and the issue carries one.
  Where it carries none, no version is named and nothing says so.
- The row itself does not change: no column gains a version, no title grows.
  The versions are read when the row is selected, which is one keystroke, and
  the columns are already spent.

Recorded assumptions:

- The description is shown as the text it is. Trackers write Markdown or their
  own wiki syntax; the board does not render either, and shows the characters
  -- the same rule as for an event's description and a message's body.
- "Fix version" is whatever the configured version field holds. The board does
  not name the field; the configuration does, and on the account this was
  built for it is the tracker's standard *Fix versions*.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement added -- what a tracker issue says is shown
  when its row is selected. Nothing existing changes: reading the version is
  already specified, and the area's own behaviour holds as written.

## Impact

- `tracker.py` -- `description` on the fields asked for and on `Issue`.
- `board.py` -- the row carries it as its note; the facts line for a tracker
  row is decided beside the rest of what is drawn.
- `main.py` -- the detail area and the focus card show the facts line for a
  tracker row where they show a task's flags.
- Suites: the tracker block (`t_track2`), the pane's rows-from-elsewhere part
  (`t_pane`), the version reading (`t_version`), all on invented issues.
- `docs/screenshots.py` -- the today picture, with the cursor on an issue so
  the area shows what this adds.
