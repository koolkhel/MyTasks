## Why

A task's tick box is drawn with `☐` (U+2610 BALLOT BOX), and no terminal font
this board is used in has that character. Every box on screen therefore comes
from whatever substitute font the terminal picks, and the pick is made per line
rather than per character: in cool-retro-term with the IBM 3278 profile the same
`☐` is drawn as a large square on a row reading `all-day` and as a small one on a
row reading `08:00` beside a Cyrillic title. The ticked and cancelled boxes come
from a different substitute again, so they are visibly smaller than the empty one
on the same line, and ticking a task changes the size of its box.

The board has met the neighbouring problem before and wrote down its answers.
The copy mark is a plain `+` because the geometric candidates are drawn double
width in a terminal configured for Chinese, Japanese or Korean. The mailbox
indicator uses `✓` and `✗`, for a different reason again: `☑` and `☒` were
already the row's ticked and cancelled marks, and repeating them in the day bar
would have said the wrong thing in the corner of the eye. Neither answer was
about a font the terminal does not have, which is the fault here, and neither
reached the row's tick box.

## What Changes

- The three row-state marks change from the ballot-box family to glyphs the
  terminal's own font provides: `□` (U+25A1 WHITE SQUARE) for an open task, `✓`
  (U+2713 CHECK MARK) for a done one, `✗` (U+2717 BALLOT X) for a cancelled one.
  All three were measured in cool-retro-term's IBM 3278 profile and drawn at one
  weight and one size whatever else was on the line.
- The rule the board picks marks by is stated rather than left in three code
  comments that each solve one case: a mark drawn in a fixed column SHALL be one
  the terminal's font provides, and SHALL look the same on every row.
- The width-in-every-locale rule is narrowed deliberately. It stays as written
  for the green star, which is ASCII, and is not extended to the row-state marks:
  `□` is East-Asian-Ambiguous and would be drawn double width in a Chinese,
  Japanese or Korean locale. The board is not run in one, and no candidate
  satisfies both that rule and the font-coverage rule at once. The design records
  what was rejected.
- `✓` and `✗` come to mean a done and a cancelled row, beside the meanings they
  already carry in the day bar for the mailbox. This reverses a decision the
  board had written down: the day bar took those two marks in order not to
  repeat the row's, and the row now takes them back. Reversed on purpose, with
  the reasoning in the design. The mailbox indicator's own comment states the
  old reason as fact and stops being true, so it is corrected in the same pass.
- The three published pictures and the README are remade, since they show the
  old boxes.

Not in scope: the event diamond and the tracker triangle, which are drawn from
the font and need no change; the mailbox indicator's marks, which this change
adopts rather than alters, though the comment explaining them is corrected; the
green star and the copy mark, both ASCII already.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `task-board`: adds a requirement fixing which marks a row's state is drawn
  with, and the property those marks must have — present in the terminal's own
  font, and identical on every row that carries them.

## Impact

- `board.py`: the `MARKS` table, and the comments beside the marks it neighbours
  that state the rule this change now writes down once.
- `main.py`: the comment beside the mailbox indicator, whose stated reason for
  choosing `✓` and `✗` is made false by this change. The marks themselves stay.
- `tests/`: three literal glyphs across two suites; six suites name `MARKS`
  rather than its contents and are unaffected.
- `docs/screenshots.py`, `docs/*.png`, `docs/crt-today.png` and `README.md`: the
  published pictures show the marks, so they are taken again.
- No configuration, no store field, no dependency, and nothing a person has to
  do after upgrading.
