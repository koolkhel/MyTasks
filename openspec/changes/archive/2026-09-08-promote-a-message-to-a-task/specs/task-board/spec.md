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

### Requirement: A promoted task carries the message it came from

The created task SHALL carry, in its note, what the thread's newest message
said and the identity of that message.

What it said, because a task reading "Build failure" is a reminder where one
that still holds the message is the work — and because the addresses a
notification carries are in its own text, so the key that opens a task's link
reaches the build, the merge request or the issue through the note without
anything further being extracted.

The identity, so that the message this task came from can still be found in
the mailbox afterwards. It is what makes the task traceable to its origin
rather than merely descriptive of it.

Where the message said nothing, the task SHALL still be created, carrying the
identity alone. The decision that something is work does not depend on there
being anything to read.

The note SHALL be written in the form the board already writes notes, so that
the key which edits a note can edit this one, and SHALL be shown as the
characters it contains.

#### Scenario: The note carries the message and the identity

- **WHEN** a thread whose newest message has a body is promoted
- **THEN** the created task's note holds that body and the identity of the message

#### Scenario: The task opens what the message pointed at

- **WHEN** a promoted task is selected and the key that opens a link is pressed
- **THEN** the thing the message pointed at is opened, found in the note

#### Scenario: A message that said nothing

- **WHEN** a thread whose newest message has an empty body is promoted
- **THEN** the task is still created, with a note carrying the identity alone

#### Scenario: The note can be edited afterwards

- **WHEN** a person edits the note of a promoted task
- **THEN** it opens in the editor holding what was written, like any other note

#### Scenario: A message written to look like markup

- **WHEN** a promoted message's body contains square brackets or text that reads as markup
- **THEN** the task's note shows every character as sent, applies no styling by it, and leaves the rest of the board as it was

### Requirement: Promoting takes the thread out of the queue

Promoting SHALL mark every message in the thread read, so that the row leaves
the inbox by the same rule that put it there. A queue that cannot be drained
from the board is a queue that will be drained somewhere else, which defeats
having it on the board.

Marking read SHALL be the only change made to the mailbox: a message SHALL NOT
change folder, be removed, nor have its content altered. Its file MAY be
renamed, and MAY move from the folder's new area to its current one, because
that is how the format records that a message has been seen; it stays in the
folder it was read from either way.

The task SHALL be created before the message is marked, and a failure to mark
SHALL NOT undo the task. A task without its message marked is a row that
appears once more; a message marked without its task is work lost, and of the
two only the first can be put right by a person who can see what happened.

Where the mailbox cannot be written to, the board SHALL say so and SHALL leave
the created task alone.

Undoing a promotion SHALL put the thread back in the queue: the created task
SHALL be removed and its messages SHALL be marked unread again, so that one
press reverses both halves. Removing the task and leaving the messages read
would take work out of the queue with nothing left to show for it — the one
outcome a person can neither see nor repair from the board.

A message marked unread again SHALL stay in the folder's current area rather
than returning to its new area. It has been looked at; the format's new area
means a message no program has yet touched, and claiming that again would be
false.

The board SHALL keep no record of what it has promoted. It holds no state of
its own on disk, every row it draws comes from a source, and the mailbox is
now that record.

#### Scenario: The thread leaves the queue

- **WHEN** a thread is promoted
- **THEN** its messages are marked read, and the row is gone from the inbox when it is next read

#### Scenario: Undoing a promotion returns the thread

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the created task is removed and the thread is in the queue again, its messages unread

#### Scenario: Nothing else about the mailbox changes

- **WHEN** a thread has been promoted
- **THEN** no message has moved folder, none has been removed, and no message's content differs

#### Scenario: The task survives a mailbox that cannot be written

- **WHEN** the mailbox cannot be written to and a thread is promoted
- **THEN** the task is still created, and the board says the message could not be marked

#### Scenario: Nothing is remembered

- **WHEN** a thread has been promoted
- **THEN** the board has written no record of it anywhere but the mailbox itself

## MODIFIED Requirements

### Requirement: The board reads a mailbox from a directory

The board SHALL read messages from a maildir at a path named in the
environment, and SHALL read nothing else: no server, no credentials, no
network call.

The board SHALL read the folders it is told to read and no others: the
mailbox's own inbox, and any further folders named in the environment. What
wants processing daily is a few folders rather than every message an account
has ever held, and reading only those is what keeps the queue a queue.

Within those folders the board SHALL read the messages not yet marked read.
A queue is what has not been dealt with; a message already read has been dealt
with, whether here or in the program the person reads mail with, and showing
it again would make the queue a list of everything instead.

Where a named folder does not exist, the board SHALL say so rather than
passing over it in silence: an empty queue and a misspelt folder look
identical on screen and mean opposite things.

How mail arrives in that directory SHALL NOT be the board's concern. A sync
tool, a mail client, an export — whichever a person uses, and whichever they
change to, the board reads the same directory. This is why the directory is
the boundary rather than a protocol.

The board SHALL alter nothing in the mailbox except to mark a message read
when its thread is promoted, as that requirement states. No message SHALL be
moved, removed, or have its content changed. Reading the mailbox SHALL change
nothing at all.

Where no mailbox is configured, the board SHALL show no mail and SHALL NOT
report a failure. A board without one is an ordinary board.

Where a mailbox is configured but cannot be read, the board SHALL say so once
and SHALL otherwise carry on: the day's tasks, the tracker and the calendar
SHALL be unaffected.

#### Scenario: Messages are read from the configured directory

- **WHEN** a maildir is configured and holds messages
- **THEN** the board reads them from it, and makes no network call to do so

#### Scenario: Only the named folders are read

- **WHEN** a mailbox holds folders beyond those named
- **THEN** messages from the named folders appear and messages from the others do not

#### Scenario: The mailbox's own inbox is read

- **WHEN** no further folders are named
- **THEN** the mailbox's own inbox is read, and it alone

#### Scenario: A folder that does not exist

- **WHEN** a named folder is not in the mailbox
- **THEN** the board says so rather than showing a queue quietly missing it

#### Scenario: A message already read is not in the queue

- **WHEN** a message in a named folder is marked read
- **THEN** it does not appear, whether it was read here or in another program

#### Scenario: Nothing is written to the mailbox

- **WHEN** the board has read the mailbox and a person has looked at it
- **THEN** no message's flags, name, folder or content have changed

#### Scenario: No mailbox configured

- **WHEN** no maildir is configured
- **THEN** the board shows no mail and reports no failure

#### Scenario: A mailbox that cannot be read

- **WHEN** a maildir is configured but missing, unreadable, or not a maildir
- **THEN** the board says so once and the rest of the board works as it did

#### Scenario: A message the board cannot make sense of

- **WHEN** one message in the mailbox cannot be parsed
- **THEN** the others are still shown, and the unreadable one does not take the view down with it

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

#### Scenario: Promoting belongs to a mail row

- **WHEN** a person presses the key that turns a mail thread into a task, with a task selected rather than a mail thread
- **THEN** nothing is created, and the board says what the key is for
