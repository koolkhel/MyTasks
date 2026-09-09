## Why

Two suites answer about the moment they ran rather than about the code.

`t_elapsed` builds its fixtures from the wall-clock hour and clamps the end of
each to 23. At the top of the day that clamp inverts what the fixture means: at
23:00 the event meant to be *under way* becomes 22:00–23:00, which is already
over. Three blocks do it, and the suite is red for the last two hours of every
day.

| block | wrong at hours |
| --- | --- |
| the three positions in time | 23 |
| with no reference at all | 22, 23 |
| keeping up as the hour passes | 23 |

`t_busy` fails the other way round, and is the more interesting of the two. Its
narrow-terminal case asserts that at 40 columns the mailbox mark is dropped for
want of room. The bar it measures is a date, built by the board, and the
threshold sits one character away: the line must reach 37 characters for the
mark to go, and in September only a Wednesday's name is long enough. It was
written on a Wednesday.

| the day it runs | the bar | the mark |
| --- | --- | --- |
| Wednesday | 37 chars | dropped — what the suite expects |
| Thursday | 36 chars | shown — fails |
| Friday | 34 chars | shown — fails |

The check is not testing that the mark is dropped when it will not fit. It is
testing that today's date happens to be wider than 40 columns.

The two are the same family and different kinds, which matters for finding the
next one. `t_elapsed` does arithmetic on the clock and a search for that finds
it. `t_busy` contains no date handling at all — not a format string, not an
hour — and asserts a layout threshold against text the board built from today's
date. A sweep of the suites for clock use would walk straight past it.

Both failures also break a requirement already written down: a suite failing
for a reason predating the work in hand is to be listed as known to fail with a
reason, because otherwise every run starts red and a red run cannot answer the
question the suites exist to answer. Neither is listed. The same requirement
says which way to resolve it — a suite is not to be listed merely because it is
inconvenient — so these get fixed rather than recorded.

## What Changes

- `t_elapsed`'s fixtures stop being clamped. An event *under way* becomes the
  current hour to the next, which is what an event spanning now looks like at
  every hour of the day; the helper already rolls an end hour of 24 to the next
  day's midnight, so nothing new is needed to express it.
- Where a position genuinely cannot exist, the suite skips it and says so
  rather than building something that claims to be it: at midnight nothing has
  ended today, and in the last hour nothing is still to come. The guards become
  exactly those conditions.
- `t_busy` stops asserting a width. It measures the bar, then brackets the
  boundary: the mark is shown one column above where it fits and dropped one
  column below. That is the board's own rule rather than a coincidence of the
  date, and it pins the boundary instead of sampling one side of it.
- Each fixed suite gains a check that it holds at hours other than the one it
  is running in, so the fix is demonstrated rather than waited for.
- Neither suite is added to the known-failure list. Both stop failing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite`: one new requirement, that a suite's result does not depend on
  when it runs — covering both kinds, the fixture built from the clock and the
  threshold asserted against text the product builds from a date. It sits
  beside the requirement that a suite never writes to the fixture it reads,
  which has the same shape and the same reason.

## Impact

- `tests/stub/t_elapsed.py` — three fixture-building blocks and their guards.
- `tests/stub/t_busy.py` — the narrow-terminal case.
- No product code. Nothing about the board changes; these suites are wrong
  about a board that is right.
- `tests/known_failures.py` is deliberately not touched.
- No live tier. Both suites are self-contained and need no credentials.
