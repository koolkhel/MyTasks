## Why

The board's keys are Latin letters, so none of them fires while the keyboard
is in a Russian layout. Every task with a Russian title therefore costs two
layout switches: one to type the title, one to get back to a keyboard the
board answers. Adding several tasks in a row means alternating layouts for
each, which is enough friction to discourage using the board for the tasks
it is most used for.

The trap is worse one level in. Pressing the date key opens the date picker,
which then wants `t`, `m`, `p`, `s` or `c` — and in a Russian layout those
keys type Cyrillic and the picker cannot be answered at all. The same holds
for the yes/no keys on the delete confirmation.

## What Changes

- Every key the board binds SHALL also answer the Cyrillic character the same
  physical key produces in a Russian layout, so the keys are the ones printed
  on the keyboard whichever layout is active. Pressing the key under `a` adds
  a task whether it types `a` or `ф`.
- This covers the modals as well as the board: the date picker, the delete
  confirmation, the focus card and the help overlay. Fixing only the board
  would leave a person able to open the date picker and unable to answer it.
- The key bar and the help overlay SHALL go on naming the English key alone.
  No Cyrillic spelling is shown anywhere: a person presses a physical key, and
  showing both spellings would double the bar's width to say something the
  keycap already says. This is a decision, not a default.
- The help overlay gains one line saying the keys work in either layout. It
  names no key, so the displayed hotkeys stay English-only; it exists so that
  a person who switches layouts knows this is deliberate rather than finding
  out by accident.

Not in scope:

- **Other layouts.** The mechanism generalises to any layout that maps the
  same physical keys, but only Russian is added: a table is only worth
  carrying if someone types in that language.
- **Changing which keys the board uses.** No binding moves; each simply gains
  the twin of the key it already has.

## Capabilities

### New Capabilities

None. The existing keys gain a second spelling.

### Modified Capabilities

- `task-board`: which keypresses the board answers changes, so a new
  requirement states that every key works in either layout and that the
  modals are included. Two existing requirements need adjusting: the key bar
  currently says it advertises *exactly* the keys the board binds, which
  becomes materially untrue once every action answers two characters; and the
  help overlay gains the line about layouts.

## Impact

- `main.py` only. A table of physical-key twins and a helper that expands a
  binding's key list, applied at the 27 bindings that need one, across
  `TaskApp`, `DatePicker`, `Confirm`, `TaskFocus` and `Help`. `TaskInput`
  needs nothing: `escape` and `enter` are the same in any layout, as are
  `space`, `backspace` and the arrow keys.
- No API involvement, no new dependencies, and no change to any behaviour
  other than which keypresses reach an existing action.
- Three facts were confirmed against Textual 8.2.8 before proposing this:
  Cyrillic characters arrive unchanged as their own key name, a binding on
  one fires its action, and a focused `Input` still receives them — so
  typing a Russian title is unaffected by binding Russian letters.
