## REMOVED Requirements

### Requirement: A green task is marked by a rail, not by colour

**Reason**: The mark is no longer a rail. Its name says "rail", its
description requires the marks on adjacent rows to "join into one unbroken
bar", and one of its scenarios asserts exactly that — none of which is true
of a mark that stands alone on each row. The joining was the reason the rail
was chosen; giving it up is the point of the change rather than an oversight,
so the guarantee is withdrawn rather than reworded.

**Migration**: None for anyone using the board; marked tasks are still marked
and still told apart without colour. The replacement requirement, `A green
task is marked by a star, not by colour`, carries over everything this one
said except the joining.

## ADDED Requirements

### Requirement: A green task is marked by a star, not by colour

A task carrying the tag SHALL be marked in the margin, before everything else
on its row, by a star that no other row carries. The mark SHALL NOT rely on
colour to be seen, and the colour the tag itself carries SHALL be ignored: a
person may not be able to tell the board's colours apart.

The mark SHALL occupy one cell in every locale, so that the columns beside it
line up wherever the board is run. It stands alone on its row: adjacent
marked tasks read as several marks, not as one joined shape.

The tag's name SHALL NOT be printed on the row. The star says which tasks are
marked, and the row's width is better spent on the task.

#### Scenario: A marked task is distinguishable

- **WHEN** a view holds both marked and unmarked tasks
- **THEN** every marked task carries the star and no unmarked task does, and they can be told apart with colour disregarded

#### Scenario: The mark is one cell wide

- **WHEN** the board is run in any locale
- **THEN** the mark takes one cell, and the columns beside it line up as they would with no mark at all

#### Scenario: Adjacent marked tasks

- **WHEN** several marked tasks are listed one after another
- **THEN** each carries its own star, and they are not required to form a continuous shape

#### Scenario: The tag is not named on the row

- **WHEN** a marked task is shown
- **THEN** its row does not print the tag's name

#### Scenario: The star is shown in every view

- **WHEN** a marked task appears on a calendar day, in the inbox or in the someday view
- **THEN** it carries the star in each of them

### Requirement: The prompt shows enough of a title to read it

The prompt that adds and renames a task SHALL be wide enough that the great
majority of a person's titles are visible in full while being typed. A person
editing a title they cannot see is guessing at what they are changing.

The prompt SHALL take its width independently of the board's other
dialogues, so that widening it does not stretch a short question, a
confirmation or a picker that reads better narrow.

Where the terminal is too narrow for that width, the prompt SHALL narrow to
fit rather than overflow, and SHALL never be narrower than the terminal can
show.

#### Scenario: A long title is visible while it is typed

- **WHEN** a person adds or renames a task with a title longer than the board's other dialogues would show
- **THEN** the prompt shows it without the beginning scrolling out of view

#### Scenario: The other dialogues are unchanged

- **WHEN** a confirmation, a date picker, a project picker, the focus view or the help overlay is shown
- **THEN** each is exactly as wide as it was before the prompt was widened

#### Scenario: A narrow terminal

- **WHEN** the board runs in a terminal narrower than the prompt's preferred width
- **THEN** the prompt narrows to fit within the terminal, and nothing is drawn outside it

#### Scenario: A title longer than any width

- **WHEN** a title is longer than even the widened prompt can show
- **THEN** the prompt still accepts and returns the whole title, showing as much of it as fits
