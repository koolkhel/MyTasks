## Why

17 open tasks are scheduled for days that have already passed. The board shows exactly one day at a time, so those tasks are invisible unless you walk backwards through the calendar looking for them — and nothing prompts you to. A day you did not finish silently disappears. Today's view is the one place a missed task will actually be seen.

## What Changes

- Today's view SHALL also list past-due tasks: unfinished tasks whose start is before today, or whose deadline has passed.
- Past-due tasks appear **above** today's own tasks, most overdue first, so what was missed leads what was planned.
- They are visually distinct: the when-column shows how overdue the task is instead of a time of day, and the title is rendered in a warning colour.
- The view reports both counts, so the header distinguishes what is due today from what is late.
- Only today does this. Moving to any other calendar day, past or future, shows that day alone, and neither dateless view is affected.
- Deferred tasks are excluded: the never view exists to set something aside, and dragging it back into today would defeat that.
- Deliberately unbounded: every past-due task is shown, not a recent window. Today all 17 fall within the last 30 days, so the tail is short in practice.

## Capabilities

### Modified Capabilities

- `task-board`: today's view gains the past-due tasks, which changes what the day view contains, how its rows are ordered, how a past-due row is presented, and what the header reports. Three existing requirements change, and two are added: one for the past-due rule itself and one for how overdue a task is reported to be.

## Impact

- `singularity.py` — the day query needs a second query for past-due tasks when the day is today, a union that de-duplicates, and a way for a task to report whether and since when it is past due. The listing needs to carry the past-due count.
- `main.py` — the row presentation for the when-column and title colour, and the header.
- `run.sh` / `--cli` — the text listing shares the day query, so it picks the behaviour up for today as well.
- No new dependencies, no change to `requirements.txt` or `.env`, and no new write path: this change only reads.
- Counts at the time of writing, recorded as the state that motivated the change rather than as fixtures: 17 past-due by start, 14 of them within the last 7 days and all within 30. Exactly 2 tasks in the whole store carry a deadline and 1 of those has passed — and that one is **already** past-due by its start, so the deadline clause currently adds no tasks at all. It is specified because it will matter if deadlines start being used, not because it changes today's list.
- Every edge case the combined rule creates is currently empty in the store — no undated task with a passed deadline, no deferred one, none dated today or in the future — so each is specified from reasoning rather than from an observed example, and the spec says what to do if one appears.
