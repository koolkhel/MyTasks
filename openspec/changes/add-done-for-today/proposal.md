## Why

The API has an endpoint that records work happening on a task today, and the board has never offered it as an action of its own. Instead the tick action quietly routes recurring tasks to it and everything else to plain completion, which conflates two different intentions under one key — and is broken besides: that endpoint refuses any task not dated today, so ticking a recurring task on its own day fails outright.

What is wanted is a separate action meaning "I did some work on this today, put it up again tomorrow", kept clearly apart from "this is finished".

## What Changes

- Add a **done for today** action on the `.` key, mirroring the app's `cmd+.`: record today's work, then schedule the task for tomorrow. The record covers tasks dated today and past-due ones alike; only undated tasks cannot carry it.
- Record first, reschedule second. The endpoint only accepts a task dated today, so moving the date first would make the record impossible.
- **Tick becomes plain completion for every task**, recurring or not. The two actions stop sharing a key, which is the whole point, and it removes the failure described below.
- The action is available in every view. In the inbox or someday it dates the task to tomorrow and clears the deferred flag, recording nothing, because the API refuses undated tasks.

### What the API actually does, measured rather than assumed

- On a task dated today, the endpoint sets `complete` from 0 to 1 and `completeLast` to the end of today. It leaves `start` and `checked` untouched — so **it does not reschedule anything**. For recurring series the next occurrence comes from the recurrence generator, not from this call. That is why this change has to move the date itself.
- It accepts any task whose start is not in the future, so **past-due tasks are recorded too** — which is most of today's view and exactly where the action is wanted. It returns **422 Unprocessable Entity** for an undated task and for one dated further ahead than tomorrow. The boundary sits a day later than local midnight because the server compares UTC dates, and a task dated tomorrow in a UTC+3 timezone is stored as today at 21:00Z; the board does not rely on that slack.
- `recurrence` is not settable through create or update, so a recurring task cannot be synthesised. The recurring path therefore cannot be exercised without writing to real recurring tasks, and this change does not attempt to.
- The failure in today's tick path is latent rather than active: 18 open tasks carry a recurrence object and are dated other days, but none is in today's view, so nothing is failing right now.

## Capabilities

### Modified Capabilities

- `task-board`: gains the done-for-today action. The requirement listing the actions changes to include it, and its rule about ticking a recurring task changes, because tick stops routing to the today-only endpoint.

## Impact

- `singularity.py` — `set_done` loses its recurrence branch, and a new method composes the record-then-reschedule pair so the order and the dated-or-deferred invariant stay in one place.
- `main.py` — one binding, one action, the help overlay, and the footer.
- No new dependency, and no change to `run.sh`, `requirements.txt`, or `.env`.
- Ordering note: `rename-never-to-someday` is applied but not yet archived, so the main spec still says "never" while the code says "someday". Both changes modify the requirement listing the actions. This change's block is written with the someday wording and preserves the same scenario names, so the two converge to the same text whichever archives first — but they should not be archived in parallel.
- The repo has no automated test suite; verification is through the Textual pilot harness and synthetic tasks, with every keypress confined to a day holding no real tasks.
