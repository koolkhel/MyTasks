## Context

See proposal.md — Why.

The ordering that decides a day is a single key per task, compared in turn:

```
   0  finished?            finished rows sink
   1  not tagged?          the tag lifts
   2  not past due?        past due leads what is merely due
   3  how overdue          most overdue first, within that band
   4  not pinned?
   5  not timed?           timed before all-day
   6  (hour, minute)
   7  hand-set order
   8  title
```

Events are put in afterwards, by insertion rather than by sorting, so that the
tasks' own sequence cannot be disturbed. The defect is not in that decision —
it is that the insertion compares only entry 6, the clock, and treats a row
naming no time as later than any event. Entries 0 to 5 are exactly what makes
untimed rows appear near the top as well as near the bottom.

## Goals / Non-Goals

**Goals:**

- An event beside the work of the same hour.
- The tasks' own order untouched, still by construction rather than by test.

**Non-Goals:**

- Where an all-day event goes. It leads the day, by an earlier decision, and
  this change does not revisit it.
- Anything an event *is*. No new field, no new fetch, no change to the row.
- Sorting events and tasks together as one list. Insertion is what makes the
  guarantee provable rather than merely tested, and it is kept.

## Decisions

**Place an event by a whole ordering key, not by the clock.**

The event is given the key of what it is — not finished, not tagged, not past
due, not pinned, timed, at its own hour — and inserted before the first task
whose key is greater. Every band falls out with no special handling: past-due
tasks lead because entry 2 separates them, finished tasks sink because entry 0
does, and an event lands among the timed rows of the ordinary band because
entries 5 and 6 put it there.

The rejected alternative was to keep comparing clocks but skip rows that name
no time — anchoring among timed rows alone. It fixes the reported case in
fewer lines and then fails on a finished task: a completed task at eight still
carries its hour and still sorts to the bottom, so "after the last timed row"
would drop an evening event below the day's finished work. That is the same
class of error as the one being fixed — reasoning about position instead of
about what decides position — so it is not worth the lines it saves.

**The key is built from the same function the tasks use.**

Not a second key of its own shape. The two must agree entry for entry, and the
only way to be sure of that is for the comparison to read the tasks' keys from
the function that produces them, with the event's key written to match its
shape. A key assembled independently would drift the first time a band is
added — as one was, when the tag was introduced.

**An event ties with a task at the same minute, and precedes it.**

An event carries no hand-set order, which is entry 7, and the store gives 0 to
a task created without one — so an event sorts as though it were first-placed
within its minute. Two rows at the same hour are then adjacent, which is what
was asked for; which of the pair is above the other is arbitrary, and being
arbitrary in a stated direction is better than being arbitrary by accident.

**Still an insertion.**

Each event is placed into the already-sorted tasks; no task key is recomputed
and no task moves relative to another. The guarantee that removing every event
leaves the tasks exactly as they were therefore holds because of how the code
is shaped, not because a test happened to cover it — which matters, since the
test that covered the *old* rule passed while the rule was wrong.

## Risks / Trade-offs

**The scenario that should have caught this passed** → The day it describes
holds one timed task and one event and nothing else, so no band but the clock
was ever exercised. The cases that reproduce the defect — a past-due row that
names no time, a finished row that names an hour — are the ones worth adding,
and a crowded day holding every band at once is what protects the guarantee
about the tasks' own order. Coverage of the shape of the data, not only of the
happy path.

**Ordering read in two places** → The tasks' key and the event's key must stay
the same shape. They are built beside each other for that reason, and a test
that asserts they have equal length is cheap insurance against a band being
added to one and not the other.

**A day ordered by title rather than by hand** → The inbox and the someday
view order by title and hold no events, so entry 7 is never consulted for an
event in a view that would read it differently. Worth stating because the key
carries an entry whose meaning depends on the view.
