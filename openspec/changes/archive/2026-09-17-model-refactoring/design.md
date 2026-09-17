## Context

See proposal.md — Why. What follows is where the boundary actually falls,
measured rather than guessed.

Of the 33 methods that take part in drawing the board, six touch a widget and
27 do not:

```
  touch a widget                     touch nothing (648 lines, 27 methods)
  ------------------------------     -------------------------------------
  repaint        206  query/clear/   row_for 114   patched 20   belongs 24
                      add_row/       matches 13    is_work 24   is_green 7
                      move_cursor    is_tracker 3  is_mail 3    is_event 3
  fit_columns     19  query          tracker_rows 32  event_rows 43
  hold_view       29  scroll_to      mail_rows 46     place_events 41
  update_daybar   18  query_one      place_issues 27  ended_count 8
  update_detail   27  query_one      has_ended 10     window_reason 10
  set_status      16  query          shortened 12     marked_cell 15
                                     title_width 17   orders_manually 9
                                     late_colour 16   _markup_title 19
                                     _mail_when 12    forget_gone_marks 41
                                     mail_fold 38     apply_window 41
```

And inside `repaint` the two halves are layered, not interleaved:

```
  3648  table = query(DataTable); fit_columns()          VIEW    30 lines
  3659  forget_gone_marks()                              model
  3666  previous, was_at, keep = cursor, scroll, id      VIEW (reads table)
  ....................................................
  3668  sort, six sources, two filters, place, count     PURE    77 lines
  ....................................................
  3745  table.clear(); add_row(row_for(t)) for each      VIEW    33 lines
  3748  which index to select, where to hold the view    pure decision,
                                                         widget-shaped
  3778  _drawn_for, _ended_shown                         model    4 lines
  3782  update_daybar(); update_detail()                 VIEW     2 lines
  ....................................................
  3789  bits = [...]  eleven conditional fragments       PURE    52 lines
  3843  set_status(" · ".join(bits))                     VIEW
```

The board has exactly **one** `table.add_row` and **one** call to `row_for`,
and `repaint` has 24 callers. The widget side is already a funnel.

What constrains the shape is the instrument. The suites read the application
directly — `app.tasks` 452 times, `app._selected_id` 74, `app.hidden_work` 20,
`app.repaint()` 97, `app.row_for()` 45, `app.is_tracker()` 41, `app.is_mail()`
40, `app.apply_window()` 21 — and 58 checks read the status line out of
`#status`. Those suites are what will say whether this went cleanly, so not one
of those names may move.

## Goals / Non-Goals

**Goals:**

- One place decides what is drawn; it can be asked without a terminal.
- `TaskApp` keeps every name and every attribute the suites reach for.
- Byte-identical behaviour: same cells, same counts, same status text, same
  cursor row, same scroll.

**Non-Goals:**

- Moving state ownership. The 61 attributes stay on `TaskApp`; only the
  deciding moves.
- The write pipeline and the per-source state (the other two seams).
- Making `main.py` small. It goes to about 5,170 lines.
- Changing the suites (see proposal.md — What Changes).

## Decisions

### A per-paint object, not a long-lived model

`board.py` defines `Board`, built from the values it reads, and thrown away
after each paint:

```python
board = Board(base=self._base, pending=self._pending, position=self.position,
              reference=self.reference, tz=self.tz, projects=self.projects,
              marked=self.marked, marked_rows=self._marked_rows,
              searching=self.searching, hiding_work=self.hiding_work,
              work_project=self.work_project, green_tag=self.green_tag,
              tracker_issues=self.tracker_issues, events=self.events,
              mail_threads=self.mail_threads, window=self.working_window,
              width=self.title_width, ...)
painting = board.paint(previous=table.cursor_row, scroll=int(table.scroll_y),
                       keep=self._selected_id, drawn_for=self._drawn_for)
```

Constructing it is attribute copying, and `repaint` already rebuilds everything
derived on every call by design — its own docstring says so, because an
optimistic view and a fetched one must not be able to disagree.

*Alternative rejected: `Board` owns the state and `TaskApp` delegates.* That is
the real MVVM shape and it is a redesign, not an extraction: the 61 attributes
are written from 34 action methods and the whole write pipeline, so moving
ownership drags all of them across in one commit. It is also unverifiable in
the way that matters — the suites read those attributes off the application 500
times, so they would have to change in the same breath.

*Alternative rejected: pass the application into `Board`.* Then `Board` reads
`app.<anything>` and nothing has been separated; the import graph would say
otherwise while the coupling stayed exactly where it was.

### What crosses the boundary

`paint()` answers one value:

```python
@dataclass(frozen=True)
class Painting:
    rows:    list[Task]               # becomes app.tasks
    cells:   list[tuple[str, ...]]    # row_for applied, in draw order
    status:  str                      # the " · " line, already joined
    cursor:  int | None               # which row to select
    scroll:  int                      # the position to hold
    marks:   list[str]                # the marks that survive
    counts:  Counts                   # shown_issues/events/mail/messages,
                                      # hidden_work, hidden_by_search,
                                      # past_due, ended
```

`TaskApp` copies those onto itself under the names they have now, so
`app.tasks`, `app.past_due`, `app.hidden_work` and the rest go on answering
what they answer today.

### What inverts

1. **Width.** `title_width` is the terminal's width less what the other columns
   cost, read from the application's own `size`. The application measures, then
   passes the number in.
2. **The theme's colour.** `late_colour` resolves `text-error` from the theme
   the application is running. Same shape as the width: the application resolves
   it, `Board` is told.
