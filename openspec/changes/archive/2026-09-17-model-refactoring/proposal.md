## Why

Deciding what the board draws and putting it on screen are the same 206-line
method. `repaint` looks up a `DataTable`, measures it, composes the rows from
six sources, filters them twice, places events and issues among them, counts
what it hid, formats every cell, assembles an eleven-part status line, fills
the table, and restores the cursor. Everything in that list except the table
work is a decision about content, and none of it needs a terminal.

The cost is measurable. Eight of the 52 self-contained suites start a whole
Textual application and never press a key: they call `repaint`, `row_for`,
`place_events`, `patched`, `shortened`, `is_event`, `neighbour_to_pass`. Of
those seven, **only `repaint` needs a widget** — the rest already touch
nothing. Those eight suites cost 3.1 minutes of the tier's 12.1, while the
seven suites that need no application at all cost about zero.

The seam is mostly cut already. Of the 33 methods involved in drawing the
board, **6 touch a widget and 27 do not**; those 27 are 648 lines that have
never needed a screen and live on the application only because that is where
the state is. `repaint` is the one place the two halves are welded, and even
there they are layered rather than interleaved — the whole board has exactly
one `table.add_row` and one call to `row_for`.

## What Changes

- A new module holds what the board draws: given the board's state, it answers
  the rows in order, every cell's text, the status line, which marks survive,
  and where the cursor belongs. It imports no widget and needs no terminal.
- The 27 methods that already touch nothing move there as they are.
- `repaint` keeps its name and its 24 callers and becomes roughly 30 lines: get
  the answer, copy it back, fill the table, move the cursor, set the status.
- Every name the suites reach for stays on the application, delegating:
  `repaint` (97 calls in the suites), `row_for` (45), `is_tracker` (41),
  `is_mail` (40), `apply_window` (21), `is_event` (20), `is_work` (10),
  `patched` (4), `belongs` (2), `place_events`, `shortened`, `is_green`. So do
  the attributes they read: `app.tasks` (**452 reads**), `app._selected_id`
  (74), `app.hidden_work` (20), `app.past_due`, `app.shown_mail` and the rest.
- **No observable behaviour changes.** Not a cell, not a count, not a
  character of the status line, not where the cursor lands.

Not in this change, deliberately:

- **Converting the eight suites.** They go on building an application and go on
  passing untouched. That is what makes this verifiable at all: 20,699 lines of
  suites that did not move are the only instrument that can say the seam was
  cut cleanly. Claiming the 3.1 minutes is a later change, with its own
  verification.
- **The other two seams.** The write pipeline (`_pending`, `_undo`, `_paced`)
  and the per-source state stay exactly where they are.
- **Shrinking `main.py`.** About 780 lines move, which takes `TaskApp` from
  4,462 to roughly 3,700 — still a large class. This is an ownership change,
  not a size change, and should not be sold as one.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: adds one requirement — what the board draws SHALL be decidable
  from its state without starting a terminal, and what it puts on screen SHALL
  be exactly that answer rather than a second computation beside it. This is a
  new externally checkable property: today it is false, because the rows cannot
  be obtained without a `DataTable` to write them into.

## Impact

- **Code**: `main.py` (`repaint` rewritten, 27 methods moved, delegates left
  behind), one new module. No other product file.
- **Dependencies**: none added.
- **Risk**: `repaint` assigns eleven derived attributes and prunes marks as a
  side effect, and the suites read those attributes 500-plus times. Missing one
  assignment breaks suites loudly; getting one subtly wrong — a count taken
  before a filter instead of after — would not. The ordering inside `repaint`
  is load-bearing and is documented in its own comments.
- **The guard**: `openspec/specs/task-board/spec.md` already specifies what
  must not move — *Task row presentation*, *The list stays where it is when it
  is redrawn* (8 scenarios about scroll and cursor), the ordering requirements,
  and the counts each source reports. Those, plus the 52 suites unchanged, are
  the acceptance criteria.
