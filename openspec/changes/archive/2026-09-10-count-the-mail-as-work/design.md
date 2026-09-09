## Context

See proposal.md — Why. The design-level facts, all read from the code:

- `is_work(task)` is `work_project is not None and task.project_id == work_project`.
  `tracker_rows` stamps `"projectId": self.work_project` on every row it
  builds; `event_rows` stamps it as `work_project if config.is_work(account)
  else None`. `mail_rows` stamps nothing.
- `repaint` counts `hidden_work` over `tasks + issues + events` and filters
  those three lists. `mails = self.mail_rows()` runs *after* that block and is
  concatenated on, so a stamped mail row would still not be filtered.
- `shown_issues` is assigned twice — once from the unfiltered list and again
  inside the `hiding_work` branch. `shown_mail` and `shown_messages` are
  assigned once, from the unfiltered list.
- `row_for` returns early for a mail row with its own tuple, putting the
  sender where a task names its project. The tracker's branch does the same
  and says why: the row is stamped with the work project for filtering, and
  what is *drawn* is the tracker's own project, because that is what names the
  row.
- `belongs()` excludes project-bearing tasks from the inbox
  (`not (position is Bucket.INBOX and task.project_id)`), which would evict
  every mail row if it saw one. It has one call site, over `self.patched()`;
  mail rows are synthesised later in `repaint` and never reach it.
- `DataTable.RowSelected` opens the focus card for any row, with no source
  guard, and the card is handed `self.projects.get(task.project_id or "", "")`.

## Goals / Non-Goals

**Goals:**

- The key reaches every source, and cannot be defeated by where a source's
  rows are concatenated.
- Mail rows do not acquire a project they do not belong to.

**Non-Goals:**

- Changing where mail sits in the view. It still follows the inbox's tasks,
  still appended rather than sorted in.
- Making work-ness configurable per mailbox, folder or sender. One account,
  all corporate; the proposal records this as a choice and names what would
  reopen it.
- Persisting the mode across restarts. Unchanged: it lasts as long as the
  board is open, which is also what bounds the blast radius of hiding several
  hundred rows.
- Retiring the tracker's stamp in favour of the rule chosen below. It works,
  it is specified, and it is covered; converting it is a separate tidy-up with
  its own risk and no user-visible gain.

## Decisions

### Mail is recognised by a rule, not by a stamped project

`is_work` becomes: the task's project is the work project, **or** the row is a
mail row.

The alternative was to mirror the tracker exactly — stamp
`"projectId": self.work_project` in `mail_rows` — which is one line and has
the closest possible precedent. Two things decided against it.

A mail row would then hold a project it does not belong to, and two readers of
`project_id` are not guarded by the mail row's refusal of writes. `row_for` is
fine: it returns before reading the project. The focus card is not. Enter on
any row opens it, mail rows included, and it is handed the project's name — so
stamping would make a mail row's card announce the work project. That is
already true of a tracker row's card today, unnoticed and asserted by no
suite; the rule avoids inheriting it rather than spreading it.

And the rule says the thing that is true. "All mail is work" is a fact about
this board's mailbox, and `is_work` is where the board decides what work is.
Expressing it as a project stamp encodes the fact as a coincidence of data.

The cost is two ways of being work where there was one, until and unless the
tracker is converted. That is a smaller cost than a card that names the wrong
project.

### Mail is filtered where the other sources are filtered

The rows move inside the `hiding_work` block: counted into `hidden_work` with
the rest, and filtered before the concatenation that appends them.

This is the half that actually fixes anything — the stamp or the rule alone
changes nothing while the concatenation happens afterwards. It is also the
mistake the comment above that block already warns about, having been made
once for the tracker and then again for mail, which is why the spec now
requires it of any source rather than of mail in particular. A source appended
after the filter is unreachable by the key however its rows are marked.

Order is preserved: `mails` is filtered in place and still concatenated last,
so the tasks keep exactly the order they had and the mail keeps its own.

### The two mail counts are taken after filtering

`shown_mail` and `shown_messages` are computed from the filtered list, the way
`shown_issues` already is. The spec's existing wording — the inbox reports how
many rows of mail it *is showing* — already commits to this, so the change is
the code catching up rather than a new undertaking.

`shown_messages` sums `MAIL_COUNT` over the rows, so filtering the rows
carries the message count with it and needs no separate arithmetic.

### The scenario that said the inbox was unaffected keeps its name

`openspec validate` compares a MODIFIED requirement's scenarios to the current
spec's **by name**, and refuses a rename as a dropped scenario — verified by
hitting it. So *The inbox is unaffected* keeps its title and its body narrows
to what it always actually meant: none of the inbox's *tasks* are hidden,
because a task with a project is already outside the inbox. A second scenario
beside it says the mail is hidden. Recorded because the shape of the delta is
otherwise hard to account for: the pair is the tool's constraint, not a
preference.

### What proves a source is inside the filter

"Rows shown plus rows hidden equals the rows there were" is the obvious
invariant and it is useless here. A source that escapes the filter is missing
from both sides of that sum: its rows stay on screen, and it contributes
nothing to the hidden count, so the sum balances exactly as it would if the
filter had worked. Checked against the unfixed board, and it passed.

What catches it is the direct statement: with the mode on, no row on screen
counts as work. On the same unfixed board that fails. The sum is kept beside
it as a weaker second check — it would catch a miscount rather than an escape.

The check is made for each source where that source's own board already
exists, rather than duplicating tracker, calendar and mailbox setup into one
suite: mail in the mail-view suite, issues in the tracker-block suite, work
events in the calendar suite, plain tasks in the work-filter suite. Between
them every source the board draws is covered.

## Risks / Trade-offs

- **Two definitions of work** — a reader asking "what counts as work?" now
  finds a project comparison and a source check in the same expression → they
  are in one function, which is the only place the question is answered, and
  the requirement states both. The alternative put the second definition in a
  row-building function instead, which is further from the question.
- **`w` in the inbox goes from a no-op to hiding several hundred rows** — on
  this mailbox about 531 of them → deliberate, and the point: the inbox is the
  only view where the key currently does nothing, and its own note about
  announcing a mode that hides nothing says why that is the worst state to be
  in. Nothing is written, and the mode does not outlive the board.
- **The mail counts vanishing could read as an empty mailbox** → the daybar
  says "work hidden (N)" in the same bar, with N being those rows, so the
  number moves from one place to the other rather than disappearing. Worth
  checking on screen during apply that the two are legible together.
- **A future personal mailbox would be hidden by a key that means work** → the
  spec names the condition and the calendar's per-account rule is the shape to
  grow into. Nothing here has to be undone to get there: `is_work` is still
  the one place that decides.
- **Someone later converts the tracker to the rule and forgets the stamp is
  load-bearing for the focus card** → converting the tracker would *improve*
  the card, not break it. Noted so the asymmetry is not read as an oversight.
