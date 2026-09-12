## Context

See proposal.md - Why. What matters here is the shape of what ships today:
the app holds `working`, a `(row id, moment)` pair set by the key that starts
a workspace; `show_focus` asks `working_since` whether the row it is about to
draw is that row, and passes the moment or `None` into the card; the card
draws a line only when it was given one.

Three parts, and after this change none of them is needed. A card that counts
its own sitting needs nothing from the app: it knows when it opened, because
it opened.

## Goals / Non-Goals

**Goals:**

- The card is the only thing that knows about the count. No caller supplies
  it, no caller can get it wrong, and there is no second card-building path to
  keep in step with the first.
- Every existing caller of the card keeps working unedited, including the six
  stub suites that construct it directly.
- The clock stays controllable by the seam the suites already use.

**Non-Goals:**

- Any per-row or per-day total. The spec forbids it; nothing here should
  accidentally make one easy.
- Marking the counting row in the list. With the count restarting on every
  open there is nothing stable to mark, and inventing one is a different
  change.
- Keeping `working` around for the latch. The latch will need to know which
  row is latched, but that is the latch's own state with its own lifetime;
  reusing a field because it happens to exist is how two features end up
  sharing a bug.

## Decisions

**The card records its start in `__init__`, not in `on_mount`.**

`compose` builds the line that shows the count, and in Textual `compose` runs
before `on_mount` -- measured, not assumed: a screen pushed in a test app
reports `__init__ -> compose -> on_mount`. A start recorded at mount would
therefore not exist yet when the line asking for it is drawn, and the card
would need a "no start yet" branch to cover a state that lasts one frame.
Recording it in `__init__` means a card always has a start, at every moment
anything can ask.

The gap between construction and mount is a frame in the board's own use --
`show_focus` builds the card and pushes it in one statement -- so nothing a
person could notice hangs on which of the two is chosen. What hangs on it is
whether the code has a branch in it that no requirement asked for.

The alternative considered was to keep the parameter and let the app pass
`datetime.now(tz)`. Rejected: it leaves two callers able to disagree, which is
exactly the drift `show_focus` was written to prevent, and it keeps a
constructor argument whose only correct value is "now".

**The `since` parameter goes rather than defaulting to now.**

It could be kept with a default, which would let a future caller pass a start
time of its own. Nothing wants to, the spec says the count is the sitting, and
a parameter that must not be used is a trap. The six suites pass four
positional arguments, so removing the fifth touches none of them.

**The clock comes from `datetime.now(tz)` inside the card, read through the
module.**

`main.py` does `from datetime import datetime`, so `main.datetime` is the name
every clock read resolves through, and the suites already move time by
rebinding it to a subclass whose `now` answers what the test wants -- that is
how `t_elapsed` puts the board at a chosen hour and how the parts added
yesterday froze it. Reading the clock in the card rather than in the app does
not move that seam; it is the same module attribute either way.

**The count's end needs no code.**

"The count ends when the card is dismissed" is not a thing to implement: the
card is the count, and dismissing it destroys both. The timer is already
stopped in `on_unmount`. What the spec rules out -- a total that survives the
card -- is ruled out by there being nowhere to put one.

**`worked_for` and the tick interval are untouched.**

Five seconds, and the redraw still happens only when the words change. Both
were chosen last change for reasons this one does not disturb.

## Risks / Trade-offs

**Every card grows a line, including cards in views built for a short
terminal.** -> `t_fit2` exists for exactly this and is run. The line is one
`Static` in the same `Vertical` as the rest, so it costs the same as the
project or deadline line a card already grows when the task has one.

**The three parts added yesterday assert behaviour this change removes.** ->
They are replaced, not adjusted. Adjusting a check whose subject is gone is
how a suite ends up asserting something no one meant; the new parts are
written against the new requirement and the old ones deleted outright.

**A person who opens a card to read a long title now sees a count they did not
ask for.** -> Accepted, and it is the point: the card is titled "Now". The
wording is "since", never "worked", so a count that is really "how long this
card has been up" cannot be read as a claim about effort.

**Removing state that shipped yesterday means the archived change's spec no
longer describes the board.** -> That is what the REMOVED delta is for, and
the archived change keeps its own record of what it did. The main spec is the
one that must be right, and after this merge it is.

## Migration Plan

None. Nothing is stored, nothing is configured, and the board forgets the
removed memory every time it stops anyway. Rolling back is reverting the
commit.
