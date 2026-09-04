## Why

Every write blocks the board for about a second and a half before anything on
screen changes, and unticking a task blocks it for four. The delay is not
mostly the write: it is the full refetch the board performs afterwards, plus
the fact that today's view costs three sequential requests rather than one.
Measured against the live API, ticking a task today is 713 ms of write
followed by 790 ms of reload, and unticking is 3246 ms followed by the same
790 ms. The board already knows what the outcome will be in every one of
these cases, so it has no reason to wait to say so.

A second, quieter problem falls out of the same code path: while a write is in
flight the board silently discards further keypresses, so a person ticking
several tasks in a row loses all but the first with no indication that
anything was dropped.

## What Changes

- The board applies a write's expected outcome to its own model and repaints
  immediately, then sends the request in the background. Perceived latency for
  every write becomes zero.
- A write that fails is undone on screen and reported, so the board never
  keeps a change the server rejected.
- A successful write no longer triggers a full refetch of the view. The
  board reconciles from what it already knows.
- The cursor follows the selected **task** across the reordering an optimistic
  write causes, rather than staying on a row index. Ticking a task moves it to
  the bottom of the list, because completion is the first ordering key, so
  without this the cursor lands on an unrelated task — the same hazard that
  makes a burst of ticks dangerous today.
- Keypresses during an in-flight write are accepted rather than dropped.
  Writes to different tasks proceed concurrently; writes to the same task are
  ordered.
- Today's three queries — the day itself, tasks with a passed start, tasks
  with a passed deadline — are issued concurrently instead of one after
  another, taking today's read from about 790 ms to about 280 ms. The
  combined result is unchanged, and a failure in any of the three still fails
  the whole load rather than showing a partial day.
- A view refresh that arrives while a write is still in flight does not
  overwrite the rows that write touched, so a background reload cannot make a
  change appear to revert.

Not in scope: any persistent local store, offline operation, or a sync
engine. Those address different problems — chiefly working without a network —
and none of them is needed to remove the lag. This change adds no new
persistent state whatsoever.

## Capabilities

### New Capabilities

None. This changes how the existing board behaves, not what it is.

### Modified Capabilities

- `task-board`: how a write reaches the screen changes from "wait for the
  server, then refetch everything" to "show the outcome, then confirm it",
  which changes observable behaviour on success, on failure, and during a
  burst of keypresses. The cursor's behaviour across a write is newly
  specified. Today's gathering of past-due tasks gains a requirement that
  concurrent queries produce the same view as sequential ones, and that a
  partial failure is not shown as a partial day.

## Impact

- `main.py`: `submit_write` and its `_busy` guard, which is replaced by
  per-task in-flight tracking; every `action_*` that writes (`toggle`,
  `done_for_today`, `cancel_task`, `schedule`, `add`, `rename`, `delete`);
  `show_tasks`, which must reconcile rather than replace wholesale; the
  cursor restore in `show_tasks`, which currently uses `min(previous, ...)` on
  a row index.
- `singularity.py`: `_past_due_tasks` issues its two queries concurrently, and
  `tasks_for_day` overlaps them with the day query. `sort_for_display` and
  `past_due_since` are reused unchanged as the local derivations an optimistic
  update must re-run — they are already pure functions over tasks, which is
  what makes this change small.
- No new dependencies. Concurrency uses the standard library, and Textual's
  worker machinery is already in use for both reads and writes.
- The API is untouched: the same endpoints are called the same number of
  times, minus the reload that each write currently provokes.
