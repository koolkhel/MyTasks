## ADDED Requirements

### Requirement: Actions available on the selected task, or on the marked rows

Every action below SHALL act on the marked rows where any row is marked, and
on the selected one otherwise. Where rows are marked the selected row SHALL
take no part: a mark is a choice somebody made, and the cursor is only where
they happen to be standing.

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, scroll the detail area up and down, mark any row and copy every marked row as text, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

Scrolling the detail area, marking a row and copying the marked rows SHALL write nothing and SHALL be offered on every row the board draws, a row from a source included: reading is not a change, and the rows whose notes least often fit are the ones the board does not own.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, project assignment, done for today, note editing and opening a link included

#### Scenario: Reordering is the one action a day alone offers

- **WHEN** a task is selected in the inbox or the someday view and a person tries to move it up or down
- **THEN** the board reports that reordering applies to calendar days, which is the single exception to every action being available everywhere

#### Scenario: Moving a task and moving the cursor are different keys

- **WHEN** a person presses the key that moves the cursor up or down
- **THEN** no task's stored order changes, and the key that moves the task is a different one

#### Scenario: Assigning a project and hiding work are different keys

- **WHEN** a person presses the key that hides the work tasks
- **THEN** no task is assigned to a project, and the key that assigns one is a different one

#### Scenario: Undoing needs no task selected

- **WHEN** a person presses the undo key
- **THEN** it reverses the last write the board made, whichever task that was and whether or not it is the selected one

#### Scenario: Promoting belongs to a mail row

- **WHEN** a person presses the key that turns a mail thread into a task, with a task selected rather than a mail thread
- **THEN** nothing is created, and the board says what the key is for

#### Scenario: Scrolling the detail area writes nothing

- **WHEN** a person scrolls the detail area on any row, including one from the mailbox, the calendar or the tracker
- **THEN** the area scrolls, nothing is written anywhere, and the row is not refused as unownable

#### Scenario: Marking and copying write nothing

- **WHEN** a person marks rows on any view, including rows from the mailbox, the calendar or the tracker, and copies them
- **THEN** no request is sent to change anything, and every task, message, event and issue is exactly as it was

#### Scenario: A write key with rows marked

- **WHEN** rows are marked and a person presses a key that writes to a task, with the cursor on a row that is not marked
- **THEN** the marked rows are written and the row under the cursor is not

#### Scenario: A write key with nothing marked

- **WHEN** no row is marked and a person presses a key that writes to a task
- **THEN** it acts on the selected row, exactly as it does with marking never used

### Requirement: Marking rows to act on them

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

A mark SHALL say which rows the next thing a person does is about. Copying
reads them; every key that writes to a task writes to them. Marking itself
SHALL go on writing nothing.

Marking SHALL be offered on every row the board draws, the mailbox's, the
calendar's and the tracker's included. Marking one does not change it, and a
day is most worth copying whole -- and where a row turns out not to be the
board's to write to, it is the write that passes it over rather than the mark
that refuses it.

What is marked SHALL be the row itself rather than the line it occupies. A row
that moves because the view was redrawn, because a write landed, or because
the person went to another view SHALL keep its mark. Marks SHALL last as long
as the board is open or until they are cleared, and nothing about them SHALL
be written anywhere.

Marks SHALL follow the person between views, so that rows gathered from the
inbox, a calendar day and the someday view can be copied, or written to, in
one go. A marked set may therefore hold rows that are not on screen, and what
is done to it happens to those rows as much as to the ones in sight.

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

#### Scenario: A mark outlives what it was made for

- **WHEN** a person marks rows, copies them, and then presses a key that writes
- **THEN** the same rows are written, because acting on a set does not consume it

#### Scenario: Rows marked in another view are written too

- **WHEN** rows are marked in the inbox and on a calendar day, and a write key is pressed from either of them
- **THEN** both rows are written, whichever view is on screen

### Requirement: A toggling key drives a marked set to one state

