## ADDED Requirements

### Requirement: Text the board did not write is drawn as text, whatever its shape

Wherever the board draws text it did not write -- a task's title or note, a
mail subject, sender or body, an issue's title or project, an event's name or
calendar, a project's name, a label read out of a task or a message, the term
a person searches for -- it SHALL show the characters that text contains, and
SHALL NOT take any of them for styling. This holds for every shape of text,
not only the ones that look like styling: a bracket followed by a capital, a
dash, a dollar sign or an underscore, an option with a value in brackets, a
backslash anywhere including at the end.

Drawing such text SHALL NOT end the session. Text arrives from other people
-- a message's sender, an issue's author, a calendar's owner -- and a row the
board cannot draw is a row a person cannot select, open or finish.

The styling the board adds itself -- a row dimmed, struck through, linked or
marked as an error -- SHALL still apply, and SHALL apply to the text it is
meant for and no other.

#### Scenario: The shape that ended the session

- **WHEN** a note, a title or a mail subject holds `[--opt=A-B]` and the board draws it in a row, the detail area, the focus view, a prompt or the status line
- **THEN** the board stays open, and every place it is drawn shows `[--opt=A-B]` as written

#### Scenario: Shapes that vanished without a word

- **WHEN** text the board did not write holds `[A]`, `[Ab] text`, `[ABC=1]`, `[$var]`, `[_x]` or `[--k=SECS] [--v=path]`
- **THEN** each place it is drawn shows every character of it, and none of it is missing

#### Scenario: Backslashes

- **WHEN** text the board did not write holds `a\[b]`, or ends with a single `\`
- **THEN** it is shown with exactly the backslashes it holds, no more and no fewer

#### Scenario: Text that names the board's own styling

- **WHEN** a title holds `[b]one[/b]`, `[dim]x[/dim]` or `[link='https://e.invalid']y[/link]`
- **THEN** the row shows those characters as written, nothing in it is bold, dim or a link because of them, and the rest of the row keeps the styling the board gave it

#### Scenario: The board's own styling still applies around such text

- **WHEN** a finished mail row, an event that is over, or a title holding a link is drawn and its text holds any of the shapes above
- **THEN** the row is struck, dimmed or linked as it would be for plain text, and the text itself is shown as written

#### Scenario: A search term in any shape

- **WHEN** a person searches for `[--opt=A-B]` or `[A]`
- **THEN** the bar names the term as typed, and the board stays open

## MODIFIED Requirements

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

A note SHALL be shown as the characters it contains, whatever their shape, and showing it SHALL NOT end the session. A note holding square brackets that lost them on screen while remaining whole in the store would tell a person who had just typed them that the board had destroyed their work; a note that could not be drawn at all would make its row impossible to select, and so its task impossible to finish on the board.

The detail area SHALL keep the same height whatever the selected row carries, and whether or not anything is selected at all. Its height SHALL NOT depend on the length of the note. A person stepping down a list is moving through rows whose notes differ from nothing at all to many screens; an area sized to each of them in turn moves the list under the hand that is moving through it, and the row a person is about to press a key on is not where they saw it.

Where the window is too short for that height to leave a usable list, the area SHALL take a share of the height instead. The height is fixed against the *content*, which is what makes the list still; being fixed against the window as well would make a short window unusable.

The area SHALL scroll, so that a note longer than the area can be read in full without leaving the list. Scrolling SHALL be by its own keys and SHALL NOT move the selection: the person is reading the row they have chosen, not choosing another.

While the area holds more than it can show, it SHALL say so. An area that is always the same height gives a person no way to tell a note that ends from one that continues, and a note read as complete when it was cut is worse than one that plainly runs on.

When the selection changes, the area SHALL show the beginning of the newly selected row's note. A note carried over at the offset the last one was read to would open part way through, at a place that means nothing.

#### Scenario: A recurring task with a note

- **WHEN** the selected task recurs and carries a note
- **THEN** the detail area reports that it is recurring and shows the note text, with no mention of priority

#### Scenario: A plain task

- **WHEN** the selected task does not recur, is not pinned, and has neither deadline nor note
- **THEN** the detail area shows no priority line

#### Scenario: A note is shown as written

- **WHEN** the selected task's note contains square brackets or text that reads as markup
- **THEN** every character of it appears, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A note quoting a command's usage line

- **WHEN** a person selects a row whose note holds an option in brackets with a value, such as `[--opt=A-B]`
- **THEN** the board stays open, the note appears with every character of it, and the selection can move on from the row and back to it

#### Scenario: The area is the same height whatever the note

- **WHEN** the selection moves between a row with no note, a row with a one-line note, and a row whose note is many times the area's height
- **THEN** the area is the same height each time

#### Scenario: The list does not move under the cursor

- **WHEN** the selection moves down a list of rows whose notes differ in length
- **THEN** the list shows the same number of rows throughout, and no row changes position because of the note being shown

#### Scenario: Nothing selected

- **WHEN** the shown view holds no rows at all
- **THEN** the area is still the same height, showing nothing

#### Scenario: A window too short for the fixed height

- **WHEN** the window is too short for the area's height to leave a usable list
- **THEN** the area takes a share of the window's height instead, and is still the same height whatever the note

#### Scenario: A long note can be read in full

- **WHEN** the selected row's note is longer than the area can show and a person scrolls the area down
- **THEN** the rest of the note is shown, and the selection has not moved

#### Scenario: Scrolling back

- **WHEN** a person scrolls the area down and then up again
- **THEN** the beginning of the note is shown again

#### Scenario: Scrolling a note that fits

- **WHEN** the selected row's note is shorter than the area and a person presses a scrolling key
- **THEN** nothing moves, and the selection has not moved

#### Scenario: There is more below

- **WHEN** the selected row's note is longer than the area can show
- **THEN** the area shows that it holds more than it is showing

#### Scenario: There is nothing more below

- **WHEN** the selected row's note fits in the area
- **THEN** the area shows no such indication

#### Scenario: A new selection starts at the beginning

- **WHEN** a person scrolls part way through one row's note and then selects another row
- **THEN** the beginning of the newly selected row's note is shown
