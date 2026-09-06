## ADDED Requirements

### Requirement: The board fits its columns to the terminal

The task list SHALL fit within the terminal it is drawn in, rather than
growing to the width of its longest title and leaving the columns beyond it
off the screen. A person SHALL be able to see every column of a row without
scrolling sideways.

The column holding a task's title SHALL take the width the other columns
leave, so that a wider terminal gives the title more room and a narrower one
gives it less. The widths SHALL follow the terminal as it is resized, not
only as it was when the board started.

Where a title is longer than the width it is given, the board SHALL shorten
it and SHALL show that it has been shortened, so that a person can tell a
title that ends from one that continues. The same SHALL hold for any other
column that must shorten what it shows: no column may cut text and leave it
looking whole.

Shortening a title SHALL NOT damage how it reads. A title carries a link, a
colour when the task is past due, and a strike when it is finished; each
SHALL survive being shortened, and none may appear as raw markup.

The title SHALL NOT be shortened below a width at which it can still be
recognised. Where the terminal is too narrow to give it that much, the board
SHALL keep the minimum and let the list scroll, rather than reducing the
title to something unreadable.

Shortening SHALL be by ending the text early, not by wrapping it onto
further lines: a row is one line, and stays one line.

#### Scenario: A long title no longer pushes the other columns away

- **WHEN** a view holds a task whose title is far longer than the terminal is wide
- **THEN** every column of that row is visible without scrolling sideways

#### Scenario: A shortened title says so

- **WHEN** a title is longer than the room the column gives it
- **THEN** the row shows as much as fits followed by a mark that says the title continues

#### Scenario: A title that fits is untouched

- **WHEN** a title is shorter than the room the column gives it
- **THEN** it is shown in full, with no mark added

#### Scenario: Shortening keeps a title readable

- **WHEN** a shortened title carries a link, or belongs to a past-due task, or belongs to a finished one
- **THEN** the link still opens, the colour and the strike still apply, and no markup is shown as text

#### Scenario: Another column that must shorten

- **WHEN** any other column holds text longer than its width
- **THEN** it too shows that the text was shortened rather than appearing to end where it was cut

#### Scenario: The terminal is resized

- **WHEN** the terminal is made wider or narrower while the board is open
- **THEN** the title column takes the new room, and titles are shortened or shown in full to match

#### Scenario: A terminal too narrow for everything

- **WHEN** the terminal is too narrow to give the title its minimum width
- **THEN** the title keeps that minimum and the list scrolls, rather than the title shrinking further

#### Scenario: A row stays one line

- **WHEN** a title is too long for its column
- **THEN** the row occupies one line, and no part of the title appears on another