The two keys that toggle -- the one that finishes a task and the one that puts
the green mark on it -- SHALL drive a marked set to a single state rather than
flipping each row against its own.

Where any marked row lacks the state, every marked row SHALL be given it.
Where every marked row already has it, every one SHALL lose it. A person
pressing the key means "make these done", not "make the done ones undone".

#### Scenario: A set where some are already finished

- **WHEN** a marked set holds both finished and unfinished tasks and the tick key is pressed
- **THEN** every task in the set is finished, and none of the finished ones is brought back

#### Scenario: A set that is finished throughout

- **WHEN** every task in a marked set is finished and the tick key is pressed
- **THEN** every one of them comes back unfinished

#### Scenario: The green mark behaves the same way

- **WHEN** a marked set holds both green and ungreen tasks and the green key is pressed
- **THEN** every task in the set is green, and pressing it again takes the mark off all of them

### Requirement: A write passes over the rows the board does not own

Where a marked set holds rows from the mailbox, the calendar or the tracker, a
write SHALL act on the board's own tasks and leave the others untouched. It
SHALL say how many rows it passed over, so that a set of six that wrote four
is not read as a set of four.

It SHALL NOT refuse the whole action because one row cannot be written. A set
gathered by hand from several views will hold such rows, and refusing on their
account would make marking useless in exactly the view it is most wanted.

#### Scenario: A set holding rows from elsewhere

- **WHEN** a marked set holds four tasks and two mail rows, and a write key is pressed
- **THEN** the four tasks are written, the two mail rows are unchanged, and the board says two rows were passed over

#### Scenario: A set holding nothing the board owns

- **WHEN** every row in a marked set came from the mailbox, the calendar or the tracker, and a write key is pressed
- **THEN** nothing is written and the board says so, rather than reporting an action it did not take

### Requirement: Deleting a marked set is confirmed once

Deleting a marked set SHALL be confirmed once for the whole set rather than
once per row, and the question SHALL name how many rows will go.

Where the set holds rows the view on screen is not drawing, the question SHALL
say so. Marks follow a person between views, so the rows that would go cannot
always be seen -- and a deletion is the one thing on this board that cannot be
undone, which makes the question the last place the set is accounted for.

#### Scenario: Confirming a set

- **WHEN** a person deletes a marked set
- **THEN** one question is asked, it names the number of rows, and answering no leaves every one of them

#### Scenario: A set reaching past the shown view

- **WHEN** the marked set holds rows the view on screen is not drawing
- **THEN** the question says so as well as naming the count

#### Scenario: Deleting is still what cannot be undone

- **WHEN** a marked set has been deleted and a person presses the undo key
- **THEN** the board says a deletion cannot be undone, and no task is created

### Requirement: Filing a marked set asks about what cannot be taken back

Filing a marked set into a project SHALL ask once before writing, where any
row in the set has no project yet. The question SHALL name how many rows would
be filed for the first time rather than how many are in the set: a row already
in a project is moving, which can be undone, and only a first filing cannot.

Rows already in the chosen project SHALL be left out of the write entirely.
Sending a task to the project it is already in asks the store to do nothing
and would count in the report as something done.

Where any row was filed for the first time, the undo key SHALL refuse for the
whole action and say why. One press of a key is one thing to take back, and an
action that reversed the rows it could while leaving the rest would report
success for a set that is now half what it was.

#### Scenario: A set where only some rows have no project

- **WHEN** a marked set holds rows already in a project and rows in none, and a project is chosen
- **THEN** the question names the number of rows with no project, not the size of the set

#### Scenario: Rows already in the chosen project

- **WHEN** a marked set holds rows already in the project being chosen
- **THEN** those rows are not written, and the report counts only the rows that moved

#### Scenario: Undoing a set that held a first filing

- **WHEN** a marked set holding at least one unfiled row has been filed, and a person presses the undo key
- **THEN** the board says a first filing cannot be undone, and no row in the set is moved back

