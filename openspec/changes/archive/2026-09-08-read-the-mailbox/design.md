## Context

See proposal.md — Why.

This is the fourth outside source, and the pattern the first three settled is
the one to follow: a module of its own with its own configuration, one failure
type, plain records, and rows the board draws without knowing where they came
from. `tracker.py` and `ical.py` are both that shape.

What the standard library already provides, verified rather than assumed:

```
   mailbox         Maildir, mbox, MH -- reading, and folders
   email           parsing, and email.header for encoded subjects
   email.utils     parsing a Date into a datetime
```

So there is no dependency to add. That matters more than it sounds: the
calendar cost three packages and made the board macOS-only.

Measured on a sample maildir shaped like a corporate inbox — fifteen messages,
nine of them in three threads:

```
   one row per message                  15
   one row per thread                    9
   tasks in the inbox it sits beside    36
   threads found by headers alone         3 of 3
   threads needing a subject fallback     0
   a coalesced Jenkins row's addresses    4, differing only in a build number
```

## Goals / Non-Goals

**Goals:**

- The notifications that change a day, on the board that shows the day.
- A queue a person can read, not a feed.

**Non-Goals:**

- Turning a message into a task. The point of the whole idea, and the first
  thing that writes, so it is its own change.
- Writing anything to the mailbox — no flag, no move, no marking read.
- How mail reaches the directory. Deliberately outside the boundary, so that
  choosing or changing a mail client does not touch the board.
- Reading anything but a maildir. Other formats are a later adapter over the
  same records, not a reason to design for them now.
- Reading the whole account. The folders to read are named; everything else in
  the mailbox is deliberately unread.

## Decisions

**The directory is the boundary, not a protocol.**

Reading a maildir needs no credential, no network and no server-specific
behaviour, and it works with whatever fills the directory. The alternative —
speaking the mail protocol from the board — would tie it to one account, put
credentials in the environment, and send them over a network the board would
then have opinions about. It would also have to be redone if the mail client
changed, which is a live possibility rather than a hypothetical.

The cost is that a client keeping mail in its own store rather than a maildir
is not read. That is a real limit and belongs in the open questions.

**A module named for the format, not the thing.**

`mailbox` is a module in the standard library; a file of that name beside the
board would shadow it and break the very thing being used. The same reasoning
named `ical.py`.

**A thread is the row, and threads come from headers only.**

Notification systems send one message per event, so messages are the wrong
unit: a run of four builds is one thing that happened four times. Following
the header that says which message answers which gives the grouping for
nothing, and it worked on every thread in the sample.

Matching subjects instead was considered and rejected. Unrelated messages
share subjects constantly — a weekly digest, a nightly report — and merging
those would *hide* mail, which is worse than listing it. A message the headers
place nowhere is its own thread.

**Its own view, not a place in the day.**

The board's other foreign rows join a day because they belong to one: an issue
is what is being worked on now, an event belongs to a date. Mail belongs to
neither. It is also of a different order of size — a handful of tasks against
a hundred notifications — so a day holding mail would be a day nobody could
read. The board already has two views that are queues rather than days; this
is a third.

**A thread offers the newest message's links, not every message's.**

Found in the sample rather than reasoned about: coalescing the messages does
not coalesce their addresses, and a four-build Jenkins thread yields four
console addresses differing only in a number. Offering all four would ask a
person to choose between things they cannot tell apart. The newest is the one
wanted — the failure, not the three successes before it.

**HTML rendered here, not by an external program.**

Notification mail is often HTML and nothing else, so reading only the plain
part would show nothing for the messages most worth peeking at. Both routes
were measured on a realistic notification:

```
                   quality                   per message   needs
   w3m             nicer tables, quotations      7.7 ms    a program installed
   the library     readable, looser lists        0.06 ms   nothing
```

A subprocess for each message is fifteen seconds on a queue of two thousand
against a tenth of a second, and the difference in output is cosmetic for a
notification. So the library's own parser does it, and `w3m` remains an
option later as a renderer named in configuration rather than a rewrite.

Either way the addresses have to be kept. Both renderers drop them by
default — the markup carries the address, the words carry only the link's
text — and this text is what the board reads to find what a row can open, so
losing them would break opening for precisely the mail most likely to have
something to open. They are collected while parsing and appended, which also
means a person peeking at the message can see them.

**Reading is off the drawing path.**

As the tracker's and the calendar's reads are. A mailbox can be large, and a
day must not wait for it.

## Risks / Trade-offs

**A client that keeps no maildir** → Apple Mail keeps its own store, so a
maildir-reading board does not see it. Named rather than hidden: the read side
is "a directory of messages" either way, so an adapter is an addition later
rather than a redesign. But if that is where the mail lives, this change does
not reach it.

**Subjects and senders are other people's text** → Escaped before drawing, as
a calendar description already is. A subject is not instruction, and its
characters must not be able to change how the board looks.

**Mail is private, and more of it than notes** → The board reads it, draws it,
and does nothing else with it: nothing is written anywhere, nothing sent. The
suite runs against a synthetic maildir alone, and verification against a real
one reports counts and never a subject or a sender. This is the source most
worth being strict about, being the largest.

**A mailbox big enough to be slow** → The sample is fifteen messages; a real
one is thousands. Reading is off the drawing path, and how much of it is read
— recent messages only, one folder only — is a question the open questions
carry, since the answer wants a real mailbox to measure.

**A feed by accident** → The whole risk of the idea. Threads shrink the list
and the separate view keeps it out of the day, but neither bounds it. If the
view proves unreadable at real volume, the answer is narrowing what is read
rather than making the rows cleverer.

## Open Questions

- No real maildir existed on this machine when this was built: the mail
  client in use speaks the mail protocol to its server directly and keeps
  nothing locally, and the indexer installed beside it has no database. So
  everything here is verified against synthetic maildirs, including one of
  two thousand messages, and the first contact with real mail is still to
  come. Recorded because it is the one piece of evidence this change could
  not gather.

- How much of the mailbox to read: every message, or a recent window, or one
  folder. The answer wants a real mailbox to measure and changes no
  requirement here — a view of everything and a view of a window differ in
  configuration, not in behaviour.
- Whether mail rows should ever appear on a day once promotion exists, for
  instance a thread already turned into a task due today. Deliberately left
  until promotion is built and has been used.
