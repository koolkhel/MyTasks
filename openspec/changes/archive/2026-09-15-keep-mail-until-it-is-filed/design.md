## Context

See proposal.md for motivation and for the measurements this rests on.

What shapes the approach is that the board has two views of one mailbox and
they are not the same view:

```
   reading                              writing
   -------                              -------
   local maildir mirror                 the mail account, over EWS
   filled by a sync tool                exchangelib, gateway.py
   no network, no credentials           moves and flags
        |                                     |
        |  what is in the folders             |  moves messages out
        +-------------------> the board <-----+
```

The board decides what is in the queue from the mirror, and changes the account
directly. Nothing keeps them in step but the sync tool, and the lag between
them is already accounted for elsewhere in the board -- the session-long set of
identities a confirmed review will not show again exists for exactly that
reason, and this change does not disturb it.

Three facts measured in the current tree, which the decisions rest on:

- The watched folder holds **878 messages in `cur` and 11 in `new`**; 525 of
  those are marked read. Dropping the read filter takes the board from 364
  messages and 282 rows to 890 messages and 385 rows, measured with the board's
  own parsing and folding.
- **The local mirror has no Archive folder at all.** It mirrors the watched
  folders and the account's own inbox, and nothing else. So the board cannot
  ask the mirror whether a message was filed -- only whether it is still here.
- The trace holds **no message identity on any successful operation**: zero
  matches for a Message-ID pattern across a full day of 53 reviews. Identities
  appear only on the failure path.

## Goals / Non-Goals

**Goals:**

- A message leaves the queue for one reason and one reason only: it left the
  folder.
- The read flag goes on being set by a review, and stops being consulted by
  anything that decides membership.
- What became of a given message is answerable from the log.

**Non-Goals:**

- **No new question asked of the account.** "Is this filed?" is already
  answered by "is it still in the folder", because filing is a move. Adding an
  archive lookup would buy nothing and cost a round trip per read.
- **No unread-only view, and no filter for it.** A second way to look at the
  queue is a second thing to keep right, and the change that just shipped gives
  a general way to narrow a view if one is wanted.
- **No change to what ticking does.** It moves, confirms, then marks read. That
  is the half of today's behaviour that was correct.
- **No attempt to stop the mail client marking messages read.** That is the
  person's own program doing its job; the fix is for the board to stop reading
  meaning into it.

## Decisions

### Membership is presence in the folder, and nothing else

The filter comes out of `mail._messages` and is not replaced by anything. A
message is in the queue because the folder holds it.

This works because filing is a move: a reviewed message is in the archive, so
the folder no longer holds it, so the row goes. A message archived by hand in
the mail client leaves the same way, through the same mechanism, with the board
needing to know nothing about who moved it.

*Alternative considered: keep the unread rule and report the discrepancy* --
count the read-but-unfiled messages and say "525 read elsewhere" beside the
counts. Rejected: it makes the leak visible without closing it, and it would
have the board reporting a number about messages it refuses to show, which
invites the question "then where are they?" with no answer on screen.

### The cost lands on parsing, and it is worth measuring rather than assuming

`_messages` skips read mail *before* parsing the body, and its docstring says
why: parsing is the expensive part, and a folder holding a year of dealt-with
mail would pay it for every message. That reasoning was right about the cost
and wrong about the conclusion -- the messages are not dealt with.

So the cost is real: 890 bodies instead of 364, a 2.4x on the read path. The
measured baseline for this account is 1,137 messages read in 0.50s and folded
in 0.02s, so the new load is inside what has already been shown to be fast
enough. The performance suite should cover the new shape rather than the old
one, so that "fast enough" stays a measurement rather than a memory.

### A message carries its read state; undo restores it

`Message` gains one field, read from the maildir filename, which already
carries the flag. It is the only new state.

The review's undo entry keeps, per message, what that field said before the
review. Undoing splits the messages in two and issues at most two flag
requests, one for each group -- `gateway.mark_seen(folder, items, seen)`
already takes the boolean and already batches, so nothing new is needed
underneath.

*Why not leave the flag alone on undo?* Because a review marks every message
read, so an undo that skipped the flag would leave a message read that the
person had never opened. Both halves have to be restored for the undo to be
one.

*Why is this newly reachable?* Today a read message never reaches the board, so
it can never be ticked, so undo can never meet one. The case appears only
because the queue changes.

### Identities in the trace, on the way in

The `about=` string each operation passes to the trace already names the folder
and the count. It gains the identities. They are what the gateway addresses a
message by, so they are available at the call site without a lookup.

The logging requirement already forbids subjects, senders and bodies and
already demands identities; this adds no new category of data to a file that
is already excluded from the repository.

## Risks / Trade-offs

**385 rows on first open is a longer list than 282, and 525 of the messages in
it are old.** → Accepted, and it is the point: they are outstanding. They fold
into 103 extra rows rather than 525, because most join threads already shown.

**The read path gets 2.4x slower.** → Inside the measured envelope, but the
suite that measures it currently builds a mailbox of unread messages, so it
would keep measuring the old shape while the real one changed. The fixture
needs the read/unread mix the account actually has.

**A message the mail client has read, then the board ticks, then the person
undoes -- and the mirror has not caught up in between.** The prior read state
is taken from the message as the board last read it, which may be stale. →
Bounded by the mirror's lag and no worse than the move it accompanies: the same
staleness already decides whether the row is shown at all, and the review's own
confirmation is what settles the move.

**Anything else that reads the flag for meaning.** → Checked: the flag is read
in exactly one place, `mail._messages`, and written in exactly one,
`gateway.mark_seen`. Nothing in `main.py` consults it.

## Open Questions

None that change the specs, the approach, or the task breakdown.
