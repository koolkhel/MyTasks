## Context

See proposal.md — Why. What the code does now:

- `Undoable.applied` counts how many of an action's writes the API has
  accepted. It is incremented in `_write_done` and read in exactly one place,
  `forget()`.
- `forget(group)` keeps an entry `if e.applied`. It is called from exactly one
  place, `_write_failed`, at the moment a refusal arrives.
- `_write_failed` pops the *whole* queue for the refused write's task, because
  the writes behind it were chosen against a state that never came about. So
  those writes can never settle.
- `_write_done` and `_write_failed` both reach the board through
  `call_from_thread` from the drain worker, so both run on the thread that also
  runs `submit_write`. An action therefore has all of its writes in
  `_pending` before any of them can settle.
- The board already derives its in-flight total rather than counting it:
  `in_flight = sum(len(q) for q in self._pending.values())`, for the status
  line. `Pending` carries the `group` its write belongs to.
- `_pending` is only ever reduced in three places: releasing an empty queue,
  re-keying a created task, and the refusal above. Nothing clears it wholesale,
  so a group always reaches nothing outstanding.

## Goals / Non-Goals

**Goals:**

- The entry is dropped on an answer that is knowable, not on the first one to
  arrive.
- No new state to keep in step.

**Non-Goals:**

- Bounding the undo stack. It is unbounded today and this does not change how
  many entries it holds — only which ones survive a partial refusal.
- Changing what a refusal reports, or what it takes back on screen. That is a
  different requirement and it is already right.
- Making an undo of a partly-refused action retry the refused write. Undo
  reverses what landed; the refused write never landed and there is nothing of
  it to reverse.
- Ordering an action's writes. They are independent per task by design, and
  the fix is to stop depending on their order rather than to impose one.

## Decisions

### Only the refusal path changes

A confirmed write cannot cause an entry to be dropped: it has just applied
something. So `_write_done` is left alone, and `_write_failed` — after the pop
it already does — asks whether any of the action's writes are still in flight.
Where some are, it decides nothing. Where none are, it drops the entry if
nothing was applied.

No record of "a refusal happened" is needed, and that is worth stating because
it is the first thing one reaches for. The rule is *keep the entry if anything
landed*, which does not mention refusals:

| the action | at the first refusal | at the last settle |
| --- | --- | --- |
| one of four refused | still three in flight, decide nothing | applied is 3, keep |
| all four refused | still three in flight, decide nothing | applied is 0, drop |
| a single write refused | nothing left in flight | applied is 0, drop — as today |

The writes abandoned behind a refusal are what makes the last row work: they
are removed from `_pending` by the same pop, so they cannot leave an action
waiting forever on writes that will never be sent.

### The count is derived, not kept

Whether an action still has writes outstanding is counted from `_pending`,
which is where they live.

The board's own argument for keeping a number is on the record — *"a number the
board owns is a number a suite can drive"* — and so is the warning that goes
with it: *"every path on which an operation ends must bring this down — there
are six, and one missed would leave the board saying wait for the rest of the
session."* That warning is the reason not to keep one here. A derived count has
no path to miss, and the board already derives the same kind of number for its
status line.

### Rejected: decide when the undo key is pressed

Delete `forget()` and have the undo key skip entries with nothing applied. It
is smaller and it moves the decision later, which sounds like the same fix.

Against it: the answer is still not knowable if writes are in flight, so it
does not actually fix the race — it relocates it to whenever the key is
pressed. The stack is unbounded, so entries for wholly-refused actions would
accumulate. And the key would have to skip past them silently, which changes
what it reports having reversed — a person pressing undo is told what happened,
and that is most of what they came for.

### Rejected: ordering an action's writes

Send an action's writes one after another so a refusal is always last, or
always first. It would make the outcome deterministic and it would make every
multi-write action as slow as the sum of its writes, for a property that costs
nothing to get right the other way.

## Risks / Trade-offs

- **A brief window where an entry is on the stack undecided** — between the
  first refusal and the last settle, an entry with nothing applied is
  reachable. Pressing undo then would put back the values the action recorded,
  which for a task whose write never landed are the values it still has: a
  write that changes nothing. Accepted, and named rather than left to be
  found. Closing it would mean the undo key consulting the queues, which is
  more machinery than the window is worth.
- **The fix is invisible except under a refusal** — nothing about a successful
  action changes, so a suite is the only place this can be seen. That is what
  the two forced orderings are for, and they are the check that fails before
  and passes after.
- **The probe is removed** — it was the instrument that found this, and its own
  docstring says it is not a suite because there was no right answer to
  assert. There is one now, so the cases move into the suite beside the check
  they explain rather than being kept in a file nothing runs.
- **Two archived changes name the probe as their instrument** — they describe
  what was true when they were written, and this change's own record says
  where the file went. That is the ordinary lifecycle of an instrument, and
  the archived artifacts are history: they are not edited to keep a path
  alive.
- **`t_undo1`'s known-failure entry is removed** — it describes this race, and
  `FLAKY` is documentation only: the runner never reads it, which is why that
  suite reported as a plain failure rather than as known. Leaving the entry
  would leave the list describing something fixed.
