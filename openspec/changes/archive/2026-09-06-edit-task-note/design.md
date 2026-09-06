## Context

See proposal.md — Why.

The board already has everything except the writing. Notes decode through one
existing property; every write already goes through one funnel that applies a
patch at once, queues the request, records an undo entry, and refuses rows the
board does not own. Adding a field to that funnel is the ordinary case.

What the format actually is, since the name misleads. A note is a **string**
holding a Quill delta: a document described as the inserts that would build it
from nothing, not a difference against a previous version.

```
   '[{"insert": "buy milk\n"}]'            one op -- the whole note

   '[{"insert": "buy "},                   a styled run
     {"insert": "milk", "attributes": {"bold": true}},
     {"insert": "\n"}]'

   [{"insert": "one"}, {"insert": "\n", "attributes": {"list": "bullet"}}]
                                            ^ line kind hangs off the NEWLINE

   [{"insert": {"image": "..."}}]           an embed: insert is not a string
```

Measured across 306 tasks on this account:

```
   notes present                     52
     shape: single insert op         52   (every one)
     ending in a newline             52   (every one)
     carrying a formatting attribute  0
     carrying an embed                0
   notes whose text is empty ("\n" alone)  10
```

So the decoder that exists is already complete for this data, and the encoder
is its mirror.

## Goals / Non-Goals

**Goals:**

- A note that can be written where it is read.
- A note that cannot be silently damaged by being written.

**Non-Goals:**

- Rich text. The board shows a note as text and will store it as text.
- TaskPaper structure — tags, projects, folding, filtering by tag. Deliberately
  out, and see the decision below on why the editor is nevertheless built as
  something that could grow it.
- Editing an event's description or a tracker issue's fields. Those rows are
  read-only everywhere else and stay so here.
- Anything about how notes are stored. The board starts writing a field it has
  only ever read; the field itself is unchanged.

## Decisions

**An editor inside the board, not the one in `$EDITOR`.**

An external editor was the first idea and was rejected on evidence. Handing the
terminal over needs the framework's suspend, and suspend **raises in the
environment the suites run in** — verified, not assumed. That makes the whole
path structurally unverifiable, in a board where every other feature is pinned
by a suite. It also imports failure modes that belong to the person's
environment rather than to this program: no editor configured, an editor that
opens a window and returns immediately, a terminal that cannot be restored.

The framework's own text component costs none of that. It arrives with
multi-line editing, soft wrap, undo and redo, cut, copy, paste and line
deletion already bound, and it can be driven key by key by the harness. The
trade is a person's own editor keys, which is a real loss and the reason the
door below is left open.

**The editor is a component of the board's, not the stock one used directly.**

A subclass with nothing added yet. Keys that act on the text — insert a
template, stamp a date, transform a line, toggle a marker — are then bindings
on a class that already exists, rather than a reason to restructure later. This
costs nothing now: it is a class statement and a name.

It is also where an "open this in `$EDITOR`" key would go if notes ever grow
past what a modal wants to hold. The external editor is rejected as *the*
answer, not as *an* answer.

**Refuse a note the board cannot represent; do not flatten it.**

Nothing in this account carries formatting today, so this changes nothing now.
It matters the first time something is styled in another client: the board
would have to drop the styling to save, and a person who cannot see what was
dropped cannot object to it. A refusal is a few lines and turns silent loss
into a sentence.

The check is exactly the two shapes above: an op with `attributes`, or an
`insert` that is not a string.

**Encode to one op, and keep the trailing newline.**

All 52 notes end in a newline because a Quill document always does; an encoder
that omits it produces a document the editor on the other end considers
malformed. Text is written as a single insert with a newline assured.

Clearing a note is not writing an empty string but a document holding only a
newline — the shape ten notes on this account already have, and which the
existing decoder already reads as empty because it strips.

**Escaping the note in the detail area belongs to this change.**

That area renders markup, so a note holding `[x]` loses those characters on
screen today. Read-only, that is a display curiosity nobody would notice. The
moment a person can type them, the board appears to eat what they just wrote —
and the store would be fine, which makes it worse, because there is nothing to
find when they go looking. The escape is one call at the point of drawing, the
same one an event's description already gets.

## Risks / Trade-offs

**Losing a person's own editor keys** → Accepted, and the reason the editor is
a class rather than a stock widget. What the framework binds already — undo,
redo, cut, copy, paste, line deletion, word motion — covers the ordinary edit.
Notes on this account are one line and 74 characters, though that number should
be trusted lightly: it describes what the current tooling permits, not what a
person would write once writing is possible, and its uniformity suggests those
notes were not written by hand at all.

**The saving key and the keyboard layout** → A real gap to check before
choosing it. The board twins every letter binding with its Russian counterpart,
but the helper that does so does not expand a modifier combination — `ctrl+s`
comes back as `ctrl+s` alone. Whether a terminal delivers `ctrl+s` or
`ctrl+`-something-else under a Russian layout has to be measured in the
terminal rather than reasoned about; if it does differ, teaching the helper to
split a modifier prefix and twin the letter is small and general. A key that is
not a letter avoids the question entirely.

**Undo sending a null** → Already met once, on tags. The funnel records the
previous value as whatever the raw task held, so a task with no note records
nothing, and undo would send a null the store refuses. Settling the field to an
empty document before the write is recorded is the same fix that change made,
and it is written here so it is not rediscovered by a failing request.

**A write that changes nothing** → Saving unchanged text spends a request and
an undo entry for no reason. Compared before writing.

**The editor and the ordering of writes** → The editor holds the text a person
saw when it opened. A write confirming underneath it, or a refresh replacing
the task, could make that stale. The window is a person's own editing session,
the board is one person's, and every other prompt on the board has the same
property, so this is accepted rather than solved — noted so that a later report
of a note reverting is recognised rather than investigated from nothing.
