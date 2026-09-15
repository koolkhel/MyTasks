## Context

See proposal.md — Why. What follows is what the existing code makes cheap and
what it leaves to be decided.

The seven write actions are one shape. Each reads `self.selected`, returns if
there is nothing or no client, and hands one task to the write queue. Two of
them ask something first through a modal screen — the date and the project —
and two refuse a row the board does not own before asking, so that a question
is never put about a row the answer cannot reach.

Sending many writes at once is solved. A queue holds writes that have not been
sent and a set holds the tasks whose writes are out; five go at a time, a
width measured against the store rather than chosen. It was built for pasting
and takes a callable, so it does not know or care what kind of write it is
carrying.

One action's writes already become one undo entry when they share a group, and
the board already knows which rows are marked, in the order they were marked,
with a copy of each remembered so a row can be reached from a view that is not
drawing it.

Two things are *not* solved and were checked rather than assumed:

Dating a task sends only its start and its deferred flag — never a stored
order. So moving a marked set to another day cannot disturb that day's
sequence, and none of the trouble the paste had with tied orders arises here.
This was the risk worth checking, and it is not present.

The two toggling keys read the state off the one task they act on. A set has
no single state to read, so what they mean for a set is a decision rather than
a generalisation.

## Goals / Non-Goals

**Goals:**

- One rule that covers every write key, rather than a rule per key.
- A set that spans views can be written to from any of them.
- Nothing irreversible without being asked, and the question true about the
  whole set.

**Non-Goals:**

- Changing what marking is, which rows accept it, how long it lasts, or what
  copying does. Only what a write does with it.
- A second selection concept, a prefix key, or a mode. The mark is the
  selection.
- Bulk reviewing of mail. The tick key files a message away when it is pressed
  on a mail row, and that stays a one-row action — see below.

## Decisions

### Marks win, and the cursor takes no part

The alternative was a second key per action — a capital to act on the set —
which cannot be pressed by accident. It was weighed and not taken: seven more
keys and a rule to remember, against a hazard the board already covers.

What covers it: deleting asks first and the question names the count; filing a
task that has no project asks first, because that cannot be undone either;
everything else is reversed by one press of the undo key. The status line
carries the number of marked rows the whole time, and escape clears them.

So the worst outcome is doing the same thing twice, which undoes, rather than
losing something.

### A write passes over what it cannot write, rather than refusing

Two actions currently refuse a foreign row out loud before doing anything. For
a set that is the wrong shape twice over: it would say the same thing several
times, and it would refuse an action that is perfectly possible for most of
the rows.

A set gathered by hand across views will hold a mail row sooner or later, and
an action that gave up on account of one would make marking useless in the
inbox, which is where the rows most want gathering. So the write takes what it
owns, leaves the rest, and says how many it left — a count rather than a list,
because the rows it passed over are not the ones being asked about.

### Bulk ticking does not file mail

On a mail row the tick key means something else: it files the message away on
the server, and the board confirms it separately. Folding that into a bulk
tick would make one keypress do two unlike things to two kinds of row, one of
them reaching an account over the network.

So a mail row in a marked set is passed over by the tick key like any other
row the board does not own, and reviewing stays where the wording already
carries its meaning.

### A toggle drives the set to one state

Where any marked row lacks the state, all of them are given it; where all have
it, all lose it. The alternative — each row flipping against its own state —
is what a loop over the single-row code would produce by accident, and it
answers a question nobody asks. Somebody pressing the tick key over a set
means to finish it.

Reading the state off the row under the cursor was considered and is
incoherent here: the cursor takes no part, and may be on a row that is not in
the set at all.

### The confirmation says what cannot be seen

A marked set can hold rows from three views. Before a deletion the board
already asks; the question now carries the count, and says when the set
reaches past the view on screen.

That second half matters more than it looks. The count alone reads as
confirmation of what is visible, and a person who marked rows on Monday and
walked to Wednesday would answer it about the wrong rows.

### The prompts run once

The date and the project are asked for once and applied to the set. Asking per
row would be the twenty-questions problem the undo-and-confirmation rule warns
about, and the answer is the same for every row by construction — it is one
decision about a set somebody chose.

## Risks / Trade-offs

**A set stays marked after being written to** → Chosen deliberately, so that a
batch can be ticked and then copied, or copied and then deleted. The cost is
that the set stays armed until escape clears it, and a second press of a write
key acts on it again. Mitigated by the count on the status line and by every
irreversible path asking first; not mitigated by anything else, and that is
the trade accepted.

**A write reaches rows that are not on screen** → The whole point, and also the
hazard. The confirmation before a deletion says when the set reaches past the
shown view. Nothing says it before a tick or a date, because those undo.

**Seven actions, one rule, written seven times** → The risk is that one of them
is missed or drifts, and nothing would fail: it would simply go on acting on
the selected row. The task list checks each of the seven by name rather than
checking the rule once, because a rule checked once is a rule checked where it
was remembered.

**The store refusing a large set** → Already answered. The queue and its width
are reused unchanged, and the width came from measuring the store rather than
from judgement.
