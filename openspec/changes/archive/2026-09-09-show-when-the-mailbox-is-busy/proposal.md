## Why

Ticking a mail row starts work that takes 10 seconds or more and shows
nothing. Measured against the real gateway: about 13 s for a row of one
message and 25 s a message for a folded row, dominated by the per-message
search of a 20,749-message archive that confirms each one arrived. Reviews
queue behind a single lock, so ticking ten rows in a minute leaves nine of
them not yet started.

The board already reports its other slow work — the status line says how many
task-store writes are in flight — and says nothing at all about the mailbox,
which is the far slower of the two.

Two things follow from that silence. Quitting mid-queue abandons every review
that had not started; nothing is lost, because those rows never moved
anything, but they come back on the next start looking exactly like the
mirror-lag symptom that took an afternoon to diagnose. And a review that
fails is announced in a sticky notice that the next review's notice
overwrites, so a failure among ten can pass unseen.

## What Changes

- A one-cell indicator at the right of the day bar, on every view, with three
  states: nothing in flight and nothing wrong, an operation running, and
  something has failed since the last reload.
- Quitting asks first while work is in flight, naming how much, through the
  confirmation the board already uses for deleting. With nothing in flight it
  quits at once, as now.
- A log file of everything the board does to the mailbox — off screen, in the
  shape this machine's other mail service already logs in: an ISO-8601 UTC
  stamp, a level, a line. It is for reading after the fact, not on screen.
- The log records outcomes, folders, counts, durations and message
  identities. It does **not** record subjects or senders: it is a durable file
  outside the mail store, and an identity is what the gateway addresses a
  message by, so it is what a person would search on anyway.
- The log lives in the repository directory and is ignored by git, beside the
  precedent already there for what a live test run records about one account.

## Capabilities

### New Capabilities

None. This reports on work the board already does.

### Modified Capabilities

- `task-board`: three new requirements — the indicator, the guard on quitting,
  and the log. Plus one modification: the requirement that the board keeps no
  record of what it has promoted says it "holds no state of its own on disk",
  and a log is a file on disk. The distinction that matters is that nothing
  reads it back and no row depends on it, which the requirement should say
  rather than leave to be inferred.

## Impact

- `main.py`: a count of gateway operations in flight, incremented where one
  starts and decremented on every path where one ends; the day bar's right
  edge; a timer that runs only while the count is above zero; a quit action
  that confirms; a failure flag cleared by reload.
- A new module for the log, so that the board, the gateway client and the
  suites all write through one place and one format.
- `.gitignore`: one line, with the reason beside it.
- `tests/`: a self-contained suite against a substituted gateway, driving
  every path on which an operation can end — confirmed, unconfirmed, already
  archived, in neither place, gateway unreachable, and given up because the
  board is closing — since a count that failed to come down would leave the
  indicator saying "wait" forever.
- Nothing outside the board: no store, no mailbox, no network. Every row in
  the new suite is generated.
