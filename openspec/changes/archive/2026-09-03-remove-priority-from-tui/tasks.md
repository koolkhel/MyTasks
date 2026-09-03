## 1. Stop displaying priority

- [x] 1.1 Drop `HIGH`, `LOW`, and `PRIORITY_NAMES` from the `singularity` import list in `main.py`; verify `./.venv/bin/python -c "import main"` succeeds and `grep -nE 'HIGH|\bLOW\b|PRIORITY_NAMES' main.py` returns nothing.
- [x] 1.2 In `row_for`, collapse the title styling to the done/cancelled strikethrough branch only, removing the bold-high and dim-low branches; verify with the Textual pilot that two open tasks whose stored priorities differ produce identical cell markup.
- [x] 1.3 In `update_detail`, remove the `priority:` entry that currently seeds the `bits` list, and handle the now-possible empty `bits` case so a task with a note but no flags renders without a leading blank line; verify with the pilot on three tasks — one plain, one note-only, one recurring with a deadline.

## 2. Remove the priority action

- [x] 2.1 Delete the `Binding("p", "priority", "Priority")` entry and the `action_priority` handler from `main.py`; verify the footer no longer lists "Priority" and that pressing `p` in the pilot leaves a synthetic task's stored priority unchanged when re-read from the API.
- [x] 2.2 Remove the priority line from `Help.TEXT`; verify the help overlay still opens on `?`, closes on `esc`, and contains no priority entry.

## 3. Remove priority from ordering

- [x] 3.1 Drop `task.priority` from the sort key in `sort_for_display` in `singularity.py`, leaving completion, pinned, timed, start time, and title; verify two same-slot tasks with differing priorities come back in title order.

## 4. Verify end to end

- [x] 4.1 Drive the pilot through add → tick → untick → rename → delete against a synthetic task on a far-future date, asserting no outgoing request body carries a `priority` key, then confirm the synthetic task is gone; do not exercise this against a real day.
- [x] 4.2 Run `./run.sh --cli` and confirm today's listing renders unchanged apart from ordering, and `./run.sh` opens the board with the reduced key set in the footer.
