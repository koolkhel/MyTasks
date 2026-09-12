## Why

The board began counting time yesterday, and it counts it in one place only:
the key that starts a workspace tells the board what is being worked on, and
the card says how long ago that was. Every other way of reaching a card --
which is every way of reaching a card that is not a tracker issue -- shows
nothing.

That is the wrong half. A person is on a thing whenever they are looking at
its card; starting a workspace is one occasion for that and not a privileged
one. The card is titled "Now", and it should be able to answer for itself how
long now has been going on.

## What Changes

- A card opened on **any** row counts from the moment it opened: a task, a
  tracker issue, a mail thread, a calendar event alike. No key is privileged
  and no row is exempt.
- The count is the **sitting**, not the task's day. It begins when the card
  opens and ends when the card is dismissed; opening the card again begins a
  new count. Leaving the card is leaving the thing.
- **BREAKING** (to the spec, not to anyone's data): the board stops
  remembering what is being worked on. The one-thing-at-a-time memory added
  yesterday is removed rather than extended -- with every card counting its own
  sitting, that memory has nowhere left to show itself, so keeping it would be
  state no one can observe.
- Starting a workspace keeps every rule it has. It still opens the card on the
  issue it started; that card now counts because every card counts, not
  because this key is special.
- Nothing is written down and nothing is added up. No total per row, per day
  or otherwise, on disk or in memory.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: the requirement added yesterday, *The board shows what is
  being worked on and since when*, is removed and replaced by one that counts
  the card's own sitting on any row. *The focus view changes nothing* is
  modified to say what the count is and is not, so the two requirements do not
  read as contradicting each other.

## Impact

- `main.py`: the app-level `working` field and `working_since` go; `show_focus`
  loses the argument it passed; `TaskFocus` takes no `since` and counts from
  its own mount. `worked_for` and the tick interval are unchanged.
- `tests/stub/t_workspace.py`: the three parts added yesterday
  (`t_working_remembered`, `t_working_one_at_a_time`, `t_working_shown`) assert
  behaviour this change removes, so they are replaced rather than adjusted.
- The six stub suites that build a card directly (`t_star2`, `t_fit2`,
  `t_pane`, `t_star`, `t_twins2`, `t_mailview`) build it with four positional
  arguments and read it by element id rather than by counting lines, so
  dropping the fifth argument and drawing one line more should leave them
  untouched. They are run to confirm it, not edited on the assumption.
- No configuration, no stored task, and nothing on disk changes.
