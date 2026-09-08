## Context

See proposal.md — Why.

The board draws an event's row from the fields `ical.Event` carries, which
already include the instant it ends — the fetch reads `endDate` and keeps it,
unused until now. So "has it ended" needs no new reading, only asking.

Two things about time on this board matter to the approach.

There is **no timer anywhere**. Nothing on the board recomputes as time
passes; a view is what the last fetch made it.

And `self.reference` — the instant every past-due decision is measured
against — is the moment the day was **fetched**, and is set for today's view
alone. Every other day carries none, deliberately: an earlier day's unfinished
tasks are late by definition, and a reference there would paint the whole view
overdue.

```
   what                     when it is measured against
   ---------------------    ---------------------------
   a task's past-due band   the fetch, today only        (existing, untouched)
   an event having ended    the current time, any day    (this change)
   the clock                the current time             (this change)
```

## Goals / Non-Goals

**Goals:**

- A day that reads as what is left of it.
- The one number needed to read it, on screen.

**Non-Goals:**

- Bringing a task's past-due state up to date. It is measured against the
  fetch and drifts in a long sitting; the clock makes that visible without
  causing it. Fixing it means deciding what to do about counts the store
  computed against its own instant — a different change with different
  evidence.
- A third state for an event under way. The data is there, and the boundary
  chosen here deliberately leaves such an event looking ordinary rather than
  marked. Available later; not asked for.
- Hiding or striking out an event that has ended. Nothing about it was
  completed.

## Decisions

**Dim, not a hue.**

Measured rather than assumed, on this board's own theme and table: with the
row cursor on it, a cell drawn dim keeps `dim=True` while its colours are
replaced; a cell drawn in a colour has that colour *replaced outright*.

```
   cursor on the row      dim attribute      foreground
   ------------------     -------------      ----------
   dim cell               kept               replaced by the cursor's
   coloured cell          --                 REPLACED -- the hue is gone
```

That is the same trap `late_colour` documents, and the reason a selected
past-due task is told apart by its age label rather than its colour. Dim
needs no such fallback, which makes it both the smaller change and the more
robust one. Dim also already means *recedes* on this board — the project
column, an event's calendar — so it is a word already in the vocabulary
rather than a new one.

A hue was what was asked for, and would work everywhere except on the row
being looked at. Swapping dim for a hue later is one expression; the
requirement is written so that whatever expresses this has to survive being
selected, which a hue alone does not.

**The boundary is the end, not the start.**

An event that has begun and not finished is one there is still a chance of
joining. Dimming at the start would mark as gone the very event most likely
to be wanted. So `end <= now` is past and everything else is not, which also
means an event under way needs no state of its own.

**Judged against the current time, not against `reference`.**

`reference` is None on every day but today, so a tint measured against it
would simply never appear elsewhere. It is also the fetch's instant, where
this needs the present one. So this asks the clock directly, and the board
then holds two ideas of "now" — deliberately, because they answer different
questions, and stated here so the difference is found on purpose rather than
by surprise.

**Redraw when the set changes, not on a schedule.**

A timer that redrew every minute would move the list under a person's hands
for nothing, fifty-nine times out of sixty. So the timer looks, compares how
many of the shown events have ended against how many had, and redraws only
when that differs. Nothing is fetched to decide it: the ends are already in
hand.

**The clock is the framework's own.**

`Header` takes `show_clock` and a `time_format`; it owns its interval and
refreshes itself without touching the table. Rolling one into the day bar
would mean a timer of ours redrawing a widget every minute, which is the
churn the decision above exists to avoid.

## Risks / Trade-offs

**A clock next to stale past-due labels** → Real, and named in the proposal
rather than fixed here. Nothing on the board recomputes how overdue a task is,
so a long sitting can show a clock past midnight beside a task still counted
as due today. The clock reveals it; it did not cause it. Fixing it properly
means reconciling with the counts the store computed, which is why it is not
folded in.

**Two instants on one board** → `reference` for tasks, the present for events.
Justified by their different questions and recorded above; the risk is that a
third feature reaches for the wrong one. The mitigation is that each is asked
for by name at its point of use, not passed around as "now".

**A minute's granularity** → An event that ended forty seconds ago still
reads as ahead until the next look. Accepted: the alternative is a timer an
order of magnitude busier for a distinction nobody acts on inside a minute.

**Dim on a theme that dims badly** → Both bundled themes are the board's own
and were checked; dim renders as reduced intensity on each. A terminal that
ignores the dim attribute entirely would show no difference, which is a
degradation rather than a fault, and the row is still marked as an event by
its own mark.
