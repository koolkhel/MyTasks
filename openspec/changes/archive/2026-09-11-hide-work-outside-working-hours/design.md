## Context

See proposal.md - Why. The requirements are in
`specs/task-board/spec.md`; this document only explains how they are met.

What exists today, read from the source rather than assumed:

- `self.hiding_work` is a plain boolean set in `__init__` and flipped by
  `action_toggle_work`. `repaint` reads it three times -- once to count the
  rows the mode removes, once to filter four lists, and once again in the mail
  pane's own summary.
- `set_interval(ELAPSED_CHECK_SECONDS, self.recheck_elapsed)` already runs a
  sixty-second tick whose whole design is to redraw only when something
  actually changed, because a redraw nobody asked for moves the list under the
  hand working it.
- Removing the selected row is already solved: `repaint` keeps the scroll
  position (`scroll=False`, then `hold_view`) and moves the selection to the
  nearest surviving row. Pressing the key already does this.
- `singularity.load_work_project` is the pattern for a personal setting: read
  from the environment at run time, absent and blank both meaning "not
  configured", and reported rather than raised.

## Goals / Non-Goals

Goals:

- The clock sets the mode; the key overrules it until the next crossing.
- A crossing is the only unbidden movement. Between crossings nothing moves.
- The rule is a pure function of a moment, so a suite can ask it about any
  hour of any day without waiting for one.

Non-Goals:

- No holiday calendar. Days of the week only.
- No per-source exemption. Mail and tracker rows go with the work tasks; a
  source that escaped the filter is exactly what the existing requirement
  forbids.
- No persistence. The mode still does not outlive the board.
- No second key and no third state.

## Decisions

### The mode stays a stored boolean, recomputed at known moments

`hiding_work` remains a plain attribute. Two attributes join it: what the
window last said, and whether a press is overruling it.

```
    _window_hides : bool | None   what the window said when last asked
    _work_override: bool | None   None = follow the window
    hiding_work   : bool          what repaint reads.  Unchanged in type.
```

One method sets all three from a moment. It is called at startup, on the tick,
and after a press.

Alternative considered: make `hiding_work` a property that reads the clock on
every access. Rejected for two reasons. `repaint` reads it three times and must
see one answer, and a property reading wall time makes every redraw depend on
when it happened -- which is the thing hardest to test and easiest to get
subtly wrong. Recomputing at named moments also matches `_ended_shown`, which
is the same shape for the same reason.

### A press lapses by the window changing its answer, not by a stored deadline

On each tick the board asks the window about now and compares with
`_window_hides`. Same answer: return, change nothing, as `recheck_elapsed`
does. Different answer: record the new one, clear the override, set
`hiding_work` from the window, repaint.

Nothing stores when a press expires. The comparison is the expiry.

This gives the invisible lapse for free, and it is worth writing down why. A
press sets the mode to the opposite of what is in force. With no earlier press,
what is in force is the window's own answer, so the press disagrees with the
window. When the window later flips, its new answer *is* what the press was
saying -- so clearing the override changes nothing on screen. Press twice and
you agree with the window again; the override is then indistinguishable from
no press, and the crossing moves rows normally. Both are in the spec and both
fall out of this one comparison.

Alternative considered: store a deadline ("this press lasts until 08:00").
Rejected: it needs the next boundary computed, which needs the weekend rule
applied forwards over a gap of days, and it reintroduces every off-by-one the
comparison avoids.

### Polling the clock, not scheduling the boundary

The check goes into the existing sixty-second tick rather than a one-shot
timer set for 18:00.

A laptop closed at 17:00 and opened at 19:00 must come back with work hidden.
A timer scheduled for a wall-clock instant does not reliably fire across a
suspend; reading the clock on the next tick after waking is correct by
construction. The cost is that a crossing lands up to sixty seconds late, which
the spec states outright.

It also means one timer rather than two. `recheck_elapsed` gains a sibling call
in the same tick; neither redraws unless its own fact changed.

### The rule is a pure function of a moment

```
    singularity.load_working_window(env) -> Window | None   config, once
    Window.hides(moment)                 -> bool            pure
```

The board's method takes the moment as an argument, defaulting to
`datetime.now(self.tz)`. A stub suite hands it a Friday at 18:01 or a Saturday
at noon directly, exactly as `t_elapsed` calls `recheck_elapsed()` itself. No
clock is frozen and nothing is monkeypatched, which matters here because every
existing stub suite builds its fixtures from the real `datetime.now` and would
be poisoned by a global clock patch.

