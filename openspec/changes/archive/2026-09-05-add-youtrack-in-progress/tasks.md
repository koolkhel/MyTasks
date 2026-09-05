## 1. Reading the tracker

- [x] 1.1 Add a module that reads the tracker: a query built from the configured assignee, projects and state, one request to the issues endpoint asking for the key, summary, project and custom fields, and a record per issue; verify against the live tracker that it returns the issues the same query returns through the API directly, compared by key
- [x] 1.2 Re-check the selection locally rather than trusting the query alone, as the digest does: drop any issue whose assignee, state or project is not the configured one; verify a check on a crafted payload containing an issue for another assignee, one in another state and one in another project that all three are dropped
- [x] 1.3 Read the configuration from the environment — tracker address, token, assignee, projects, state — treating a missing address, token or assignee as "no tracker configured" rather than an error; verify a check that a full configuration reads back, and that removing any one of those three reports the tracker as unconfigured rather than raising
- [x] 1.4 Give every request a timeout and turn a transport failure into a plain "could not reach the tracker" rather than an exception the caller must know about; verify against an unreachable address that the call reports failure within the timeout and raises nothing that escapes the module
- [x] 1.5 Confirm nothing identifying is in the source; verify a check that no tracked file contains the assignee login, any project code, the tracker's host, or a token
- [x] 1.6 Add the tracker settings to `.env`; verify by reading them back through the loader and fetching the issues the live tracker reports

## 2. Showing the block

- [x] 2.1 Build a row for an issue that carries its key and summary, its page address, and the work project's id; verify a check that the row shows the key and the summary, that its address is the tracker's base with the issue key, and that the board counts it as work
- [x] 2.2 Append the issues after the day's tasks have been selected, filtered and sorted, so they take no part in the ordering; verify a check on a day holding past-due, due-today and finished tasks that every issue is listed after all of them
- [x] 2.3 Confirm the block does not move when the day reorders; verify with `Pilot` that ticking a task reorders the tasks and leaves the tracker rows in the same sequence, still last
- [x] 2.4 Show the block on today alone; verify with `Pilot` that another day, the inbox and the someday view show no tracker row
- [x] 2.5 Apply the work filter to the appended rows as well as to the tasks; verify with `Pilot` that hiding work removes the tracker rows and that pressing the key again brings them back
- [x] 2.6 Include them in the hidden-work count; verify with `Pilot` that the count the board reports when hiding covers the tracker rows it removed
- [x] 2.7 Report how many issues are in progress, separately from the count of tasks; verify with `Pilot` that the task count is the number of tasks the board manages and the issue count is reported beside it

## 3. Read-only

- [x] 3.1 Refuse any write against a tracker row in the one place every write passes through, saying the issue is not editable here; verify a check that a write submitted for a tracker row sends nothing and reports that message
- [x] 3.2 Confirm every writing action refuses; verify with `Pilot` that with a tracker row selected each of ticking, done-for-today, cancelling, renaming, dating, filing, moving and deleting says so and sends nothing
- [x] 3.3 Confirm reordering says why rather than doing nothing; verify with `Pilot` that moving a tracker row up or down reports that the issue lives in the tracker and no order changes
- [x] 3.4 Confirm undo has nothing to reverse for an issue; verify with `Pilot` that pressing keys against a tracker row leaves the undo stack empty
- [x] 3.5 Confirm the day's own tasks stay editable while the block is shown; verify with `Pilot` that ticking, renaming and moving a real task all work with tracker rows present

## 4. Opening an issue

- [x] 4.1 Make the key that opens a link open the selected issue's page; verify with `Pilot` and a stubbed opener that it is handed the tracker's base address, `/issue/`, and the issue key
- [x] 4.2 Confirm opening changes nothing; verify with `Pilot` that no request to change the issue is made and the row is unchanged
- [x] 4.3 Confirm the live address resolves; verify against the live tracker that the address built for a real in-progress issue answers successfully

## 5. When the tracker cannot be reached

- [x] 5.1 Fetch on a worker of its own, not awaited by the day's load; verify with `Pilot` and a slow stub that the day's tasks appear before the tracker answers
- [x] 5.2 Keep a tracker failure inside the tracker: never report it as the day failing to load, and never let it stop the day's tasks appearing; verify with a stub that raises that today loads normally and that the message names the tracker rather than the day
- [x] 5.3 Say that the tracker could not be reached, distinguishably from reporting nothing in progress; verify with `Pilot` that the two cases produce different messages and that neither is silence
- [x] 5.4 Say nothing about the tracker when none is configured; verify with `Pilot` that an unconfigured board shows the day and reports no tracker failure
- [x] 5.5 Confirm recovery; verify with `Pilot` that a reload after a failure shows the issues and stops reporting the failure
- [x] 5.6 Confirm every task action still works while the tracker is down; verify with `Pilot` that ticking, renaming and undo behave exactly as they do without a tracker

## 6. Verify against the live tracker and the live API

- [x] 6.1 Show the real in-progress issues in today's view; verify by comparing the rows the board shows against the issues the tracker reports for the configured query, by key
- [x] 6.2 Confirm the board is unharmed with the tracker unreachable; verify by pointing the configuration at an unreachable address and checking today's own tasks, counts and ordering match captures taken with the tracker working
- [x] 6.3 Confirm no regression: verify the previously passing suites still pass, and that today, the inbox and the someday view show the same tasks and counts as captures taken beforehand
