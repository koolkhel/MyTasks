## 1. Today's reads run concurrently

- [x] 1.1 Change `_past_due_tasks` to issue its two queries on a `ThreadPoolExecutor` and read both futures' results before combining, keeping the existing union-by-id and `past_due_since` filter unchanged; verify `tasks_for_day()` returns the same task ids as the current implementation for today, compared as sets against a capture taken before the change
- [x] 1.2 Overlap the day query with the past-due pair in `tasks_for_day` so all three run together; verify by timing `tasks_for_day()` over five runs and confirming the median drops from roughly 790 ms to under 450 ms
- [x] 1.3 Confirm a failure in any one query still fails the whole load: verify by pointing one of the three at an invalid filter in a throwaway script and checking `SingularityError` propagates out of `tasks_for_day` rather than a partial `Listing` being returned
- [x] 1.4 Confirm order-independence: verify by running `tasks_for_day()` ten times and asserting the ordered id list is identical every time

## 2. The optimistic model

- [x] 2.1 Add a pending-write record holding task id, the raw keys the write expects to change, and their previous values; verify with a unit-style check that applying a record to a fetched task yields the expected `Task` accessors and that dropping it restores the originals
- [x] 2.2 Add a per-task pending queue (`dict[task_id, deque]`) plus a helper answering whether a given task has a write in flight; verify a check that two ids queue independently and that one id's operations retain insertion order
- [x] 2.3 Build the view the board renders as fetched-tasks-with-patches-applied, running `sort_for_display` and the past-due count over the patched tasks; verify a check that a patched task marked done sorts to the finished group and that the reported counts agree with the rows
- [x] 2.4 Make reconciliation drop patches whose task is absent from the fetched base, so a patch never keeps a row alive; verify a check that a patch for an id missing from the base contributes no row

## 3. The cursor follows the task

- [x] 3.1 Replace the `min(previous, len(tasks) - 1)` row-index restore in `show_tasks` with selection by remembered task id, falling back to the nearest surviving position when that task is gone; verify with `run_test`/`Pilot` that ticking a task that is not last leaves the same task id selected
- [x] 3.2 Handle the emptied view: verify with `Pilot` on a far-future day holding one throwaway task that removing it leaves nothing selected and the board reporting the view as empty

## 4. Writes apply before they are sent

- [x] 4.1 Replace `submit_write`'s `_busy` early-return with enqueueing onto the task's pending queue, and drain each queue in a worker; verify with `Pilot` that three ticks pressed faster than the API answers all reach the API, by counting requests in a stubbed client
- [x] 4.2 Make `action_toggle` apply its patch and repaint before sending; verify with `Pilot` that the row reads as finished and the done count has risen within one frame, before the stubbed write resolves
- [x] 4.3 Stop calling `self.load()` after a successful write, reconciling from the write's own response instead; verify with a stubbed client that a successful tick issues no `GET /task`
- [x] 4.4 Give `action_rename`, `action_cancel_task` and `action_add` their patches; verify with `Pilot` that each is visible before the stubbed write resolves, and that a rename then a cancel on one task reach the API in that order
- [x] 4.5 Ask each view's own membership rule whether a patched task still belongs, and use that for `action_schedule`, `action_done_for_today` and `action_delete`; verify with `Pilot` that rescheduling to another day removes the row, that rescheduling today's task to today keeps it, and that a past-due task rescheduled into the past stays in today's view
- [x] 4.6 Confirm `done_for_today`'s accepted refusal still undoes nothing: verify with a stubbed client that returns 422 from the record call that the task is still shown as scheduled for tomorrow and no failure is reported

## 5. Refused writes are undone

- [x] 5.1 On a write's failure, drop its patch, repaint and report the error; verify with a stubbed client that raises `SingularityError` that the row returns to its pre-write appearance and the status line shows the failure
- [x] 5.2 Confirm one failure among several leaves the others standing; verify with a stubbed client that fails only the second of three concurrent ticks and check the other two rows remain ticked

## 6. A refresh does not revert a write in flight

- [x] 6.1 Make a fetch replace the base tasks while leaving pending patches applied on top; verify with `Pilot` that ticking a task and pressing `r` before the stubbed write resolves still shows the task ticked
- [x] 6.2 Confirm a fetch with nothing pending replaces the view wholesale as before; verify with `Pilot` that `r` with no write in flight shows exactly what the stubbed fetch returned

## 7. Verify against the live API

- [x] 7.1 Exercise every write end to end against the real API on a far-future day, creating throwaway tasks and selecting by task id before each keypress, then deleting them; verify each action's effect by re-fetching the day and comparing task fields, never by relying on the create response
- [x] 7.2 Measure the result on today's real view: verify ticking a task repaints within one frame and that the previously measured ~1.5 s tick and ~4 s untick no longer block the board
- [x] 7.3 Confirm no requirement in the task-board spec regressed: verify the inbox, someday and day views still show the same tasks and counts as before the change, compared against captures taken beforehand
