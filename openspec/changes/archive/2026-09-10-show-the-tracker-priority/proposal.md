## Why

The tracker block shows what is being worked on now, and says nothing about
how urgent any of it is. A person triaging four issues in progress has to open
each one to find out which the tracker calls urgent.

The board already fetches the answer. `ISSUE_FIELDS` asks for every custom
field the tracker has, and the parser keeps each one by name, so an issue's
priority arrives with every fetch and is thrown away. Only the value's
localised name is missing from the request, and that is one token.

The letter is derivable rather than invented. The tracker names its own
priorities, and their first letters are the ones a person already reads off
its web interface:

| the tracker's own name | letter | the value the API sends |
| --- | --- | --- |
| Неотложная | Н | Show-stopper |
| Критический | К | Critical |
| Серьезная | С | Major |
| Обычный | О | Normal |
| Незначительный | н | Minor |

This is the same move the board already makes for a tracker state, where it
keeps the last word of whatever the tracker calls it rather than carrying a
list of states in its own source.

Two letters collide, and it is the worst pair available: **Н** is both
Неотложная, meaning drop everything, and Незначительный, meaning ignore.
Lower case separates them. The letter said quietly is the quiet one, which
keeps every letter meaning what a person reading the tracker expects and does
not pretend the two words start differently.

## What Changes

- A tracker row shows its priority as one letter, in the leftmost column,
  which is empty on every tracker row today: that column carries the
  configured tag's mark, and a tracker row carries no tags at all.
- The letter is the first letter of the name the tracker gives the priority,
  upper case, except the lowest priority which is lower case.
- An issue with no priority set shows nothing, as it does now.
- The request gains the localised name of a custom field's value. No extra
  call, no extra page, nothing else asked for.
- **Not** coloured, and **not** ordered by priority. Both were measured
  against the real tracker and both are unusable — see below. The row's order
  and every other cell are unchanged.

## Capabilities

### Modified Capabilities

- `task-board`: one new requirement for the priority letter — where it is,
  where it comes from, and how the two words sharing a letter are told apart.
  Added rather than folded into the requirement that lists what a tracker row
  carries: that requirement's behaviour is unchanged, and a modification would
  have to restate its ten scenarios to add nothing to any of them.

### New Capabilities

None.

## Impact

- `tracker.py` — one token added to the fields asked for, and the priority
  read out of the custom fields the parser already collects into an `Issue`.
- `main.py` — the tracker row carries the priority, and `row_for` puts the
  letter in the leftmost cell instead of the empty string it puts there now.
- Nothing is written anywhere. A tracker row already refuses every write, and
  this adds no key.
- The letter is Cyrillic, and a Cyrillic capital is East Asian Width
  *Ambiguous* — the class the mailbox marks deliberately avoid, because such a
  character may take two cells in a terminal configured for CJK while the
  column is one wide. A deliberate departure, recorded, and the alternative
  would be a letter from an alphabet a person does not read the tracker in.

## Why not colour, and why not order

Both were tried against the real tracker before being ruled out, and both fail
on the same fact: this tracker defines its priorities more than once, and the
definitions disagree.

- The tracker supplies each priority's own colour, which would have been the
  faithful thing to use. But the same priority carries different colours in
  different definitions — one names Critical red and another pink, one names
  Show-stopper the same red as Critical — so a colour would say two things and
  distinguish neither. That is before reaching the question of whether a
  person can read colour, and the answer here is that they would rather not.
- Ordering by priority would need the values to be comparable. Their ordinals
  run from -2 in one definition and from 0 in another, so a number means
  nothing across projects, and in one of them Critical sorts above
  Show-stopper.

The letter is the only part that means the same thing twice. Where the same
priority is worded differently — Обычный and Обычная, Серьезная and Серьезный,
gender differing between definitions — the first letter is unchanged.

## Why this does not reopen removing priority

An archived change took SingularityApp's priority out of the board in four
places, on the grounds that priorities were not part of how the board is used
and that each affordance was a way to change data by accident.

Neither reason reaches here. That was a writable field on a person's own
tasks; this is a read-only field on rows the board already refuses to change,
it adds no key, and the issues in question are exactly the work the board is
used for. The removal also left the client's priority handling in place
deliberately, so that a future caller could still read the field.
