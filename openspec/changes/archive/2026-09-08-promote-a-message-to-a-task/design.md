## Context

See proposal.md — Why. This change depends on the mailbox being read at all,
which is `read-the-mailbox` and came first.

Three things already exist and this change joins them up.

The board creates tasks: a title, a date at midnight flagged as all-day, and a
stored order past everything the day holds. That path is used by the key that
adds a task and is the one to reuse.

Every write goes through one funnel that shows it at once, queues the request,
records an undo entry, and refuses rows the board does not own.

And a note is a field the board now writes: encoded as the store wants it,
drawn escaped, editable by its own key. The key that opens a task's link reads
the note as well as the title.

```
   a mail thread                      a task on today
   -------------                      ---------------
   what it is about        ------>    its title
   what its newest         ------>    its note -- so the addresses the
     message said                       message carried are reachable by
   which message it was    ------>      the key that opens a link, and the
                                        message can be found again
   its messages, unread    ------>    marked read, so the row is gone
```

## Goals / Non-Goals

**Goals:**

- A queue that drains into the day, and drains: the promoted row leaves.
- A task that still reaches the thing it came from, and still says what it
  said.

**Non-Goals:**

- Reaching the mail server. That is two systems away: the board writes the
  directory, and whatever fills that directory tells the server. Whether a
  read flag propagates back to an account is the sync tool's business.
- Dismissing a message that is *not* work. Flagged in the proposal as the
  known gap: most notification mail is noise, and a queue with only a promote
  action still will not drain. Left out deliberately rather than overlooked.
- Any mailbox write beyond the read flag: no move, no removal, no rewrite.
- Remembering what has been promoted anywhere but the mailbox.
- Promoting into any view but today, or more than one thread at a time.

## Decisions

**Reuse the path that adds a task; do not invent one.**

Promoting is adding a task whose title came from somewhere else. Everything
that already holds for an added task — shown before the store answers, one
undo entry, a stored order that does not disturb the day's sequence, a failure
reported rather than swallowed — holds for this for free, and could only be
got wrong by writing it again.

**The note carries the message's body, not merely its address.**

The earlier draft of this change put the offered address in the note. Measuring
the sample mailbox settled it the other way: in all nine of its threads, the
address the mail row offers is *inside that thread's own body text*, and the
HTML reader appends each link's target to the text it produces, so this holds
for HTML mail too. Carrying the body therefore carries the address — the key
that opens a task's link finds it by the same scan it runs on any note — and
carries the rest of the message as well.

That is the whole difference. A task reading "Build #4812 failed" with the
address alone is a pointer; the same task holding what the message said is the
work, readable on the board without going back to a mail client at all. And it
costs nothing extra: one field instead of one line of it.

The message's identity goes in too, so the task remains traceable to its
origin. A person asking "why is this on my list" can find the message.

Both in the note rather than the title: a title is what a person reads at a
glance down a list, and neither a body nor an address belongs there.

**Promoting marks the thread read, and that is how the row leaves.**

This reverses the earlier draft, which wrote nothing to the mailbox and left
the queue to be drained in a mail client. What changed is where mail lives: it
is in the inbox now, beside the tasks, not in a view of its own. A row that
stays after being dealt with is not a queue — it is a list that grows, and the
inbox is the one place on this board where that is fatal.

The board already reads unread messages only. So marking a thread's messages
read makes the row leave by the rule that put it there, with no second
mechanism and no record of its own: **the mailbox is the record.** That is the
same architectural property the earlier draft was protecting, reached by
writing one flag rather than by refusing to write at all.

Marking read renames the file and, for a message sitting in a folder's new
area, moves it to that folder's current area — which is what the format
requires of a message that has been seen, and is why a rename is not enough on
its own. It stays in the folder it was read from; the sample mailbox delivers
every message into `new`, so this is the ordinary path rather than an edge.

The cost is stated plainly: this **gives up "the board alters nothing in the
mailbox"**, shipped one commit ago in `read-the-mailbox`. Hence the spec delta
MODIFIES that requirement rather than only adding to this one. What is kept is
the narrower and more useful promise — the board changes a message's read flag
and nothing else: no move, no rename beyond flags, no removal, no rewrite.

The alternatives were each worse. Remembering locally would give the board its
first file on disk; it has none today and every row is derived from a source.
Deriving it from the task store would mean finding a task by its text, which
the store cannot do — it filters by date, state, tags, project and priority,
and by nothing textual.

**The task is created first, and a mailbox that cannot be written does not
undo it.**

Of the two ways this can half-happen, only one is recoverable by a person who
can see the screen. A task made and not marked shows the row once more, which
is a visible annoyance. A message marked and no task made is work that has
silently left the queue. So the order is task, then flag; a failure to flag is
reported and the task stands.

**Marking read needs the message's file, which `Message` does not carry.**

`read()` returns `Message` values holding sender, subject, date, identity,
what it answers and its text. Nothing there can find the file again: the
identity falls back to the mailbox key only when a message has no Message-ID,
and the folder is not recorded at all. So `Message` gains the folder it was
read from and its key within that folder, and marking read reopens that folder
and adds the flag by that key.

Carrying the key rather than re-searching by identity is the honest choice:
maildir keys are what the library addresses messages by, and searching every
folder for a Message-ID would be slower and would still be ambiguous for the
messages that have none.

**A key of its own, refused elsewhere.**

Promoting is not "add", because it takes no input and acts on a row. It is not
"open". So it is its own key — `f`, for filing it — and on any row that is not
a mail thread it says what it is for rather than doing nothing, which is the
board's habit for every key that cannot act.

`f` because `m` is no longer the obvious choice: it read as "mail" when there
was a mail view to go to, and there is not one now.

## Risks / Trade-offs

**The board now writes to the mailbox** → The property given up above. Bounded
by keeping the write to a single flag on messages the board was already
reading, by never touching content, name or folder, and by a scenario that
compares the mailbox file by file after a promotion to prove nothing else
moved.

**A read flag is a claim about a person's mail, made by a task board** → If
the directory syncs back to an account, promoting here marks the message read
there. That is the intended effect — it is the same act as reading it — but it
is the first time this board's keystroke reaches outside the task store, and it
is worth the user knowing before it is bound to a key.

**A title chosen by a machine** → A subject is what somebody else called the
thing, and a task list reads worse for it. Accepted because the alternative is
asking for a title at the moment of triage, which turns a keystroke into a
sentence and would make the queue slower to drain than it is worth. The rename
key is one press away.

**A note that grows a convention** → Putting a body and an identity in one
note gives the note a shape the board otherwise has no opinion about, and a
person editing it could break an address without knowing it mattered.
Mitigated by the address being read by the same scan that reads any note, so a
broken one degrades to "no link" rather than to an error — and by the identity
being for a person to read, not for the board to parse.

**A long body in a note** → A notification can be long, and the whole of it
lands in the note. Accepted: the notes pane already scrolls, the editor already
handles it, and truncating would throw away the part a person needs about as
often as not.

**A task that outlives its message** → The message will eventually be archived
or removed where mail is managed, leaving the task's identity pointing at
nothing in the mailbox. Accepted: the body and its addresses are in the note
and stay useful, and a task is meant to outlive the notification that prompted
it.
