## Context

See proposal.md for why. What shapes the approach is what the store actually
returns, which its own API does not document: `recurrence` is typed there as an
object with no fields at all. Everything below was read off the live account
during exploration, as field names, value shapes and counts.

A series is a task carrying a `recurrence`. An occurrence is a task carrying a
`recurrenceGeneratorId` naming its series. The two sets do not overlap.

```
  a series                                  its occurrences
  +---------------------------------+       +--------------------------+
  | .recurrence = {                 |       | .recurrenceGeneratorId   |
  |    repeat: {everyweek: {...}}   |<------+    = the series' own id   |
  |    onlyOnComplete: true|absent  |       | no .recurrence of its own |
  |    startTime, nextTime, lastTime|       | an ordinary dated task    |
  |    time: "18:00"   (sometimes)  |       +--------------------------+
  |    ending: {limit, date, iters} |
  |    lastGeneratedTaskId ---------+-----> the furthest one made so far
  +---------------------------------+
```

On the account probed: 18 series, 458 occurrences, 56 tasks with neither, and
every generator id resolved to one of the 18. Occurrences ran from three days
back to two years ahead.

`repeat` is a single-key tagged union and the tag is the kind:

| tag | what hangs off it |
|---|---|
| `everyday` | `{interval}` |
| `everyweek` | `{type: 1, interval, days: [0..6]}` |
| `everymonth` | `{type: 2, interval, days: [{dayNumber: N}]}` |

A yearly tag presumably exists and the account had none, which is the whole
reason the spec requires an unreadable repeat to say so. `type` duplicates the
tag, so a reader must not trust one over the other without saying which it used.

`onlyOnComplete` is the wait-or-stack flag, and the account settled its meaning
beyond doubt:

| `onlyOnComplete` | series | live occurrences each |
|---|---|---|
| `true` | 7 | exactly 1 |
| absent | 11 | 4 to 67 |

The waiting ones each had a single occurrence, several of them overdue, sitting
until finished. The stacking ones had occurrences materialised far ahead.

## Goals / Non-Goals

**Goals:**

- One view answering "what am I signed up for", from facts rather than from
  arithmetic on the rule.
- A reading of the repeat that a person can check against the app, and an honest
  refusal where the board cannot read it.
- Reuse of the archive's machinery rather than a second way of doing the same
  thing.

**Non-Goals:**

- Authoring or editing a repeat. Absent from the store's create and update
  bodies, so not reachable; whether an undocumented field would be accepted is
  its own investigation and its own risk.
- Reconciling the recurring glyph with occurrences. A real defect, found here,
  deliberately left: it needs a decision about what an occurrence should show,
  and answering it inside this change would hide it.
- Any model of what the store will generate next. The board reports what is
  there.

## Decisions

### The view sweeps every task, because no filter exists

The store's task listing has twenty filters and none of them is about a repeat.
So the rows can only be found by reading the account's tasks and keeping those
that carry one. Three pages of two hundred on the account probed.

The alternative looked attractive and is a trap. The listing has
`includeAllRecurrenceInstances`, and with it off the server is meant to collapse
a series' occurrences, which would be exactly this view for one request. It does
not work: the server post-filters after paging, so offsets lie. Asked that way
the account returned 61 series where 18 exist and 367 rows against a reported
total of 532 — duplicates and gaps together. The board already forces the flag
on in its paging helper; this change relies on that and the spec now says so.

### Held until a reload, drawn as it arrives

The archive's arrangement, adopted wholesale rather than reasoned out again: the
fetch runs when the view is first asked for, what it produces is held, returning
does not re-ask, and a reload drops what is held. Pages are drawn as they land
so the table is never blank while requests finish.

Rejected: fetching on every entry. Three requests on each press of a key, for a
list that changes when a person edits a repeat in the other app, which is rare.

Rejected: folding the series into the ordinary load so the view needs no fetch of
its own. It would put three extra requests on every day the board draws, to serve
a view most days are not spent in.

### The queued count is counted, never derived

The rule and the store can disagree, and when they do the store is what a person
is living with. So the count and the furthest-ahead date come from the
occurrences the sweep actually saw. This is free: the sweep has already read every
task, and grouping occurrences by their generator id costs one pass.

It also means the count is honest about the waiting case. A series that waits
shows one queued occurrence, which is the truth and is the shape of the whole
feature.

### Ordered by the next occurrence

