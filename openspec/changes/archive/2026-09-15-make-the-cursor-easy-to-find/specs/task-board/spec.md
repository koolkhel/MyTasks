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

A marked row SHALL be drawn as a bar across the whole of the row, so that
how much of a list is chosen can be seen at a glance rather than read one
character at a time.

A marked row SHALL be tellable from the selected one by the colour of its bar,
not by the weight of its text. The selected row's bar SHALL be the brighter of
the two. Weight has to be read; colour is seen from the corner of the eye, and
a cursor sitting in a run of marked rows is exactly the case where reading
each row in turn is what a person is trying to avoid.

The cursor is where a person is; a mark is what they chose. They are different
things and are drawn in different colours.

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

#### Scenario: A cursor inside a run of marked rows

- **WHEN** several adjacent rows are marked and the cursor is on one of them
- **THEN** that row's bar is a different colour from the bars either side of it

#### Scenario: Which bar is brighter

- **WHEN** a marked row and the selected row are both drawn
- **THEN** the selected row's bar is the brighter of the two

### Requirement: A theme keeps the board's distinctions visible

Whatever theme is active, the board SHALL keep apart the things its other requirements rely on being told apart: a past-due title from an ordinary one, muted text from ordinary text, the selected row from the rest, the selected row from a marked one, and the text on any bar or panel from the surface behind it. A theme that renders any of these indistinguishable SHALL NOT be offered.

The selected row SHALL differ from the rows around it whether or not those rows are marked. Marked rows carry a bar of their own, so "differs from the surrounding rows" is a claim about the marked case as much as the ordinary one -- and it was the marked case that made it false.

#### Scenario: A past-due title still reads as past due

- **WHEN** today's view holds both a past-due task and one due today, under any offered theme
- **THEN** the two titles are drawn in different colours

#### Scenario: Muted text is still muted

- **WHEN** the board draws muted text — the status line, the project column, the detail strip, the key bar's labels — under any offered theme
- **THEN** it is a different colour from an ordinary task title

#### Scenario: The selected row still stands out

- **WHEN** a row is selected under any offered theme
- **THEN** its background differs from the surrounding rows and its text is legible against that background

#### Scenario: Text on a bar is legible against it

- **WHEN** a theme gives a bar or panel a light background
- **THEN** the text drawn on it is dark rather than light, and the reverse for a dark background

#### Scenario: A link is not mistaken for ordinary text

- **WHEN** a task's title carries a link under any offered theme
- **THEN** the link is drawn differently from the rest of the title

#### Scenario: The selected row stands out among marked ones

- **WHEN** the rows above and below the selected one are marked, under any offered theme
- **THEN** the selected row's background differs from theirs, and its text is legible against it
