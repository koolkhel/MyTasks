## Why

Starting work on a tracker issue means opening a terminal, remembering which
version the issue is against, remembering which several repositories belong to
that project, checking them all out at the same version, and only then
beginning. The board is already showing the issue and already holds the
answer to the first question, so it can hand all of it to one program instead
of a person retyping it.

The board is not the right place for the checkout itself: the repositories, the
host, the branch naming and the several clones are a shell problem that changes
far more often than a task board should. So the board learns one thing --
which program to run, and what to tell it -- and nothing else.

## What Changes

- The tracker's issues carry their version. It already arrives on every
  response and is thrown away; nothing new is asked of the tracker.
- Which custom field holds the version is configured, because "the version an
  issue is against" is a tracker convention rather than a fact about trackers.
- A new key on a tracker row runs one configured program, handing it the
  issue's key, its project and its version.
- The program is named by configuration and run as a list of arguments, never
  as a shell string and never taken from anything a row's text says.
- Where an issue names several versions the board asks which; where it names
  none it says nothing and passes none, leaving the program to decide what
  that means.
- **BREAKING for the spec, not for a person**: a tracker row now has two
  actions rather than one. Both are read-only; nothing about the issue is
  changed by either.

Not in scope: the program itself. It lives outside this repository, and this
change defines only the command line it is called with.

## Capabilities

### New Capabilities

None. This extends the tracker rows the board already draws.

### Modified Capabilities

- `task-board`: one requirement changed, four added.
  - MODIFIED `Only opening acts on a tracker issue` -- a tracker row now has a
    second read-only action, and the rule becomes "nothing here changes the
    issue" rather than "only opening".
  - ADDED `An issue's version` -- where it comes from, how it is configured,
    and what an issue with none or several means.
  - ADDED `Starting a workspace from an issue` -- the key, which rows offer
    it, and what happens on each.
  - ADDED `What the workspace program is told` -- the command line, exactly.
  - ADDED `Nothing but a configured program is run` -- the security rule: a
    configured path, a list of arguments, no shell, nothing from a row's text.

## Impact

- `tracker.py`: `ISSUE_FIELDS` is unchanged -- it already asks for every
  custom field. `_custom_fields` currently keeps only single values, so every
  multi-value field is discarded; it learns to keep lists. `Config` gains the
  name of the version field, read beside the states and the projects it
  already takes from the environment. `Issue` gains the versions it holds.
- `main.py`: a tracker row carries its versions the way it already carries its
  page and its state. One binding, one action, one configured program path,
  and a picker when an issue names more than one version. The launch is routed
  through a method of the app's own, as the link opener is, so a suite can
  assert the command line without running anything.
- `singularity.py`: one more configuration reader, beside the ones for the
  work project, the green tag and the working window.
- `tests/stub/`: a new suite for the command line, the refusals and the
  picker; a check that no shell is used anywhere near it.
- `tests/tracker/`: one check that the configured version field is really read
  off the account, which no stub can show.
- Nothing is written to the tracker, to the task store, or to any file.
