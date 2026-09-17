## Context

See proposal.md for why. What shapes the approach is what the store will and
will not do, measured against the real account before any of this was written:

- Every archived task carries `journalDate`, the date the store archived it,
  and the task query filters on it (`.gte`, `.lte`, `.isSet`).
- The query has **no text filter and no sort parameter**. Rows come back in the
  store's own order, which is not by any date. Searching and ordering are the
  board's work or they do not happen.
- The account holds about 9,100 archived rows against 541 live ones. One page
  of 1,000 costs 1.1 s and 1.1 MiB of JSON, so the whole of it is about ten
  requests and eleven seconds.
- Holding them costs 14.7 MiB as the API hands them over, 6.2 MiB trimmed to
  what a row draws. Measured, not estimated.
- Drawing them is the expensive part: a repaint of 9,100 rows costs 158 ms
  against 9 ms for 500, and a repaint is what every mark, every search and
  every arriving page triggers.
- `journalDate` is the archivation moment, not the tick. On 597 of 1,000 rows
  it is within two minutes of the last modification; about one in nine sits at
  local midnight, where the store swept it the night after it was done.

The board already has the machinery this needs. A view is a `position`, a value
that is a date or a bucket; `board.Board` decides every row, cell, order and
count from state alone; `refuse_foreign` is the single funnel every write
passes through; and `iter_tasks` pages a query to exhaustion.

## Goals / Non-Goals

**Goals:**

- The archive is a view like the others, so that search, marking, copying, the
  focus card, the work filter and the status line reach it without being
  written twice.
- What is drawn stays immediate however large the archive grows.
- The store is asked for the archive once a session, and only if asked for.

**Non-Goals:**

- No cache on disk. The board reads no state back from a file today and this
  change does not make it start.
- No trimming of held rows. 14.7 MiB is measured and affordable; a trimmed row
  would mean re-fetching a task to read its note.
- No editing of the record. Rename, note, project, tag, cancel, delete and
  done-for-today stay refused in the archive; only the two writes that take a
  task *out* of it are offered.
- No archive-side date filtering. `journalDate.gte` would make a per-day
  archive cheap, and a per-day archive is the thing that cannot be searched.

## Decisions

### The archive is a position, not a screen

A pushed screen would need its own table, its own search, its own marking and
its own copy, and would then hold a second expression of what a row says --
exactly what "what the board draws is decided without a terminal" exists to
forbid. As a position it inherits all of it: `Board.paint` already answers rows,
cells, order, counts and surviving marks from the position it was given.

### Its own sentinel, not a third `Bucket`

`Bucket.deferred` is an API flag -- the thing that separates the inbox from
someday -- and the archive has no answer for it. Four suites iterate
`for b in Bucket` and would silently start iterating a view that is not a
bucket. So the archive is a separate singleton, and `Position` becomes
`date | Bucket | Archive`.

The nine `isinstance(position, Bucket)` sites in `main.py`, `board.py` and
`singularity.py` divide into two meanings that have never needed telling apart:
"this view has no calendar day" and "this view is one of the two dateless
buckets, with its `deferred` flag". The first becomes a test for not being a
date; the second stays as it is. Auditing those nine is a task of its own
because getting one wrong is a silent bug, not a failure.

### Fetched with the existing pager, filtered here

`iter_tasks` already forces `includeAllRecurrenceInstances=True` and pages by
offset -- the two things that make offset paging safe against this store. The
archive query adds `includeArchived=True` and `journalDate.isSet=True`, and the
rows that are neither completed nor cancelled (about 4%) are dropped locally.

The alternative was `checked.in`, which would let the store do the dropping. Its
type is declared as a number in the store's own schema, so a comma-separated
list is a guess about an undocumented encoding; one local pass over rows already
in hand is certain.

### Held whole, drawn bounded

The board holds every fetched row and draws at most 500 of them: the most
recently archived, or the most recently archived that matched. 500 because the
measurement says a repaint of that many is 9 ms and of 2,000 is 40 ms, and a
repaint happens on every press of the marking key.

