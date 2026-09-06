## Why

A third tracker state, `Requires improvement`, reads on the board as
`Requires`. The rule that shortens a state to fit its column was tuned for the
only two states that existed when it was written: it drops a leading `In ` and
cuts the rest to eight cells. That works when the word which distinguishes one
state from another comes first, and `Requires improvement` is the first state
where it comes second.

The same rule leaves the column's capitalisation to chance. Every other label
in that column is lowercase -- `all-day`, `14:30`, `999d ago` -- and the
tracker rows match only because `progress` and `review` happen to be lowercase
once `In ` is removed. `Requires` is the first capital letter to appear there,
and it will not be the last.

## What Changes

- A tracker state is shown as its last word, lowercased. `In progress` reads
  `progress`, `In review` reads `review`, and `Requires improvement` reads
  `improvement`.
- The column that carries it widens from eight cells to eleven, which is what
  `improvement` needs. The task labels that share the column are unaffected:
  the widest of them, `999d ago`, is eight cells and still fits.
- The column's width stops being written down twice. Today the same number
  appears as a constant used to trim the label and as a literal used to size
  the column, with nothing keeping them equal.

No behaviour outside the tracker block changes, and nothing about which issues
are shown, how they are ordered, or how they are counted changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: `Today shows the issues the tracker reports for me` currently
  requires that a row carry the state its issue is in and that the state be
  visible without opening the issue, but says nothing about the form the state
  takes. It gains that: the last word, lowercased, fitted to the column, and
  the column wide enough for the task labels that share it.

## Impact

- `main.py`: `_state_label`, the `_STATE_WIDTH` constant, and the `When`
  column's declared width.
- `singularity.py`: the docstring on `overdue_label`, which explains its
  eight-cell bound by reference to a column that is no longer eight cells.
- Nothing else reads or renders a tracker state; `main.py` shows it in exactly
  one place.
- No configuration changes. `YOUTRACK_STATES` already carries
  `Requires improvement`; this change is only about how it is drawn.
