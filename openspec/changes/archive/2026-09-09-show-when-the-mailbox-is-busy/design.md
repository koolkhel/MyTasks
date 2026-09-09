## Context

See proposal.md — Why. What follows is what shapes the approach, measured
where it could be.

The board has two kinds of slow work and reports only one of them:

```
   store writes                      mailbox operations
   ------------                      ------------------
   submit_write -> _pending queue    review()  -> file_away worker
   drain per task id                 undo      -> put_back worker
   status line: "N saving"           nothing on screen at all

   ~200 ms a write                   13 s for a row of one message
                                     25 s a message for a folded row
                                     one at a time, behind _mail_gate
```

Where the time goes, measured against the real gateway: finding each
message's number is a search at ~2 s, the move is one request at ~1 s, proving
the folder no longer holds them is one flags fetch at ~0.2 s, and confirming
each arrival is a search of a 20,749-message archive at **11.5 s a message**.
That last one is the cost, and it is per message, so a row of nineteen — the
largest currently in the inbox — is about eight minutes.

Those are one sitting's numbers, and the gateway is not that consistent: see
the last risk below, where the same single message took anywhere from 13 s to
119 s.

Two existing pieces of the board are the pattern for this:

- the clock, whose requirement already says that keeping itself current must
  not redraw the list;
- `tests/local/`, ignored by git with a line in `.gitignore` saying why —
  what a live run records about one account.

And this machine already has a mail service that logs the way this should:
`~/Library/Logs/mail-sync.log`, one line per run,
`2026-09-08T14:53:16Z OK synced in 15s, 0 new message(s)`.

## Goals / Non-Goals

**Goals:**

- Answer "has what I ticked landed?" at a glance, without reading anything.
- Make a failure survive the notice that would otherwise paint over it.
- Leave a record a person can read afterwards, or paste into a bug report.

**Non-Goals:**

- Any view of the log inside the board.
- Any report on the external sync. Whether the local mirror has caught up is
  a different question with a different answer, and its interval is
  configured elsewhere.
- Counts on screen. One cell, three states, no numbers.
- Progress *within* one operation. The board knows how many messages a row
  holds and could show three-of-nineteen, but that is a second design and the
  question asked was whether anything is in flight.

## Decisions

**One count, incremented and decremented by the board itself.**

Not by asking Textual how many workers are running: the board already counts
store writes in its own structures rather than asking, the worker manager
offers no count by group, and a number the board owns is a number a suite can
drive.

The count is the whole state behind the in-flight half of the indicator. It
goes up where a review or an undo is launched and down on every path where
one ends. Those paths are the risk, and there are six: confirmed, unconfirmed,
already archived, in neither place, gateway unreachable, and given up because
the board is closing. A missed decrement leaves the indicator saying "wait"
for the rest of the session, which is worse than showing nothing — so each of
the six is a check rather than a reading of the code.

**Glyphs chosen for width, not only for looks.**

Every candidate was measured. `◐` and `◑` are width-*ambiguous* — a
CJK-configured terminal may render them two cells wide — while `◓` and `◒` are
not, so a spinner mixing them would make the bar's right edge jitter by a cell
between frames. The four arcs `◜ ◝ ◞ ◟` are all unambiguously one cell, and
they read as rotation. `✓` and `✗` are the same width class.

`✗` rather than `☒`, and `✓` rather than `☑`: those two are already the
board's cancelled and ticked task marks, and reusing them would say the wrong
thing in the corner of the eye.

**The animation is its own timer, running only while there is work.**

Four frames at about four a second. Started when the count leaves zero,
stopped when it returns — so nothing moves on screen while nothing is
happening, which is what the clock's requirement asks of anything that
animates here.

It rewrites the day bar's one `Static`, never the table. The day bar is
rebuilt by the same function a repaint calls, so the indicator is drawn from
the same place whichever reason brought it about, and animating costs one
widget update.

**The failed state is sticky, and reload is what clears it.**

Clearing it on the next success would paint over the fault this exists to
surface. Clearing it on a keypress needs a key, and there is no natural one:
`r` already means "start again", which is exactly the gesture that should
mean "I have dealt with that". So the flag is set on any failure and cleared
by an explicit reload, or by restarting.

The alternative considered was an unread-marker for a log view, cleared by
opening the log. That was the design until the log was settled as off-screen;
with no view to open, reload is the only gesture that already means the right
thing.

**Quitting confirms through the dialogue that already exists.**

`Confirm` is what the board uses before deleting. Reusing it means the
question looks like the board's other questions and answers to the same keys.

The alternative was to let quitting proceed and simply say what was abandoned.
Rejected: by then the board is gone, and the message with it.

**The log is a module, not a function on the app.**

The board, the gateway client and the suites all need to write in one format,
and the format is the thing that must not drift. A module also means the log
can be written from a worker thread without reaching into the app.

Its path is resolved against the board's own files, not the working
directory: the launcher happens to change directory into the repository, but
`main.py` can be run from anywhere, and a log that lands wherever a person
started from is a log nobody finds twice.

`logs/mytasks.log`, and `logs/` in `.gitignore` with the reason beside it, so
anything added later needs no second line. It holds identities and folder
names from a real account; the repository is shared.

**Best-effort, and silent about itself.**

Every write is wrapped. A missing directory, a full disk or a permission must
not fail a review, and must not produce a notice either — a person told their
log could not be written, in the middle of clearing a queue, learns nothing
they can act on. The suite checks that an unwritable log changes nothing at
all.

## Risks / Trade-offs

**A missed decrement makes the indicator lie in the worst direction** → Six
paths, six checks, each driving the real code through a substituted gateway
rather than calling the decrement directly. This is the one thing in the
change that could be worse than not doing it.

**A sticky failure mark becomes noise once it has been read** → Accepted, and
bounded: `r` clears it, and `r` is a key already pressed often. The
alternative — clearing on success — loses the failure among nine successes,
which is the fault being fixed.

**Four frames a second is motion in the corner of the eye** → Only while work
is in flight, which is when motion is the point. When the board is idle
nothing moves, which is the rule the clock's requirement already sets.

**A log without subjects is harder to read than one with them** → Accepted
deliberately. The identity is what the gateway is addressed by, so it is what
a person searches on to find the message again, and it is the piece least
costly if the file is ever shared. The board's own notices name the row on
screen, where it is already visible.

**One cell cannot say how long the wait is** → A row of nineteen looks the
same as a row of one. Counts were considered and dropped as asked; if the
wait turns out to matter, the count already exists behind the indicator and
showing it is a one-line change.

**The wait is far more variable than the numbers above** → Those figures —
13 s for one message, 25 s a message folded — were measured in one sitting.
Read back off the board's own log after a day of real use, and measured again
while building this: one message has taken **13 s, 32 s, 91.7 s and 119 s**
on the same account, depending on what else was talking to the gateway. The
help text says "ten seconds or more", which stays true; the design's single
numbers do not, and the spread is the strongest argument for the indicator
existing at all. There is no predicting it from the row, which is also why
showing a count would not have told a person much.
