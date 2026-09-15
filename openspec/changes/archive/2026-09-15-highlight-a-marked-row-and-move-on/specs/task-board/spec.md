## ADDED Requirements

### Requirement: A marked row's title is drawn plainly

While a row is marked, its title SHALL be drawn in the ordinary text colour:
the colour a past-due title carries and the dimming of a finished one SHALL be
left off.

Those colours are unreadable against the bar. Measured against it, a past-due
title comes out at about 1.3 to 1 and a dimmed one at about 1.2 to 1, where
the ordinary colour is about 2.7 to 1 -- which is the contrast the selected
row's own text already has. A row nobody can read is worse than a row drawn
without its colour.

This is not a new rule but an existing one reaching a second kind of row. The
selected row already loses its title colour, for the same reason, and a
past-due row that is selected is told apart by the age label it carries
instead. A marked row SHALL be told apart the same way.

This SHALL hold for every row the board dims, not only its own tasks: a mail
row whose issue the tracker has finished, and a calendar event that has
already ended, are dimmed by the same reasoning and are as unreadable on the
bar for the same reason.

A style that is not a colour SHALL survive being marked. A finished task's
title and a mail row whose issue the tracker has finished are struck through,
and a strike is as legible on the bar as off it.

#### Scenario: A past-due row that is marked

- **WHEN** a past-due row is marked
- **THEN** its title is drawn in the ordinary colour rather than the past-due one, and the row is still told apart by the age it shows

#### Scenario: A finished row that is marked

- **WHEN** a finished task, or a mail row whose issue is finished, is marked
- **THEN** its title is not dimmed, and it is still struck through

#### Scenario: An event that has ended, marked

- **WHEN** a calendar event that has already ended is marked
- **THEN** its title is not dimmed, so that it can be read on the bar

#### Scenario: An unmarked row keeps its colour

- **WHEN** a past-due or finished row is not marked
- **THEN** it is drawn exactly as it was before, with its own colour and dimming

## MODIFIED Requirements

### Requirement: Marking rows to copy them

The board SHALL offer a key that marks the row under the cursor, and that
unmarks it when it is pressed again on a row already marked. Marking SHALL
write nothing anywhere.

Marking SHALL then move the cursor to the next row, so that a run can be
marked by pressing the one key over and over: the rows a person marks are
usually next to each other, and leaving the cursor where it was made every
mark cost a second keypress that was nearly always the same one. It SHALL move
on whether the press put a mark on or took one off, which is one rule rather
than two. On the last row the cursor SHALL stay where it is, and the mark
SHALL still be made.

Marking SHALL be offered on every row the board draws, the mailbox's, the
calendar's and the tracker's included, for the same reason reading one is:
copying a row does not change it, and a day is most worth copying whole.

What is marked SHALL be the row itself rather than the line it occupies. A row
that moves because the view was redrawn, because a write landed, or because
the person went to another view SHALL keep its mark. Marks SHALL last as long
as the board is open or until they are cleared, and nothing about them SHALL
be written anywhere.

Marks SHALL follow the person between views, so that rows gathered from the
inbox, a calendar day and the someday view can be copied in one go.

The board SHALL forget the mark on a row it no longer holds, so that a task
deleted or a message filed elsewhere cannot leave behind a mark that can
neither be seen nor cleared.

A marked row SHALL be drawn as a bar across the whole of the row, in the
colour the selected row's bar already uses, so that how much of a list is
chosen can be seen at a glance rather than read one character at a time.

A marked row SHALL still be tellable from the selected one. The cursor keeps
the bolder, paler text it already carries on that bar where a marked row
carries the ordinary text: both are bars, and the cursor is the bold one. The
cursor is where a person is; a mark is what they chose; they are still
different things, and what separates them is now weight and colour rather than
a character against no character.

A row that is both marked and selected SHALL be drawn as the selected row,
because where a person is outranks what they chose. It SHALL nonetheless still
carry the mark's own character, which on that row is the only thing that says
it is marked at all -- without it a person could not tell whether a press of
the key had just put a mark on or taken one off.

The bar SHALL be drawn under every theme the board offers.

#### Scenario: Marking and unmarking the same row

- **WHEN** a person presses the marking key on a row and then presses it again on that same row
- **THEN** the row is marked and then unmarked, and nothing is written either time

#### Scenario: A mark survives the view being redrawn

- **WHEN** rows are marked and a write lands, a fetch answers, or the mailbox adds rows, so that the view is rebuilt and the rows move
- **THEN** the same rows are still marked, and no row that was not marked has become marked

#### Scenario: Marks gathered from several views

- **WHEN** a person marks rows in the inbox, moves to a calendar day and marks more, and then moves to the someday view
- **THEN** every row marked in every one of those views is still marked

#### Scenario: A row the board does not own can be marked

- **WHEN** a person marks a mail row, a calendar event or a tracker issue
- **THEN** the row is marked, nothing is written, and it is not refused as unownable

#### Scenario: A mark on a row that is no longer there

- **WHEN** a marked task is deleted, or a marked message leaves the folder the board reads
- **THEN** the mark is forgotten with the row, and the count of marked rows no longer counts it

#### Scenario: The cursor and a mark are different

- **WHEN** a person marks a row and then moves the cursor to another row
- **THEN** the first row is still marked, the cursor is on the second, and the two are drawn differently

#### Scenario: A run marked with one key

- **WHEN** a person presses the marking key several times in succession
- **THEN** a different row is marked by each press, working down the view, and the cursor ends below the last of them

#### Scenario: Taking a mark off moves on as well

- **WHEN** a person presses the marking key on a row that is already marked
- **THEN** the mark comes off and the cursor moves to the next row, the same as when a mark goes on

#### Scenario: Marking the last row

- **WHEN** a person marks the last row of the view
- **THEN** the row is marked and the cursor stays on it, rather than moving to nothing

#### Scenario: A marked row is drawn as a bar

- **WHEN** a row is marked and the cursor is elsewhere
- **THEN** that row is drawn with a bar across its whole width, and an unmarked row beside it is not

#### Scenario: The cursor over a marked row

- **WHEN** the cursor is moved onto a marked row
- **THEN** the row is drawn as the selected row is, and still carries the mark's own character so that the mark is not hidden by the cursor

#### Scenario: The bar in either theme

- **WHEN** a row is marked and the board is switched between the themes it offers
- **THEN** the bar is visible against the ground in both
