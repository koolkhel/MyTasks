## Context

See proposal.md for motivation.

What shapes the approach is that the board already has a filter, and it was
built carefully. `repaint` builds every source -- the store's tasks, the
tracker's issues, the calendar's events, the mailbox's threads -- and then
filters them all at one place, with a comment recording why: mail was once
appended *after* the work filter and went unhidden for three changes, because
a source added past the filter is a source no key can reach, however its rows
are marked. A second filter either joins that line or repeats that bug.

Three further facts measured in the current tree, which the decisions below
rest on:

- **Textual 8.2.8.** `DataTable.BINDINGS` holds 11 keys -- enter, the four
  arrows, page up and down, ctrl+home, ctrl+end, home, end -- and `App.BINDINGS`
  holds `ctrl+q` and `ctrl+c`. Escape is bound by neither, so an app-level
  escape binding receives the key while the table has focus.
- **The board binds 62 keys across 30 actions, with no collisions.** Every
  Latin key is paired with the character its physical key produces in a Russian
  layout. The `/` key produces `.` there, which is "done for today"; its shifted
  `,` is help's twin. `/` is the first key the board has wanted whose twin is
  already spent.
- **Scale.** The real inbox is some 570 rows folded from some 1,200 messages.
  A substring test over 570 titles is not a cost worth designing around.

## Goals / Non-Goals

**Goals:**

- One more filter, sitting where the existing filter sits, composing with it.
- The search survives every redraw the board performs for its own reasons --
  a write confirming, mail arriving, the tracker answering.
- The board is never quietly shorter. An empty view explains itself.

**Non-Goals:**

- **No next/prev match keys.** `n`/`N` were the original request, from a
  jump-style search. With a filter the results *are* the list, so `j` and `k`
  already walk them. Adding match-stepping keys would spend `n` (Note) or a
  letter for a gesture that duplicates the arrow keys.
- **No as-you-type preview.** See the prompt decision below.
- **No regular expressions, no fuzzy matching, no field-qualified terms.** The
  board can grow a richer match later without changing what the key means.
- **No persistence.** The search is not written anywhere and does not survive
  the board closing.

## Decisions

### The filter goes where the work filter goes

One attribute holding the live term, read by `repaint` and by nothing that
depends on the clock -- the same shape as `hiding_work`, and for the same
reason: `repaint` consults it more than once and must see one answer.

The filtering happens in the block that already filters, after every source is
built and before the sources are placed among each other. Filtering a list
preserves the order of what survives, so narrowing cannot disturb the ordering
the sort produced.

*Alternative considered: filter in `belongs()`.* Rejected twice over. `belongs`
answers where a task *lives*, which is the question the work filter's own
design was careful not to disturb; and mail, events and issues never pass
through `belongs` at all, so a filter there would reach only the store's tasks
-- exactly the bug the existing comment was written about.

### The term is matched against the title the row carries

Not the string drawn in the cell. The cell has been through three
transformations by the time it is drawn: `escape()` turns `[` into `\[`,
a mail subject gains ` (3)` for its thread count, and `shortened()` cuts it to
the column width. Matching the drawn string would mean a bracket in a subject
defeating a search, a search for a digit hitting thread counts, and a long
subject being findable only by its first few words.

One function answers "what does this row's search read as", used by nothing
else, so the drawn cell and the searched text cannot drift apart as the row
format changes.

### Escape clears it, and the prompt's escape is a different escape

Escape is bound at app level, verified unbound by Textual's own `DataTable` and
`App` in the installed version.

While the prompt is open it is a modal screen, and a modal's bindings take the
key first -- so escape inside the prompt cancels the prompt and leaves any live
search untouched, while escape on the board clears the search. Two meanings,
each unambiguous in its context, and the same split `less` has.

### The prompt is a modal, like every other prompt on this board

*Alternative considered: a one-line input on the status row*, which is what
`vi` and `less` show and what would allow narrowing as the person types.
Rejected for this change. It would be the board's first inline editing widget
and the first time focus leaves the table -- and the note pane's comment
records the board's position on that directly: a pane that could hold focus
"would take the arrow keys off the list the moment it was tabbed into -- a
mode, which this board does not have."

The modal costs the as-you-type preview and nothing else. If the preview turns
out to be what makes this feature good, moving the prompt to the status row is
a later change that alters no requirement written here.

### Two keys, `/` and `;`

`/` because that is the character this gesture carries in `vi`, `less`, `man`
and every pager since, and it is what was asked for.

`;` because `/` alone cannot be reached in a Russian layout and the board
promises every action can be. `;` is punctuation rather than a letter, so it
spends no mnemonic a later action might want, and its Russian character `ж` is
free. The key bar names a binding by its first key, so the bar goes on reading
`/`.

*Alternative considered: `/` alone, with the layout requirement amended to
allow an exception.* Rejected: the requirement exists precisely to stop an
action being reachable in one layout only, and help is required to state that
the keys work in either layout -- which would become untrue.

*Alternative considered: dropping `/` for a twin-safe letter.* Rejected: it
satisfies the letter of the rule by giving up the idiom that made the feature
worth asking for.

### What the board says, said twice

The day bar carries the term; the status line carries how many rows were
removed. That is the division the work filter already uses -- `work_note()` in
the bar, `N work hidden` on the status line -- and copying it keeps two filters
reading the same way rather than each inventing its own place.

Both are said whenever a search is in force, including when it removed nothing.
`work_note`'s docstring already argues this and the argument carries over
unchanged: a mode that hides nothing is otherwise indistinguishable from a key
that does not work.

## Risks / Trade-offs

**A bare escape can arrive late, because escape is also the first byte of every
arrow-key sequence.** Terminals disambiguate by timing and Textual handles
this, but I have not measured what the delay is here or whether it is
noticeable. → Measure it during apply against the running board; if a clear
feels sluggish, the fix is a second key for clearing, not a redesign.

**A future source appended after the filtering silently escapes the search.**
This has already happened once on this board, with mail and the work filter. →
The suite asserts it per source rather than in general: a check for each of
tasks, mail, events and issues, so adding a fifth source without a check is
visible as an absence rather than passing quietly.

**The restored scroll position can point past the end of a narrowed list.**
`hold_view` puts the view back where it was before reconciling the cursor. →
Already handled: `scroll_to` clamps, and the position is read back rather than
assumed, which is what the existing code does and comments on.

**A search that matches nothing leaves a person with an empty board and one
key to get out of it.** → This is the specified behaviour, chosen deliberately.
The mitigation is not a different behaviour but the reporting requirement: the
term is on the day bar in every view, so the board always says what it is
doing.

**Two filters mean two keys to get back to a full board.** → Accepted. Folding
them into one clear-everything key would give the work filter a third state,
which its requirement forbids in as many words.

## Privacy

Nothing here writes to the mailbox log, which is required not to record a
subject, a sender or any part of a body. The search term is a person's words
about their own mail and the matched rows are subjects; neither is recorded
anywhere, which is achieved by the search doing no logging at all rather than
by filtering what it logs.
