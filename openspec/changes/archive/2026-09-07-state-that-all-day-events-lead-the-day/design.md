## Context

See proposal.md — Why.

The board prepends all-day events to the finished list of rows, after the
timed events have been placed among the tasks and before the tracker block is
inserted. So they lead everything, and have since the calendar block was
built. Only the requirement is behind.

```
   all-day events                     <- prepended, ahead of everything
   [ past due ][ timed rows and timed events ][ untimed ]
   tracker block                              <- inserted before the finished
   [ finished ]
```

## Goals / Non-Goals

**Goals:**

- A requirement that states the decision instead of gesturing at it.
- Scenarios covering the rows the old wording left unmentioned.

**Non-Goals:**

- Changing where anything appears. This change alters no source.
- Revisiting where a *timed* event goes. That was settled, with its own
  scenarios, when events were placed among the bands.

## Decisions

**State the position against every kind of row, not one kind.**

The old sentence named only the rows that happen at a time. Three kinds of row
went unmentioned — past-due tasks, the day's own untimed tasks, and the
tracker block — and an implementation could have put an all-day event below
any of them while satisfying the requirement as written. Naming all three is
what makes the requirement able to fail.

That is not hypothetical for this board. A rule about untimed rows being "at
the end of a day" is exactly the assumption that misplaced every timed event
until it was fixed; the same silence about untimed rows sits in this sentence.

**Give the reason, so the rule survives being reread.**

An all-day event describes the whole day, so nothing that happens inside the
day outranks it. Stated in the requirement rather than left to be re-derived,
because a placement with no recorded reason is one that gets changed by
whoever next finds it surprising.

**Say that several are stable among themselves.**

Already true — they are sorted by time and then title — but unstated, and a
day here holds more than one often enough to notice if it ever stopped being
true.

## Risks / Trade-offs

**A requirement written to match the code rather than the other way round** →
The honest description of this change, and worth being plain about. The
protection is that the behaviour was chosen deliberately and is now confirmed,
and that the scenarios added are ones that can fail: each names a kind of row
the board would visibly get wrong if the placement ever changed.

**No source change means the suite is the only new evidence** → So the suite
is where the work is. Each added scenario becomes a check against synthetic
events, and the day it runs against holds a past-due row, untimed tasks and a
tracker block at once, which is the arrangement the old wording ignored.
