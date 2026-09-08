## Context

See proposal.md — Why. This change depends on the mailbox being read at all,
which is `read-the-mailbox` and comes first.

Three things already exist and this change joins them up.

The board creates tasks: a title, a date at midnight flagged as all-day, and a
stored order past everything the day holds. That path is used by the key that
adds a task and is the one to reuse.

Every write goes through one funnel that shows it at once, queues the request,
records an undo entry, and refuses rows the board does not own.

And a note is a field the board now writes: encoded as the store wants it,
drawn escaped, editable by its own key.

```
   a mail thread                     a task on today
   -------------                     ---------------
   what it is about        ------>   its title
   what it pointed at      ------>   its note, so the key that opens
   which message it was    ------>   a link still reaches the thing
```

## Goals / Non-Goals

**Goals:**

- A queue that drains into the day.
- A task that still reaches the thing it came from.

**Non-Goals:**

- Writing anything to the mailbox. Not a flag, not a move, not marking read.
- Reaching the mail server. That is two systems away: the board would tell the
  directory, and something else would tell the server.
- Remembering what has been promoted. Explicitly rejected below.
- Promoting into any view but today, or more than one thread at a time.

## Decisions

**Reuse the path that adds a task; do not invent one.**

Promoting is adding a task whose title came from somewhere else. Everything
that already holds for an added task — shown before the store answers, one
undo entry, a stored order that does not disturb the day's sequence, a failure
reported rather than swallowed — holds for this for free, and could only be
got wrong by writing it again.

**The note carries the address and the message's identity.**

The address because a task reading "Build failure" is a reminder, where one
that opens the build is the work — and the key that opens a task's link now
reads the note as well as the title, so putting it there is enough to make it
reachable. That was built two changes ago and this is the first thing to lean
on it.

The identity because a task ought to be traceable to what caused it. A
person asking "why is this on my list" should be able to find the message.

Both in the note rather than the title: a title is what a person reads at a
glance down a list, and an address in it would crowd out the words that say
what the task is.

**The board keeps no record of what it promoted, so promoting twice makes two
tasks.**

The alternatives were each worse. Remembering locally would give the board its
first file on disk — it has none today, every row is derived from a source,
and that property is worth more than the annoyance it would save. Deriving it
from the task store would mean finding a task by its text, which the store
cannot do: it filters by date, state, tags, project and priority, and by
nothing textual. Setting a flag on the message would mean writing to the
mailbox, which is the boundary this change is deliberately not crossing.

So the queue drains where mail is already managed. Archiving in the client
that fills the directory removes the message from what the board reads, which
is the same mechanism that already governs what appears there at all. The cost
is that promoting the same thread twice is possible; it is one task to delete,
against an architectural property worth keeping.

**A key of its own, refused elsewhere.**

Promoting is not "add", because it takes no input and acts on a row. It is not
"open". So it is its own key, and on any row that is not a mail thread it says
what it is for rather than doing nothing — the board's habit for every key
that cannot act.

## Risks / Trade-offs

**Promoting twice** → Possible by design, for the reason above. Worth watching
in use: if it happens often enough to matter, the answer is most likely the
maildir flag, which is a small addition and needs no redesign — the design
above rejects it as scope, not as impossible.

**A title chosen by a machine** → A subject is what somebody else called the
thing, and a task list reads worse for it. Accepted because the alternative is
asking for a title at the moment of triage, which turns a keystroke into a
sentence and would make the queue slower to drain than it is worth. The rename
key is one press away.

**A note that grows a convention** → Putting two facts in a note gives the
note a shape the board otherwise has no opinion about, and a person editing it
could break the address without knowing it mattered. Mitigated by the address
being read by the same scanner that reads any note, so a broken one degrades
to "no link" rather than to an error — and by the identity being for a person
to read, not for the board to parse.

**A task that outlives its message** → Archiving the message leaves the task
pointing at an identity no longer in the mailbox. Accepted: the address still
opens, and a task is meant to outlive the notification that prompted it.
