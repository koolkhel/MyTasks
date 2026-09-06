## 1. The key an event stands on

- [x] 1.1 Give an event the ordering key of what it is — not finished, not tagged, not past due, not pinned, timed, at its own hour — built to the shape the tasks' own key has, and verify the two keys have the same length so a band added to one cannot be missed from the other
- [x] 1.2 Verify the key orders an event after a past-due task, before a finished one, and beside a task sharing its hour, by comparing keys alone and without drawing anything

## 2. Placing it

- [x] 2.1 Insert each timed event before the first task whose key is greater, replacing the comparison against the clock, and verify it is still an insertion: no task key is recomputed and no task moves relative to another
- [x] 2.2 Verify an all-day event still leads the day, unchanged
- [x] 2.3 Verify two events at the same minute keep their order between themselves

## 3. The cases that reproduce the defect

- [x] 3.1 Verify a past-due task naming no time is listed above a later event, and that the event is not lifted to the top of the day — the reported case
- [x] 3.2 Verify a finished task whose hour is earlier than an event's is listed below that event
- [x] 3.3 Verify an event falls beside the task sharing its hour on a day that also holds a past-due task and an earlier task
- [x] 3.4 Verify a tagged task and a pinned task each keep their place relative to an event, since both are bands above the ordinary one

## 4. The guarantee

- [x] 4.1 Verify on a day holding events together with past-due, tagged, pinned, timed, untimed and finished tasks that disregarding the events leaves those tasks in exactly the order they would have had alone
- [x] 4.2 Verify the same on a day whose tasks carry hand-set orders, so that the sequence a person set is not disturbed by an event falling into it

## 5. Verification

- [x] 5.1 Write a suite covering the key, the placement, all four defect cases and both guarantee cases against synthetic events and tasks, and verify it passes
- [x] 5.2 Verify against the real board, reading kinds and times only and never an event's title or description, that today's events fall among the tasks by hour rather than above the past-due block
- [x] 5.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand — the tasks' order in particular must be identical, since that is what this change promises not to touch
