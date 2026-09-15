## Context

See proposal.md — Why. What follows is only what the board's existing shape
forces on the approach.

Four facts about the board decide most of this change.

The view is rebuilt, not adjusted. `repaint` clears the table and reconstructs
every row from the fetched tasks and the pending writes, and it runs whenever
a write lands, a fetch answers, or any source replies. Rows move under a
person constantly.

The leftmost two columns are already spoken for, and narrow. The table has a
one-cell column for the green star and a two-cell column for the row's own
mark — the tick box for a task, and a character of its own for a mail row, an
event and a tracker issue.

A write is queued against a task's identifier and drained by a worker of its
own. When the first write in a queue is a creation, confirming it trades the
placeholder identifier for the real one and moves the queue, the worker and
the selection across together, so a write queued behind a creation reaches the
task that creation made.

The store has no way to create a finished task. Completion is a separate call
against a task that already exists.

## Goals / Non-Goals

**Goals:**

- Marking that survives everything the board does to its own rows.
- A reader and a writer for the text that are pure functions of their input,
  so both directions can be checked without a board, a store or a terminal.
- A paste that is one action end to end: one undo, one report, one ordering.

**Non-Goals:**

- Matching a pasted line to a task that already exists. Ruled out by the
  person asking for this: five lines mean five tasks.
- Carrying any structure the outliner had — nesting, projects, tags. The store
  has no sub-tasks, so an indented line is a task like any other.
- Restoring cancelled state on the way in. See the decision below.
- A second selection model for the write keys. Marks are read by the copy key
  and by nothing else.

## Decisions

### Marks are an ordered list of row identifiers, not a range of lines

A visual range in the style of vim is anchored to line numbers. Here that
fails within seconds: `repaint` rebuilds the table from scratch whenever a
background write confirms, and the rows reorder. A range would silently slide
onto different rows.

Identifiers survive that untouched, and they also give marks across views for
free, which is what the person asked for — the rows they want to break down
are not all on one day.

Ordered rather than a set because the copied lines have to come out in some
defined order, and the order the views drew them in is not defined when the
marks come from three different views. The order of marking is.

Alternative considered and rejected: a range plus a second "add to selection"
key, which is two concepts where one does.

### The mark is drawn in the row-mark column, which has a free cell

That column is two cells wide and every row draws one character in it. Putting
the mark in the spare cell costs no width anywhere, which matters on a board
that already fits its title column to the terminal and has a requirement about
doing so.

The mark must survive the cursor. This was measured for the strike on a
finished mail row: the cursor replaces a colour outright, while a style such
as dim or strike survives. A glyph is not a style at all, so it survives by
construction — which is the second reason to prefer a character here over
colouring the row.

Measured rather than assumed, before anything was written: the column is two
cells wide, every kind of row -- task, mail, event, tracker issue -- draws
exactly one character in it, and putting a two-character value there changed
neither the table's width nor the title column's. The board's own row-overhead
arithmetic reserves those two cells, so the width is fixed rather than fitted
and a second character cannot reflow anything. The spare cell is real and the
fallback of widening the column is not needed.

### Both clipboard routes, not one

Textual writes the clipboard with an escape sequence the terminal interprets.
Its own documentation says this does not work on macOS Terminal; iTerm needs a
preference turned on; kitty allows it by default. It does work through a
remote session.

`pbcopy` always works on this machine and never works through a remote
session. The board already starts programs for opening links and workspaces,
so a subprocess is in character.

The two cover different halves and neither covers both, so do both. Writing to
a clipboard twice is harmless.

### The paste handler goes on the board, and the prompt's own paste is overridden

The terminal delivers pasted text to the application as one event carrying the
whole text. The board has no handler, so today it is discarded — that is why
pasting needs no key.

The prompt for a title is a different matter. The input widget the prompt uses
takes the first line of a paste, drops the rest, and stops the event before
anything else sees it. That behaviour is live now and loses work silently.
Overriding it in the board's own prompt is the fix; what it should do instead
— refuse, or accept and add the tasks — is settled by the spec, not here.

