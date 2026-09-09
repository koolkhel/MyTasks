## Context

See proposal.md — Why. What follows is the current shape and the numbers that
decide the approach; everything measured here was measured against Textual
8.2.8 with a throwaway app, not assumed.

Today the pane is one widget:

```
  Vertical#body
    Static#daybar        height 1
    DataTable#tasks      height 1fr        <- gives up rows to whatever is below
    Static#detail        height auto, max-height 40%
```

`height: auto` is the whole problem: the pane is as tall as its text, the
table takes what is left, and so the list's height is a function of the
selected row's note. Nothing else on the board is sized by its content.

Two facts about how this is drawn, both measured:

- `border-top` counts inside the height box, so a pane declared `height: 9`
  shows **8 rows of text**. The requirement is written in rows of text; the
  stylesheet has to be written in the box.
- A scrollable container shows its vertical scrollbar only when its content
  overflows, and hides it when it fits. That is the "there is more below"
  signal the spec asks for, with nothing to build.

Measured across three windows, with an empty note, a one-line note and a
40-line note (the table's height is the number that must not move):

| window | pane text rows | table rows | scrollbar with 40 lines |
|---|---|---|---|
| 80×44 | 8 | 36 | shown |
| 80×20 | 8 | 12 | shown |
| 80×12 | 3 | 8 | shown |

The table's height is identical for all three notes at each window size,
which is the property the change exists for.

## Goals / Non-Goals

**Goals:**

- The list's height is a function of the window and nothing else.
- A note longer than the pane can be read where it is.
- No new mode: every key goes on meaning one thing.

**Non-Goals:**

- Making the pane resizable, or remembering a height between runs.
- Editing in the pane. `n` still opens the note in an editor.
- Wrapping, folding or rendering the note differently. It is the same text,
  in a box of a different size.
- Any change to what a note *is* or where it is stored.

## Decisions

**A scrollable container around the same `Static`, not a scrollable `Static`.**

The pane becomes `VerticalScroll#notes` holding `Static#detail`, and the text
goes on being written to `#detail` exactly as now.

The alternative — making the detail widget itself the scrollable thing — reads
more simply and is rejected for one concrete reason: `#detail` is what the
suites query, and two of them assert on `query_one("#detail").render()`. An id
is an interface here. Keeping the text on the widget that has always held it
means the change is invisible to everything that reads it, and the container
is a new name for a new thing.

The container must be told not to take focus. A scrollable container is
focusable by default, and a focusable pane would take the arrow keys away from
the list the moment it was tabbed into — the mode this change is meant not to
introduce.

**Eight rows of text, capped at 40% of the window.**

`height: 9; max-height: 40%` — nine because the border is in the box.

Fixed against the content is the requirement; fixed against the window as well
would be worse than what we have on a 12-row terminal, where eight rows of
note would leave a list of four. The cap keeps the pane proportionate there
and never binds on a window anyone reads mail on: it takes effect below about
22 rows.

Eight rather than a share of the window because "predictable" is the whole
point, and a person who has learnt where the list ends should find it there on
every terminal they open. It is a stylesheet constant, and one line to change
if it turns out to be wrong.

**A page at a time, less one line, by `[` and `]`.**

`scroll_page_down` moves by exactly the pane's height, which drops the line
being read off the top. Scrolling by the height minus one keeps one line of
overlap, which is what a pager does and for the same reason.

`[` and `]` were chosen over the alternatives on the board's own stated
grounds: plain characters cannot be swallowed by a terminal the way a modified
arrow can, and both already have Cyrillic twins in the key table
(`х` and `ъ`), so `keys()` handles them with no new entry. They are also
adjacent under one hand and unbound today.

`page up`/`page down` were considered and rejected: the table wants them for
the list, and taking them would be a worse trade than two new characters.

Scrolling is bound at the app, not at the pane, so it reaches the pane while
the table keeps focus — verified: after `]` the pane's offset moved and the
cursor did not, and `down` still moved the cursor afterwards.

**Reset the offset when the selection changes, and only then.**

The obvious place is `update_detail`, which is where the text is written — but
that runs on every repaint, and repaints happen for reasons that have nothing
to do with the person: a mail load returning, a write confirming, a timer
noticing an event has ended. Resetting there would yank a half-read note back
to the top while somebody was reading it.

So the pane remembers which row it was last drawn for, and returns to the top
only when that changes. A repaint of the same row leaves the offset alone.

**The scrollbar is the indication, and the only one.**

No "…more" marker, no line count in the corner. The scrollbar appears exactly
when there is more and disappears exactly when there is not, it is what every
other scrollable thing on a screen uses, and it costs nothing.

Its one cost is a column: when a note overflows, the text has one column less
and rewraps. The list does not move, which is what was asked for, and a
rewrapping note in a pane whose scrollbar has just appeared is legible as
cause and effect.

**Escaping the note in the focus card, in this change.**

The card draws `Static(note)` where the pane draws `Static(escape(note))`, so
a note containing `[bold]` is characters in one place and styling in the
other. It is a one-word fix in the same region of the same file, and the spec
now says the two places agree. The proposal flags it as strikeable: it is a
defect of its own, and if it should be its own change then the requirement
sentence and its scenario come out together.

## Risks / Trade-offs

**Eight rows is a guess about somebody else's screen** → It is a stylesheet
constant and the suite pins the *behaviour*, not the number: that the height
does not vary with the note, and that the cap takes over on a short window.
Changing eight to ten is one line and no test rewritten.

**The pane is eight rows even when nothing is selected, or the note is empty**
→ Accepted, and it is the point: an area that collapsed when empty would move
the list exactly as it does now. Empty rows below a short note are the price
of the list holding still, and they are quiet.

**A note that overflows rewraps by one column when the scrollbar appears** →
Accepted. The alternative is a permanently reserved column, which would waste
it on every note that fits — the common case.

**`[` and `]` are two more keys to know** → They go in the key bar and the
help overlay, and they do nothing surprising if pressed with nothing to
scroll. A person who never learns them is exactly where they are today,
except the list no longer moves.
