## ADDED Requirements

### Requirement: Undoing the last write

The board SHALL offer a key that reverses the most recent write it made,
then the one before it, and so on back through the session. Where nothing
remains to reverse, the board SHALL say so.

An undo SHALL name what it reversed. A person pressing this key does not
necessarily know what happened, and being told is most of what they need.

An undo SHALL NOT itself become something to undo: pressing the key again
SHALL reach further back rather than reinstating what was just reversed.

A write the API refused SHALL NOT be reachable, because it never took effect.

#### Scenario: Undoing a tick

- **WHEN** a person ticks a task and then presses the undo key
- **THEN** the task is unfinished again, and the board names the action it reversed and the task it acted on

#### Scenario: Walking back through several writes

- **WHEN** a person makes three writes and presses the undo key three times
- **THEN** each press reverses the next most recent write, naming it, and all three are reversed

#### Scenario: Nothing left to undo

- **WHEN** a person presses the undo key with nothing left to reverse
- **THEN** the board says so and nothing changes

#### Scenario: Pressing undo twice does not turn round

- **WHEN** a person undoes a write and presses the undo key again
- **THEN** the write before it is reversed, not the undo itself

#### Scenario: A refused write is not on the stack

- **WHEN** a write is refused and a person presses the undo key
- **THEN** the refused write is not reversed, because it never happened, and the key reaches past it to the last write that did

#### Scenario: Undo does not outlive the board

- **WHEN** a person makes writes, closes the board, and opens it again
- **THEN** there is nothing to undo

### Requirement: What an undo restores

An undo SHALL restore exactly the fields its own write changed, and no
others, so that reversing an older write cannot disturb something that has
changed since.

An undo SHALL be sent as a write like any other: shown before the API
answers, and taken back if the API refuses it.

Where a single action wrote more than one task, its undo SHALL restore all of
them together. One action SHALL be one undo, however many requests it took.

Where the task an undo would restore no longer exists, the board SHALL say so
and move on rather than failing silently.

#### Scenario: Only the fields that write changed

- **WHEN** a person renames a task, then something else about that task changes, and the rename is undone
- **THEN** the title returns to what it was and the other change is left alone

#### Scenario: An undo shows before it is confirmed

- **WHEN** a person undoes a write
- **THEN** the view shows the restored value before the API has answered

#### Scenario: A refused undo is taken back

- **WHEN** the API refuses an undo
- **THEN** the view returns to what it showed before the undo, and the refusal is reported

#### Scenario: One action that wrote several tasks

- **WHEN** a person moves a task in a run with no numbering room, so that several tasks are written, and then undoes it
- **THEN** one press restores every task that action wrote, and the run is as it was

#### Scenario: The task is gone

- **WHEN** the task a pending undo refers to no longer exists
- **THEN** the board says so, and that entry is not left waiting to be tried again

### Requirement: What cannot be undone, and how the board says so

An undo SHALL NOT create or destroy a task. Where the most recent write
cannot be reversed, the board SHALL name it and say why, rather than doing
nothing or appearing to succeed.

Three writes cannot be reversed, and each SHALL be reported in its own terms:
deleting a task, because it is gone; filing a task that had no project,
because the API refuses every value that would return it to having none; and
adding a task, because reversing it would mean deleting, which this key does
not do.

Each of those three is already confirmed before it happens. What cannot be
undone is what the board asks about, and the two SHALL stay in step: an
action added later that cannot be undone SHALL be confirmed, and one that can
be undone SHALL NOT need confirming.

#### Scenario: The last write was a deletion

- **WHEN** a person deletes a task and presses the undo key
- **THEN** the board says a deletion cannot be undone, and no task is created

#### Scenario: The last write was a first filing

- **WHEN** a person files a task that had no project and presses the undo key
- **THEN** the board says the filing cannot be undone, and the task keeps its project

#### Scenario: The last write was an addition

- **WHEN** a person adds a task and presses the undo key
- **THEN** the board says adding cannot be undone and suggests deleting the task instead, and the task is not deleted

#### Scenario: Undo never destroys

- **WHEN** a person presses the undo key any number of times
- **THEN** no task is ever deleted by it

#### Scenario: Moving between projects can be undone

- **WHEN** a person moves a task that already had a project to another one and presses the undo key
- **THEN** the task returns to its previous project, because a project it can return to still exists

### Requirement: Undoing done for today is partial, and says so

Marking a task done for today does two things: it records that work happened,
and it moves the task to tomorrow. Undoing it SHALL restore the date, and
SHALL say that the record of the day's work remains, because the API offers
no way to withdraw it.

The board SHALL NOT imply the action was fully reversed.

#### Scenario: Undoing done for today

- **WHEN** a person marks a task done for today and then undoes it
- **THEN** the task returns to the date it was on, and the board says the record of the day's work could not be withdrawn

#### Scenario: The task is where it was

- **WHEN** the date is restored by an undo
- **THEN** the task appears in the view it was in before, not the one it was moved to

## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, undo the last write it made, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, project assignment, done for today and opening a link included

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
