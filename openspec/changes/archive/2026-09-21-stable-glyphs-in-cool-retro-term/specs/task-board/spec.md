## ADDED Requirements

### Requirement: A row's state mark is drawn from the terminal's own font

A task's row SHALL carry one mark saying whether the task is open, done or
cancelled, and the three SHALL be told apart with colour disregarded: a person
may not be able to tell the board's colours apart.

Each mark SHALL be a character that the fixed-width fonts this board is run in
provide. A character its font lacks is not refused; the terminal draws it from a
substitute font of its own choosing, and it may choose differently for different
rows. The same character then appears at two sizes on one screen, and a box
changes size when the task beside it is ticked. The marks SHALL therefore NOT be
drawn from the ballot-box block, U+2610 to U+2612, which the fonts this board is
used in do not provide.

A mark SHALL be decided by the row's state alone. Nothing else about the row
SHALL change which mark is drawn: not its title, not the script that title is
written in, not whether it carries a time or lasts the whole day, not the
project beside it, and not whether the row is selected or marked for copying.

Each mark SHALL occupy one cell in the locales this board is run in, so that the
columns beside it line up. This is deliberately narrower than the rule the green
star follows. A state mark MAY be a character that a terminal configured for
Chinese, Japanese or Korean draws two cells wide, because no character satisfies
both that rule and the font-coverage rule above, and the coverage rule is the one
that shows on screen every day.

#### Scenario: The three states are told apart

- **WHEN** a view holds an open task, a done task and a cancelled task
- **THEN** each row carries a different mark, and the three can be told apart with colour disregarded

#### Scenario: The mark follows the state and nothing else

- **WHEN** two tasks share a state but differ in title, in the script their titles are written in, in whether they carry a start time, and in their project
- **THEN** both rows carry the same mark

#### Scenario: No state mark needs a substitute font

- **WHEN** the marks a task's state is drawn with are listed
- **THEN** none of them lies in the ballot-box block, U+2610 to U+2612

#### Scenario: Each state mark is one cell

- **WHEN** a row's state mark is drawn in a locale the board is run in
- **THEN** it occupies one cell, and the columns beside it line up as they do on every other row

#### Scenario: Ticking a task changes its mark and nothing else about the row's shape

- **WHEN** an open task is ticked
- **THEN** its row shows the done mark in place of the open one, in the same single cell, and every column beside it stays where it was

#### Scenario: A row marked for copying keeps its state mark

- **WHEN** a task is marked for copying
- **THEN** its row shows the copy mark beside the state mark its state calls for, and the state mark is the one that state always draws