### A finished pasted line is a creation with a completion queued behind it

The store cannot create a finished task, so `- [x]` is two calls. This needs no
new machinery: the second is queued against the placeholder identifier, and
the existing adoption moves the queue onto the real identifier when the
creation confirms. That path exists because a person can already act on a task
they have just added.

### Ordering is computed once for the whole paste

The board picks the stored order it sends rather than letting the API default
it, by reading the last place in the day and adding a step. Read once per
task, before any write lands, that answers the same number every time and ties
every pasted task together — they would then be ordered by title, and the
sequence the person pasted would be gone.

So the paste reads the day's last place once and spaces its own tasks from
there. This is the one place the existing rule needed extending rather than
reusing.

### Cancelled goes out but does not come back

A cancelled task is written with a ticked box and its title struck through, so
that it is not read back as an ordinary finished task and so the distinction is
visible in the editor. Coming the other way the tildes are stripped and the
task is finished, not cancelled.

Restoring it would mean a third call per line against yet another endpoint, to
recover a state the person is unlikely to have meant to recreate from a
breakdown. The asymmetry is deliberate and is stated in the spec so that it is
not discovered as a bug.

### Undo deletes, which this board otherwise refuses

One paste is one undo group, reversed by deleting the tasks it created. The
board refuses this in general — the undo key does not delete — but it already
makes the exception for a promoted mail thread, for the argument that applies
here too: the same action created the task, it holds nothing but what that
action put there, and no time has passed for anything to depend on it.

This change resolves the resulting contradiction in the spec rather than
adding to it. The old requirement promised that no undo ever deletes a task,
while the mail requirement already described one that does. It is retired and
reissued with the exception stated.

## Risks / Trade-offs

**A paste of many lines sends many requests at once** → Each task gets its own
drain worker, so N lines start N workers and the store sees them together, and
nothing in the client paces them. Measured against the real store before
anything was written, creating tasks in parallel at four widths: 5 of 5 and 10
of 10 were created, 17 of 20, and 5 of 40. The refusals were HTTP 500 naming a
server-side queue and its depth -- 3 deep at a width of 20 and 30 deep at 40 --
so this is the store's own queue backing up rather than a rate limit, and a
paste of forty lines unpaced would have lost thirty-five tasks without a word.

So the paste caps how many creations are in flight. The cap is 5 rather than
the 10 that also passed: the board makes writes of its own while a paste is
running -- a tick, a move, a fetch answering -- and a paste that took the whole
proven-safe budget would push those into the same failure. Every request took
about the same time whatever the width, so the cost of the smaller cap is
rounds rather than throughput: forty lines in eight rounds instead of four,
against a board that has already drawn them all.

Retrying a refusal is deliberately not the answer. The status was 500 and not
429, so the store accepted the request and failed inside it; a retry could
leave two tasks where the person pasted one line, and nothing in the response
says which happened. Failures are reported and their rows withdrawn instead.

**Marks that cannot be seen** → A mark survives a view switch and a filter, so
a person can copy a row that is not on screen. Mitigated by the count, which
reports every mark including the invisible ones, and by escape clearing them
all. The alternative — dropping marks on a view change — would defeat the
whole point, since the rows being gathered are on different days.

**The clipboard may not arrive** → If the terminal ignores the escape sequence
and the subprocess is unavailable, the copy silently does nothing. The board
says what it copied, which is a report that the copy ran rather than proof it
landed; there is no way to read the clipboard back to confirm. Worth stating
plainly rather than pretending to verify.

**A pasted line is not validated** → Whatever the editor left in the line
becomes the title. This is the deliberate choice — guessing is worse — but it
means a paste of the wrong thing creates a screenful of nonsense tasks. The
single undo is what makes that recoverable, which is why it is a requirement
rather than a convenience.
