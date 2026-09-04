## Context

See proposal.md — Why for the motivation and the measurements.

Four facts about the current code shape the approach:

- `Task` is a plain, non-frozen dataclass wrapping the raw API dict
  (`singularity.py:141`). Its every accessor reads through to `raw`, so
  changing one key changes everything derived from it.
- `sort_for_display` and `past_due_since` are pure functions over tasks
  (`singularity.py:755`). They are the only places ordering and lateness are
  decided, so re-deriving locally means calling the same code the server path
  calls, not a parallel reimplementation.
- Completion is the **first** ordering key — `task.done or task.cancelled`
  (`singularity.py:771`). Any optimistic tick reorders the view. This is not
  an edge case to handle later; it is the central consequence.
- `submit_write` (`main.py:551`) guards with a single `self._busy` boolean and
  returns early when set, so a second keypress is dropped. It then calls
  `self.load()` unconditionally on success.

The client holds one shared `requests.Session` (`singularity.py:393`). Its
headers are set once at construction and never mutated afterwards.

## Goals / Non-Goals

**Goals:**

- Keep every local derivation in `singularity.py`, called by both paths, so
  the optimistic view and the fetched view cannot drift apart.
- Make in-flight state per task, not global, so concurrency falls out of the
  data structure rather than being managed.
- Leave the API surface untouched.

**Non-Goals:**

- No persistence, no `modifiedSince` polling, no `/v2/batch`. The API offers
  all three and they are the right tools for offline work; none is needed to
  remove lag, and each would add state that outlives the process.
- No change to what the API is asked for. The same endpoints, the same
  filters, the same number of calls minus the reloads.
- No general-purpose undo. Rollback here is confined to one refused write.

## Decisions

### Optimistic state lives as a patch over the fetched task, not as a mutation of it

Each in-flight write records `(task id, dict of raw keys it expects to change,
the previous values)`. The board renders `fetched.raw | patch`, and derivations
run over the patched task.

Rejected: mutating `task.raw` in place. It is possible — the dataclass is not
frozen — and it is the shortest path, but it destroys the pre-write values that
rollback needs, and a fetch that lands mid-write would silently discard the
optimistic change. Keeping the patch separate is what makes both rollback and
"a refresh does not revert a write in flight" fall out for free: reconciliation
drops the patch, and a fetch replaces the base underneath it.

Rejected: a full local mirror of the task list. That is Tier 3 in disguise and
brings the conflict policy with it.

### Per-task ordering via one queue per task id

`dict[task_id, deque]` of pending operations, with a worker draining each
task's queue in order. Different task ids drain concurrently; a single task's
operations are strictly sequential. When a task's queue empties, its entry is
removed, which is also the signal that the task has no write in flight.

Rejected: a global lock (the current `_busy` behaviour, minus the dropping). It
would serialise a burst of ticks on different tasks for no reason — the case
the requirement about bursts exists to fix.

Rejected: firing every write immediately with no per-task ordering. Rename
followed by cancel could then reach the API reversed, and the spec forbids it.

### Derivations are re-run wholesale, not patched incrementally

After applying or dropping a patch, the board recomputes the whole view from
its task list: `sort_for_display`, the past-due count, the done count, the
status line. The list is a few dozen rows at most, so recomputing is cheaper to
write and to trust than working out how each field moves.

This is what makes the past-due requirement hold without new logic: the board
calls `past_due_since` with the same reference instant it was given, on the
patched task.

### Whether a task still belongs in the view is asked of the view, not of the write

Each view already knows its membership rule — the day's bounds, the inbox's
"undated, undeferred, unfiled", someday's `deferred`. Rescheduling and
done-for-today re-ask that rule of the patched task rather than hard-coding
"this action removes the row". A task rescheduled from today to today stays put,
and today's view keeps a rescheduled-into-the-past task because its past-due
rule still matches.

Rejected: an explicit "removes the task" flag per action. It gets the common
case right and the interesting cases wrong.

### The cursor is tracked by task id

`show_tasks` currently restores with `min(previous, len(tasks) - 1)` on a row
index. It becomes: remember the selected task's id, find it after reordering,
select it; if it is gone, select the row that now occupies the nearest
surviving position.

This is a latent hazard being fixed, not only a new feature: with reordering
now instant rather than arriving 1.5 seconds later, an index-based cursor would
make a fast burst of ticks act on tasks the person never selected.

