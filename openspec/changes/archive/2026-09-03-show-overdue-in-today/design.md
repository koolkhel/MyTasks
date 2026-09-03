## Context

See proposal.md — Why. The constraints that shape the approach:

The day view is one query today: `tasks_for_day` asks for tasks whose start falls inside the local day and hands back a `Listing`. Rows are rendered by `row_for`, which puts `start_label` in the when-column, and ordering comes from `sort_for_display`, whose key is (finished, not pinned, not timed, start time, title).

Two facts established against the live API rather than assumed:

- Query filters combine with **AND**, not OR. Asking for `start.lt=<today>` returns 17 tasks and `deadline.lt=<now>` returns 1, but sending both in one request returns 1 — the intersection. There is no OR operator in the filter vocabulary, so "past due by start *or* by deadline" cannot be one request.
- Completion and archiving are **not** the same thing. A task can be `checked` while its `journalDate` is still empty, and `includeArchived=false` returns it — 2 of the 17 tasks whose start is before today are in exactly that state. So the past-due query cannot lean on the archive flag to mean unfinished; it has to check completion itself.

## Goals / Non-Goals

**Goals:**

- One reference instant per load, so the rows, the ordering, and the counts all agree about when "now" is.
- The past-due determination testable without the API, from a task and an instant.
- The `--cli` listing picks the behaviour up without its own copy of the rule.

**Non-Goals:**

- Changing any other day. Only today gathers past-due tasks; the spec pins this with a scenario.
- Any write. Nothing here reschedules, completes, or nags — a past-due task is shown, not touched. Re-dating it is already possible with the existing date assignment.
- A lookback window, a cap, or paging over the past-due set. The proposal deliberately shows all of it.
- Reviving the deadline field as a first-class concept. It is read here and nowhere else.

## Decisions

**Two queries and a client-side union.** Forced by the AND-only filters above. The day query keeps its current shape; a second query fetches past-due tasks; the results are merged and de-duplicated by task id. The alternative — fetching a broad range and filtering locally — was rejected because "every task before today" has no bound and would mean pulling the whole store.

**One reference instant, captured once per load and carried on the listing.** "Now" is needed three times: to decide which day is today, to compare against deadlines, and to compute how overdue each row is. Deriving it separately at each site invites rows that disagree with the header, and a day that rolls over mid-load. Capturing it once and passing it down makes those disagreements impossible rather than unlikely.

**Past-due-ness is a function of a task and an instant, not a flag set on the task.** It also carries the completion check, which the query cannot express — see the archiving note above. A method that answers "since when has this been past due", returning the earliest passed trigger or nothing, keeps the rule pure and lets it be verified against synthetic tasks with a fixed instant — no API, no clock. Mutating a field on the returned tasks was considered and rejected: the same task would carry a stale answer if it were ever reused across loads.

**The rule lives in the client, keyed on whether the requested day is today.** That is where the timezone and the existing day-window quirks already live, and it means the text listing inherits the behaviour rather than reimplementing it. The board never assembles the past-due query itself.

**Ordering extends the existing key rather than pre-grouping the rows.** A past-due component slots in behind "finished" and ahead of "pinned", with the trigger instant ordering the past-due group among itself. Concatenating two separately sorted lists was rejected: finished tasks must still sink below everything, and one key keeps that single rule in one place.

**The when-column shows a compact age, and the column is 8 cells wide.** "3d ago" and "365d ago" both fit. A task more than 999 days late would not, so anything that old is shown as a saturated value instead of overflowing the column. This matters only in principle today — the oldest past-due task is within 30 days.

## Risks / Trade-offs

- **Today's view costs a second request.** → Accepted; it is one extra call on a view that is already loaded in the background, and only for today.
- **The past-due set is unbounded by design, while the client caps a listing at 1000 rows.** → A store with more than 1000 past-due tasks would silently truncate. Recorded rather than solved: today the figure is 17, and a bound would contradict what the proposal asks for.
- **A task dated in the future can appear in today because its deadline passed.** → Intended, and specified. Its detail and focus views still show the real start and deadline, so the row's age never hides where the task actually sits.
- **The colour must survive both terminal themes.** → Use the palette's existing semantic colour rather than a literal, as the error status line already does.
