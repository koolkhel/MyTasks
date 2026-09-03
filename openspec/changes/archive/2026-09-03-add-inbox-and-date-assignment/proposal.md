## Why

37 open tasks currently sit with no date at all, and the board offers no way to see them: it only ever shows one calendar day, so an undated task is invisible and undatable from here. There is no triage step — the place where a captured task gets turned into a task with a day. A further 2 tasks are marked deferred, which is the API's "someday" flag, and those are equally unreachable.

## What Changes

- Add an **inbox view** listing tasks with no date that are not deferred, reachable with `i`.
- Add a **never view** listing tasks with no date that are deferred, reachable with `n`. This is the "special day" the inbox sends things to.
- Add **date assignment** on the selected task, opened with `d`, offering: today, tomorrow, a picked `YYYY-MM-DD`, never, and clear-the-date. Available in every view, so a task can be dated straight from the inbox or re-dated from a day.
- Assigning any real date SHALL clear the deferred flag, and choosing never SHALL clear the date. The two are mutually exclusive, and the API does not enforce this itself.
- Generalise the board's notion of "what am I looking at" from a calendar date to one of three views — a day, the inbox, or never — so the header, the add action, and the load path all follow the selected view.
- The inbox and never views exclude finished tasks, unlike the day view, which keeps showing what was completed on that day.

## Capabilities

### Modified Capabilities

- `task-board`: gains the inbox and never views alongside the existing day view, gains date assignment as an action on the selected task, and gains ordering and view-indication rules for the two dateless views. The existing requirement for actions on the selected task changes, since date assignment joins the set.

## Impact

- `singularity.py` — needs task queries for the two dateless buckets (`start.isSet=false` split by `deferred`), and a way to set or clear a task's date and deferred flag together as one update.
- `main.py` — `TaskApp` currently holds `self.day: date` as its entire notion of position; that becomes a view selector. Affects `load`, `update_daybar`, the `prev_day`/`next_day`/`today` actions, `action_add` (which derives a new task's start from `self.day`), `BINDINGS`, and `Help.TEXT`.
- No new dependencies; no change to `run.sh`, `requirements.txt`, or `.env`.
- Observable elsewhere: tasks dated from this board become visible in the other SingularityApp clients on the day they were given, and a task sent to never appears in the app's own deferred list.
- Grounding for the exclusion of finished tasks: undated tasks number 39 while the day view is open, but 2127 once archived ones are included; deferred tasks are 2 versus 377. Including finished tasks would make both views useless.
- The repo has no automated test suite; verification is through the Textual pilot harness and synthetic tasks, never against real dated days.
