## Context

See proposal.md — Why. The facts that shape the fixes, all measured:

- `t_elapsed`'s helper already handles an end hour of 24, rolling it to the
  next day's midnight. Nothing new is needed to express an event that runs to
  the end of the day; the clamps are working around a limit the helper does not
  have.
- Five fixtures across four blocks are clamped. Enumerating them by hour needs
  two columns, and the gap between them is the interesting part: the hours at
  which the fixture is not the position it claims, and the narrower set at
  which the suite actually goes red.

  | fixture | lies at | fails at |
  | --- | --- | --- |
  | `positions` — under way = `max(h-1,0) .. min(h+1,23)` | 23 | 23 |
  | `positions` — to come = `h+1 .. h+2`, guarded `h <= 21` | none | none |
  | no-reference — to come = `min(h+1,22) .. 23` | 22, 23 | 23 |
  | selected — to come = `min(h+1,22) .. 23` | 22, 23 | 23 |
  | keeping-up — crosses = `max(h-1,0) .. min(h+1,23)` | 23 | 23 |
  | keeping-up — to come = `min(h+2,22) .. 23` | 22, 23 | 23 |

  At hour 22 a clamped *to come* becomes 22:00–23:00, which is **under way**.
  The check asks only whether the row is receded, and an event that has started
  but not ended is not receded either — so it passes, for the wrong reason.
  That is worth more than the outright failures: an assertion passing on a
  fixture that means something else is the failure mode nobody goes looking
  for.

- The board decides an event has ended against the present, not against the
  fetch's `reference`, and its docstring says why: the two are deliberately
  different clocks answering different questions, and `reference` is absent on
  every day but today.
- **The suite already moves that clock.** `keeping_up` rebinds `main.datetime`
  to a subclass whose `now` runs three hours ahead, so an event's end can pass
  without waiting for it. The seam this design was going to describe as
  feasible-but-unbuilt is in the file already, which makes checking a fixture
  at an arbitrary hour a matter of aiming the existing technique rather than
  building anything.
- The mailbox mark is padded onto the day bar and dropped when
  `len(text) + 2 > room`, with `room` two columns narrower than the terminal.
  Measured on the live board: with a 36-character bar the mark shows at 40 and
  41 columns and is dropped at 38 and 39.

## Goals / Non-Goals

**Goals:**

- Each fixture correct at every hour it can be built at, by construction
  rather than by a range check.
- The narrow-terminal case testing the board's rule rather than today's date.

**Non-Goals:**

- A clock seam in the *product*. None is needed: the suite already rebinds the
  board's `datetime` for its own purposes, so the seam exists on the test side
  where it belongs. And a seam would not have caught the case that broke —
  `t_busy` reads no clock at all.
- A tool that sweeps the suites across simulated times. Attractive, and the
  wrong size for two suites and five fixtures. Noted below as what it would
  take, for whenever the class turns out to be bigger than it looks.
- Recording either suite as known to fail. The requirement that governs that
  list says a suite is not listed for being inconvenient, and both of these are
  fixable in an afternoon.
- Any change to the board. These suites are wrong about a board that is right.

## Decisions

### The fixtures are built to be true, not clamped into range

Three shapes replace all five clamped ones, each verified against every hour of
the day:

| position | fixture | wrong at | skipped at |
| --- | --- | --- | --- |
| spans now | `h .. h+1` | no hour | none |
| after now | `h+1 .. h+2` | no hour | 23 |
| before now | `0 .. h` | no hour | 0 |

`h .. h+1` is the whole of the fix for *under way* and *crosses*: the current
hour to the next contains the present at any minute, and at 23 the helper rolls
the end to midnight rather than clipping it back to 22:00, which is what
inverted the fixture. `0 .. h` for *over* also widens where the case can be
tested — an event ending at the top of the current hour has ended for any hour
from 1, where `h-2 .. h-1` needs 2.

The clamps were the bug, not a defence against one. `min(h+1, 23)` keeps the
number legal and makes the fixture false, which is the worst combination
available: nothing raises, and the assertion quietly reverses.

### A position that cannot exist is skipped, and the guard says which

Two cases genuinely have no example at some hours: at midnight nothing has
ended today, and in the last hour nothing is still to come. The guards become
exactly `h >= 1` and `h <= 22` — the conditions under which an example exists,
rather than the wider margins now in place.

One trap to keep in mind while doing it: the helper takes `start_h % 24`, so an
unguarded *to come* at hour 23 would ask for hour 24 and get **00:00 today** —
in the past. The check would then pass, for the opposite of its reason. The
guard is load-bearing, and a comment should say so, because the modulo makes
the failure silent rather than loud.

### The narrow-terminal case measures, then brackets

Render the bar wide, measure the text, and assert either side of the boundary
the board's own rule gives: shown at four columns above the text's length,
dropped at three. Verified on the live board at today's date, and derived from
the rule rather than from the date, so it holds on any day.

This is a stronger check than the one it replaces. The original sampled three
widths and asked whether the mark was there; two of the three were nowhere near
the boundary, and the third was on it by accident of the calendar. The
replacement pins the boundary itself.

Rejected: switching that case to the inbox view, whose label is a constant
length. It would be deterministic and would stop testing the thing worth
testing — that a long day bar pushes the mark out — which is the realistic way
a person meets this.

### No clock seam in the product, and no sweep tool yet

A sweep is feasible: the board imports `datetime` by name, so a runner could
rebind it and exec a suite under a chosen instant, and the suite's own reading
of the clock would follow because it happens at import. That is the shape to
build if this class turns out to be larger.

Against building it now: two suites and five fixtures do not need a harness,
and — the deciding argument — it would not have found the case that actually
broke. `t_busy` reads no clock. Its dependence lives in the length of a string
the board computed, and the only way to see it is to notice that a threshold
was asserted rather than measured. That is a habit, recorded as a requirement,
not something a sweep detects.

What each fixed suite does instead is smaller and enough: show the behaviour
holding at hours other than the one the run is in. For the fixtures that means
building the same three positions around several hours and asserting each is
what it claims; for the bar it means the bracket, which is already independent
of the moment.

## Risks / Trade-offs

- **A run crossing an hour boundary mid-suite** — `NOW` is read once at import,
  so a suite that starts at 10:59:59 could assert at 11:00:01 against fixtures
  built for hour 10 → read the hour where the fixture is built rather than at
  import, which narrows the window from the suite's whole runtime to
  milliseconds. Not eliminated: eliminating it needs the frozen clock this
  change is declining to build, and the residue is one run in some millions.
- **The bracket could drift if the board's padding changes** — it derives the
  boundary from a measurement plus a constant of four columns → the constant is
  the one thing still assumed. Asserting both sides of the boundary means a
  changed padding fails one of the two rather than passing silently, which is
  the failure mode worth having.
- **The new requirement could be read as banning the clock in suites** — most
  of the suites read `now()` to build relative dates and are right to → the
  requirement is about a fixture meaning what it says and a threshold being
  measured, not about abstinence. Worth keeping in mind when it is next cited.
- **`over = 0 .. h` is a longer event than `h-2 .. h-1`** — it spans the whole
  morning, so a suite checking placement among the day's bands would see it
  differently → these blocks check whether a row is receded, not where it sits;
  the bands have their own suite, and this fixture does not go near it.
