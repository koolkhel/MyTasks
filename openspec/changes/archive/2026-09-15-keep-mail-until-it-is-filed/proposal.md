## Why

A message that arrived at 15:33 was not on the board, and was still sitting in
the mail account's inbox. Read against the account and the logs, what happened
was this: the board's queue is the *unread* messages in the watched folders,
and the message had been read in the mail client without being filed. It left
the queue having been dealt with by nobody, and the board said nothing.

Ticking is not at fault. Across the day the board performed 53 reviews: 53
moves out of the watched folder into the archive, 53 flag requests marking the
moved messages read *in the archive*, every one confirmed, no failure of any
kind. The board has no path that marks a message read where it sits, so it
cannot produce the state that was observed.

The size of what the queue has been dropping, counted in the watched folder:

| | messages |
|---|---|
| unread — what the board counts today | 364 |
| **read and never filed — gone from the queue, still in the inbox** | **525** |

The requirement that produced this says why it was written:

> Within those folders the board SHALL read the messages not yet marked read.
> A queue is what has not been dealt with; a message already read has been
> dealt with, whether here or in the program the person reads mail with.

That last clause is the mistaken part. Reading a message in a mail client is
not dealing with it, and on this account it is the ordinary case: a message
that arrived at 22:35 tonight was marked read within minutes, with the board
idle since 22:29.

Separately, and the reason the diagnosis took an account inspection rather than
a grep: the trace records counts, folders and durations but no message
identity on any successful operation, so "was *this* message archived?" cannot
be answered after the fact. The logging requirement already says identities
SHALL be recorded; no scenario checks it on the success path, which is how the
gap survived.

## What Changes

- **The queue becomes what is in the watched folders.** Membership stops
  consulting the read flag. A message is in the queue because it is in a folder
  the board watches, and for no other reason.
- **A row leaves only when its messages leave the folder** — filed from the
  board, or archived by hand in the mail client. Both are moves, and the board
  needs no new question to notice either.
- **Ticking goes on marking messages read**, in the archive and after the move,
  exactly as it does today. Unchanged, and named here because it is the half of
  the current behaviour that was right.
- **Undo restores each message's prior read state** rather than marking every
  message unread. A message read in the mail client, then ticked, then
  un-ticked, comes back read — the state belongs to the person, not to the
  review. This is newly reachable: today a read message never appears on the
  board, so it can never be ticked.
- **A message carries whether it was read**, which is what undo restores and
  what the maildir already records in the filename.
- **The trace records message identities on successful operations**, not only
  on the failure path, so that what became of one message is answerable from
  the log.

Measured cost of the queue change, on the real account:

| | messages read | rows drawn |
|---|---|---|
| today | 364 | 282 |
| after | 890 | 385 |

**+103 rows, not +526**: the messages that were being dropped mostly fold into
threads already on the board, arriving as a higher count on an existing row
rather than as a new one.

## Capabilities

### New Capabilities

None. This corrects how an existing capability decides what is in its queue.

### Modified Capabilities

- `task-board`: three requirements, one of them retired and reissued.
  - *The board reads named folders from a directory of maildirs* is
    **removed**, and returns as *The board reads every message in the named
    folders*. A modification could not express this: the requirement carries a
    scenario, **A message already read is not in the queue**, asserting exactly
    the behaviour being reversed, and OpenSpec refuses to let a MODIFIED block
    drop a scenario — rightly, since a requirement holding both the old
    assertion and the new one would not say which wins. The other ten scenarios
    return unchanged.
  - *An archive is confirmed before a row is retired* — the sentence requiring
    undo to mark messages unread, and the reason given for it, are replaced by
    restoring each message's prior state. Scenario **Undoing a review puts the
    mail back** keeps its name and gains the corrected outcome.
  - *The board logs what it does to the mailbox* — a scenario is added
    requiring the identity of each message on the success path, which the
    requirement's text already demands and no scenario checked.

## Impact

**Code**

- `mail.py` — the read/unread skip in `_messages` goes; `Message` gains a field
  saying whether the message was read. The skip currently happens *before* the
  body is parsed, so removing it means parsing every message in the folder
  rather than a third of them.
- `main.py` — the undo entry for a review carries each message's prior read
  state, and the undo path restores it instead of marking everything unread.
- `gateway.py` — `mark_seen` is already able to set or clear the flag for a
  batch, so undo needs at most two requests: one for the messages that were
  read and one for those that were not. The trace gains identities.

**Performance** — the read path parses 890 message bodies instead of 364. The
measured baseline for this account is 1,137 messages read in 0.50s, so this
stays inside what has already been measured, but it is a real 2.4x on that
path and the existing performance suite should be made to cover it.

**Not affected** — what ticking does, the confirmation before a row is retired,
the archive folder, the counts the board reports, and everything outside mail.

## Assumptions recorded

- **The trace change is in scope on my recommendation**, not by request. It is
  what makes "did this message get filed?" answerable, which is what this whole
  investigation needed and did not have. It touches a different requirement
  from the other two and can be dropped without affecting them.
- **A message whose flags cannot be read is treated as unread** for the purpose
  undo restores, matching what the current code already does when it cannot
  read a flag: it declines to infer that anything was dealt with.
