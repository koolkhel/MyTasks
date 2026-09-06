## ADDED Requirements

### Requirement: Editing a task's note

The board SHALL let a person edit the selected task's note without leaving the
board. The editor SHALL open holding the note's current text, or empty where
the task has none, and SHALL accept text of several lines.

Saving SHALL store what was written and show it at once, by the same path
every other write takes, so that it can be undone and so that a failure is
reported the way any other failed write is. Leaving without saving SHALL write
nothing.

Saving text that differs in no way from the note already stored SHALL write
nothing, because a write that changes nothing still spends a request and still
occupies the undo history.

Saving an empty note SHALL clear it. A cleared note SHALL be restorable by
undo, like any other write.

The board SHALL NOT require the editor's keys to be typed in any one keyboard
layout, as it does not for any other key it binds.

#### Scenario: Editing a note that exists

- **WHEN** a person opens the editor on a task carrying a note
- **THEN** the editor holds that note's text, and saving stores what was written

#### Scenario: Writing a note where there was none

- **WHEN** a person opens the editor on a task with no note and writes something
- **THEN** the editor was empty, and saving gives the task that note

#### Scenario: A note of several lines

- **WHEN** a person writes a note of more than one line and saves it
- **THEN** every line is stored, and reopening the editor shows them all

#### Scenario: Leaving without saving

- **WHEN** a person opens the editor, changes the text, and leaves without saving
- **THEN** the note is unchanged and nothing was written

#### Scenario: Saving what has not changed

- **WHEN** a person opens the editor and saves without having changed the text
- **THEN** nothing is written

#### Scenario: Clearing a note

- **WHEN** a person empties the editor and saves
- **THEN** the task carries no note, and undo brings the old one back

#### Scenario: The note survives the round trip

- **WHEN** a note is saved and read back from the store
- **THEN** its text is exactly what was written, including its line breaks and any non-ASCII characters

### Requirement: A note the board cannot represent is not rewritten

Where a note carries formatting the board does not represent — styled runs,
line kinds, or anything embedded that is not text — the board SHALL decline to
edit it and SHALL say why.

The board edits a note as text. Saving one of these would mean storing the text
and discarding everything else, and a person who cannot see what was lost
cannot know to object. Declining is worse than editing and better than
destroying.

#### Scenario: A formatted note is refused

- **WHEN** a person opens the editor on a note carrying formatting the board does not represent
- **THEN** the editor does not open, nothing is written, and the board says the note cannot be edited here

#### Scenario: An ordinary note is not refused

- **WHEN** a person opens the editor on a note that is text alone
- **THEN** it opens normally

### Requirement: Only a task's note can be edited

The key that edits a note SHALL act on tasks alone. On a calendar event or a
tracker issue it SHALL refuse at once and say the row is not the board's,
opening nothing — as every other key that would change such a row does.

#### Scenario: An event's description is not editable

- **WHEN** a person presses the note key with an event selected
- **THEN** no editor opens, nothing is written, and the board says the event belongs to the calendar

#### Scenario: A tracker issue's note is not editable

- **WHEN** a person presses the note key with a tracker issue selected
- **THEN** no editor opens, nothing is written, and the board says the issue lives in the tracker

## MODIFIED Requirements

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

A note SHALL be shown as the characters it contains. The area draws its text as markup, so a note is escaped before it is drawn; otherwise a note holding square brackets would lose them on screen while remaining whole in the store, and a person who had just typed them would be told the board had destroyed their work.

#### Scenario: A recurring task with a note

- **WHEN** the selected task recurs and carries a note
- **THEN** the detail area reports that it is recurring and shows the note text, with no mention of priority

#### Scenario: A plain task

- **WHEN** the selected task does not recur, is not pinned, and has neither deadline nor note
- **THEN** the detail area shows no priority line

#### Scenario: A note is shown as written

- **WHEN** the selected task's note contains square brackets or text that reads as markup
- **THEN** every character of it appears, no styling is applied by it, and the rest of the board is drawn as it was

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, undo the last write it made, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

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
