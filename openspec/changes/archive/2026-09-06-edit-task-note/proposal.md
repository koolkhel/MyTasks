## Why

A task's note is the only thing the board shows that it cannot change. Every
other field has a key; a note can be read and nothing more, so the moment a
detail needs recording the board stops being the place the work happens and
SingularityApp's own client has to be opened.

The reading half already exists and is complete: notes are stored as a Quill
delta — a JSON string describing a document as the inserts that build it — and
the board already decodes one. Nothing encodes one back.

Measured on this account: of 306 tasks, 52 carry a note, every one is a single
insert ending in a newline, and **not one carries a formatting attribute or an
embed**. The format that looks like an obstacle is, for this data, one line of
JSON in each direction.

## What Changes

- A key opens the selected task's note in an editor inside the board, holding
  the note's current text, and saving writes it back. Cancelling writes
  nothing.
- Saving an empty note clears it, and clearing is undoable like any other
  write.
- The editor is a component of the board's own, so that keys which act on the
  text — a template, a stamp, a line transformed — have somewhere to live
  later without the editor being rebuilt for them.
- A note carrying formatting the board cannot represent is refused rather than
  flattened: the board would have to throw the formatting away to save, and
  losing it silently is worse than declining.
- Events and tracker issues refuse the key, as they refuse every other key
  that writes.
- A note is shown in the detail area as the characters it contains.
  **This is a fix, not a new feature**: that area renders its text as markup
  today, so a note containing `[x]` already loses those characters. Read-only
  it was a curiosity; once a person can type them it reads as the board
  destroying what they wrote, which is why it belongs to this change and not
  a later one.

## Capabilities

### New Capabilities

None. This completes an existing capability rather than introducing one.

### Modified Capabilities

- `task-board`: one requirement added — editing a task's note. Two modified —
  the list of actions the board offers gains note editing, and the detail
  requirement gains that a note is shown as its own characters.

## Impact

- `singularity.py` — an encoder beside the existing decoder, and the note
  written through the update the board already uses.
- `main.py` — a key, an editor screen, and the editor component the screen
  holds.
- No new dependency. The editor is built from what the UI framework already
  ships, which also means the whole path can be driven by the test harness —
  an external editor could not have been, because suspending the board is not
  supported in the environment the suites run in.
- Nothing about how notes are stored changes; the board starts writing a field
  it has only ever read.
