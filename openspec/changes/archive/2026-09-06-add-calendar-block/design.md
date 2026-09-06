## Context

See proposal.md — Why.

Everything below was measured on this machine before it was decided. The board
already reads one outside source read-only — the issue tracker — and that
module's shape is the one this follows: its own configuration, one failure
type, and rows the rest of the board takes without knowing where they came
from.

## Goals / Non-Goals

**Goals:**

- A day that reads in the order it will be lived.
- A calendar the board cannot damage.

**Non-Goals:**

- Writing to the calendar. Completing or editing an event would need the
  change to survive a round trip and reconcile with whatever else edited it —
  a two-way sync, and a different project.
- Every calendar on the machine. Two accounts of seven, chosen deliberately.
- Working anywhere but macOS. This reads the local calendar through the
  system's own framework; there is no portable version of that, and pretending
  otherwise would mean an abstraction with one implementation.

## Decisions

**Read through the system's calendar framework, not the scriptable interface
or the files.**

Three routes exist, and two were tested rather than assumed:

```
   route                      speed        repeats expanded?   permission
   scripting interface        21 SECONDS   NO                  already granted
   the calendar's own files   --           --                  blocked outright
   the system framework       1-3 ms       YES                 must be granted
```

The scripting interface answered a single day in twenty-one seconds and, worse,
does not expand repetitions: its idea of an event is the rule, not the
occurrence. Over the next fortnight this machine holds 106 events and **all 106
come from a repetition** — that route would have shown almost nothing while
appearing to work. The files sit behind a permission the system refuses
outright.

The framework answers a day in one to three milliseconds. That is fast enough
that a day change can simply ask again: no cache, nothing to invalidate, no
staleness. It still runs off the drawing path, because the day must not wait
for it — the same reason the tracker's fetch does.

**Filter by account, not by calendar.** The names a person thinks in are the
account headings, not the calendars beneath them. Measured here: 11 calendars
under 7 accounts, and the two that matter hold 53 of the 104 events in the
next fortnight — the rest being a club calendar, a shared file account, and
some holiday subscriptions. Filtering by account also survives a calendar being
added under one, which filtering by calendar name would not.

**Two entries in the environment, not one list.** The work filter has to know
which account is work; a single list of accounts could not say. So one entry
names the account whose events count as work and another names the rest. This
mirrors the tracker, whose issues already count as work, and reuses that
requirement's shape rather than inventing a second way to mean the same thing.

**Interleaved by time, not a block of its own.** The tracker's issues are
pinned above the day because they are what is being worked on now, whatever
day is shown. An event is different: it belongs to a date and to an hour, and
its worth is in sitting between the tasks it makes impossible. A block would
have been the cheaper copy of an existing pattern and the wrong answer.

This is what makes the change touch the ordering requirements. The day's rows
were all tasks; now some are not, and the rules that order tasks must be
stated as ordering *tasks* rather than *rows*. The safeguard written into the
requirement is that removing every event leaves the tasks exactly as they were
— a property that can be checked rather than argued about.

**A module named for the format, not the thing.** `calendar` is a module in
Python's own library; a file of that name beside the board would shadow it and
break something unrelated later.

## Risks / Trade-offs

**The permission can be granted in a way that looks like success** → Handled,
and it cost a round trip to discover: the system offers "add events only",
which reports itself as granted while returning no events. A day would then
show as free rather than unreadable. The requirement therefore treats partial
permission as no permission. A newly granted permission also does not reach a
terminal that was already running, which is worth saying plainly to whoever
grants it.

**A dependency that works on one operating system** → Accepted and stated. It
brings two further packages with it. The board has been portable until now, and
this is the first thing to make it not; naming that in the proposal rather than
discovering it later is the point.

**The board now shows something it can never fix** → Accepted, and the reason
every writing key must refuse rather than silently ignore. A row that looks
like a task and quietly resists being ticked is worse than one that says why.

**Events could bury the tasks** → A real possibility: this machine has a day
with 11 events in the next fortnight. Nothing in this change limits how many
are shown, because a day genuinely full of meetings is information rather than
clutter. If it proves otherwise, limiting it is a later change with its own
evidence rather than a guess made now.
