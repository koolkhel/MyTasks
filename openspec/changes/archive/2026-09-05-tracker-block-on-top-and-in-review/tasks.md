## 1. Several states instead of one

- [x] 1.1 Make the configured state a configured list, read from the environment, keeping the existing default when none is set; verify a check that a comma-separated setting reads back as a list in the order written, that whitespace around each entry is ignored, and that an empty setting still yields the default
- [x] 1.2 Build the query from every configured state; verify a check that two states produce the tracker's comma-separated braced form, that one state produces what it produces today, and verify against the live tracker that the two-state query returns the issues both single-state queries return, compared by key
- [x] 1.3 Re-check the selection locally against the whole list rather than one state; verify a check on a crafted payload that an issue in any configured state is kept and one in an unconfigured state is dropped, alongside the assignee and project checks that already exist
- [x] 1.4 Order issues by the position of their state in the configured list, then by key; verify a check that issues in the second configured state all follow those in the first, that within a state they are ordered by key, and that the order is the same on two fetches of the same data
- [x] 1.5 Confirm a configured state matching nothing contributes nothing rather than failing; verify a check that adding a state no issue is in leaves the other states' issues unchanged
- [x] 1.6 Update the setting in `.env` to the two states in the order they should appear; verify by fetching against the live tracker and checking both states come back, with the first-configured state's issues leading

## 2. The block on top

- [x] 2.1 Join the block before the day's rows rather than after; verify a check on a day holding past-due, due-today and finished tasks that every tracker row precedes all of them
- [x] 2.2 Confirm the work filter still reaches the block now it joins on the other side; verify with `Pilot` that hiding work removes the tracker rows and that the hidden count includes them
- [x] 2.3 Confirm the block still takes no part in the day's ordering; verify with `Pilot` that ticking a task reorders the tasks while the tracker rows keep their sequence, still first
- [x] 2.4 Confirm the day's own tasks are otherwise untouched; verify with `Pilot` that their order and contents are identical to a board with no tracker configured
- [x] 2.5 Confirm the cursor starts on the first row as it always has, and that the refusal it produces reads clearly; verify with `Pilot` that a fresh board has the cursor on row one and that pressing the tick key there names the issue and says it lives in the tracker

## 3. Telling the rows apart

- [x] 3.1 Show each issue's state in the column that held the constant, dropping a leading "In " and truncating anything still too wide; verify a check that "In progress" renders as "progress", "In review" as "review", a short state unchanged, and an over-long one truncated rather than overflowing
- [x] 3.2 Confirm a tracker row is still distinguishable from a task without colour; verify a check that a tracker row's mark differs from every mark a task can carry, and that no colour is applied to a row for being from the tracker
- [x] 3.3 Confirm the key and summary are still shown; verify a check that a row carries both, and that the tracker's own project is still in the project column

## 4. What the board reports

- [x] 4.1 Stop naming the count by one state; verify with `Pilot` that with issues in two states the reported count describes them without claiming they are all in either state
- [x] 4.2 Confirm the count is still separate from the task count; verify with `Pilot` that the task count is the number of tasks the board manages and the issue count is reported beside it
- [x] 4.3 Confirm the other counts still appear beside it; verify with `Pilot` on a today holding past-due tasks, hidden work and tracker issues that all three counts are reported together

## 5. Verify against the live tracker and check nothing regressed

- [x] 5.1 Show the real issues in both states, in the configured order; verify against the live tracker that the board's rows are exactly the issues the two-state query returns, that those in the first configured state lead, and that each row names its own state
- [x] 5.2 Confirm opening still works for an issue in either state; verify against the live tracker that the address built for an issue in each state resolves
- [x] 5.3 Confirm the board is still unharmed with the tracker unreachable; verify that today's own tasks, order and counts match captures taken with the tracker working, and that the board says it could not be reached
- [x] 5.4 Confirm no regression: verify the previously passing suites still pass, and that today, the inbox and the someday view show the same tasks and counts as captures taken beforehand
