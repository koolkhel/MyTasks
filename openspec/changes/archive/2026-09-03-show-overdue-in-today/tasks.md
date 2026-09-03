## 1. Decide what is past due

- [x] 1.1 Add a way for a task to answer, given a reference instant, since when it has been past due — the earliest of a passed start and a passed deadline, nothing when neither has passed, and never for a deferred task; verify against synthetic tasks and a fixed instant covering: start passed only, deadline passed only, both passed (earlier one wins), neither passed, a deferred task with a passed deadline, and a finished task.
- [x] 1.2 Fetch past-due tasks with their own query and union them into the day result, de-duplicated by task id, and only when the requested day is today; verify the union size equals the API's own totals for the two filters combined without double-counting (17 at time of writing, with the one task matching both rules appearing exactly once), and that requesting any other day returns only that day's own tasks.
- [x] 1.3 Carry the reference instant and the past-due count on the listing; verify past-due plus due-today equals the number of rows, that a day other than today reports zero past due, and that both dateless buckets report zero.

## 2. Present them distinctly

- [x] 2.1 Extend the display ordering with a past-due component and order the past-due group by how overdue each task is; verify with synthetic tasks that past-due rows lead every task due today, that the most overdue is first, that finished tasks still sink to the bottom, and that a non-today day's ordering is unchanged.
- [x] 2.2 Render a past-due row with its age in the when-column instead of a time and its title in a theme-aware colour; verify a past-due row reads as an age while a today row still reads as a time, and **verify the colour stays legible when that row is the selected row** — the cursor background is `$accent`, which is the same value as `$warning` in the default theme, so a title in `$warning` could become invisible exactly when selected. Check the selected case from a rendered screenshot, not from the markup.
- [x] 2.3 Keep the age within the 8-cell when-column, saturating rather than overflowing for very old tasks; verify a synthetic task around 1200 days overdue neither widens the column nor truncates the neighbouring cells.
- [x] 2.4 Report both counts in the header when today has gathered past-due tasks, and report nothing extra when it has not; verify both cases, and that the inbox and never headers are unchanged.

## 3. Verify end to end

- [x] 3.1 Against the live store, read-only: today's view contains every unfinished task whose start is before today or whose deadline has passed, contains no finished or deferred task, and lists the both-rules task once; a past day and a future day each contain only their own tasks; the inbox and never views are unchanged. Do not modify any of these tasks.
- [x] 3.2 Confirm the text listing follows: `./run.sh --cli` for today shows the past-due tail, and `./run.sh --cli --date <another day>` does not.
- [x] 3.3 Confirm this change writes nothing: with a request spy, load today, switch between all three views, and verify no POST, PATCH, or DELETE was sent. Then regression-check the other keys — enter opens the focus card without ticking, space ticks and unticks, backspace asks before deleting — on a far-future day holding no real tasks, selecting by task id before each press.