The view's first question is what is about to come round, so soonest first, with
no-next-occurrence last. Rejected: the store's own order, which is an order for a
day's list and means nothing across series; and alphabetical, which answers a
question nobody asks of eighteen rows.

### Every write refused, by action rather than by row

The archive refuses by the name of the action, with a small allow-list, because
its rows are the board's own and what decides is what is being asked. The same
applies here with an empty allow-list, and the same benefit: a write added later
is refused without anybody remembering to add it.

The reason is worth keeping separate from the mechanism. This is not a read-only
row like a tracker issue, which the board could not write to if it tried. A
series is writable. What is unknown is the blast radius: the store has already
made up to sixty-seven occurrences from a series, and nothing establishes whether
a rename or a reschedule reaches them. Refusing is the conservative reading and
the one the person asked for.

### Sunday is day zero, established rather than assumed

`everyweek` carries weekday numbers and the store documents none of them. Read
off the account, every weekly series with exactly one day agreed: day 0 fell on a
Sunday, 1 on a Monday, 2 on a Tuesday, 3 on a Wednesday. Four series, no
disagreement, so the store counts from Sunday as JavaScript does and not from
Monday as Python does.

This matters beyond tidiness. Under the wrong convention a `[1,2,3,4,5]` series
reads as Tuesday to Saturday instead of the working week, which is a phrase a
person would believe and act on. The conversion SHALL therefore be written once,
with this reasoning beside it, rather than inlined wherever a day is rendered.

### The key's label is five characters, and the reason is the notes area

The key bar wraps to the window. At eighty columns it sat on five lines with
eight cells to spare, so a label of six characters or more takes a sixth line.
That line does not come out of nothing: in a twelve-row window it comes out of
the notes area, which then has nothing at all, and a note is cut with no sign
that it was. `Repeats` did exactly that and turned a suite green at HEAD into a
suite failing here.

Two existing requirements collide at that size -- the key bar shows every key
without clipping, and the notes area takes a share of the height where the
window is short -- and at eighty by twelve with forty keys both cannot hold. A
floor on the area does not help; the layout has no row to give it, and
`min-height` is simply not honoured.

So the collision is avoided rather than resolved: `Recur` is five characters,
fits on the fifth line, and is the word the day bar already uses for the view.
Resolving the collision properly would mean deciding which of the two
requirements yields, and that is a change of its own.

### Ending is reported only where it is real

`ending` came back as `{date, limit, iterations}` on all eighteen series, with
`limit: 5` every time and `ending.date` an exact copy of `startTime` every time.
So `limit` selects the mode and, in the mode all eighteen were in, the other two
fields are inert. `iterations` held large numbers that look computed rather than
chosen.

The board therefore SHALL treat an unknown `limit` as "no ending it can read"
rather than reporting a date that is really the start. One observed mode is not a
vocabulary, so the reading is deliberately narrow: this mode means no ending, and
anything else is unread.

## Risks / Trade-offs

- **The repeat's shape is known only by observation, from one account.** → The
  spec requires an unreadable repeat to say so, and the view to survive one. The
  yearly tag nobody has seen will land as an honest refusal rather than a wrong
  reading or a crash.
- **`ending` is read from a single observed mode.** → Reported as unreadable
  outside it, per the decision above. A person who needs the end date has the
  app; a person shown a wrong one has nothing.
- **The sweep costs three requests and grows with the account.** → Once per open,
  and the store's throttle is the reason it is not once per entry. A very large
  account makes the first draw slower, which the page-by-page drawing is there to
  absorb.
- **The queued count is only as good as the sweep.** → It depends on the
  instance flag being on. That is now a requirement rather than an implementation
  habit, with the paging numbers recorded as the reason.
- **A person may read the view as a place to fix a repeat.** → The refusal says
  what the view is rather than only that the key did nothing. The inability to
  author a repeat is the store's, and saying so is more useful than a key that
  appears to be missing.

## Migration Plan

Nothing to migrate. No stored data changes, no configuration is added, and the
view is reached by a key that does nothing today. A person who upgrades gains a
key.

Rolling back is removing the key, the position and the fetch.

## Open Questions

- Which `ending.limit` values mean what. Answerable later by making a series with
  an end date in the app and reading it back, and it changes nothing here: the
  narrow reading is already specified, and widening it later adds a case without
  disturbing the view.
- Whether the store accepts an undocumented recurrence field on an update. Out of
  scope, deliberately, and settled by one throwaway task when somebody wants to
  author repeats. It does not affect this change, which writes nothing.
