## Why

A program the board starts typed into the board.

Pressing the key on a tracker issue opened the help overlay, moved the
selection one row, and opened the wrong issue's page in a browser. None of
that was a defect in the key, the bindings or the selection: the program the
board started reached the board's own terminal, and what came back arrived in
the input queue the board reads.

The board already sends the program's three streams to nowhere, and that was
not enough. A child process can open `/dev/tty` -- the controlling terminal --
and bypass every inherited stream. The terminal it finds there is the one the
board is drawing on, and a terminal that is written to answers back.

So the requirement written for this was right and the implementation reached
half of it. A program started by a full-screen board must not be able to reach
that board's terminal at all, in either direction.

## What Changes

- A started program is put in a session of its own, with no controlling
  terminal, so `/dev/tty` is not there for it to open.
- The requirement grows the second direction: not only that the program's
  output cannot be seen, but that the program cannot reach the terminal, and
  so cannot cause anything to arrive as though somebody had typed it.
- A check that the board cannot be typed into by what it starts.

Not in scope: the program that did it. Its own repository will stop it asking
a terminal for something it should ask a socket for; this change makes that a
matter of tidiness rather than the only thing standing between a board and a
stray keystroke.

Also not in scope: the mail password command, which the board also runs. It is
awaited rather than left to run, and a credential helper may legitimately need
a terminal to ask on. Severing it is a different decision with a different
answer, and is recorded in the design rather than taken here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement.
  - MODIFIED `Starting a workspace from an issue` -- the paragraph about the
    program's output becomes a paragraph about the program's reach: it is
    started detached from the board's terminal, so it can neither write there
    nor cause anything to be read from there.

## Impact

- `main.py`: one argument on the call that starts the program, and the reason
  beside it.
- `tests/stub/t_workspace.py`: a check that the program is started detached,
  read off the source in the way the no-shell checks already are -- the
  property is about what the code cannot do rather than about what one run
  did.
- No configuration changes, nothing new to set, and no behaviour any person
  will notice except the absence of a board typing to itself.