3. **The present.** Found during the work rather than planned: `has_ended` and
   `_mail_when` read the clock, and six places in the suites steer the board's
   clock by patching `main.datetime` — a clock read from inside `board.py` would
   have escaped every one of them, which `t_elapsed` said at once (34/36). So
   the application reads the clock and hands the instant over. It is better
   besides: one paint now sees one instant rather than a slightly different one
   per row.
4. **Cursor and scroll.** The restoration reads `table.cursor_row` and
   `scroll_y`; those become arguments, and the chosen index and the position to
   hold come back as results.
5. **Derived state.** `repaint` assigns eleven attributes today. They come back
   in the `Painting` and are assigned in one place.

The first three are exactly the "measurement given, not fetched" clause of the
new requirement, and they are why the requirement is phrased that way rather
than forbidding framework knowledge outright.

### `apply_window` is not composition and does not move

Listed for the move when this was planned, and wrong: it sets the mode from the
working window and calls `repaint` when the answer has changed. That is a state
transition the application performs, not a question about what is drawn. What
the composition needs from it is `window_reason`, the words the status line
says, and that moves on its own.

### Pruning marks becomes a question, not a side effect

`forget_gone_marks` mutates `self.marked` and `self._marked_rows` in the middle
of `repaint`. Its decision — which marks the shown view can say are gone — needs
`_base`, `mail_threads`, `belongs`, `is_event`, `is_tracker` and `shows_mail`,
all of which are the `Board`'s. So the `Board` answers the surviving marks in
the `Painting`, and `TaskApp` performs the assignment.

It keeps its position in the order: before anything is counted, because a mark
on a row that has gone must not reach the count.

### The application keeps the names, as delegates

Each of the twelve methods the suites call stays on `TaskApp` as a one-line
delegate that builds a `Board` and asks it. That costs a construction per call
in the suites and nothing in the product, where the composition path builds one
`Board` and uses it throughout.

### Order of work, and the one severable step

1. `row_for` and the formatting helpers — one call site, easiest to prove.
2. The composition block — the 77 lines that produce the rows and counts.
3. The status line — 52 lines of fragments producing one string, guarded by 58
   checks that read `#status`.
4. The cursor decision — which index to select and where to hold the view.

Step 4 is severable. It is the fiddliest logic in the file: its comment records
a measurement on a 600-row inbox, where ticking row 7 of 20 scrolled the view
thirteen rows and left the cursor on the last visible line, and
`openspec/specs/task-board/spec.md` spends eight scenarios on what it must do.
If it resists, leaving it in the view costs the change nothing that the other
three steps deliver — the eight suites that would stop needing an application
call `repaint`, `row_for` and `place_events`, none of which is step 4.

### Naming

`board.py`, class `Board`, result `Painting`. The module names what it is about
rather than the pattern it is an instance of; every other module here is named
for its subject (`mail`, `ical`, `tracker`, `journal`, `singularity`).

## Risks / Trade-offs

- **A derived attribute is left unassigned.** → It breaks loudly: `app.tasks`
  alone is read 452 times by the suites.
- **A count is taken at the wrong point.** `shown_issues` is assigned three
  times inside `repaint` as the filters narrow it, and `hidden_work` and
  `hidden_by_search` are each counted across all four sources *before* any is
  dropped. Moving a count one line changes a number nobody would notice. → The
  status line is asserted 58 times, and every count appears in it. Step 3 is
  where that is proved, and it comes after the composition step deliberately.
- **Source order is load-bearing and undocumented outside comments.** Events are
  placed among tasks, issues go in as a block where the unfinished work ends,
  mail is appended last and never sorted in — and each of those is filtered
  before placing, because a source filtered after placing is a source the work
  filter cannot reach. → The comments in `repaint` state each rule and its
  history; they move with the code rather than being summarised.
- **The cursor step breaks a redraw rule subtly.** A view that scrolls under the
  hand is the exact failure *The list stays where it is when it is redrawn*
  exists to prevent, and it is not visible in a count. → Eight scenarios and the
  suites that drive them; and step 4 can be dropped.
- **Delegates hide a cost.** A suite calling `app.row_for` 45 times builds 45
  `Board`s. → Irrelevant at that scale, and the product path builds one.

## Migration Plan

Each step: move the code, leave a delegate, run the self-contained tier, and
require it unchanged — 52 suites, the same check counts, no failures. The
status line and the cursor have their own guards named above.

Rollback is per step, because each one is a move plus a delegate and nothing
else; a step that will not reconcile reverts without disturbing the ones before
it.

## What it came to

Measured after the four steps, against the predictions above:

| | predicted | actual |
|---|---|---|
| `main.py` | ~5,170 | **5,148** |
| `TaskApp` | ~3,700 | **3,797**, 165 methods |
| `board.py` | ~780 moved | **1,250**, of which `Board` is 989 over 33 methods |
| `repaint` | ~30 lines | **69** |

`board.py` is larger than the 780 lines predicted because the prediction
counted only the methods: the row vocabulary -- 37 constants and the four
labels built from them, with their comments -- moved too, since the module
that decides what a row says is where the words a row is made of belong.

`repaint` is 69 lines rather than 30 because eleven of them are the
assignments that hand the answer back to the application, and a dozen more are
the comments that were already there about the scroll and the order things
happen in. Every line of it is now either a widget call or an assignment from
the answer; none of it decides anything.

## Open Questions

None that change the specs, the approach or the tasks. Step 4's fate is a
decision the work itself will settle, and the tasks say what to do either way.
