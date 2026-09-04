## 1. Reading and ordering by the stored order

- [x] 1.1 Add a way to read `scheduleOrder` off a task, treating a missing value as 0; verify a check that a task with the key absent and one with it set to 0 both read 0, and one set to 12345 reads 12345
- [x] 1.2 Give `sort_for_display` a parameter that makes the stored order its final key, with title breaking a tie in it, and leave the dateless views passing nothing so they keep ordering by title; verify a check that three synthetic all-day tasks with orders 3/1/2 come out 1,2,3 with the parameter on and alphabetically with it off
- [x] 1.3 Confirm the manual order cannot override a key above it; verify a check that two timed tasks at 08:00 and 18:00 carrying orders 900 and 100 still come out 08:00 first, and that a past-due task carrying a high order still leads a task due today
- [x] 1.4 Pass the parameter from the day path and not from the bucket path; verify against the live API that a day view's ordered ids change to the stored order while the inbox and someday views return exactly the ids and order captured beforehand

## 2. Writing a new position

- [x] 2.1 Add a client method that posts a list of operations to `/v2/batch`, each with a client-supplied uuid, returning the per-operation results; verify against the live API with two PATCHes on two throwaway tasks on a far-future day, checking both took effect in one call
- [x] 2.2 Establish whether the batch is atomic and whether it is idempotent; verify by replaying an identical batch and checking nothing applied twice, and by sending a batch whose second operation fails and checking whether the first still applied — record the answer, since the choice of move mechanism depends on it
- [x] 2.3 Add a pure helper that picks an integer strictly between two stored orders, answering that there is none when the two are adjacent, and using a fixed step when one side is unbounded; verify a check that it returns a value strictly between 100 and 300, nothing between 100 and 101, one step below an unbounded lower side, and one step above an unbounded upper side
- [x] 2.4 Respace a run of tasks into a range above every stored order in the day, preserving their sequence and spacing them by the step, as one write per task so each shows and rolls back on its own; verify against the live API on four throwaway tasks holding adjacent values that they end up distinct, evenly spaced, above the day's previous maximum, and in the same relative order
- [x] 2.5 Confirm a partly-applied respacing cannot collide; verify a check that the target range is disjoint from every stored order in the day, so that applying any subset of the writes leaves all orders distinct

## 3. Choosing the neighbour to move past

- [x] 3.1 Add a helper that answers which task the selected one may trade with in a given direction, by comparing every sort key above the manual order; verify a check that an all-day task offers no neighbour upward when a timed task is above it, that a past-due task offers none when the task above is due today, and that two equal all-day tasks do offer each other
- [x] 3.2 Handle tasks that already share a stored order, which existing data contains; verify a check on synthetic tasks that three tasks all carrying 0 can be moved into a definite sequence and that the resulting values are distinct
- [x] 3.3 Confirm no task outside the moved one is disturbed; verify a check over a synthetic day of eight tasks that an ordinary move changes exactly one stored order and leaves the other seven untouched

## 4. Moving a task from the board

- [x] 4.1 Add the move itself: work out the moved task's new stored order from its destination neighbours, renumbering that run first when there is no value available, and send it as one write against the moved task; verify a check over a synthetic day that a move changes exactly one stored order, that the resulting sequence is the intended one, and that every order in the day stays distinct
- [x] 4.2 Bind `K` to moving the selected task up and `J` to moving it down, and add both to the key bar and the help overlay; verify with `Pilot` that the keys are bound, that lowercase `j`/`k` still only move the cursor and change no stored order, and that the key bar shows both without clipping at a narrow width
- [x] 4.3 Make a move optimistic: reorder on screen before the batch is sent, with the selection staying on the moved task; verify with `Pilot` and a stubbed client that the rows have swapped within a frame while the write is still in flight, and that the moved task is still selected
- [x] 4.4 Report why a move at an edge cannot happen and change nothing; verify with `Pilot` that moving the top all-day task up under a timed task reports it, that moving the last task down reports it, and that no write is sent in either case
- [x] 4.5 Report that reordering applies to calendar days when the keys are pressed in the inbox or someday view, changing nothing; verify with `Pilot` in both buckets that a message is shown and no write is sent
- [x] 4.6 Roll a refused move back; verify with a stubbed client that fails the write that the rows return to their original sequence, that the failure is reported, and that no task's stored order changed

## 5. Where a new task lands

- [x] 5.1 Send a stored order past the largest among the day's tasks when creating one, taken from the day already loaded rather than a fresh request; verify against the live API on a far-future day with three existing tasks that the created task's stored order exceeds all three
- [x] 5.2 Confirm two tasks added in succession do not tie; verify against the live API that adding two to the same day yields two distinct stored orders in the order they were added, then delete both
- [x] 5.3 Confirm adding to an empty day works; verify against the live API on a day with no tasks that the created task carries the order the board chose rather than 0
- [x] 5.4 Leave the dateless views' creation unchanged; verify that a task added from the inbox is created without a stored order being sent, since that view does not order by it

## 6. Verify against the live API and check nothing regressed

- [x] 6.1 Exercise a full sequence end to end on a far-future day: create five throwaway tasks, move them into a chosen order with the keys selecting by task id before each press, reload the view, and verify the order persisted by re-fetching each task and comparing stored orders; delete all five afterwards
- [x] 6.2 Confirm the order is the one other clients see; verify by re-fetching the day through the client after a move and checking the ids come out in the moved sequence once sorted by stored order
- [x] 6.3 Confirm today's real view is unchanged apart from the ordering of tasks the other keys leave equal; verify that the set of ids, the past-due count, and the finished count all match captures taken beforehand, and that the timed tasks are still in ascending start time
- [x] 6.4 Confirm the inbox and someday views are untouched; verify their ids, order, and withheld counts match captures taken beforehand exactly
- [x] 6.5 Confirm the previous change's guarantees still hold: verify with `Pilot` that a burst of moves is neither dropped nor lost, and that a refresh arriving mid-move does not revert it
