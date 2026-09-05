## Why

Half the day's work is not in the board. Issues in progress in the company's
issue tracker are the part that actually gets billed, and they live somewhere
the board cannot see, so the board shows a day that is missing whatever the
job currently is. Seeing both together is the point: a workload you can look
at in one place.

The tracker is read from and never written to. Issues are worked in the
tracker's own interface; what is wanted here is to see them beside the day and
to be one keypress from opening one.

## What Changes

- Today's view SHALL additionally show the issues assigned to a person and
  currently in progress, in a fixed block below the day's own tasks. Only
  today: an issue in progress is what is being done now, not something
  scheduled, and repeating it under every date would say otherwise.
- The block SHALL be read-only. No action that changes a task SHALL act on
  one, because the board does not own them and pretending otherwise would
  show a change the tracker never made.
- The block SHALL NOT take part in the day's ordering. It sits after
  everything the board manages, in a fixed sequence, and no reordering key
  reaches it.
- An issue SHALL open in a browser from the board, at its page in the tracker.
- Issues SHALL count as work, so the key that hides work hides them too. This
  is what a person means by putting the job out of sight for an evening: the
  tracker rows are the job more literally than anything else on screen.
- Which issues are shown SHALL be configured rather than fixed: the assignee,
  the projects and the state are read from the environment, so no login,
  project name or credential is written into the board.
- **Where the tracker cannot be reached, the board SHALL work exactly as it
  does now and SHALL say that it could not reach the tracker.** The tracker
  is on a corporate VPN and is often unavailable; with one issue typically in
  progress, an empty block is the ordinary case, so a silent failure would be
  indistinguishable from a quiet day. The board's own day SHALL never fail to
  load because the tracker did.

Not in scope:

- **Writing to the tracker.** Nothing on the board changes an issue: not its
  state, not its assignee, not a comment. Issues are worked in the tracker.
- **Any tracker view other than "in progress".** The same assignee has 71
  unresolved issues in these projects and one in progress. The backlog is not
  a workload and would bury the day.
- **Issues assigned to anyone else.** The digest this borrows from reports on
  a team; this shows one person's own work.
- **Reaching the tracker through another machine.** It answers this laptop
  directly when the VPN is up, so nothing is proxied and no remote host is
  contacted at run time.

## Capabilities

### New Capabilities

None. Today's view gains a section, and the existing keys gain a subject they
refuse to change.

### Modified Capabilities

- `task-board`: new requirements cover showing the tracker block, its being
  read-only and unordered, opening an issue, its counting as work, and what
  happens when the tracker cannot be reached. Existing requirements change
  where the board reports what a view holds and does not hold, and where the
  actions on a task are listed.

## Impact

- A new module for reading the tracker, kept apart from the SingularityApp
  client: a query built from configuration, one request to the issues
  endpoint, and the fields needed to render a row. The digest project on the
  team server has a working version of this logic whose query and field
  selection are worth copying; its roster validation and per-member grouping
  are not, since this shows one person.
- `main.py`: the fetch on its own worker so the day never waits on it and a
  failure cannot reach the day's own load; the block appended after the sorted
  rows; a guard in the one place every write already passes through; the
  counts the board reports; the key bar and help unchanged in shape.
- `.env` gains the tracker settings, the address and token among them, so the
  board works however it was launched rather than only from a shell that
  happened to export them. `.env` is already outside version control. The
  environment still wins where it is set, so an exported value keeps working.
- `requests` is already a dependency. Nothing new is added.
