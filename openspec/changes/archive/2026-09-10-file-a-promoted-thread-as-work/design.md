## Context

See proposal.md — Why. What matters here is the machinery that already exists.

- `TaskApp.action_promote` builds one `fields` dictionary — `start`, `useTime`,
  `note` — and uses it twice: the optimistic placeholder is constructed from
  it, and the write closure passes it to `create_task`. Anything added to that
  dictionary is therefore both shown and sent, with no second place to change.
- `TaskApp.is_work` is the one place that decides. A mail row counts because it
  is mail; a task counts when `task.project_id` equals the configured work
  project. Nothing else is consulted, by the filter or by the report of what
  was hidden.
- `SingularityClient.create_task` forwards arbitrary fields to `POST /task`.
- `SingularityClient.set_project` exists, and goes through `/move`, because a
  plain `projectId` update on a task that already holds a group belonging to
  another project is refused with `GROUP_PROJECT_MISMATCH`.

The last two are why this needed evidence rather than a guess: nothing in the
board had ever sent `projectId` at creation, and a task filed without a group
would be a task the board could not write to afterwards.

## Goals / Non-Goals

**Goals**

- One field, in the dictionary that already exists, sent in the request that
  already exists.
- Evidence that the store accepts it and that the resulting task is writable.

**Non-Goals**

- Changing how anything is counted as work. `is_work` is untouched.
- Filing tasks promoted before this change. There is no migration; the key
  that files a task handles them one at a time if anyone wants them filed.
- Choosing the project. The board is told which project counts as work and
  has no opinion beyond that.

## Decisions

### The project is set when the task is created, not afterwards

Probed against the live store with the suites' token, one task named `zz-`
on a day in 2099, deleted in a `finally`:

| probe | result |
| --- | --- |
| `POST /task` with `projectId` and the fields a promotion sends | accepted |
| the created task comes back filed | yes, in the creation's own response |
| title, note and stored order kept | yes |
| rename, tick, untick, reorder, reschedule afterwards | all accepted |
| still filed after all of them | yes |
| a later move to a different project | accepted |
| the same creation with no `projectId` | comes back unfiled, as today |

So the group question is answered: a task *created* filed gets a group
consistent with its project, and every write the board makes on a task
afterwards succeeds. `GROUP_PROJECT_MISMATCH` is a hazard of changing the
project of a task that has one, not of creating a task with one.

Rejected: create the task, then file it through `/move`. It works — that call
is proven — but it costs a second request, admits a state where the task
exists unfiled, and, worse, makes a promotion a first filing of a task that
has no project. The spec confirms that action before performing it, precisely
because it cannot be reversed, so route B would have to modify that
requirement to carve out an exception. Creating the task filed never raises
the question: there is no task to file, and undo removes the whole task.

Rejected: stamping the project onto the row and filing later, as the tracker's
rows are stamped. A promoted row is not a row from a source — it is the
board's own task, and the store is the only place the fact belongs.

### The field is omitted when no work project is configured, never sent empty

`self.work_project` is `None` when `WORK_PROJECT` is unset, and the store
refuses `""` and `null` for this field with `Must start with one of: "P-"`.
So the key is added to the dictionary conditionally rather than assigned a
value that may be `None`. `action_add` already does exactly this for a task
added in the inbox, and for the same reason.

This is also asserted from the other side: a stub check reads the board's own
source and fails if it contains `projectId` set to `None` or to `""`. The
conditional form is what keeps that check honest rather than merely passing.

Where the setting is absent, promoting behaves as it does today and says
nothing new. The board already reports a missing work project at the one place
a person asks about work — the key that hides it — and a notice on every
promotion would repeat that answer to somebody who did not ask.

### The placeholder is filed too, by construction

The placeholder is built from the same dictionary, so it carries the project
without a line of its own. That is the existing convention and it is load
bearing here: the view sorts and filters the placeholder exactly as it will
filter the real task.

On screen this changes nothing at the moment of promotion — mail is shown only
in the inbox, and the placeholder carries a start date, so it leaves the inbox
whether or not it has a project. What it fixes is the day the task landed on:
walk to today and the task is already the right kind of row, before the store
has answered.

### Nothing about `is_work` changes

Mail counts by rule while it is mail; the task it becomes counts by its
project, like every other task. The change is one field precisely because the
work filter was built to read a task's project and needs no knowledge of where
the task came from.

## Risks / Trade-offs

- **The store could stop accepting `projectId` at creation** → the live
  promotion suite checks that the task it made came back filed, so the
  regression surfaces as a failed check naming the field rather than as
  promoted tasks quietly going unfiled.
- **A promoted task cannot be un-filed from the board** → true of any filed
  task; the API refuses every value that would un-file one. The escape is the
  same as everywhere else: undo, which deletes the task outright, or the key
  that moves it to another project.
- **Somebody promotes work they wanted in a personal project** → the filing is
  a consequence of pressing the key that means "this message is work", and the
  key that files a task moves it in one press. Not worth a confirmation on the
  common path; filing in bursts is what the board is for.
- **A second, non-corporate mailbox would falsify the premise** → it would
  falsify the requirement that mail counts as work first, which is where the
  premise is written down and argued. This change inherits that reasoning
  rather than restating it.

## Migration Plan

None. Tasks promoted before this change stay unfiled; the key that files a
task handles any of them a person cares about. Rollback is removing the field.
