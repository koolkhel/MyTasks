## Context

See proposal.md — Why.

Three facts from the existing board shape everything below.

The key that opens a link already branches once: it takes a tracker row's own
page from a marked field on the row, and otherwise takes whatever address is
found in a task's title. An event is a third case on a line that already has
two.

The detail area already draws the selected row's note from a single field. A
row that carries a note in that field gets it drawn with no new code.

And the rule for what counts as an openable address — a scheme allowlist, plus
the reading of a bare host as `https` — lives with the task code and is used
today for task titles. It is one rule, in one place, and it decides what the
board is willing to hand to the operating system.

Measured on this machine over 42 days, from the configured accounts:

```
   events examined                            128
     with a description                        47
     with an address in the description        47
     with an address in the location           47
     where the two named the SAME address      47
     where location was ONLY the address       41
     with the calendar's dedicated URL field    0
     addresses per event, where any             1
   description length: 3-12 lines, 35-856 characters, no markup
```

All 47 come from the work account and one meeting system, over 13 distinct
repeating series. The personal account carries no descriptions at all.

## Goals / Non-Goals

**Goals:**

- The address that joins a meeting, one keystroke from the row.
- What a meeting is for, readable without leaving the board.

**Non-Goals:**

- Opening a link found in a *task's* note. The same blind spot exists there —
  a task's address is read from its title only — but it is a different row
  type with different evidence, and folding it in here would change behaviour
  for tasks that work today. Deliberately left alone.
- Anything that writes to the calendar. Following what the calendar points at
  is still reading it.
- Recognising particular meeting providers. The board opens an address; it
  does not know what is on the other end.

## Decisions

**The calendar module carries the text; the board decides what may be opened.**

`ical.py` gains the event's location and description verbatim and stops there.
The board resolves which of them holds an address, using the same function
that already decides it for a task's title.

The alternative — an `url` property on the event record — reads better in
isolation and was rejected. It would need the scheme allowlist, which means a
second copy of a security-relevant rule that must never drift from the first.
`ical.py` imports nothing of the board's today, exactly as `tracker.py` does
not, and that separation is worth more than the tidier record. What may be
launched is a property of the board, not of the calendar.

**Location first, description second.**

Not because one is more correct: where both were filled here, all 47 agreed.
It is that the location is *only* the address in 41 of 47, so there is nothing
to parse, while a description is prose with an address somewhere inside it.
Preferring the unambiguous field means the parsing path is the fallback rather
than the norm.

Both are read because a calendar system may fill either. A location is also
where a physical address or a room name goes, which is exactly why finding no
openable address there must fall through rather than conclude there is none.

**The description travels in the field the detail area already draws.**

The event row puts its description where a task keeps its note. The detail
area then needs no knowledge of events at all, and an event's description
cannot come to be drawn differently from a task's note, because it is drawn by
the same code.

**The resolved address travels in the row's own field, beside the tracker's.**

The row carries the address it resolved to, in a field of its own, and the
opening action reads it for an event as it already reads the tracker's for an
issue. Resolving once when the row is built rather than each time the key is
pressed keeps the parsing off the keystroke and out of the drawing path.

**A description is escaped before it is drawn.**

The detail area renders its text as markup: given `[bold]` it applies a style,
and given `plain [x] text` it draws `plain  text` — the bracketed characters
are consumed. A description is written by whoever created the meeting, which
for a work calendar is somebody else, so its characters must be shown rather
than obeyed. It is escaped on the way in.

## Risks / Trade-offs

**Generalising from one meeting system** → Named rather than hidden. Every
event with an address here comes from one account and one provider; the
personal account offers no evidence at all. Reading both fields instead of the
one this provider fills is the whole mitigation — it costs nothing and is what
makes a second provider likely to work without a change. If one appears that
puts the address somewhere else again, that is a new change with new evidence,
not a guess made now.

**A description is text written by other people** → Escaped before drawing, so
its characters are shown rather than interpreted. The board draws it and does
nothing else with it: it is never treated as instruction, never parsed for
anything but an address, and never leaves the machine.

**The same field is unescaped for a task's note today** → Observed while
designing this, and left alone. A note containing square brackets already
loses them in the detail area. It is a real defect, it predates this change,
and fixing it would alter behaviour for existing tasks under a change scoped
to events. Recorded here so it is found deliberately rather than rediscovered.

**A long description in a short terminal** → The detail area grows to fit its
content and stops at two fifths of the height, which clips rather than
scrolls. A 12-line description — the longest measured — fits a full-height
terminal and would be cut in a very short one. This is how a long task note
already behaves; making that area scrollable is its own change, and nothing
here makes the situation worse than the notes already do.

**Descriptions are personal content** → They now sit in the row's data and on
the screen. They are never written to disk, never sent anywhere, and must not
reach a test fixture, a captured board state, a commit message or a log. The
suite uses synthetic events; verification against the real calendar reports
counts only, never a description and never a title — the rule the calendar
block already follows.

**More than one address in a description** → Every event measured had exactly
one, so this is undefined by evidence rather than by design. The first that
may be opened wins, stated in the requirement, so the behaviour is defined
even where the evidence is silent.
