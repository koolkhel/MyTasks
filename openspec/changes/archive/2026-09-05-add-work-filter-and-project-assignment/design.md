## Context

See proposal.md — Why for the motivation.

Established against the live API before proposing, rather than assumed:

- Filing a task also puts it in one of the project's groups: a task created
  with no project had `group` `""`, and after filing it carried a `Q-...`.
- **A plain `projectId` update therefore cannot move a filed task.** It works
  on a task that has no project, but on one that does it fails with
  `GROUP_PROJECT_MISMATCH`, because the group it still holds belongs to the
  old project. `/v2/task/{id}/move` reassigns the group with the project and
  handles both cases; it is idempotent, and it left the title, start,
  completion, deferred flag and stored order untouched.
- **It cannot be cleared.** Both `null` and `""` were refused with
  `HTTP 400: Must start with one of: "P-"`, and the schema declares
  `pattern: ^(?:P)-` with no null. There is no un-file operation.
- Three projects exist, all live. Of 536 tasks paged, 268 have no project,
  266 are in one project and 2 are in the work project. The separation this
  filters on barely exists yet, which is why filing comes with the filter.
- Project titles carry an emoji from a separate field, assembled by
  `project_names`. Matching a project by its title would therefore be
  matching against something the board itself composes.
- Both intended keys are unbound, and the layout table already supplies their
  Russian twins, so neither needs anything added to it.

What the code already provides:

- `Listing` carries `filed_out` beside `tasks` (`singularity.py:349`) — a
  count of what a view deliberately withheld, which is the exact shape the
  hidden-work count needs.
- `belongs` (`main.py:934`) answers whether a task is in the shown view by
  that view's own membership rule, and `repaint` recomputes every derived
  thing from scratch rather than adjusting it.
- `load_token` reads `.env` through `load_dotenv` before the environment
  (`singularity.py:381`), so a second setting has a pattern to follow.

## Goals / Non-Goals

**Goals:**

- A filter that cannot be mistaken for an empty day.
- An irreversible action guarded like the other irreversible action.
- No personal identifier in the repository.

**Non-Goals:**

- No project management: creating, renaming and deleting projects stay in
  the real client.
- No pretence of un-filing. The board will not offer what the API refuses.
- No state on disk. The mode is turned off by the same key that turned it on.

## Decisions

### The filter is a mode over the view, not part of what a view is

`belongs` answers "is this task in this view", which is a property of the
task and the position. Whether work is currently hidden is a property of the
session. Keeping them apart means the filter cannot be mistaken for a change
to what a day contains, and `belongs` goes on answering the question it
already answers.

So the rows are chosen as they are now, and the mode removes some of them
afterwards. The count of what it removed is what the board reports.

Rejected: folding the work project into `belongs`. It would make a day's
membership depend on a mode, so a task could stop "belonging" to the day it
is scheduled on — and the optimistic layer decides whether a written task
stays on screen by asking `belongs`, which would then conflate "you hid this"
with "this moved elsewhere".

### The hidden count is derived where the other counts are

`repaint` already recomputes the ordering, the past-due count and the row
count from the tasks it holds. The hidden count joins them: the rows the mode
removed, counted at the same moment from the same list.

Deriving rather than tracking is what keeps it honest when a write lands. A
task filed under work while the mode is on leaves the view and the count
rises, without anything having to notice that those two facts are connected.

### The work project comes from the environment, beside the token

Read the same way the token is, so `.env` is the one place a personal
identifier lives and it is already outside version control.

Rejected: matching the project by title. The title is assembled from a
separate emoji field, so the board would be matching against its own
composition; and a Russian project name in the source is exactly the kind of
personal detail that has had to be scrubbed from a repository before.

Rejected: a constant in the source. Same objection, without the indirection.

An absent setting is reported rather than treated as "hide nothing", because
those two are indistinguishable on a day with no work tasks, and one of them
is a broken configuration.

### The first filing is confirmed; a move between projects is not

Filing a task that has no project is irreversible through this API, which
makes it the second action of that kind after deleting, and it gets the same
treatment. Moving a task that is already filed gives up nothing it still has,
so asking would be ceremony.

The distinction is drawn from the task's current state rather than from which
project was chosen, so it stays correct however many projects exist.

Rejected: confirming every assignment. Filing is done in bursts, and a
confirmation on the common case would make the tedious part more tedious
while guarding nothing.

Rejected: confirming none. The board asks before deleting for exactly this
reason, and an accidental filing can only be undone on another device.

### Filing goes through `/move`, not an ordinary update

The first plan was to treat a project as a raw field like a title or a date.
That is wrong for anything already filed: the task keeps a group belonging to
its old project, and a `projectId` update is refused with
`GROUP_PROJECT_MISMATCH`. `/move` reassigns the group with the project, works
equally on a task with no project, and is idempotent — so one call covers
filing and moving, and the distinction the spec draws between them stays a
matter of whether to confirm rather than which request to send.

It still rides the existing optimistic write. The patch shown on screen is
the project alone, because the group is not something the board reads or
displays; the fetch that follows brings it into line without anyone waiting.

A task filed from the inbox leaves it immediately because the inbox's own
membership rule excludes tasks with a project — which the optimistic layer
already consults.

## Risks / Trade-offs

- **A mis-filing cannot be undone from the board** — the whole reason for the
  confirmation, and it remains true after it → the confirmation names the
  consequence rather than asking a bare question, so the person declining
  knows what they are declining.
- **The filter looks broken before anything is filed** — two tasks are in the
  work project today, so the key will appear to do nothing → the board
  reports the mode even when it hides nothing, which is what distinguishes
  "on and nothing to hide" from "not working".
- **A hidden task is still counted by the API's own view of the day** — the
  board's totals and what another client shows will differ while the mode is
  on → the reported counts say what is shown and what is hidden separately,
  as the inbox already does, rather than presenting a smaller day as the
  whole day.
- **The setting can name a project that no longer exists** — a deleted or
  renamed project leaves an identifier matching nothing → hiding then removes
  no rows, which is indistinguishable from having no work tasks; worth
  reporting the configured project by name so a stale setting is visible.