### Configuration: two keys, beside WORK_PROJECT

```
    WORK_HOURS=08:00-18:00
    WORK_DAYS=mon-fri          # optional; mon-fri when absent
```

Both read by `singularity.py` beside `load_work_project`, for its reason: a
person's working hours are theirs, and `.env` is the one place already outside
version control.

`WORK_HOURS` absent means the feature is off and the board behaves exactly as
today. That makes the whole change opt-in and leaves every existing scenario
for the key true on an unconfigured board.

Days are three-letter English abbreviations, a comma list or a range, case
insensitive; a range may run round the end of the week, because a working week
that starts on Sunday is somebody's ordinary one. Hours are `HH:MM-HH:MM`
within one day; an end not later than the start is unreadable rather than
wrapped around midnight, because a window that wraps has no single "day outside
the window" and the weekend rule stops making sense.

The two ends are held as minutes since midnight rather than as `time` values,
so that `24:00` can be an end. Without it the last minute of every day falls
outside every window that can be written, `18:00-24:00` cannot be said at all,
and a suite asserting on an all-day window is wrong one run in fourteen
hundred -- which is the class of flake this repo has already been red for.

Alternatives considered: separate `WORK_START`/`WORK_END` keys (two more keys
for the same information); minutes since midnight (unreadable in a file a
person edits by hand).

The parsing is a pure function of two strings, with the reader a thin wrapper
that fetches them. That split is not tidiness: python-dotenv finds `.env` by
walking up from `singularity.py`, so a suite that empties the environment does
not hide the real one -- four suites here were mistaken for self-contained for
exactly that reason. A parser taking strings can be exercised in the
self-contained tier without going near a file at all.

### An unreadable window is reported once and then behaves as absent

The board opens. The existing status-notice path says the setting could not be
read. The tick does not repeat it -- a complaint every sixty seconds about a
setting nobody can fix from inside the board is noise, and it would overwrite
the counts forever.

### The status line names the boundary, and only when the clock is the reason

`repaint` already appends `f"{self.hidden_work} work hidden"`. It gains a
reason when `_work_override is None` and the window is what hid the rows:
"after 18:00", "before 08:00", "outside the working week". When a press hid
them, the line is exactly what it is today. When work is shown the board says
nothing, as the existing requirement has it -- the person pressing the key
knows they pressed it. The daybar's own short note carries the same reason,
because that is the line that speaks when the mode hides nothing at all.

The window returns the phrase rather than a token the board turns into one, so
the reason it gives and the reason it acts on cannot drift apart.

That reason is also what the tick compares on, not the bare hidden/shown side.
A Friday evening and the Saturday after it are both hidden but for different
boundaries, and comparing on the side alone would leave the board giving
Friday's reason all weekend. Comparing on the reason costs one extra redraw a
week, at a midnight.

## Risks / Trade-offs

- **A person who works past the window presses the key every evening.** This
  turns a stop signal into a daily chore. → Mitigation is the configuration
  itself: the window is whatever hours are wanted, and leaving `WORK_HOURS`
  unset restores today's board exactly.
- **The mail queue disappears in the evening**, because all mail is work. This
  is the largest single effect and the most surprising. → Not mitigated by
  design: exempting a source is what "no source is reached only by being
  marked" exists to forbid. It is stated in the spec so it cannot be a
  surprise twice.
- **A crossing lands up to sixty seconds late.** → Accepted, and stated in the
  spec, rather than shortening a tick that exists precisely to be cheap.
- **A crossing repaints while a dialogue is open.** → No new exposure:
  `recheck_elapsed` already repaints from the same tick under the same
  conditions. Worth a check, not a design change.
- **A new attribute colliding with Textual's own.** Two collisions have landed
  here before, one of which stopped a running app accepting messages. →
  `hasattr(App, name)` and a grep for `def <name>(` before naming anything, as
  a task.

## Migration Plan

None needed. The change is inert until `WORK_HOURS` is set, and removing that
line restores the previous behaviour exactly. Nothing is written, nothing is
stored, and no task is touched.

## Open Questions

None. The window's shape, the lapse rule, the weekend default and the reporting
are all settled in the specs.
