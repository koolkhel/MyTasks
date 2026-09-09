## Context

See proposal.md — Why. What follows is only what shapes the approach, and
almost all of it was measured rather than assumed.

The mail directory is a mirror of a corporate account, kept in step by a sync
tool through a local gateway. A neighbouring project built that and wrote down
what it verified; the facts below come from its configuration and its measured
notes, not from documentation about the tools in general.

```
   ~/Mail/{Gitlab,Jenkins,YouTrack}     READ: a directory walk, microseconds
        |  folders are real directories
        |  1,775 messages, 1,233 unread
        v
   fold: same configured issue + same first address
        |  973 -> 121 rows | 194 -> 58 rows | 0 folds
        v
   inbox: 35 tasks, then ~460 mail rows
        |
        +-- tick / promote --> IMAP MOVE to Archive --> confirm both sides
                                   |
                                   +-- Archive is NOT in the sync's folder list
                                       so an archived message cannot come back
```

The asymmetry that decides the design: bulk *flags* over the gateway are
nearly free — a fetch over 20,699 messages measured 0.88 s next door, and
291 of them 0.14 s here — while anything per-message costs about 150 ms.

Two figures taken from those notes turned out not to hold for the requests
this makes, and both were measured again while building it: a bulk fetch of
*headers* is not cheap (45 s for a folder of 291), and a search is not under
a second in a folder the size of the archive (11.5 s in one of 20,816). What
follows uses the measured numbers; where a decision was made on the older
ones, it says so.

Three facts constrain what may be written:

- the sync pulls new mail, pulls removals, and syncs flags both ways, but
  **never pushes removals**;
- moving a maildir file by hand is recorded as breaking the sync outright,
  leaving a duplicate-UID failure that needs a folder rebuilt;
- the archive folder is deliberately absent from the sync's folder list.

## Goals / Non-Goals

**Goals:**

- A reviewed message never appears again.
- One row per thing to decide about, at the volumes actually present.
- One's own tasks reachable without scrolling past somebody else's mail.

**Non-Goals:**

- Any write to the local mail store. Not a flag, not a rename. (On the
  *server* the board sets one flag: a confirmed archive is marked read.)
- Reading the archive, searching, or holding an index of any kind.
- Sending mail, or reading folders beyond the three.
- Making the board work without the gateway. Reading does; reviewing does not.

## Decisions

**Reviewing moves the message on the server, and nothing local is touched.**

The obvious cheap alternative was to set the local seen flag: it is what the
board does today when promoting, the sync does push flags, and it would retire
the row instantly with no network call. It is rejected because a flag says
only "one program has seen this". The queue is *these folders*, and the way
out of a folder is to leave it.

The stronger reason is that the durable answer costs nothing extra. The
archive folder is not in the sync's folder list, so once a message is moved
there it is not merely marked — it has nowhere to come back from. The removal
propagates because the sync pulls removals; within one sync interval the local
file is gone. Reviewing therefore needs nothing written anywhere: not a file,
not a flag, and no record of what has been decided.

What it does need, found while implementing it, is one set in memory. "Within
one sync interval" is up to five minutes, and every change of view re-reads
the folders — so a person who reviewed ten rows and pressed `i` met all ten
again, which is exactly what "a reviewed message never appears again" was
meant to rule out. So the board holds the identities the gateway has
*confirmed* are in the archive, for the session only, and leaves them out of
each read; the set is pruned on every read to what the mirror still returns,
so it is bounded by the lag rather than growing all day, and an undone review
drops its identities at once. This is not a record of decisions — the account
is still that — it is the board declining to show what it has already been
told is gone.

And a local write is the one thing documented to break this setup. A hand-move
of a maildir file produced a duplicate-UID failure needing a folder rebuilt.
The board writing flags into a mirrored store is a smaller version of the same
mistake, and there is no reason left to take it.

**A confirmed message is marked read, and that flag costs nothing.**

Asked for after the first day's use: reviewed mail sat unread in the archive,
so the account and every other program reading it still called it new. The
board's own queue is defined by that flag, so leaving it alone was
inconsistent with the very rule that draws the queue.

It is free, which is what makes it worth doing here rather than in a change
of its own. The confirmation already searches the archive for each message,
and that search returns the message's number; it was being thrown away.
Keeping it turns the flag into one `STORE` for the whole row.