### Today's three queries run on a thread pool sharing the one session

A `ThreadPoolExecutor(3)` in `tasks_for_day`, submitting the day query and the
two past-due queries together, then combining results exactly as now — union by
id, filter through `past_due_since`, sort. The union is already order-independent
(`_past_due_tasks` de-duplicates with `setdefault`), which is why the
"order does not matter" scenario needs no new logic to hold.

`requests.Session` is not documented as thread-safe. Measured here, three
concurrent GETs on the shared session completed in 399 ms against 790 ms
sequential, with the adapter's `pool_maxsize` at 10 — so connection reuse, not
contention, is the operative behaviour. The hazard with a shared session is
concurrent mutation of its state; this code sets headers once at construction
and never touches them again. Accepted with that reasoning recorded, and a
per-thread session is the fallback if it misbehaves.

Rejected: `asyncio` and an async HTTP client. It would fit Textual's event loop
more naturally than threads, but it means replacing `requests` throughout
`singularity.py` and rewriting the `--cli` path, for a saving of one round trip.

### Failure of any of today's queries fails the load

`ThreadPoolExecutor` surfaces an exception when its future's result is read, so
gathering results propagates the first failure and the existing error path in
`load` reports it unchanged. This preserves today's behaviour deliberately: a
day silently missing its past-due tail looks like a day with nothing overdue,
which is worse than an error.

### Ticking advances the selection; every other write does not

Following the ticked task is what the cursor decision implies, but completion
being the first ordering key means following it to the bottom of the list — so
repeated presses toggle one task instead of working down the day. Ticking
therefore moves the selection to the next unfinished task, chosen by identity
from the list on screen after the repaint. Every other write, unticking
included, leaves the selection on the task it changed.

The hazard the cursor decision exists to remove is still removed: the advance
picks a task, never a row number, so no keypress can act on something the
reordering moved under the cursor.

Rejected: following the ticked task everywhere. Consistent, and the second
press becomes an undo, but it makes the common case — clearing a day — need a
second key between every tick.

Rejected: holding the row index for ticks only. It works down a list by
accident and reintroduces exactly the hazard: the row under the cursor is a
different task, and a fast further press acts on it unseen.

### A refusal outranks the counts on the status line until superseded

The first implementation reported a failure and was then overwritten within
milliseconds by the next confirmation's repaint, because repainting rewrites
the status from the view's counts. A refused write is now held in one field
that repainting prefers over the counts, cleared when the person next acts or
when a fetch replaces the view. Without this the requirement to report a
refusal held only until another write happened to land.

### Repainting tolerates the widget tree being gone

Confirming a write can arrive while the app is shutting down, and repainting
then queries widgets that no longer exist. Both the repaint and the cursor
handler check first rather than assuming. The same window existed before —
`show_tasks` also moved the cursor — but a write confirming is far more
frequent than a fetch landing, so it went from theoretical to reachable.

## Risks / Trade-offs

- **A patch outlives the task it applies to** — a task deleted elsewhere, or
  gone after a fetch, leaves a patch keyed to an id no longer present →
  reconciliation drops patches whose task is absent from the base; a patch is
  never a reason for a row to exist.
- **The optimistic outcome is wrong** — the board guesses what the server will
  do, and for `done_for_today` that is a two-step operation whose first step is
  allowed to fail → the spec already fixes that case as an accepted refusal;
  for the rest, the write's own response replaces the patch, so a wrong guess
  is visible for one round trip rather than permanently.
- **A refused write's rollback surprises the person** — a row changes back
  under them, possibly seconds later → the failure is reported at the same
  moment, which is the whole reason the requirement pairs restoring with
  reporting.
- **Concurrent writes to one task from a queue that drains slowly** — a long
  queue means later keypresses are shown instantly but sent much later, so
  quitting the app could drop them → out of scope to solve properly without
  persistence; worth showing that writes are still in flight, and the status
  line is the place for it.
- **Shared session under concurrency** — see the decision above; measured to
  work, not formally guaranteed → per-thread sessions if it misbehaves.
- **Reordering-on-tick becomes noticeable** — the reorder was always there, but
  arriving after 1.5 s it read as a refresh; instant, it reads as the row
  jumping away → this is the honest behaviour of the existing ordering, and the
  cursor following the task is what keeps it from being disorienting.
