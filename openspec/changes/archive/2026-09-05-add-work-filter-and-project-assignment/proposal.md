## Why

Work and everything else sit in one list. There is no way to put the job out
of sight for an evening, and no way to say which tasks are the job in the
first place — the board reads a task's project but has never been able to set
one. Of the tasks in this account, two are filed under the work project and
over five hundred are not, so the separation the board would filter on does
not yet exist to be filtered.

That makes this one change rather than two: a way to mark work, and a way to
hide what is marked. Either alone is useless.

## What Changes

- A key toggles between showing everything and hiding the work tasks. It has
  two states and no third, it lives for as long as the board is open, and it
  applies to every view. The inbox is unaffected without needing to be
  excluded: a task with a project is already outside it.
- The board says when it is hiding work, and how much, in the same place it
  already says how many tasks a view holds and how many the inbox withheld. A
  filter that hides rows silently is indistinguishable from a day that is
  simply emptier than expected.
- A key assigns the selected task to a project, chosen from the projects that
  exist, showing which one the task is in now.
- **Assigning a project to a task that has none SHALL ask first**, because the
  API cannot undo it: `projectId` must match `^(?:P)-`, and both `null` and
  `""` are refused, so nothing the board can send returns a task to having no
  project. Moving a task that is already filed asks nothing, since it gives up
  nothing. Deleting is the only other irreversible action and it already asks.
- Which project counts as work is read from the environment rather than
  written into the board, so a personal project identifier never enters the
  repository. Where it is not set, the toggle says so rather than filtering
  nothing and looking broken.

Not in scope:

- **Creating, renaming or deleting projects.** The three that exist are
  enough to separate work from the rest, which is the whole goal.
- **Un-filing a task.** The API offers no way, so the board will not pretend
  to. A task can be moved to another project; it cannot be returned to none.
- **Remembering the mode between runs.** The board keeps no state on disk,
  and a mode that is turned off by pressing the key again does not need to
  outlive the session that turned it on.
- **Filtering by any other project.** One filter, one purpose.

## Capabilities

### New Capabilities

None. The board gains two actions and a mode over the views it already has.

### Modified Capabilities

- `task-board`: two new requirements cover hiding work and assigning a
  project. Two existing requirements change: the list of actions the board
  offers gains both keys, and what the board reports about the shown view
  gains the hidden-work count, alongside the counts it already reports.

## Impact

- `main.py`: a filter applied to the rows a view has already selected, a mode
  on the app, a project picker modal, the confirmation before a first filing,
  and two bindings with their key-bar and help entries. The Russian twins for
  both keys come from the existing table without further work.
- `singularity.py`: reading the work project from the environment beside the
  token, and a method to set a task's project. `projectId` goes through the
  ordinary update; the `/v2/task/{id}/move` endpoint also works but requires
  `projectId` and offers nothing more here.
- `.env` gains one line, and it is already outside version control.
- The optimistic write layer needs nothing new. Filing changes a raw field
  like every other write, and a task leaving the inbox the moment it is filed
  already falls out of that view's own membership rule.
- No new dependencies.