It is set last, after both halves of the confirmation, so nothing is marked
read on the strength of a move that could not be confirmed. Undoing a review
clears it before moving the message back, or the row would return to a queue
that does not show it.

The alternative was to set it in the source folder before the move, which
needs no search at all — and is wrong twice over: the flag would reach the
local mirror, taking the row out of the queue even if the move then failed,
and it would be a write to a mirrored store, which is the thing this change
exists to avoid.

**Confirm both sides; the row retires on evidence, not on a returned OK.**

After the move, the messages must be absent from the folder they were in and
present in the archive. Checking only that the move returned OK would trust a
gateway that has already been caught returning a part's body where the
protocol requires its headers — a deviation that silently emptied message
bodies in a mail client until someone measured it. The same gateway's move is
not more trustworthy for being more convenient.

Confirming costs 11.5 s a message against the real archive — the figure was
assumed to be under a second and measured afterwards — which is why it runs
where every other write on this board runs: behind the screen, with the row
already gone and a failure bringing it back.

Absent from both places is its own outcome, not a failure to report as one:
it means something else moved that message, and saying so is more useful than
either succeeding or erring.

**Batch the moves; address and confirm the messages one at a time.**

A row can stand for 39 messages. The ready-made client moves one message per
call, and each call opens the folder and searches it, so a large row would
take over a minute before any confirmation. The move is therefore batched:
it takes a set of server-side numbers and is one round trip per row however
many messages the row holds.

Getting those numbers was where the cost model misled. "Bulk metadata is
nearly free" was measured on a *flags* fetch, and this gateway does not
answer a *header* fetch the same way — it fetches each message from Exchange.
Measured against the real folders while implementing this:

| request | folder of 291 |
|---|---|
| bulk `FETCH 1:* (FLAGS)` | 0.14 s |
| bulk `FETCH 1:* (BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])` | 45 s |
| `SEARCH HEADER Message-ID` for one | 2.1 s |

So the numbers are found with one search a message: a row of eight costs 17 s
against 45 s, and it does not grow when the folder does — the YouTrack folder
is twice the size again.

One `SEARCH` OR-ing the row's identities would have been a single round trip
for the lot. It was tried: this gateway answered an OR of eight identities
with two matches, all eight of which are found when searched for one at a
time. That is the same class of deviation the confirmation below exists for,
so it is not used, and the suites' substituted server refuses an OR search
outright so the product cannot come to make one.

`UID MOVE` would have handed over the destination numbers for nothing: the
gateway advertises `UIDPLUS`, and RFC 6851 says such a server answers a move
with `COPYUID`. It was tried too, on one real message: no `COPYUID`, tagged
or untagged, in either direction. Two advertised capabilities that are not
there — which is the argument for confirming rather than trusting, made by
the gateway itself.

A search of the *archive* is the expensive one: 11.5 s against a folder of
20,816, where the design assumed under a second. That is what a row's
confirmation costs, a message at a time, and it is why the number it returns
is kept rather than discarded — see the read flag above.

Absence after the move is proved by asking the folder for the numbers just
moved — a flags fetch of numbers already known, the cheap half of the model,
one round trip. Presence in the archive stays a search per message at 11.5 s
each, which is the dominant cost of a review.

Measured end to end against the real account: one message archived and
confirmed in **32 s**, a folded row of two in **49 s** — about 25 s a
message, with a board running beside it competing for the gateway. A row of
97 took 25 minutes, measured by a live check that unwisely picked the largest
row there was.

That is accepted rather than optimised because the alternative is to confirm
a sample and trust the rest, and knowing was the whole point; it happens
behind the screen with the row already gone. It is the first thing to revisit
if reviewing comes to feel slow, and the honest note is that a person
clearing a hundred rows has a hundred of these behind them — which is why
they go one at a time rather than all at once.

**Fold on the issue *and* the address, which validates itself.**

Grouping by the issue named in a subject is what folds a tracker's
notifications, and it must be a configured project's key rather than a general
letters-dash-digits pattern: that pattern also matches a version or a standard,
and the board already has one place that knows which projects count.

