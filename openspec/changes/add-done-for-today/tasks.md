## 1. Separate the two completions in the client

- [x] 1.1 Remove the recurrence branch from the tick path so ticking always means plain completion; verify a synthetic task completes and uncompletes, and confirm by reading the source that the today-only endpoint is no longer reachable from the tick path.
- [x] 1.2 Add one client method that records the day's work and then schedules the task for tomorrow, in that order, rescheduling through the existing schedule method rather than a bare date write; verify against synthetic tasks on a far-future day that a task dated today ends up dated tomorrow with its progress counter incremented and its completion untouched, and that a past-due task and an undated task each end up dated tomorrow with no error surfaced.
- [x] 1.3 Absorb only the one refusal status from the record call, and only from that call; verify that a refusal for an ineligible task does not raise, and that a different failure from the same call still does — exercise the second case by pointing a client at a bad token or an unroutable base URL, so a real fault is proven to propagate rather than being assumed to.
- [x] 1.4 Confirm the invariant still holds through the new path: verify an undated deferred task marked done for today comes back dated tomorrow **and** not deferred, so no task is left both dated and deferred.

## 2. Wire it to its own key

- [x] 2.1 Bind the action to `.`, leaving the tick key alone; verify the binding registers, that pressing it acts on the selected task, and that pressing the tick key still completes rather than recording — both on a far-future day holding no real tasks, selecting by task id before each press.
- [x] 2.2 Make it work in all three views; verify from a day, from the inbox, and from the someday view that the selected task ends up dated tomorrow, using a synthetic task moved into each view rather than any real one.
- [x] 2.3 Do nothing when no task is selected; verify that pressing the key on a view with no tasks issues no request and leaves the board as it was.
- [x] 2.4 Add the action to the help overlay and confirm the footer; verify the overlay describes it as distinct from ticking, still opens and closes, mentions no priority action, and that the footer's other entries are unchanged.

## 3. Verify end to end

- [x] 3.1 Walk one synthetic task through the whole action on a far-future day holding no other tasks: dated today, marked done for today, and confirmed to be dated tomorrow, unfinished, with its progress recorded — then deleted. Assert on the captured request bodies that the record was attempted before the reschedule, and that no body carries a `priority` or pairs a `start` with `deferred`.
- [x] 3.2 Confirm nothing else regressed: the inbox still reports its shown and filed counts, today still gathers past-due tasks with their ages, the focus card still opens without ticking, the date picker still offers its five choices, and backspace still asks before deleting.
- [x] 3.3 Confirm no real task was touched: snapshot today's view, the inbox, and the someday view before and after the whole run and verify every field is identical, and that no stray synthetic task remains.
