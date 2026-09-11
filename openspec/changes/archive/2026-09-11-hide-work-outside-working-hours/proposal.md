## Why

The work filter is a key a person has to remember to press. Work is hidden
only when they think to hide it, which is never the moment they most need it
hidden -- the evening, when the day is over and the queue is still on screen.
A clock does not forget. Outside working hours the board should hide work by
itself, and say so, so that closing the day is something the board does rather
than something the person has to decide to do.

## What Changes

- The board reads a working window from its configuration: the hours work is
  shown, and the days it applies to. Weekends are outside the window by
  default.
- Outside that window the work filter is on, from the moment the board opens
  and at every crossing while it is open. Inside it, the filter is off.
- The key keeps its two states. Pressing it overrules the clock until the next
  crossing, and the overrule then lapses -- which is always invisible, because
  it lapses exactly when the clock comes to agree with it.
- The board says *why* work is hidden when the clock hid it, not only how much.
- Absent configuration is not a new behaviour: with no working window set, the
  board behaves exactly as it does today -- everything shown until the key is
  pressed.

Not breaking: every existing scenario for the key holds unchanged when no
window is configured, and the key's own two states hold whether one is
configured or not.

## Capabilities

### New Capabilities

None. This extends the existing work filter rather than adding a capability
beside it.

### Modified Capabilities

- `task-board`: three requirements changed, two added.
  - MODIFIED `Hiding the work tasks` -- the mode has a second thing that sets
    it, the clock, and the key still offers two states and no third.
  - MODIFIED `How long the work filter lasts, and where it applies` -- a press
    lasts until the next crossing of the window, not until the board closes.
    It still does not outlive the board.
  - MODIFIED `The board says when it is hiding work` -- when the clock hid it,
    the board says which boundary did it.
  - ADDED `The working window` -- what it is, how it is configured, what
    happens when it is absent, unreadable, or has no work project to act on.
  - ADDED `The board crosses the window while it is open` -- what happens at a
    crossing, how soon, and what must not move between crossings.

## Impact

- `singularity.py`: two configuration readers beside `load_work_project`, and
  the pure rule that turns a moment into "inside the window or not". The rule
  takes the moment as an argument so that a suite can ask it about any hour of
  any day without waiting for one.
- `main.py`: the filter's state stops being one boolean. The mode becomes the
  clock's answer unless a press has overruled it; `action_toggle_work` records
  the overrule, and the sixty-second timer that already runs
  `recheck_elapsed` also notices a crossing. It redraws on a crossing and not
  otherwise, for the reason that timer already gives: a redraw a person did
  not ask for moves the list under their hands.
- The row-removing path itself is untouched. A crossing reuses exactly what
  the key already does, including keeping the scroll position and moving the
  selection to the nearest surviving row.
- Every source the filter reaches goes with it -- mail rows and tracker rows
  included -- because all mail is work and an issue carries the work project.
  In the evening the inbox shows its own tasks and no mail.
- `tests/stub/`: a new suite for the window rule and the overrule, and the
  existing work-filter suites re-run to show the unconfigured board unchanged.
