## MODIFIED Requirements

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

A note SHALL be shown as the characters it contains. The area draws its text as markup, so a note is escaped before it is drawn; otherwise a note holding square brackets would lose them on screen while remaining whole in the store, and a person who had just typed them would be told the board had destroyed their work.

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

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, scroll the detail area up and down, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

Scrolling the detail area SHALL write nothing and SHALL be offered on every row the board draws, a row from a source included: reading is not a change, and the rows whose notes least often fit are the ones the board does not own.

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

### Requirement: Focus view of the selected task

The board SHALL offer a focus view of the selected task, showing its title in full without truncation, when it is due, its project when it has one, its deadline when it has one, and its note when it has one. The view SHALL be dismissable, and dismissing it SHALL return to the same view and the same selected task.

The focus view SHALL show a note as the characters it contains, by the same rule the detail area follows and for the same reason. The two places a note is shown SHALL agree: a note holding square brackets is a note holding square brackets in both.

#### Scenario: Opening the focus view

- **WHEN** a person opens the focus view on a selected task
- **THEN** the task's whole title is shown, along with when it is due and its project

#### Scenario: A long title is not cut off

- **WHEN** the selected task's title is longer than the width the task list gives it
- **THEN** the focus view shows the title in full, unlike the row it was opened from

#### Scenario: A task with a note and a deadline

- **WHEN** the selected task has a note and a deadline
- **THEN** the focus view shows both

#### Scenario: A task with nothing optional set

- **WHEN** the selected task has no project, no deadline, and no note
- **THEN** the focus view shows its title and when it is due, and omits the parts it has nothing to show for

#### Scenario: Dismissing returns to the board

- **WHEN** a person dismisses the focus view
- **THEN** the board is shown again, in the same view, with the same task still selected

#### Scenario: Available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the focus view can be opened on it just as from a day

#### Scenario: Nothing is selected

- **WHEN** a person asks for the focus view while the shown view holds no tasks
- **THEN** no focus view opens and the board is left as it was

#### Scenario: A note is shown as written here too

- **WHEN** the selected task's note contains square brackets or text that reads as markup and a person opens the focus view
- **THEN** every character of it appears there, and no styling comes from it
