## Why

The board runs in a terminal tab that says whatever the shell last put there —
the working directory, or the command that started it. With several tabs open,
nothing distinguishes the one holding the task board except remembering where
it was opened.

A terminal will name its tab whatever the running program asks it to. The
board asks for nothing, so it inherits a name that says nothing about it.

## What Changes

- While the board is running, the terminal tab is named for it.
- On exit the previous title is put back, so quitting leaves the tab as it was
  found. This is the half that matters: the board is opened and quit often,
  and a tab left permanently misnamed would be worse than one that was never
  named at all.
- The title is restored even when the board exits by failing, not only when it
  is quit deliberately.
- Nothing is written when the board's output is not a terminal, so a piped or
  redirected run stays free of escape sequences.

The name is fixed rather than describing the day, the counts or the view. A
tab that changes as work is done is noise in a tab bar, and a fixed name is
what makes the tab findable.

Only the board is affected. The command-line listing runs from a different
entry point and is untouched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: gains a requirement that the board names its terminal tab
  while it runs, restores what was there when it leaves, and writes nothing
  when its output is not a terminal.

## Impact

- `main.py`: the entry point that starts the board, and a constant holding the
  name.
- No change to `singularity.py`, `tracker.py`, the ordering, any write, or any
  key.
- No new dependency: the escape sequences are three short strings.
