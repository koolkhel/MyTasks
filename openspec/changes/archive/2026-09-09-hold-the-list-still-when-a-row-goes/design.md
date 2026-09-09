## Context

See proposal.md — Why. What follows is the mechanism, measured rather than
reasoned about.

`repaint` is the one function every view on this board goes through. It
rebuilds the table on each call:

```
  previous = table.cursor_row          # kept for "the task is gone" case
  keep     = self._selected_id
  ...                                  # ordering, filtering, counting
  table.clear()                        # <-- Textual sets scroll_y = 0 here
  for task in tasks:
      table.add_row(...)
  index = the row `keep` is now at, else `previous` clamped
  table.move_cursor(row=index)         # <-- scroll=True by default
```

Textual's own `DataTable.clear()`:

```python
self.cursor_coordinate = Coordinate(0, 0)
self.scroll_y = 0
self.scroll_target_y = 0
```

and `move_cursor(scroll=True)` scrolls the *minimum* distance that reveals the
row. From an offset of zero the minimum is "put it on the last visible line".

Two screenshots of the real inbox, one space press apart, in a 20-row
viewport with the selection on the first mail row (index N):

| | offset | cursor's line |
|---|---|---|
| before | N − 6 | 7 |
| after | N − 19 | 20 |

`N − 19` is `N − 20 + 1`, which is that minimum exactly. So this is not a
subtle interaction; it is the documented behaviour of two calls that were
never meant to meet.

Probed on a running board before deciding anything:

- saving the offset, rebuilding, and restoring it **sticks** — 136 before,
  136 after, cursor back on the same line;
- restoring an offset a shrunken list cannot honour **clamps by itself** —
  600 rows scrolled to 136, rebuilt with 10 rows, gave 0;
- a view change resets the cursor to the previous *row number* clamped to
  the new list. **This probe was wrong about what follows from that**: it
  used a six-row day, where the clamp happens to give row five and the
  offset clamps to zero, so it looked as though a new view already began at
  its beginning. It does not. Measured again on a sixty-row day, entering
  it from row 300 of the inbox lands on its *last* row, and coming back
  carries that number into the inbox as row 20 — an arbitrary task twenty
  lines down. Reported from use before this correction was made, as "it
  jumps strangely when I switch to the inbox view".

  So there is something to guard, and the requirement about changing view
  needs the cursor reset as well as the offset: a different view is a
  different list, and the row number the cursor was on means nothing in it.
  The board remembers which view the table was last drawn for and starts
  a new one at row zero — the same shape as the note pane remembering which
  row it was drawn for.

## Goals / Non-Goals

**Goals:**

- The view moves when the person moves it, and at no other time.
- A row can be dealt with, and the next one dealt with, without the eye
  moving.

**Non-Goals:**

- Changing how `j`, `k` and the arrows move the cursor. Walking into the
  bottom edge scrolls the list under the cursor; that is the toolkit's
  behaviour and it is not what was reported.
- A margin that keeps the cursor clear of the edges (vim's `scrolloff`).
  It would change movement everywhere on the board, and the report was about
  the view moving on its own.
- Rebuilding only the rows that changed. See the trade-off below.

## Decisions

**Save the offset, restore it, and stop `move_cursor` scrolling.**

Three lines around the rebuild, in the one place the rebuild happens.

`scroll=False` on `move_cursor` is belt and braces: restoring the offset
afterwards overwrites whatever it scrolled either way, so the suite cannot
tell the two apart. It is kept because without it the view scrolls and is
scrolled back on every redraw, and because it states the intent where the
call is rather than leaving it to the order of two lines.

The alternative worth naming is the deeper one: stop clearing the table at
all, and update only the rows that changed. That would make this class of
bug impossible rather than corrected, and it would make a 600-row repaint
cheaper than the measured 0.03 s. It is rejected for now because it rewrites
the function every view goes through, for a symptom three lines fix, and the
measurement says drawing is not the problem. It is the right change to make
the day repaints become slow.

**Reveal the row when it is genuinely out of sight, and centre it then.**

A blanket `scroll=False` has a hole: it would leave a cursor a person cannot
see. So the rule is conditional — if the restored view already shows the row,
leave the view alone; otherwise reveal it.

Which case is that? Ticking a *task*, where the ticked task re-sorts down
among the finished ones. The selection moves to the next unfinished task,
which is adjacent, so it is usually still on screen — but "usually" is not a
rule, and the day a filter or an ordering puts it elsewhere the board must
not strand the cursor.

When it must scroll, centring rather than revealing-by-minimum is the whole
point of the change: the minimum is what puts a row on the last line with
nothing after it.

**Say what the check is against, not what it computes.**

The condition is "is the selected row within the visible band" — the offset
and the viewport's height, both of which the table knows. Nothing needs to be
remembered between repaints, which is what makes this safe: no new state, no
staleness, nothing to get out of step with the rows.

**Two entries in the key bar's own name table.**

The bar already translates Textual's key names — `full_stop` to `.`,
`question_mark` to `?`. The bracket keys were bound without being added, so
the bar advertises `left_square_bracket`. It is a dict, not a mechanism.

The alternative was `Binding(..., key_display="[")`, which puts the display
next to the binding. Rejected: the bar's table is where every other
translation lives, and splitting the same job across two places is how one
of them comes to be forgotten — which is exactly what happened here.

## Risks / Trade-offs

**A restored offset could disagree with a list that reordered under it** →
The cursor is placed by identity, not by row number, and that is unchanged;
only the *view* is restored. If the row moved far, the visibility check
catches it and reveals it. The offset itself cannot be wrong in a way that
matters, because nothing is inferred from it.

**Centring on reveal is a second behaviour to hold in mind** → It fires only
when the selection has left the visible band, which a person sees as "the
board found my row for me". The alternative is the bottom-edge pin that
prompted this change.

**This change makes a pre-existing race lose more often** → Holding the view
still shifts the timing of a redraw, and `t_undo1`'s check "the entry
survives the one refusal" turned out to depend on timing: when one action
writes several rows and one write is refused, `forget()` drops the undo entry
if nothing has been applied *at that instant*, while the group's other writes
are still in flight. Forced either way, both orderings behave identically on
the commit before this change — the entry is lost when the refusal settles
first and kept when it settles last — so the defect is in the write
machinery, not here. Measured, the suite fails about 1 run in 5 under a
loaded tier with this change and 0 in 5 without it.

Deliberately not fixed here. It has nothing to do with the list moving, the
fix adds state to the path every write on the board takes, and bundling it
into a scrolling change is how one of the two gets less attention than it
needs. It is recorded in `known_failures.FLAKY` with the signature that
identifies it, and the instrument that proved it is committed as
`tests/probes/t_race.py`, which asserts nothing and prints both orderings.

**The suite has to assert on a scroll offset, which is a toolkit detail** →
Accepted, and it is the only honest instrument: the property is "the view did
not move", and the offset is what the view's position *is*. The suite reads
it through the widget rather than computing it, and it also checks the
consequence a person sees — which row is on the top line, and which line the
selection is on.
