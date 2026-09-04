## Why

A day's tasks come out in an order the board derives entirely from their
fields, and the last thing it falls back on is the title. Alphabetical is
arbitrary: it says nothing about what to do first. For the bulk of a day —
15 of today's 17 rows are all-day tasks, which share every other ordering
key — the sequence on screen is therefore decided by spelling.

The API already carries the field for this. Every task has an integer
`scheduleOrder`, populated on all of them, writable on create and update,
and plainly the field SingularityApp's own drag-to-reorder writes: the
values in this account carry the sparse-index signature of a hand-ordered
list, gaps of ~8684 in untouched regions and ~100-300 where rows have been
moved repeatedly. Nothing on the board reads it today.

## What Changes

- A person can move the selected task up or down within a calendar day, and
  the position sticks: it is stored on the task, so it survives a reload and
  is the same order SingularityApp's own clients show.
- `K` moves the selected task up, `J` moves it down. Lowercase `j`/`k`
  already move the cursor, so uppercase moving the task reads as the same
  gesture with more force. Both are plain characters, which no terminal can
  swallow.
- The manual order replaces the title as the day's final ordering key. Every
  key above it stands unchanged: unfinished before finished, past due before
  due today, most overdue first, pinned first, timed before all-day, earlier
  start before later. Title survives as a last-resort tie-break.
- A task added to a day is placed at the end of that day's order rather than
  the beginning. Today every task the board creates is stored with
  `scheduleOrder` 0, which is the lowest value there is — so without this,
  every added task would jump to the top of its group and tie with every
  other one the board has ever added.
- Moving a task against the edge of its group — trying to lift an all-day
  task above a timed one — reports why it cannot move rather than doing
  nothing, in the way day navigation already explains itself in the buckets.

Deliberately not in scope, with reasons:

- **The dateless views keep their alphabetical order.** A triage queue and a
  someday list are not sequences of work, and the data agrees: 27 of the 29
  tasks in this account's inbox carry `scheduleOrder` 0, so ordering by it
  would move 24 of 29 rows and leave them tied anyway. Reordering is offered
  on calendar days only, and the keys say so in the other views.
- **Past-due tasks stay in most-overdue-first order.** They can be sequenced
  by dating them to today, which is the point at which a person has decided
  to do the thing; a task whose deadline has genuinely passed stays where
  overdue order puts it.
- **`cmd`+arrow is not used, because it cannot be.** Textual exposes no
  `super`, `meta`, or `command` modifier at all, and macOS does not forward
  Cmd to the terminal, so no binding on it could ever fire.

## Capabilities

### New Capabilities

None. This is the existing board gaining an ordering it does not have.

### Modified Capabilities

- `task-board`: the day's final ordering key changes from the title to a
  manual order a person sets, two actions are added for setting it, and
  where a newly added task lands becomes specified rather than incidental.
  The ordering of the dateless views is deliberately unchanged.

## Impact

- `singularity.py`: `Task` gains a way to read `scheduleOrder`;
  `sort_for_display` takes the manual order as its final key for day views
  while the dateless views keep the title, so the one function serves both;
  the client gains a way to send several writes as one operation, and
  `create_task` needs the order the caller wants rather than the server's
  default of 0.
- `main.py`: two bindings and their actions; the key bar and help gain two
  entries; `submit_write` currently records a write against exactly one task
  and a swap touches two, so it needs to carry a write that spans a pair —
  otherwise half a swap can land and leave two tasks sharing one order value.
- The `/v2/batch` endpoint is newly used, so that a swap is one atomic round
  trip rather than two writes that can half-fail. It accepts POST, PATCH and
  DELETE with a client-supplied UUID for idempotency, which has been
  confirmed against the live API to deduplicate a replayed operation.
- No new dependencies.
