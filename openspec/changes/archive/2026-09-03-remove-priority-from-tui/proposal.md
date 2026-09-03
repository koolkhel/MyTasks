## Why

The task board surfaces SingularityApp's `priority` field in four separate places — a `p` cycle key, bold/dim row styling, a line in the detail pane, and a tiebreaker in the sort order — but priorities are not part of how this board is actually used. Each affordance is interface weight and a way to change data by accident, earning nothing in return.

## What Changes

- Remove the `p` keybinding and its `action_priority` handler from the TUI, so the board can no longer write `priority` back to the API.
- Remove priority-driven row styling: titles no longer render bold for high or dim for low. The strikethrough on done and cancelled tasks stays.
- Remove the `priority: <name>` entry from the detail pane. The pane keeps recurring, pinned, deadline and note.
- Remove the priority line from the in-app help overlay.
- Remove `priority` as a sort tiebreaker in `sort_for_display`. Tasks sharing a slot now fall through to title order.
- **Not changing**: `singularity.py` keeps `HIGH`/`NORMAL`/`LOW`, `PRIORITY_NAMES` and `Task.priority`, so the client stays a faithful wrapper of the REST API and a future caller can still read the field. Only the board stops using it.

## Capabilities

### New Capabilities

- `task-board`: the day-at-a-time terminal view of tasks — what a task row displays, how rows are ordered within a day, what the detail pane shows for the selected task, and which keys act on it.

### Modified Capabilities

None. `openspec/specs/` has no capabilities yet, so this change introduces the first one rather than amending an existing spec.

## Impact

- `main.py` — the `singularity` import list, the `Help.TEXT` overlay, `BINDINGS`, `row_for`, `update_detail`, and the `action_priority` handler.
- `singularity.py` — `sort_for_display` only. The priority constants, `PRIORITY_NAMES`, and the `Task.priority` property are deliberately left in place.
- No changes to dependencies, `requirements.txt`, `run.sh`, `.env`, or any API request the client sends other than dropping the `PATCH /task/{id}` call that set priority.
- Observable behavior change beyond the removals: tasks that share a start slot may appear in a different order than before, because title now breaks the tie that priority used to.
- The repo has no automated test suite; the change is verifiable through the Textual pilot harness and the `--cli` listing.
