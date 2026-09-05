## Context

See proposal.md — Why for the motivation.

Measured against the live tracker before proposing, from this laptop:

- It answers this machine directly when the VPN is up, authenticated as the
  configured person. Nothing needs proxying through another host.
- The selection matters enormously. For the same person and projects:
  one issue in progress, 71 unresolved, 158 in total. Of the 71, forty-five
  are merely `Open`. A backlog is not a workload, and 71 rows would bury a day
  of about twenty-five.
- A fetch takes 260–510 ms, against roughly 250 ms for the board's own load of
  today. Fetching inline would double the wait even when it works.
- With the VPN down there is no HTTP status at all — the connection fails —
  so the failure arrives as a transport error, not a response to inspect.
- An issue's page is the tracker's base address, `/issue/`, and the issue key.

What the board already provides:

- Every write passes through `submit_write`: all eleven calls into the client
  sit inside its lambdas. One check there covers every action, and every
  action added later.
- `load` catches only `SingularityError` (`main.py`). Anything else raised in
  it would escape as a worker crash, and a tracker error raised there would be
  reported as the day failing to load.
- `is_work` compares a task's project id against the configured work project,
  and `action_open_link` opens whatever address a row carries.

## Goals / Non-Goals

**Goals:**

- The day is never worse for the tracker existing: not slower, not more
  fragile, not different when the tracker is down.
- Read-only by construction rather than by nine separate refusals.
- Nothing identifying in the source.

**Non-Goals:**

- No writing to the tracker, in any form.
- No second view, no issue detail, no search. One block, one key to open it.
- No caching to disk, no offline copy. The tracker is either reachable or it
  is not, and the board says which.

## Decisions

### A small module of our own, not a copy of the digest's

The digest project on the team server has this working, and its query shape
and field selection are worth taking verbatim — they are proven against this
tracker. Its roster validation, per-member grouping and message formatting are
not: they exist to report on six people, and this reports on one.

Copying the file would bring a roster model, an unused exception type and a
grouping function that no caller here would ever use. The part that matters is
small: build a query, ask the issues endpoint for it, read the key, summary
and state out of the custom fields.

### Tracker rows are appended after ordering, not admitted through `belongs`

A tracker issue has no date, so today's membership rule rejects it: the rule
asks whether the task starts on the shown day or is past due, and an issue is
neither. That is not an obstacle to work around — it is the same fact as "the
block is not part of the day's ordering", arriving from the other side.

So the rows are appended after the day's tasks have been selected, filtered
and sorted. The block cannot be interleaved because it is never in the list
being sorted, and it cannot be reordered because the ordering has already
happened. The guarantee is structural rather than a sort key that has to be
respected.

Rejected: giving issues a synthetic date so they pass the membership rule.
It would put them in the ordering, where every future ordering change would
have to keep remembering them.

### But the work filter must reach the block

The filter that hides work is applied to the rows a view selected, before
sorting. Appending afterwards would carry the block straight past it, so the
filter has to be applied to the appended rows as well.

This is the one place where appending later costs something, and it is worth
naming because the failure would be quiet: pressing the key would hide the
work tasks and leave the tracker rows — the most work-like rows on screen —
sitting there.

### One read-only guard, where writes are made

Every write passes through `submit_write`. A single check there refuses any
write against a tracker row, which covers the nine actions that exist and
every action added later, and cannot be forgotten in a new one.

Rejected: a guard in each action. Nine places to write it and nine to forget
it, and a tenth action would silently be able to write.

Undo needs nothing at all: it records what writes replaced, and no write is
ever made, so no entry ever exists.

### The tracker is its own worker, and its failures stay inside it

The fetch runs separately from the day's load and is not awaited by it. Two
consequences, both required: the day appears in its own time rather than the
slower of the two, and a tracker failure cannot surface as "today failed to
load", which is what would happen if it were raised where only
`SingularityError` is caught.

A failure is remembered as a state the board reports, not as an exception that
propagates. With one issue typically in progress, an empty block is the normal
case, so "could not reach the tracker" and "nothing in progress" have to look
different or the VPN being down is invisible.

### Belonging to the work project is reuse, not a special case

An issue carries the configured work project's id, so the key that hides work
hides it, the hidden count includes it, and `is_work` is untouched. The row's
project column shows the tracker's own project, which is what identifies the
issue to a person; the id underneath is what the filter reads.

Likewise the row carries its page address, so the existing key that opens a
link opens the issue with no new action.

## Risks / Trade-offs

- **The row shows a project column that is not the project it belongs to** —
  the column reads the tracker's project while the id says the work project →
  accepted, and it is the useful way round: the id is machinery, the column is
  for a person, and showing the work project on every tracker row would say
  nothing.
- **Configuration names a person, projects, an address and a token** — all
  identifying, and the token is a credential → they live in `.env`, which is
  already outside version control and already holds the board's own token; a
  task asserts no tracked file names any of them.
- **`.env` now holds a second credential** — more in one file to leak →
  unchanged in kind: it was already the file holding the board's API token,
  and keeping both there is better than a board that only works when launched
  from one particular shell.
- **The tracker's own definition of "in progress" could change** — a renamed
  state would silently return nothing → the state is configured rather than
  compiled in, and an empty block is reported differently from a failure, so
  "nothing in progress" is at least visible as a claim.
- **A fetch that hangs rather than fails** — a VPN half up could stall →
  the request carries a timeout, and until it resolves the board shows the day
  without a block, which is the same as any other unavailability.
- **The block competes for screen with the day** — a long list of issues would
  push tasks off → not a risk at one issue, and the selection is deliberately
  the narrowest the tracker offers; if it ever grows, that is a reason to
  revisit the query rather than the layout.
