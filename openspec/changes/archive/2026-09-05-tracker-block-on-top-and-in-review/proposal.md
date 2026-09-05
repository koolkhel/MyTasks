## Why

Two things are wrong with the tracker block now it has been used.

It sits at the bottom, after the day's finished tasks, which is where a
person stops looking. The issues it shows are the ones being worked on right
now, so they belong where the eye lands first.

And it shows only what the tracker calls in progress, which for this person
is one issue. The work waiting on review is equally theirs and equally
unfinished — eleven of them — and none of it appears.

Fixing either alone would be worse than fixing both: moving one row to the
top gains little, and adding eleven rows to the bottom buries them further.

## What Changes

- The block moves to the **top** of today's view, before every task the board
  manages, rather than after them.
- The states it shows become a configured list rather than one state, so the
  issues in review appear beside those in progress. Adding a third state
  later is a configuration change, not a code change.
- The block is ordered by that configured list and then by issue key, so the
  states appear in the order they are configured and what is being worked on
  can be put first. Within a state the order stays stable between fetches.
- Each row says which state its issue is in, in the column that until now
  said only "tracker" — a word the row's own mark already conveys. With more
  than one state shown, which one an issue is in is the thing a person needs
  and could not previously see.
- What the board reports about the view stops calling them "in progress",
  since they are no longer only that.

Deliberately not changed:

- **No colour is used to set the block apart.** The row's mark distinguishes
  a tracker row from a task, and the state label distinguishes tracker rows
  from each other. That is the distinction wanted, and it costs no palette.
- **The cursor still starts on the first row, whatever it is.** It is the
  simpler rule, and it is the one the board already follows. The consequence
  is accepted knowingly: with the block on top, the first key pressed after
  opening acts on a read-only row and is refused, so that refusal has to
  read clearly.
- Everything else about the block stands: read-only, today only, counting as
  work, opening in a browser, and the board carrying on when the tracker
  cannot be reached.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: what the block shows, where it sits, how it is ordered and
  what each row says all change, as does what the board calls the issues it
  is counting.

## Impact

- `tracker.py`: the configured state becomes a configured list; the query
  names each of them; the check that re-tests the selection locally asks
  whether a state is one of them rather than equal to one; the order becomes
  the configured position of the state, then the key.
- `main.py`: the block is joined before the day's rows rather than after; the
  row's second column carries the state; the count is named for what it is.
- `.env`: one setting renamed and given a list.
- No new dependency, no new request, and no change to how often the tracker
  is asked.

Two things deliberately survive untouched, which is the check that this is a
small change rather than a rethink: the block still takes no part in the
day's ordering — it is concatenated, only on the other side — and the filter
that hides work must still be applied to it, which was the subtle part and
is unaffected by which side it joins.
