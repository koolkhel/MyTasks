## 1. Narrow the inbox to unfiled tasks

- [x] 1.1 Add the no-project condition to the inbox's side of the dateless-bucket query, leaving the never view's query untouched; verify the inbox length equals the API's `pagination.total` for undated, undeferred, `projectId.isSet=false` (29 at time of writing), that no returned task carries a `projectId`, and that the never view still returns its filed task.
- [x] 1.2 Have the inbox listing also report how many unfinished undated undeferred tasks were left out for having a project, taking both numbers from one request rather than a second round trip — fetch undated and undeferred once, then split on project; verify shown plus left-out equals the unsplit total (29 + 6 = 35) and that the left-out count ignores finished tasks.

## 2. Report what the inbox leaves out

- [x] 2.1 Make the header show the left-out count alongside the task count while the inbox is shown; verify in the pilot that the header names the inbox, its task count, and the filed count, and that a day view's and the never view's headers are unchanged.
- [x] 2.2 Suppress the left-out figure when nothing is left out; verify the header renders with no filed count when the count is zero, exercising that case directly rather than waiting for the store to happen to be empty of filed undated tasks.

## 3. Keep adding from the inbox self-consistent

- [x] 3.1 Ensure a task added while the inbox is shown is created with no project, so it lands in the view it was added from; verify with a synthetic task that its `projectId` comes back empty and that it appears in the inbox listing, then delete it.

## 4. Verify end to end

- [x] 4.1 Confirm against the live store that every unfinished undated undeferred task with a project is absent from the inbox while the header accounts for all of them, and that the same tasks are still reachable by their project in the API; do not modify any of them.
- [x] 4.2 Confirm the other views are untouched: the never view still lists its undated deferred tasks including filed ones, and a calendar day still shows its tasks with finished ones retained and sunk to the end.
- [x] 4.3 Regression pass: `./.venv/bin/python -c "import main, singularity"` succeeds, `./run.sh --cli` runs, and the board still writes no `priority` and never pairs a `start` with `deferred=true`.
