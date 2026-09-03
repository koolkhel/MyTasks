## Context

See proposal.md — Why. The constraints that shape the approach:

`TaskApp` currently holds `self.day: date` as its entire notion of position, and `load` calls `client.tasks_for_day(self.day)`. Every other piece of chrome — the header, `action_add`'s start date, the day-movement actions — reads that one field. Adding two views that are not dates means that field has to become something wider, and it is the only place the widening is needed.

Facts established against the live API while planning, not assumed:

- Tasks can be filtered by `start.isSet` and by `deferred.eq`, so both buckets are single queries rather than client-side scans.
- In the real store, `deferred=true` **always** coincides with `start=None` (2 of 2 open, 0 dated). The API models "someday" as undated + deferred; the board does not need a concept of its own.
- `PATCH /task/{id}` with `start: null` clears a date cleanly.
- The server does **not** clear `deferred` when a date is set. A probe produced `deferred=true` alongside a real `start` — a combination absent from all 525 open tasks. Whatever enforces the invariant has to be on this side.
- Bucket sizes: undated is 39 open but 2127 including archived; deferred is 2 open but 377 including archived.

## Goals / Non-Goals

**Goals:**

- One position value the whole app switches on, so no view can be half-selected.
- Date assignment reachable from any view, since triage happens in the inbox but correction happens on a day.
- The dated-or-deferred invariant enforced in one place rather than at each call site.

**Non-Goals:**

- Project assignment. SingularityApp's own Inbox is the no-project bucket (253 tasks); this change is about dates only, and conflating the two was considered and rejected in the proposal.
- Setting a time of day. Dates assigned here are all-day; the existing clients handle times.
- A calendar widget. A typed `YYYY-MM-DD` is enough for the "a given day" case.
- Showing finished tasks in the dateless views, or changing anything about the day view's existing content.

## Decisions

**A view is one value, not a set of flags.** Replace `self.day: date` with a single position that is either a `date` or one of two named sentinels for inbox and never. Alternatives considered: separate `self.day` plus `self.showing_inbox`/`self.showing_never` booleans — rejected because it admits contradictory combinations and every reader has to check them in the right order; and one Textual screen per view — rejected because it duplicates the table, footer, and load plumbing for what is a change of query. A single value keeps one `load` path and makes the three cases exhaustively matchable.

**The bucket queries belong in the client, not the TUI.** `singularity.py` already hides the API's quirks — the ISO-Z-only date filters, the `includeArchived` requirement for finished tasks — behind `tasks_for_day`. The two new buckets get the same treatment, so the TUI never assembles filter dictionaries. This also keeps the `--cli` path able to list them.

**One call sets date and deferred together.** A single client method that takes the intended schedule — a day, or never, or nothing — and issues one `PATCH` carrying both `start` and `deferred`. Rationale: the probe above shows the server will not maintain the invariant, and two separate calls would both double the round trips and leave a task dated-and-deferred if the second failed. Having exactly one entry point means the invariant cannot be violated by a new caller later.

**Finished tasks are excluded from the dateless views.** This is the one place the new views deliberately diverge from the day view, and the numbers force it: an inbox that included finished tasks would show 2127 rows instead of 37, and a never view 377 instead of 2. The day view keeps showing what was completed that day, because that is a useful record of the day.

**Reuse `sort_for_display` rather than writing a second sort.** Its key is (finished, not pinned, not timed, start time, title). In a dateless view the tasks are all unfinished and all untimed, so the first four components are constant and the key degrades exactly to pinned-then-title — the ordering the spec asks for. Adding a parallel sort function would be two things to keep in step for no gain.

**The picker is a modal screen, matching `TaskInput` and `Confirm`.** It presents the five choices and returns which was chosen; the "a given day" choice chains into a text prompt for the date. An inline one-key-per-option scheme without a visible menu was rejected — the whole point of the feature is triage, and the options need to be visible while sorting.

**Day movement is inert in a dateless view.** Asking for the next day from the inbox has no sensible answer: any day it landed on would be arbitrary. `t` remains the way back to the day view. Making `h`/`l` jump to today was considered and rejected as surprising in the opposite direction — a movement key that changes view.

**A task that is somehow both dated and deferred shows on its day.** No such task exists in the store today, but another client could create one. Both dateless queries filter on `start.isSet=false`, so such a task falls out of them naturally and appears under its date. No special handling is needed; this decision is recorded so the behavior is not read as a bug later.

## Risks / Trade-offs

- **Clearing a date depends on `start: null`, which the docs do not describe.** → Verified against the live API during planning; if a future API version rejects it, the failure is visible and localised to the one client method that sets schedules.
- **"A given day" costs three keystrokes plus typing.** → Accepted: today, tomorrow, never and clear are all two keystrokes, and those are the common triage choices.
- **Neither dateless view paginates.** → The client caps a listing at 1000 and the inbox holds 37. If an inbox ever grew past the cap the view would silently truncate; worth revisiting only if that becomes plausible.
- **The inbox is defined by absence of a date, so it includes the 8 undated tasks that already have a project.** → Deliberate, per the proposal: the alternative leaves those 8 reachable from no view at all.
