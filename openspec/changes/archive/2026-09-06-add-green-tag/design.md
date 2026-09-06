## Context

See proposal.md — Why.

Four facts from the API shape everything below. They were established by
probing, each against a synthetic task on a far-future day that was deleted
afterwards.

- A task's tags arrive with the task. Nothing extra is fetched to know
  whether a task is marked.
- `PATCH /task/{id}` accepts `tags`, and the whole array is replaced rather
  than merged. Marking is therefore a read-modify-write over the task's own
  tags, not an append.
- The array can be emptied. Unlike a project, which cannot be cleared and so
  made filing irreversible, the tag comes off again — which is what makes the
  key a toggle and the write undoable with no special case.
- Listing tags is refused for want of a scope, but reading one by its
  identifier is not. So the board can confirm a configured identifier without
  being able to search for a tag by name.

The board's ordering is one tuple, in `sort_key`, whose tail is the manual
order and the title. `group_key` is that same tuple minus the last two, and
its docstring already says an ordering key added above the manual one keeps
it honest without a second edit.

## Goals / Non-Goals

**Goals:**

- One key that both marks and unmarks, reaching the state a person wants
  without their having to know which state the task is in.
- A mark that survives a person who cannot tell colours apart.
- Marking that means something to the order, not only to the eye.

**Non-Goals:**

- More than one tag. The board is not gaining a tag system; it is gaining one
  tag, named in the environment, that it can set, show and sort by. Every
  other tag on a task is left exactly as it is.
- Reading the key from the tag. The tag record carries a hotkey field of its
  own, and the board ignores it: `g` is bound like every other key.
- Filtering by the tag. `w` hides work; a key that showed only marked tasks
  is a plausible neighbour but is not part of this.
- Using the tag's colour, which the tag record also carries.

## Decisions

**Green sits second in the sort key, above the past-due band.**

The key becomes, in turn:

```
  0  done or cancelled       finished sink
  1  not green               <-- new
  2  past due before due today
  3  most overdue first
  4  pinned first
  5  timed before all-day
  6  start time
  7  manual order            <- group_key stops here
  8  title
```

Simulated against a mixed day, which is how the cost was found rather than
guessed at:

```
  as the board orders today          with green second
    work-16d-overdue                   || GREEN-3d-overdue
 || GREEN-3d-overdue                   || GREEN-14:30
    work-2d-overdue                    || GREEN-allday
    work-09:00                            work-16d-overdue   <-- was first
 || GREEN-14:30                           work-2d-overdue
 || GREEN-allday                          work-09:00
    work-allday                           work-allday
    work-done                             work-done
```

Placing it here, rather than below the past-due band, is what makes the rail
one bar instead of two: below the band, marked tasks would lead within
"past due" and again within "due today", and the margin would show two runs
with untagged work between them. The cost is the fourth row above — a task
sixteen days overdue now sits below a marked task that is not yet due. That
is the tag's whole purpose stated mechanically, but it is a real change to
how a day reads and is why the ordering requirements are being modified
rather than quietly broken.

Position 1 rather than 0 keeps finished work sunk: a marked task that is done
should not float over unfinished ones.

**`group_key` needs no edit.** It is `sort_key` minus its last two entries,
so the new key joins the group prefix by construction. A manual move
therefore cannot carry a task across the rail, which is the behaviour wanted,
at no cost.

**The rail is `║` (U+2551), in a column of its own.**

A one-cell double vertical, which joins between rows into an unbroken bar.
Strict ASCII cannot express a double line in one cell: `||` costs two cells
and still reads as a separate mark per row.

```
  ║ ☐  14:30    a personal thing          Личное
  ║ ☐  all-day  another green one         Личное
    ☐  09:00    a work task               Работа
```

`║` is ambiguous-width, which in an East Asian locale renders two cells wide
and would break the columns. This is not a new exposure: the board already
uses `≡` for a note, which has exactly the same property.

