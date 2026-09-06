## Why

Two things a person notices while using the board, one an aesthetic judgement
and one a measurable loss.

The mark against a task carrying the green tag is a double vertical rule. It
was chosen so that a run of marked tasks would join into one unbroken bar,
which it does — but read on the board day after day, it does not say "this
one is mine" the way a star does. The joining was a good idea that turned out
to matter less than being recognisable at a glance.

The prompt that adds and renames a task is 50 cells wide. Measured against
the tasks currently on the board, 36 of 108 titles are longer than that, so a
third of the time a person is typing or editing a title they cannot see all
of. The prompt is a fixed 62 cells however wide the terminal is, so the space
to fix this is already there and simply unused.

## What Changes

- The mark on a marked task becomes an asterisk. It stops being a rail, so a
  run of marked tasks reads as several marks rather than one bar. **BREAKING**
  for anything that asserts the bar: that was a stated guarantee and it is
  being withdrawn deliberately, not quietly.
- The asterisk retires a risk rather than adding one: it is the only mark on
  the board that is guaranteed one cell wide in every locale, where the rule
  it replaces could render two cells wide in an East Asian locale.
- The prompt that adds and renames a task gets wider, on its own, so that
  nine titles in ten fit rather than two in three. The other five dialogues
  keep the width they have: a short yes-or-no question does not want to be
  stretched.
- A narrow terminal still narrows the prompt rather than overflowing it.

Nothing about which tasks are marked, how they are ordered, or how they are
counted changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: the requirement naming the mark a rail is withdrawn and
  replaced, because both its name and its guarantee that adjacent marks join
  into one bar stop being true. The capability also gains a requirement that
  the prompt shows enough of a title to read while it is being typed, and
  narrows rather than overflows on a small terminal.

## Impact

- `main.py`: the constant holding the mark and its name, and one stylesheet
  rule giving the add-and-rename prompt its own width.
- No change to `singularity.py`, to the ordering, or to any write.
- The suites that assert the rail and its joining need updating to the new
  mark; that is the change being made, not a regression.
