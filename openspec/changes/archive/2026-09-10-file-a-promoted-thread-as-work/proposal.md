## Why

A mail row counts as work while it is mail, and stops counting the moment it
becomes a task. Promoting a thread is how a message that turns out to be work
joins the day — and the task it makes is unfiled, so the key that hides work
cannot hide it. The one action that declares a message *is* work produces the
one task that cannot be treated as such.

## What Changes

- A thread promoted to a task is created already filed under the work project,
  so the key that hides work hides it like every other work task.
- The project goes in at creation, in the same request that makes the task.
  The store accepts it there, and a task created filed takes every later write
  the board makes.
- Where no work project is configured, promoting creates an unfiled task as it
  does today and says nothing new. The key that hides work is where a missing
  setting is reported, and it already reports it.
- Nothing changes about how a row is counted as work: mail still counts because
  it is mail, and a task still counts by its project.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one new requirement saying a promoted task is filed as work,
  beside the ones that say a tracker issue and a work account's event are. No
  existing requirement changes: promoting keeps every property it promises now,
  and *Filing a task for the first time is confirmed* is untouched because a
  task created filed is never a task being filed.

## Impact

- `main.py`: `action_promote` alone — one field added to the dictionary it
  already builds, which the optimistic placeholder is built from too.
- `tests/stub/t_promote.py`: what the promotion sends, and that the promoted
  row is hidden by the key for work.
- `tests/store/t_prolive.py`: the live promotion's task comes back filed.
- No API surface changes: `create_task` already forwards arbitrary fields, and
  the store was probed to confirm it accepts this one.
