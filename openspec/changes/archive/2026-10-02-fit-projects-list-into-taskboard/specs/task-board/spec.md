## MODIFIED Requirements

### Requirement: The board fits its columns to the terminal

The task list SHALL fit within the terminal it is drawn in, rather than
growing to the width of its longest title and leaving the columns beyond it
off the screen. A person SHALL be able to see every column of a row without
scrolling sideways.

The width the columns are fitted into SHALL be the width the list can actually
draw in, not the width of the window around it. Where the list keeps room for
furniture of its own — a scrollbar it reserves whether or not it is scrolling —
that room SHALL be counted before the title takes what is left. A fit computed
against the larger number lays out more cells than can be shown, and the
rightmost column loses whatever the difference is, silently and at every width.

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

#### Scenario: Nothing is lost to the list's own furniture

- **WHEN** a row is drawn in a list that keeps room for a scrollbar of its own
- **THEN** the drawn row ends within the room the list can show, and the rightmost column is complete

#### Scenario: The room is counted whether or not the list is scrolling

- **WHEN** the list holds too few rows to scroll
- **THEN** the columns are fitted exactly as they are when it holds too many, and no column is cut in either case

## ADDED Requirements

### Requirement: The column naming a project is wide enough to read

The column that names a task's project — and, for a row that came from
elsewhere, the calendar, tracker project or correspondent that stands in its
place — SHALL be wide enough to show the names actually in use without
shortening them.

This is not the rule the title column follows, and deliberately. A title is
the person's own words and reads sensibly when it ends early: enough of it
survives to recognise the task. A project name is a label drawn from a small
fixed set, often short, and one that has been cut has to be guessed at. Two
names differing only past the cut are indistinguishable, which is worse than
a narrower list.

The title column SHALL be the one that gives up the room. It is the column
with the most to spare at any usable width, it is the only one whose content
has no natural length, and it shortens gracefully where the others do not.

The width SHALL be a fixed one, not a width taken from whatever names are on
screen at the moment. A column that measured its contents would change width
as a person moves between days, and so would the title column beside it,
moving the rows under the hand that is moving through them. The board holds
elsewhere that nothing moves for nothing, and this follows it.

Where a name is longer than the column even so, it SHALL be shortened and
SHALL show that it was, as every other column does.

#### Scenario: A project name is shown in full

- **WHEN** a row carries a project name of the length the account actually uses
- **THEN** the column shows it whole, with no mark added

#### Scenario: A name longer than the column

- **WHEN** a row carries a project name longer than the column is wide
- **THEN** it is shortened and shows that it was, as any other column would

#### Scenario: The width does not follow what is on screen

- **WHEN** a day holding only short project names is shown, and then a day holding a long one
- **THEN** the project column is the same width in both, and so is the title column beside it

#### Scenario: The title is what pays for the room

- **WHEN** the project column is given more room
- **THEN** the title column is the one that has less, and every other column is unchanged