#### Scenario: A set where every row was already filed

- **WHEN** every row in a marked set already has a project and the set is moved to another
- **THEN** nothing is asked, and one press of the undo key returns every row to the project it was in

### Requirement: A marked set's writes are one action

Everything a key does to a marked set SHALL be one action: one entry for the
undo key to reverse, and one report of what happened rather than one per row.

The writes SHALL be sent at the width the store was measured to accept, by the
same queue a paste uses. A set is as many writes at once as a paste is, and
the store refuses them in bulk for the same reason.

#### Scenario: Undoing a set

- **WHEN** a marked set has been ticked and a person presses the undo key once
- **THEN** every task in the set is unticked, and pressing the key again reaches the write before it

#### Scenario: A large set reaches the store whole

- **WHEN** a marked set larger than the width the store accepts is written
- **THEN** every task in it is written, none is lost to the number sent at once

#### Scenario: One report, not one per row

- **WHEN** a marked set is written
- **THEN** the board says once what it did to how many rows

## MODIFIED Requirements

### Requirement: Ticking a task moves the selection on

Ticking a task off SHALL move the selection to the next unfinished task, so that a list can be worked down with one key. Every other write SHALL leave the selection on the task it changed, unticking included — a task brought back is what the person is then looking at.

Ticking a marked set SHALL move the selection nowhere. The rule exists so that one key works a list down a row at a time, and a set is not worked down: there is no next row that follows from having finished several at once, and moving to one of them would be a guess.

#### Scenario: Ticking moves on to the next unfinished task

- **WHEN** a person ticks a task that is not the last unfinished one
- **THEN** the ticked task moves to where finished tasks are ordered, and the selection is on the next unfinished task

#### Scenario: Ticking the last unfinished task

- **WHEN** a person ticks the only unfinished task left
- **THEN** the selection stays on a task that is still shown, and no keypress is left pointing at nothing

#### Scenario: Working down a list

- **WHEN** a person presses the tick key several times in succession, faster than the API answers
- **THEN** a different task is ticked by each press, and every press acts on the task that was visibly selected when it was made

#### Scenario: Unticking keeps the task selected

- **WHEN** a person unticks a task
- **THEN** the selection stays on that task as it moves back among the unfinished ones

#### Scenario: Ticking a marked set moves nothing

- **WHEN** a person ticks a marked set
- **THEN** every task in it is finished and the selection is where it was

### Requirement: Undo and confirmation cover the same set

Each write that cannot be undone is already confirmed before it happens. What cannot be undone is what the board asks about, and the two SHALL stay in step: an action added later that cannot be undone SHALL be confirmed, and one that can be undone SHALL NOT need confirming.

One question SHALL cover as many rows as the action writes. An action on a marked set is one action, so it is asked about once; asking per row would turn a set of twenty into twenty questions and teach a person to answer without reading.

#### Scenario: Moving between projects can be undone

- **WHEN** a person moves a task that already had a project to another one and presses the undo key
- **THEN** the task returns to its previous project, because a project it can return to still exists

#### Scenario: One question for a whole set

- **WHEN** a person deletes a marked set of several rows
- **THEN** the board asks once rather than once per row, and nothing is deleted until it is answered

## REMOVED Requirements

### Requirement: Actions available on the selected task

**Reason**: Its name says the actions are offered on the selected task, which
stopped being the whole truth once a key could act on the marked rows instead.
A name that is read as a guarantee should not be left saying something narrower
than what the board does.

**Migration**: Reissued as *Actions available on the selected task, or on the
marked rows*, which keeps every action and every scenario it listed and states
which rows each acts on.

### Requirement: Marking rows to copy them

**Reason**: Marks were made for copying and now say which rows any write is
about. The name would have gone on naming one of the two things a mark is for.

**Migration**: Reissued as *Marking rows to act on them*, keeping every scenario
unchanged and adding what a mark now means to a key that writes.
