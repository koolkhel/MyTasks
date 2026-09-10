## Why

Confirming a reviewed row opens the archive once for every message in it, and
undoing one opens it three times per message. The archive holds everything the
account has ever kept, and opening it was measured on the account at about
fourteen seconds. Searching it takes about one.

    archive()   confirmation:   n + 1 archive opens
    restore()   per message:    3n archive opens

The gateway already knows better. `numbers()` opens a folder once and then
searches it per message, which is what the confirmation wants and what the
undo wants; it simply is not used for either.

| row | confirmation now | after |
| --- | --- | --- |
| 1 | 29 s | 29 s — unchanged |
| 2 | 44 s | 30 s |
| 4 | 74 s | 32 s |
| 7 | 120 s | 36 s |
| 16 | 256 s | 46 s |

**Most rows gain nothing.** Of 545 rows in this mailbox, 387 hold one message
and are already at the minimum. The other 158 hold 755 of the 1,142 messages,
and that is where the cost is: a sixteen-message row spends over four minutes
opening the archive to confirm what it just moved, and would spend under one.

The stronger reason is not speed. The crash that took an afternoon to
diagnose happened on a seven-message row, and the reasoning already recorded
for it is that an operation stays open for tens of seconds and the longer it
is open the better its chance of being cut. Two minutes of confirmation
becoming half a minute is a smaller window for the line to drop in, which is
a different kind of gain from being quicker.

A quit also takes effect sooner. The board is required to let an operation
part way through give up cleanly when it is forced to end, and today that
check sits between messages — so a quit waits out an archive open and a
search, about fourteen seconds. With the archive opened once, the same check
between searches waits about one.

## What Changes

- Confirming a row opens the archive once, whatever the row's size, and
  searches it per message as `numbers()` already does. The two groups a
  confirmation asks about — the messages just moved, and the ones that turned
  out to be elsewhere — are asked in the same opening.
- `numbers()` takes an optional way to give up, asked between searches, so the
  give-up the board relies on survives the loop being replaced and becomes
  finer-grained than it was.
- Undoing a row opens the archive three times whatever its size: once to find
  the messages, once to mark them unread, once to move them back. It was three
  times per message, one message at a time, where both the marking and the
  moving already take a list.
- An undo becomes all or nothing. Where it fails, every message stays unread
  in the archive and the row does not come back, rather than some messages
  being in the folder and the rest in the archive. One state to reason about
  and one notice to read, on the path whose job is not to lose mail.
- Nothing else about a review changes: the same confirmation, both halves of
  it, the same reporting of a message found in neither place, the same
  marking-read last of all.

## Capabilities

### Modified Capabilities

- `task-board`: *An archive is confirmed before a row is retired* gains what a
  confirmation may cost — a number of folder openings that does not grow with
  the row — and says that an undo is all or nothing. *The board shows whether
  the mailbox is busy* cites measured figures in its reasoning, and the folded
  one stops being true: about 25 seconds a message becomes about 8 at four
  messages and 3 at sixteen. A spec carrying a stale measurement is the thing
  the change that added the trace existed to stop, so it is corrected here.

### New Capabilities

None.

## Impact

- `gateway.py` — the confirmation loop in `archive`, the whole of `restore`,
  and `numbers` gaining a way to give up. No new method and no new dependency.
- No change to `main.py`. The board calls the same two functions and handles
  the same two exceptions.
- `tests/stub/t_trace.py` asserts the shape being removed — eleven selects and
  eight archive opens for a seven-message row. That assertion moves, which is
  why it was written as a check rather than a comment.
- No new request is made to the account. Strictly fewer.

## What was measured

- Against the recording server, archive openings by row size: `archive()` 2, 3,
  4, 8 for rows of 1, 2, 3, 7; `restore()` 3, 6, 9, 21 for the same.
- Against the real account, from the board's own trace: opening a folder is
  81.9 s of 88.9 s across twenty requests — 92 % — with archive openings at
  13.2, 13.8 and 16.6 seconds and searches at about 1.1.
- Row sizes in this mailbox: 387 of one message, 54 of two, 31 of three, 33 of
  four, and 44 rows of five to sixteen.

## What is not being done

- A single search for the whole row. This gateway answers an OR of eight
  identities with two matches, which is recorded in the gateway's own source
  and is why the confirmation searches one message at a time in the first
  place.
- Making `_select` remember what is open and skip a redundant opening. It is
  the smaller change and it would reach paths nobody audited; its correctness
  rests on the server keeping a selected mailbox live rather than snapshotted,
  and this is the server already caught deviating from its protocol. See
  design.md.