But the key alone is wrong. In one folder read daily, mail about a merge
request names the issue it mentions, so several unrelated requests cite the
same issue: folding on the key alone merged 24 of 38 groups wrongly. Requiring
that the messages also carry the same first address splits those apart again,
and it costs nothing — the address is already extracted for the key that opens
things.

This matters more than tidiness because reviewing a row archives every message
in it. A wrong fold does not merely misdraw a row; it files away mail that was
never looked at.

The rule needs no list of which folders to fold. It folds where the evidence
supports it and does nothing where it does not, which is why it is preferred
to naming the tracker's folder in configuration.

**The earliest anchored address, falling through to today's rule.**

Within a row, an address carrying a fragment names a place inside a page; the
earliest such address is where a discussion should be entered so it reads
downward. The earliest and latest differ in 75 of 121 folded rows, so the
distinction is real.

Where a row has no anchored address the existing rule stands untouched: take
the newest message's addresses, because a run of build notifications carries
one near-identical address per message. That reasoning was formed on a folder
which carries no fragments at all, so it keeps precisely the behaviour it has.

This is why the change reads as a reversal and is not one. Two rules, each
applying where its evidence lies.

**Mail follows the tasks, because the volume inverted the argument.**

The shipped requirement puts mail first so that "processing starts at the top
rather than after a scroll". With 35 tasks and some 460 mail rows, that
sentence argues for the opposite order: leading with mail guarantees the
scroll it was meant to avoid. The requirement is modified rather than deleted,
and keeps its reasoning, because the reasoning was never wrong — only its
premise about relative volume was.

**Carry a trimmed copy of the gateway client, not a dependency on it.**

The neighbouring project offers its client to be copied. Depending on it by
path would mean this repository no longer works from a fresh clone, which the
change that brought the suites in spent considerable effort establishing.

So: a copy trimmed to what is used — the credential lookup, the folder-name
encoding, a bulk identity-to-number fetch, a batched move, and a search — with
attribution and a note of where the original lives. Its send, attachment and
index paths are not brought over.

The trimmed parts are exactly where the verified traps live, so each is copied
with the comment that records why it is written the way it is.

## Risks / Trade-offs

**The board makes a network call on a keystroke for the first time** → Every
write until now went to the task store; this writes to a mail server, and a
gateway that is down means reviewing does not work while reading still does.
Mitigated by the existing write machinery: the row goes at once, the failure
comes back with a reason, and nothing else on the board is affected.

**A credential prompt while the terminal is owned by a full-screen
application** → Established, and it does not happen. The prompt for an
unauthorised keychain item is drawn by SecurityAgent, a windowed process of
its own, so nothing reaches the terminal the board has repainted; a missing
item comes back as an error in 14 ms with nothing written to the terminal at
all. So the credential is fetched at the moment a review needs it, and the
fallback of fetching it at startup is not taken — that would hold a password
in memory for a session that may never review anything.

What is hardened instead is the configurable part: the password command runs
with its input closed and its output captured, so it cannot wait on a person
at the terminal or write over the view. A command that opens the terminal
device itself could still reach it, which is the choice of whoever configured
that command.

**Confirming a large row takes the better part of a minute** → Accepted, and
invisible unless a person watches for it. The row is already gone. Worth
revisiting only if rows that large turn out to be common; measured, the
typical row holds eight messages.

**A row returns after an undo only when the mirror catches up** → Up to one
sync interval, five minutes as configured. The requirement says the board must
say so rather than pretend. Nothing better is available without holding state,
which is the property being protected.

**Reviewing mail is now indistinguishable from ticking a task, by keystroke**
→ The same key does two very different things depending on what is selected:
one completes work, the other files mail away in a place the board cannot show
again. The refusal wording is what carries the distinction, and it is thinner
than a confirmation would be. Left as one key because a review is a hundred
keystrokes a day and a confirmation on each would be worse than the risk.

**Volume in one view** → Some 460 rows, redrawn whenever the table is rebuilt.
Reading and folding them measured about 0.6 s in total, so the cost is in the
drawing rather than the parsing, and it is not yet measured. It should be
before this is called done.

## Open Questions

- Whether a single view holding 35 tasks and 460 mail rows repaints fast
  enough to keep the board's feel. Deferrable: it changes no requirement and
  no interface, only whether a later change needs to draw mail lazily.
