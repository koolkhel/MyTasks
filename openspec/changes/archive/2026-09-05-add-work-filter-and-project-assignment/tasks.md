## 1. Knowing which project is work

- [x] 1.1 Read the work project's identity from the environment the same way the token is read, loading `.env` first and treating an absent or blank value as "not configured" rather than an error; verify a check that a set value is returned, that an unset one and a blank one both read as not configured, and that an environment value overrides nothing it should not
- [x] 1.2 Confirm the identifier appears nowhere in the source; verify a check that no file tracked in the repository contains a project identifier or the work project's title, and that `.env` is still outside version control
- [x] 1.3 Add the line to `.env` for this account's work project; verify by reading it back through the loader and checking it matches the project the API reports

## 2. Setting a task's project

- [x] 2.1 Add a client method that puts a task in a project, using `/move` rather than an ordinary update because filing also assigns a group and a plain `projectId` update is refused for a task that already has one; verify against the live API on a throwaway task on a far-future day that its project is set, then deleted
- [x] 2.2 Record what the API refuses, so no later work assumes otherwise; verify against the live API that sending an empty value and sending nothing are both rejected, and that the rejection names the pattern the field requires
- [x] 2.3 Confirm moving between projects works; verify against the live API that a throwaway task already in one project can be put in another, and that its project afterwards is the second one

## 3. Hiding the work tasks

- [x] 3.1 Add the mode to the board, defaulting to off, and apply it to the rows a view has already selected rather than to what the view contains; verify a check that with the mode on the work tasks are absent from the rendered rows, that with it off they are present, and that `belongs` answers identically either way
- [x] 3.2 Derive the hidden count where the other counts are derived, from the same list at the same moment; verify a check that the count equals the number of work tasks the view holds, and that shown plus hidden equals what the view would show with the mode off
- [x] 3.3 Bind the key to toggling the mode, with its key bar and help entries; verify with `Pilot` that pressing it twice returns the view to exactly the rows it started with, in the same order
- [x] 3.4 Confirm the mode applies to every view and survives navigation; verify with `Pilot` that hiding work on one day leaves it hidden after moving to another day and to the someday view, without the key being pressed again
- [x] 3.5 Confirm nothing is written; verify with a stubbed client that toggling the mode any number of times sends no request and leaves every task's fields untouched
- [x] 3.6 Confirm the mode does not outlive the board; verify that a freshly constructed board has the mode off

## 4. Saying that work is hidden

- [x] 4.1 Report the mode and the hidden count where the view's other counts are reported; verify with `Pilot` that the board says work is hidden and how many rows that removed, and that the shown count is the number of rows on screen
- [x] 4.2 Report the mode even when it hides nothing; verify with `Pilot` on a view holding no work task that the board still says work is hidden
- [x] 4.3 Report nothing about it when the mode is off; verify with `Pilot` that no mention of hidden work appears
- [x] 4.4 Confirm it sits alongside the counts already reported rather than replacing them; verify with `Pilot` on today's view holding past-due tasks and work tasks that the past-due count and the hidden count are both present
- [x] 4.5 Report when no work project is configured, and when one is configured that matches no existing project; verify with `Pilot` in both cases that pressing the key says which of the two is wrong and hides nothing

## 5. Assigning a project

- [x] 5.1 Add a picker over the projects that exist, marking the one the task is in now or showing that it has none; verify with `Pilot` that it lists every project the API reports and marks the task's own
- [x] 5.2 Bind the key to opening the picker, with its key bar and help entries; verify with `Pilot` that the key opens it and that escape closes it without writing
- [x] 5.3 Confirm a first filing before writing, naming that it cannot be undone from the board; verify with `Pilot` that assigning a project to a task with none asks first, that agreeing files it, and that declining sends nothing and leaves the task unfiled
- [x] 5.4 Do not confirm a move between projects; verify with `Pilot` that assigning a project to a task that already has one writes without asking
- [x] 5.5 Make filing go through the existing optimistic write, so the row updates before the API answers and rolls back if refused; verify with a stubbed client that the change shows within a frame and that a refused write restores the task's previous project and reports the failure
- [x] 5.6 Confirm a task filed from the inbox leaves it at once; verify with `Pilot` in the inbox that the row disappears when the filing is confirmed, and that no separate rule was needed to make it happen
- [x] 5.7 Confirm a task filed under the work project while the mode is on disappears; verify with `Pilot` that the row leaves the view and the hidden count rises by one
- [x] 5.8 Confirm the board offers no way to un-file; verify a check that no action, key or picker entry removes a task from its project

## 6. Verify in the running app

- [x] 6.1 Exercise the whole flow end to end against the real API on a far-future day: create throwaway tasks, file one under the work project through the picker and its confirmation, toggle the mode and confirm the row disappears and returns, then delete them; select by task id before each keypress and confirm each effect by re-fetching
- [x] 6.2 Confirm today's real view is unaffected with the mode off; verify that its tasks, order and counts match captures taken beforehand
- [x] 6.3 Confirm no regression: verify the previously passing suites still pass, and that the inbox and someday views show the same tasks and counts as captures taken beforehand
