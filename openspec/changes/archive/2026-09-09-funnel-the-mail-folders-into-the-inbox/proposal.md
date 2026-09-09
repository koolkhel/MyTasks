## Why

The board can read a mailbox and turn a message into a task, but it has been
reading a synthetic sample. Pointed at the real one, three things break at
once.

**Volume.** The three folders processed daily hold 1,775 messages, 1,233 of
them unread. The board threads by header, which for the issue tracker's mail
gives 385 rows where 199 issues exist — one row per update instead of one per
issue. Reviewing that is not a queue, it is a wall.

**Nothing drains.** Promoting marks a message read, and the local store is a
pull-only mirror: the read flag is the only trace, and it says nothing to the
mail client the same account is read in elsewhere. Ticking a mail row does
nothing at all — the board refuses every write on it. So a reviewed message
comes back.

**Order.** Mail leads the inbox's tasks, on the reasoning that processing
should "start at the top rather than after a scroll". With 35 inbox tasks and
some 460 mail rows, that reasoning now argues the other way: it guarantees a
460-row scroll to reach one's own work.

## What Changes

- The board reads the three folders processed daily from the real mail
  directory. Its layout is folders as real directories, not the nested form
  the board assumes today.
- **Messages about one issue fold into one row.** The rule is one a person
  did not have to configure: messages naming the same issue in a configured
  tracker project *and* pointing at the same address are one row. Measured on
  the real folders it folds 973 messages into 121 rows for the tracker, folds
  conservatively where the evidence is weaker, and does nothing at all where
  the subjects name no issue.
- **Ticking a mail row archives it.** The message is moved to the archive
  folder on the server over IMAP, by its Message-ID, and the row retires only
  once that is confirmed — gone from the folder it was in *and* present in the
  archive. This is what makes a reviewed message not come back: the archive is
  outside what the local mirror syncs, so the message has nowhere to return
  from.
- Promoting archives too. One review, one outcome.
- **The board writes nothing to the local mail store.** Not a flag, not a
  rename. A hand-move of a maildir file is documented to break the sync
  outright; the read flag it sets today goes away, and reviewing is recorded
  where it is authoritative — on the server.
- **Mail rows follow the inbox's tasks** rather than leading them.
- `o` opens the earliest anchored address in a group, so the browser lands at
  the start of a discussion and reads downward. Where a group carries no
  anchor it falls through to today's behaviour exactly.
- **Not in scope:** sending mail, reading any folder but the three, browsing
  the archive, searching, and any local index. Reading stays a directory walk.
- **Also not in scope:** making the archive reachable from the board. Once a
  message is archived it is gone from the board's view, which is the point.

## Capabilities

### Modified Capabilities

- `task-board`: five requirements change and three are added. Reading gains a
  folder layout and loses every local write; the mail rows' place in the inbox
  is reversed; what can be opened is chosen from a group rather than from its
  newest message; a mail row stops refusing every key, because ticking now
  acts on it; and promoting takes the thread out of the queue by archiving
  rather than by marking read. Added: how messages fold into one row, what
  reviewing a message does, and that an archive is confirmed before a row is
  retired.

## Impact

- `mail.py` — the folder layout, folding, and no local writes.
- `main.py` — the tick, the ordering in the inbox, what `o` offers.
- A new module for the gateway: bulk UID lookup, a batched move, and the
  confirmation. The neighbouring project offers a verified client to copy;
  whether to copy it whole, trim it, or depend on it is settled in the design.
- `.env` — where the mail directory is, which folders, and how to reach the
  gateway.
- The corporate mailbox — one message moved per review, and nothing else. No
  message is deleted, and nothing is written to the local store at all.
- **The board reaches a network service for the first time on a keystroke.**
  Everything it has written until now went to the task store; this writes to a
  mail server, and a confirmation costs about a second per message.
