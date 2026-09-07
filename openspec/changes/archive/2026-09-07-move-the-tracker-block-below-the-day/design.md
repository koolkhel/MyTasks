## Context

See proposal.md — Why.

The block joins the day in one line today: the issues are put in front of
whatever the ordering produced. Everything else about a tracker row — that it
counts as work, that only opening acts on it, that reordering cannot reach it,
that it is counted apart from the tasks — is decided before that line and is
untouched by where the rows land.

The day's rows are banded, and this change is about which band boundary the
block sits on:

```
   [ green ][ past due ][ pinned ][ timed ][ untimed ][ finished ]
    ^                                                  ^
    the block sits here today            it moves to here
```

The right-hand boundary is the one the requirement now names: after every
unfinished task, before the first finished one.

## Goals / Non-Goals

**Goals:**

- The block beside the day's untimed work, which is what an issue resembles.
- The block still legible at the end of a day, when most rows are finished.

**Non-Goals:**

- Interleaving issues among the all-day tasks. The block stays a block: its
  rows are grouped by configured state, which sorting them among tasks by
  title would destroy, and that grouping was asked for deliberately.
- Anything about a tracker row other than where it sits.
- Where an all-day calendar event goes. It still leads the day, by an earlier
  decision this change does not revisit.

## Decisions

**The block sits on the boundary, not at the foot.**

"At the bottom" has two readings and they differ by more than they look.
Measured on this account earlier the same day, 13 of 23 tasks were finished by
the evening — so a block at the true foot of the list would spend every
evening below more completed rows than live ones. That is the exact condition
the original placement was avoiding when it put the block on top, and moving
the block to the foot would reproduce it rather than fix it.

Sitting before the first finished row keeps the block adjacent to the untimed
tasks all day, whatever gets ticked, which is what "near the all-day tasks"
asks for.

**Ticking a task now moves it past the block.**

A consequence rather than a feature, and stated because it is visible. The
block becomes the line where the day's unfinished work ends, so a task
crossing that line on being ticked is the same event as the line meaning
something. The alternative — the block below the finished rows — has no such
crossing, and buries the block; that trade was made deliberately.

**The two requirements are replaced rather than edited.**

Not a matter of taste: a modification may not rename a scenario, and each of
the two requirements has a scenario whose *name* states the old position —
`Above everything the board manages` and `The issues appear above today's
tasks`. Keeping those names beside corrected bodies would leave the spec
contradicting itself in its own headings. So both are removed and added under
names that describe what they now say, with every other rule and scenario
carried across unchanged.

The second requirement's new name is also the better one on its own merits:
most of what it states is what each row carries and how a state is rendered,
which its old name did not mention.

**Placement stays separate from the day's ordering.**

The block is still assembled and inserted whole, not given an ordering key the
way a calendar event now is. An event is one row that belongs at an hour; the
block is several rows that belong together in a configured sequence. Giving
each issue a key would sort them among the all-day tasks by title and lose
that sequence, which is the thing the block exists to preserve.

## Risks / Trade-offs

**An issue in progress is now further down the screen** → Accepted, and the
point of the change. The reason the block led the day was that an issue in
progress is what is being worked on now; the reason to move it is that an
issue names no hour and reading the day means reading past it. If issues
start being missed, the evidence for moving it back is the same kind that
moved it here.

**A day where everything is finished** → The block then leads the list, which
follows from the rule rather than being a special case, but it is the one
arrangement where the block is at the top again. Stated in the requirement and
worth a scenario so it is deliberate rather than incidental.

**The count and the filter must not shift** → The tracked count, the hidden
count and the work filter are all computed before placement. Nothing about
them changes, and a regression check that the counts and the tasks' own order
are identical before and after is the cheapest proof of it.
