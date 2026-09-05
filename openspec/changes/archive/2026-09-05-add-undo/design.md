## Context

See proposal.md — Why for the motivation.

What the board already has, which decides most of this:

- Every write is recorded as a `Pending` carrying `patch` — the raw fields it
  changes — and `previous`, their values beforehand (`main.py`). That record
  exists so a refused write can be taken back, and it is exactly what an undo
  needs. `_write_done` currently drops it once the API agrees.
- Writes queue per task and drain concurrently, so an undo can be enqueued
  like anything else and will not overtake a write still in flight on the same
  task.
- Repainting recomputes every derived thing from the tasks it holds, so a
  restored value needs no special handling to appear correctly ordered.

Confirmed against the live API before proposing:

- `checked` is settable to 0, 1 and 2 through the ordinary update, so ticking,
  unticking and cancelling all reverse as plain field writes.
- Completing a task changes `checked` and nothing else — `journalDate`,
  `complete`, `completeLast` and `seenToday` were all unmoved — so restoring
  the one value restores the task.
- There is no inverse for `complete-today`. The only endpoint mentioning today
  is the one that records it.
- `projectId` still refuses both an empty value and none, so a first filing
  has nothing to restore to.
- One move keypress writes one task where there is room, and one per task in
  the run plus the move where there is not: five writes across four tasks in
  the cramped case.

## Goals / Non-Goals

**Goals:**

- One record type, reused rather than reinvented: the values a write replaced.
- One gesture, one undo, whatever it cost in requests.
- A key that can be pressed in ignorance and leaves the person better informed.

**Non-Goals:**

- No redo. Reaching further back is the only direction this key goes.
- No persistence. Nothing survives closing the board.
- No creating or destroying tasks, so no undo of an add or a delete.
- No inverse operations written per action. Anything needing one is a sign the
  approach is wrong.

## Decisions

### An undo is the write record played backwards, not an inverse action

Each action already declares the fields it changes and their previous values.
Undoing is sending the previous values back. Nothing knows that unticking
reverses ticking, or that a date can be put back — those follow from the
record.

This is what keeps the feature from rotting. A per-action inverse would need a
new branch for every action added later, and each branch would be a place to
get it wrong; a record of what changed is right by construction and was
already being kept.

It also bounds the blast radius: an undo touches only the fields its write
touched, so an old entry cannot revert something that moved since.

Rejected: reverse endpoints per action — `uncomplete` for a tick, a stored
previous date for a reschedule. It is what the board reaches for first,
because `complete_task` and `uncomplete_task` exist as a pair, but it makes
undo a parallel implementation of every action.

### An entry covers an action, not a request

Moving a task in a cramped run writes every task in it. Those writes are one
keypress, and one press of the undo key must reverse all of them, so an entry
maps task ids to the previous values for each — not a single task.

The multi-task shape costs almost nothing: the same dictionary, keyed one
level deeper. Making it the shape from the start avoids the alternative, which
is discovering after the fact that a person must press undo five times to
reverse one keystroke.

### A refusal drops an entry only when nothing of it was applied

A refused write is not something to undo, so a lone refusal leaves no entry.
But an action can take several writes, and one failing does not unhappen the
others: this API refuses a write now and then and succeeds on a retry, and a
move that respaced a run of four takes five. Dropping the whole entry on one
refusal would throw away the ability to undo the four that landed — which is
worse than not recording it at all, because the board would have changed those
tasks and then denied any knowledge of it.

An entry therefore counts how many of its writes the API accepted, and is
discarded only when that count is zero. This was found by running the live
test: it passed, then failed, then passed again, with the run left respaced
and the entry gone.

### Nothing that creates or destroys goes on the stack

The three writes that cannot be reversed — deleting, adding, first filing —
are recorded so that the key can name them and say why, but they are never
acted on. That is better than leaving them off the stack entirely, which would
make the key silently skip past the very action a person is asking about.

The boundary is worth stating because it is not a coincidence: those same
three are the ones the board confirms beforehand. Undo and confirmation cover
the same set from opposite sides, and the spec ties them together so a later
action cannot quietly be neither.

### Undo is a write like any other

It goes through the same optimistic path: shown at once, queued per task,
rolled back if refused. So an undo of a task with a write still in flight
queues behind it rather than racing it, and a refused undo behaves like any
other refused write.

An undo does not push its own entry. Pressing the key twice reaches back two
writes rather than turning round — which is what the key is for, and what
makes repeated presses predictable.

### Done for today is undone in part, and says so

The record and the reschedule are two operations, and only one has an inverse.
Restoring the date is right and useful; claiming the whole action was reversed
would not be. The board says which half came back.

Rejected: refusing to undo it at all. The date is the part that moved the task
out of view, and it is the part a person notices.

## Risks / Trade-offs

- **An action half applies and the undo restores all of it** — the entry
  restores previous values for every task the action touched, including one
  whose write was refused → harmless, because restoring a value a task
  already holds changes nothing; the alternative, tracking which writes
  landed per task, buys precision no one can observe.
- **An old entry restores a value the person has since changed elsewhere** —
  they tick a task, change it on their phone, then undo → the undo restores
  only the fields that write changed, so the phone's change survives unless it
  touched the same field; nothing else can be caught by it.
- **The stack grows for a long session** — every write is remembered → entries
  are small, hold no task objects, and die with the board; if it ever matters,
  a bound is a one-line change rather than a redesign.
- **A person walks back further than they meant** — repeated presses reverse
  real work → every press names what it reversed, which is the only defence
  that scales, and there is no press that destroys anything.
- **Undo restores a task into a view it is not in** — undoing a reschedule
  from another day changes a task the person cannot see → the board names the
  task it acted on, so the message carries what the view cannot.
