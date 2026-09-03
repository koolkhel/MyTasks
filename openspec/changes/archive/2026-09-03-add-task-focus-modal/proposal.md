## Why

The board never shows a task in full. The table gives the title whatever width is left after the mark, when, and project columns, so anything long is cut off, and the detail strip under the list is a couple of muted lines about flags and the note. There is no view that answers "what am I working on right now" at a glance. Meanwhile the enter key is spent duplicating the tick that space already does, so it is free for something that earns it.

## What Changes

- Pressing enter on the selected task opens a focus card showing it in full: the whole untruncated title, when it is due, its project, its deadline, and its note.
- The card is display-only. It closes on escape and no write path runs from it, so every way of changing a task stays exactly where it is today.
- Enter is taken off the tick binding, where it was dead weight: the task list binds enter to its own row-selection action and consumed the key before the board ever saw it, so `space,enter` only ever ticked via space. Nothing a person could actually do is removed.
- The card is reachable in all three views, matching the existing rule that what works on a day works in the inbox and in never.

## Capabilities

### Modified Capabilities

- `task-board`: gains a focus view of the selected task. This is a new requirement on the existing capability; nothing already specified changes, because the spec describes tick and untick as an action without naming the keys that reach it.

## Impact

- `main.py` — a new modal screen alongside `TaskInput`, `Confirm`, and `DatePicker`; the bindings list, where `space,enter` splits so enter carries the new action; and the help overlay, which the spec already requires to list only keys the board actually binds.
- `singularity.py` — no change. `Task` already exposes the title, the start label, the deadline, the note as plain text, and the project id, and the board already holds the project-id-to-name map it needs for the card.
- No new dependencies, and no change to `run.sh`, `requirements.txt`, or `.env`.
- Nothing in the store changes: this is the first behavior added to the board that issues no requests at all.
- The repo has no automated test suite; verification is through the Textual pilot harness, and the assertion that the card writes nothing is checked by watching the outgoing requests while it is opened and closed.