**Marking is a read-modify-write, and it is the first write that is.**

Every other write the board makes sets a field to a value. This one has to
take the task's existing tags, add or drop one, and send the rest back —
because the array is replaced whole. Two consequences: a task's other tags
must be preserved, and the write must be built from the task the board is
holding rather than from a fresh fetch, so that it goes through the same
optimistic path as everything else.

**The configured tag is verified, not trusted.** The identifier comes from
the environment, as the work project's does, and the board reads the tag back
once. A wrong identifier is reported and everything else keeps working — the
same shape as a work project that is missing.

The lookup runs *after* the day is on screen, not before it, for the reason
the tracker's fetch does: nothing about the rail needs the tag's name, only
the sentence the board says back, so making the first paint wait on another
request buys nothing and costs a visible delay. This was found by existing
suites failing rather than reasoned out in advance — the lookup was on the
critical path first, and three of them timed out waiting for a day that had
not painted.

Because the lookup now lands after the first paint, "not looked up yet" and
"looked up, and it names nothing" are separate states rather than both being
an absent title. Only the second refuses the key; the first lets the write
go, and an identifier the account does not have is refused by the API and
reported through the path every failed write already uses.

## Risks / Trade-offs

**A removal that follows a recent tag write is held back.**

The assumption recorded here first — that serialising writes per task would
be enough — was tested and is false. Sending the writes one at a time, each
awaiting its own response, outside the board entirely:

```
  mark alone              (g)         4/4 applied
  mark, unmark, mark      (g, g, g)   4/4 applied
  mark then unmark        (g, g)      1/4 applied     <-- the failing shape
```

The store answers 200 and does not apply the write. It is specifically a
removal — an empty tag list — arriving soon after another tag write; a
sequence ending in a non-empty list always applied. Spacing the two about two
seconds apart made it stick. Sweeping the gap afterwards, over five trials
each: 1.0s applied 2/5, and 2.5s, 4.0s and 6.0s applied 5/5. The board waits
2.5s — the shortest gap measured to be reliable, with nothing gained by
waiting longer. A longer burst (unmark, mark, unmark) under the same rule
ended correct 4/4 at both 2.5s and 4.0s. No alternative form was reliable:
sending the empty list bare cleared 1/4, sending it with an unrelated field
alongside 3/4, sending it twice 0/4.

Waiting alone was then measured over many more trials and found to be very
good but not certain: about one removal in a dozen still failed to apply
after the full wait. A requirement that says the removal must be reliable is
not met by "nearly always", so the board also reads the task back after a
removal and sends it again when the tag is still there, up to three attempts
spaced by the same wait. Setting a tag is never read back — that direction
was never seen to fail — and a read that itself fails counts as "still
tagged", so a request that never arrived causes another attempt rather than
false confidence.

So a removal waits behind a recent tag write to the same task, and only then.
The wait happens on the queue that already serialises that one task's writes,
so it delays nothing else: the rail disappears when the key is pressed, every
other key still answers, and the board reports the write in flight exactly as
it reports any other. Unmarking a task marked on some earlier day — the
ordinary case — sends at once, because there is no recent write to wait
behind.

This is a workaround for a defect in something the board does not own, so it
is written down here rather than left as an unexplained sleep, and the
requirement it satisfies says what must be true rather than how long to wait.
It is the same sync layer that intermittently returns `HTTP 500 Sync error`
under rapid writes.

**A badly overdue task can be pushed down the day** → Accepted, and it is the
point. Recorded here and in the modified ordering requirements so that it is
a decision rather than a surprise.

**Two marked tasks separated by an unmarked one show two short rails** →
Accepted. It cannot happen within a day now that the tag sorts above every
other key except finishedness, but a finished marked task sinks below the
unmarked open ones, so a day holding one will show a second rail at the
bottom. That reads correctly: it is a different block.

**`║` in an East Asian locale** → Accepted, as above: `≡` already carries the
same risk and the board is used in a Latin locale.
