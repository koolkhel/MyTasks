## Context

See proposal.md — Why, which records what the endpoint was measured to do. The constraints that shape the approach:

`set_done` currently branches on `task.recurring` and sends those tasks to the today-only endpoint. `set_schedule` already exists and is the single place that sends `start` and `deferred` together, which is what makes a task dated-and-deferred unreachable. The board's date picker already computes tomorrow from the client's timezone.

The two facts that force the shape of this change: the endpoint records progress but never moves a date, and it refuses a task whose start is in the future as well as an undated one. Past-due tasks it does accept, so the 15 past-due rows in today's view are recorded like any other — but an inbox or someday task never can be.

## Goals / Non-Goals

**Goals:**

- One action that means "worked on it, see it tomorrow", reachable by its own key and never by the tick key.
- The record attempted whenever it can succeed, and its refusal treated as an outcome rather than a failure.
- Rescheduling routed through the one method that already enforces the dated-or-deferred invariant.

**Non-Goals:**

- Reproducing what the recurrence generator does. A recurring series advances by itself; this action does not try to create the next occurrence of anything.
- Exercising the recurring path in tests. `recurrence` cannot be set through create or update, so a recurring task cannot be synthesised, and real recurring tasks are not test fixtures.
- Showing the recorded progress anywhere. The counter is written and left for the app to render; the board displays nothing new.
- Any confirmation prompt. The action is reversible by re-dating the task, unlike deletion.

## Decisions

**Record first, reschedule second.** Not a preference: the endpoint accepts a task only while it is dated today, so the order is the only one that can work. Writing it as a single method rather than two calls at the call site keeps that ordering from being reinvented incorrectly later.

**A 422 from the record is an expected outcome; anything else is a failure.** Undated tasks are always refused, and a task dated well ahead would be too, and neither must surface as an error — but a swallowed `catch everything` would also hide an expired token or a server fault, leaving a person believing work was recorded when nothing reached the store. So only the one status that means "this task is not eligible" is absorbed, from only that one call, and every other error propagates to the status line as usual.

**Reschedule through the existing schedule method rather than a bare date write.** It sends `start` and `deferred` together, so the inbox and someday cases clear the deferred flag without this action knowing that it has to, and the invariant keeps a single enforcement point. A direct `PATCH start=tomorrow` was considered and rejected precisely because it would leave a someday task both dated and deferred — the state the spec forbids and the server does not police.

**Tick loses its recurrence branch entirely.** Keeping the branch but guarding it with "only when dated today" was considered. It would fix the 422, but it would leave one key meaning two different things depending on the task in front of you, which is the conflation this change exists to remove. Plain completion for everything is both simpler and what was asked for.

**Tomorrow is derived from the client's timezone, once per action.** The same reasoning as the past-due reference instant: a date computed twice can disagree with itself across midnight.

## Risks / Trade-offs

- **Ticking a recurring task now completes it rather than advancing one occurrence.** → Deliberate, and the reason the new action exists; recorded here because it is a real behaviour change for recurring tasks rather than a pure addition.
- **Two writes per action, and the second can fail after the first succeeded.** → The task then keeps its record but stays on today, and the status line says so. Retrying is safe in the sense that the reschedule is idempotent, but the record is not — `complete` increments each time — so a person retrying a partly-failed action may count a day twice. Accepted as the lesser evil against not recording at all.
- **The progress counter is bounded at 999.** → At one increment a day that is years away, and nothing in the board reads the value; noted so it is not a surprise if the API starts rejecting increments.
- **The recurring path ships unverified.** → Unavoidable while `recurrence` is unsettable. The endpoint's behaviour is measured on non-recurring tasks and the recurring case differs only in what the generator does afterwards, which is outside this board.