This is the one place the view is unlike the others, so the status line carries
it: how many the archive holds, how many are drawn, and -- when a search is in
force -- how many matched. The board already reports what a view withholds for
the inbox's filed tasks and for off-view marks; this is the same rule.

### Rows appear as pages arrive

Eleven seconds of empty table would be the worst part of this feature. Because
the bound keeps a repaint at 9 ms, repainting after each page costs nothing, so
the view fills while it loads and says it is still loading until the last page
lands. A search run against a half-loaded archive answers from what arrived,
which the existing requirement about rows arriving during a search already
covers -- and the status line says the fetch is still running, so a partial
answer is never silently partial.

### Two writes, refused by name, before anything is announced

Un-ticking and dating are allowed in the archive; everything else is refused.
Because what decides is the *action* and not the row, the refusal cannot live
in `refuse_foreign`, the funnel every single write passes through: the funnel
does not know which key it is serving. It lives in `rows_for_write`, which
every set-capable write key calls by name (`"toggle"`, `"schedule"`,
`"cancel"`, ...) before gathering its rows, and in the two single-row keys that
do not use it (rename, note), which ask for themselves.

Before anything is announced matters. The first draft gated the funnel only,
and the funnel is reached after a key acting on a marked set has reported
itself: three archived rows were refused one at a time while the board said
"Brought back 3". Nothing was written and the board said the opposite. The
user found it by hand in the first minute.

It is a test of the shown view, not of the row -- the same finished task shown
on its own calendar day stays as editable as it has always been.

### A row written to stays until the archive is re-read

Elsewhere a row leaves a view the moment it stops belonging. Here membership
is decided by the fetch: the archive is what was read, with pending writes
laid over it, and nothing taken away. Two reasons. The row is what a person
is looking at when they choose where to send the task they just brought back,
and un-ticking that removed the row would leave `d` nothing to act on. And a
confirmed write folds into the archive's own copy of the row (`_write_done`
updates both `_base` and `self.archive`), so what is drawn stays truthful
rather than reverting to "finished" when the patch is dropped. A reload reads
again and the brought-back rows are gone.

Measured against the store on a throwaway task: `uncomplete` alone clears the
archive date, so no second call is needed, and the task reappears on its own
day -- and on today as overdue, that day being past.

### The date is the archive date, and is called that

Shown in the `When` column, which is 11 characters wide -- exactly what
`%d %b %Y` comes to. Named "archived" in the column heading and on the focus
card, because for a row the store swept at midnight the completion was the day
before, and the store does not hold which.

Ordering is by archive date descending, ties broken by title, so that the order
never depends on the order the store answered in.

### The held archive is given to the board, not fetched by it

`Board` already takes the tasks, the events, the issues, the threads and the
clock as values. The archive is one more, handed in by the application that
fetched it on a worker. Nothing in `board.py` learns how to reach the store,
and a suite can paint an archive of any size with no account at all.

## Risks / Trade-offs

- **Ten requests in a burst; the store throttles.** → The fetch happens once a
  session and only when the view is asked for. A refusal surfaces as the
  archive failing to load, on its own worker, never as the board failing --
  the pattern the tracker and the calendar already follow.
- **The archive can be a day behind what was finished.** A task ticked today is
  not archived until the store sweeps it, so it is on its day and not yet in the
  archive. → The view names the archive date rather than completion, and a
  reload re-fetches.
- **14.7 MiB held for a session.** → Measured, and freed on quit. Trimming to
  6.2 MiB stays available if it ever matters.
- **A clock read inside `board.py` escapes the suites' patch.** The suites steer
  time by patching `main.datetime`, which is why `Board` is given `now` as a
  value. → The archive's date formatting uses the given value and reads no
  clock, and the new suite checks a fixed instant.
- **A new binding can push the key bar past the terminal's width**, which is its
  own requirement. → The label is one short word, and `t_fit` is run before the
  change is called done.
- **The nine position checks.** → Each one is read and decided rather than
  pattern-replaced, and the existing view suites are the instrument.
