## Why

A stray keypress changes a task and there is no way back. Worse, there is no
way to find out what happened: the row moved, something is different, and the
board says nothing about which key did it. Ticking is the common case, because
it is bound to the space bar and reorders the list the moment it lands.

Every write the board makes already records the values it is about to replace
— that is how a refused write is rolled back. What is missing is keeping that
record after the write succeeds, and a key that plays it back.

## What Changes

- A key undoes the most recent write, then the one before it, and so on back
  through the session. Each press says what it undid, by name: knowing what
  the stray keypress did is most of the value, since a person pressing this
  key is by definition unsure what just happened.
- An undo restores exactly the fields its own write changed, and no others.
  A write from further back therefore cannot overwrite something that has
  moved since, and an entry needs nothing from the view it was made in.
- An undo SHALL NOT create or destroy a task. It reverses changes to tasks
  that exist, and nothing else.
- Where the last write cannot be undone, the board SHALL say which one and
  why, rather than doing nothing:
  - **Deleting** — the task is gone, and the API has no way back.
  - **Filing a task that had no project** — `projectId` must match `^(?:P)-`
    and refuses both an empty value and none, so nothing returns a task to
    having no project.
  - **Adding** — undoing it would mean deleting, which this key will not do.
  Each of those three already asks for confirmation before it happens, which
  is the same boundary drawn from the other side: what cannot be undone is
  asked about, and what is asked about need not be undone.
- Marking a task done for today is undone **in part**, and says so. The date
  it moved comes back; the record that work happened cannot be withdrawn,
  because the API offers no inverse for it.
- One gesture is one undo. Moving a task sometimes writes several tasks — the
  board respaces a run when there is no numbering room between two rows, one
  write per task in the run plus the move itself, measured at five writes
  across four tasks for a single keypress — so an undo entry covers every task
  a single action wrote, not every request it sent.

Not in scope:

- **Redo.** An undo is not itself something to undo; pressing the key again
  reaches further back rather than turning round. A redo key would be a
  separate idea with its own stack.
- **Surviving a restart.** The board keeps nothing on disk, and undo is for
  the keystroke you just regretted.
- **Undoing what another client did.** The stack holds what this board wrote.

## Capabilities

### New Capabilities

None. The board gains one action over the writes it already makes.

### Modified Capabilities

- `task-board`: three new requirements cover undoing a write, what an undo
  restores, and what cannot be undone. One existing requirement changes: the
  list of actions the board offers gains the key.

## Impact

- `main.py`: the write record kept after a write is confirmed rather than
  dropped, a session-long stack of them, one action and one binding, and the
  key-bar and help entries. The Russian twin comes from the existing table.
  `respace` and the move it serves need to record one entry between them
  rather than one each.
- `singularity.py`: nothing, or close to it. Restoring is an ordinary field
  update, including for completion: `checked` was confirmed settable to 0, 1
  and 2 through the ordinary update, and completing a task was confirmed to
  change no other field, so a tick reverses with a single value.
- No new dependencies, no new endpoint, and no change to what any existing
  action does.
