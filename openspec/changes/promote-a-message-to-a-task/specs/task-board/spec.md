## ADDED Requirements

### Requirement: A mail thread can be turned into a task

The board SHALL let a person turn the selected mail thread into a task on
today, so that a message which turns out to be work joins the day's
commitments rather than being remembered.

The task SHALL be titled from what the thread is about. A title a person did
not choose is better than no task, and it can be renamed by the key that
renames any task.

The task SHALL be created the way every task the board creates is created:
shown at once, sent behind the screen, reversible by undo, and reported if it
fails. Promoting SHALL NOT be a special path through the board's writing.

Promoting SHALL act on a mail thread alone. On any other row the board SHALL
say so and create nothing.

#### Scenario: A thread becomes a task

- **WHEN** a person promotes the selected mail thread
- **THEN** a task appears on today, titled from what the thread is about

#### Scenario: It is shown before the store has answered

- **WHEN** a thread is promoted
- **THEN** the task is on screen without waiting for the store, as any added task is

#### Scenario: Promoting can be undone

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the task is removed, and the board says what it reversed

#### Scenario: A failed promotion is reported

- **WHEN** promoting is refused by the store
- **THEN** the board says so, and does not leave a task on screen that does not exist

#### Scenario: Promoting acts on mail alone

- **WHEN** a person presses the key on a task, a calendar event or a tracker issue
- **THEN** nothing is created, and the board says what the key is for

### Requirement: A promoted task carries what the thread pointed at

The created task SHALL carry, in its note, the address the thread pointed at
and the identity of the message it came from.

The address, so that the task can be opened to the thing it is about by the
key that opens a task's link — a task saying only "Build failure" is a
reminder, where one that opens the build is the work.

The identity, so that the message this task came from can still be found in
the mailbox afterwards. It is what makes the task traceable to its origin
rather than merely descriptive of it.

Where the thread pointed at nothing, the task SHALL still be created. The
decision that something is work does not depend on there being a link.

The note SHALL be written in the form the board already writes notes, so that
the key which edits a note can edit this one.

#### Scenario: The note carries the address and the identity

- **WHEN** a thread carrying an address is promoted
- **THEN** the created task's note holds that address and the identity of the message it came from

#### Scenario: The task opens what the thread pointed at

- **WHEN** a promoted task is selected and the key that opens a link is pressed
- **THEN** the thing the thread pointed at is opened

#### Scenario: A thread pointing at nothing

- **WHEN** a thread carrying no address and naming no issue is promoted
- **THEN** the task is still created, with a note carrying the identity alone

#### Scenario: The note can be edited afterwards

- **WHEN** a person edits the note of a promoted task
- **THEN** it opens in the editor holding what was written, like any other note

### Requirement: Promoting changes neither the mailbox nor the thread's row

Promoting SHALL NOT alter the mailbox: no flag SHALL be set, no message moved,
renamed, removed or marked read. The board reads the mailbox and does not own
it, and that holds after a promotion as before one.

The thread SHALL remain in the mail view. The queue drains where mail is
already managed — archiving in the client that fills the directory, after
which the message is no longer read — rather than by the board reaching into
the mailbox.

A thread promoted twice SHALL create two tasks. The board SHALL NOT remember
what it has promoted: it holds no state of its own on disk, every row it draws
comes from a source, and a record of promotions would be the first exception
to that.

#### Scenario: The mailbox is untouched

- **WHEN** a thread has been promoted
- **THEN** no message's flags, name, folder or content have changed

#### Scenario: The thread stays in the view

- **WHEN** a thread has been promoted
- **THEN** it is still shown in the mail view, unchanged

#### Scenario: Promoting twice

- **WHEN** a person promotes the same thread twice
- **THEN** two tasks exist, because the board keeps no record of what it promoted

## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

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

#### Scenario: Promoting belongs to the mail view

- **WHEN** a person presses the key that turns a mail thread into a task, with a task selected rather than a mail thread
- **THEN** nothing is created, and the board says what the key is for
