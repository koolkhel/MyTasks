## Context

See proposal.md — Why.

What the board already has:

- `action_start_workspace` ends with a status line and nothing else. It is
  already `async` and already pushes a screen and waits for it (the version
  prompt), so pushing one more at the end costs it nothing structurally.
- `TaskFocus(task, when, project, tz)` is the card, opened by
  `action_focus_task` with `push_screen`. It is a modal and it writes nothing.
- The app already runs a once-a-minute heartbeat, `set_interval(
  ELAPSED_CHECK_SECONDS, self.each_minute)`, and `_spinner = self.set_interval(
  MAIL_SPIN_SECONDS, self.spin)` is the precedent for an interval that is
  started and stopped rather than run for the life of the app.
- `tests/stub/t_star2.py` constructs `TaskFocus` directly with four arguments.

## Goals / Non-Goals

**Goals**

- The card opens on what was just started, and says since when.
- The same card, opened any other way, says the same thing about the same row.
- Nothing stored, nothing configured, no new dependency.

**Non-Goals**

- Accumulating time across sittings, days or restarts. Explicitly out: the
  spec says the board forgets, so that a later change adding a record has a
  clean thing to add rather than a half-kept one to correct.
- Timing anything but a workspace. The key that latches a task until it is
  done is a separate change and will set the same field when it lands.
- Pausing, resuming, or editing the start. The count answers "since when",
  and a count a person can adjust is a record, which this is not.

## Decisions

### The app holds one pair, not a map

One field: what is being worked on, and when that began. A map from row to
start would let two things be "in progress", which the board would then have
to draw and explain, and which is not true of a person anyway. One pair makes
"start work on something else" a plain assignment and makes the spec's "one at
a time" true by construction rather than by discipline.

The name must not collide with the framework: `App` and `ModalScreen` were
checked for `working`, `started`, `since`, `work_started`, `working_since` and
`shown_since`, and none of them exists on either. This board has been bitten
twice by that — `_closing` is Textual's own message-pump flag and a
`mail_failed` attribute shadowed a method of that name — so the check is part
of the work rather than a formality.

### Wall-clock, not a monotonic count

The card has to say *when* work began, so the start is kept as an aware
datetime and the elapsed time is the difference from now. A monotonic clock
would survive a system clock change and cannot answer "since when", so it
would have to be kept beside the datetime for a case this change does not
promise anything about. One value, and a clock change moves the count — said
in the design rather than defended in code.

### The card refreshes itself

The card owns an interval while it is open, rather than the app reaching into
a screen it has pushed. The app's minute heartbeat exists for the day's own
reasons and is the wrong thing to hang a modal's repaint on: a card opened at
:59 would otherwise jump a minute a second later and then sit still for
fifty-nine.

Started on mount, stopped on unmount, as the mail spinner's is.

### The new argument is optional

`TaskFocus` gains one optional argument. `t_star2.py` builds the card directly
with four, and a suite that has to be edited to keep passing is a suite that
was testing the constructor rather than the card. It keeps passing unchanged.

### `action_focus_task` decides, the card only draws

The key that opens a card knows the selected row; the app knows what is being
worked on. Comparing them is the app's job, and the card is handed either a
start or nothing. The card then has one rule — draw the line if you were given
one — and no knowledge of what is being worked on, which is what keeps "opened
by either key" true without either key knowing about the other.

### Wording

`since 14:03 · 42m`, beside the facts the card already shows. "Since" rather
than "worked" because the board is counting the clock and not the effort, and
the spec asks for wording that says so. Under an hour it reads in minutes;
past an hour, hours and minutes.

## Risks / Trade-offs

- **The count is wall-clock and will flatter a long lunch** → the wording says
  "since", and the spec forbids presenting it as effort. A count that tried to
  be honest about effort would need input the board does not have.
- **A restart loses the start silently** → the spec makes forgetting the
  promise rather than a defect, so a person who restarts sees no count rather
  than a wrong one. The alternative, writing it down, is the change that would
  also have to decide what an unclosed start means the next morning.
- **A system clock change moves the count** → accepted, and recorded here. The
  board is not a timekeeper of record.
- **Two ways to reach the card, one of them new** → the card's own behaviour is
  unchanged; both keys hand it the same thing. The suites check both paths
  rather than assuming they agree.

## Migration Plan

None. Nothing is stored, nothing is configured, and removing the change
removes the line.
