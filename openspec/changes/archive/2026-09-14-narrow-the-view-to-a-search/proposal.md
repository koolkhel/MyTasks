## Why

The inbox is long. Measured against the real folders, it holds some 1,200
unread messages folding to some 570 rows, beside the day's own tasks. Finding
one thread in it means scrolling and reading, because the board offers no way
to look for anything at all.

Every other way of shortening a view is already there -- the inbox withholds
filed tasks, the work filter removes a project, the working window removes it
by the clock -- and all of them decide for the person. This is the one that
lets the person decide.

## What Changes

- A key opens a prompt for a search term. Confirming it narrows every view to
  the rows whose title contains that term; escape clears it and the rows come
  back.
- The term is matched against the row's title alone: a mail row's subject, a
  task's, an event's or a tracker issue's title. Not the sender, the project,
  the date, or the body of a message.
- It is matched against the title the row carries, not the string drawn in the
  cell -- before the thread count is appended to a mail subject, and before the
  column truncates it to fit. A word a person can read on the focus card is
  otherwise unfindable because the column cut it off.
- Every source the view draws is narrowed: the store's tasks, mail threads,
  calendar events and tracker issues. The narrowing happens where the work
  filter already happens, so no source can reach the view past it.
- The search lasts across view changes and for as long as the board is open,
  as the work filter does. Moving between the inbox, a day and the someday
  view does not change what it means.
- The board says a search is narrowing the view wherever it already reports
  what the view holds -- including when the search hides nothing, and when it
  hides everything. A view that is quietly shorter must not be
  indistinguishable from a light day, and an empty one must not be
  indistinguishable from a board that has broken.
- Nothing is written. The search decides which of the rows a view already
  chose are drawn, and changes no task.
- Two keys open it: `/`, which is the character this gesture carries in `vi`,
  `less` and every pager since; and `;`, because `/` alone cannot satisfy the
  board's promise that every key works in either keyboard layout.

### Why the search key needs two keys

The board binds 62 keys across 30 actions today, every Latin one paired with
the character its physical key produces in a Russian layout, and no two
actions sharing a key. The `/` key produces `.` in that layout, which is
already "done for today"; its shifted character `,` is already help's twin. So
`/` is the first key the board has wanted whose physical twin is spent, and
binding it alone would either collide with an existing action or leave search
reachable in one layout only.

A second key, freely chosen from the keys whose twins are free, keeps the
promise that matters -- the action is reachable in either layout -- without
moving an action a person already knows. `;` is punctuation rather than a
letter, so it spends no mnemonic that a later action might want.

## Capabilities

### New Capabilities

None. This is the board behaving differently, not a new area of it.

### Modified Capabilities

- `task-board`: three requirements added -- what the search does and what it
  matches, how long it lasts and where it applies, and what the board says
  while one is in force. One requirement modified: *Keys work in either
  keyboard layout*, which today admits no case where a key's physical twin is
  already spent by another action.

## Impact

**Code** -- `main.py`: a new attribute for the live search term; one filtering
step in `repaint`, beside the work filter's; a count of what it removed; a note
in the day bar and one on the status line; two bindings and an escape binding;
a prompt screen; and an entry in `Help.TEXT`, which is written by hand rather
than derived from the bindings.

**Tests** -- a new suite under `tests/stub/`. Nothing here needs an account, a
network or a mailbox: the fixtures already build mail rows, calendar events and
tracker issues for the existing suites.

**Not affected** -- no request is sent, no task changes, and the mailbox
indicator keeps reading the mailbox rather than the drawn rows, so a search
cannot hide unfinished mail work or a mail failure behind a short list.

## Assumptions recorded

- **Case-insensitive.** Searching a subject line for a word should not depend
  on how the sender capitalised it.
- **A plain substring**, not a pattern or a fuzzy match. The board can gain a
  richer match later without changing what the key means; starting rich and
  narrowing later would change it.
- **The two filters compose.** With the work filter on as well, a row is drawn
  only if it survives both. Neither key clears the other.
