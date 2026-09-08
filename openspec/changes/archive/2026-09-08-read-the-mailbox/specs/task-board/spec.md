## ADDED Requirements

### Requirement: The board reads a mailbox from a directory

The board SHALL read messages from a maildir at a path named in the
environment, and SHALL read nothing else: no server, no credentials, no
network call.

The board SHALL read the folders it is told to read and no others: the
mailbox's own inbox, and any further folders named in the environment. What
wants processing daily is a few folders rather than every message an account
has ever held, and reading only those is what keeps the queue a queue.

Where a named folder does not exist, the board SHALL say so rather than
passing over it in silence: an empty queue and a misspelt folder look
identical on screen and mean opposite things.

How mail arrives in that directory SHALL NOT be the board's concern. A sync
tool, a mail client, an export — whichever a person uses, and whichever they
change to, the board reads the same directory. This is why the directory is
the boundary rather than a protocol.

The board SHALL NOT alter the mailbox. No flag SHALL be set, no message moved,
renamed or removed, and nothing marked read. The mailbox is read the way the
calendar is read.

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

### Requirement: Messages are grouped into threads

Messages SHALL be grouped into threads, and a thread SHALL be one row. A
notification system sends one message per event, so a view of messages is a
feed; a view of threads is a list a person can read.

Grouping SHALL follow the headers that exist for it, each message being joined
to the one it answers, and a chain being followed to its start.

Grouping SHALL NOT fall back to matching subjects. Unrelated messages share a
subject often — a digest, a recurring report — and merging those would hide
messages rather than tidy them. A message whose headers place it in no thread
SHALL be a thread of its own.

A thread SHALL be ordered among the others by its newest message, so that what
moved most recently reads first.

#### Scenario: A run of notifications about one thing

- **WHEN** a mailbox holds several messages that answer one another
- **THEN** they appear as a single row, not as one row each

#### Scenario: A message that answers nothing

- **WHEN** a message's headers place it in no thread
- **THEN** it appears as a row of its own

#### Scenario: Two unrelated messages sharing a subject

- **WHEN** two messages share a subject but neither answers the other
- **THEN** they remain separate rows

#### Scenario: The newest decides where a thread sits

- **WHEN** several threads are shown
- **THEN** they are ordered by the arrival of each thread's newest message, newest first

### Requirement: Mail is shown in the inbox

Mail SHALL be shown in the inbox view, which is the board's queue of things
that have arrived and not been decided about. A message needing a decision and
an undated task needing one are the same kind of thing at the same cadence,
and two queues asking that question separately would be worse than one.

Mail SHALL NOT appear among a day's rows. A day holds what has been promised.

Mail rows SHALL lead the inbox's tasks. Mail is time-ordered and perishable
where an undated task waits indefinitely, so the processing starts at the top
of the view rather than after a scroll.

Mail SHALL NOT take part in the ordering of tasks, and removing every mail row
from the inbox SHALL leave its tasks in precisely the order the rules for
tasks give them.

The inbox SHALL report how many threads it is showing and how many messages
they stand for, beside what it already reports about tasks, so the size of
each queue is visible without counting rows.

#### Scenario: Mail is in the inbox

- **WHEN** a person asks for the inbox and the mailbox holds messages
- **THEN** the threads appear there, above the tasks awaiting triage

#### Scenario: A day holds no mail

- **WHEN** any day is shown
- **THEN** no mail row appears in it

#### Scenario: Someday holds no mail

- **WHEN** the someday view is shown
- **THEN** no mail row appears in it

#### Scenario: The inbox's tasks keep their own order

- **WHEN** the inbox holds mail and tasks together
- **THEN** disregarding the mail leaves the tasks in exactly the order they would have had alone

#### Scenario: Both queues are counted

- **WHEN** the inbox is shown with mail and tasks in it
- **THEN** it reports how many threads and how many messages, beside what it reports about tasks

#### Scenario: An inbox with no mail at all

- **WHEN** no mailbox is configured, or it holds nothing
- **THEN** the inbox is exactly the view it was before, tasks and counts alike

### Requirement: What a mail row shows

A mail row SHALL show when its newest message arrived, who it is from, what it
is about, and — where the thread holds more than one message — how many.

The row SHALL be distinguishable from a task at a glance, and not by colour
alone, as a calendar event's row and a tracker issue's row already are.

Where a sender or a subject is longer than its column, it SHALL be shortened
rather than pushing the row's other columns off the screen.

A subject SHALL be shown as the text it is. It is written by whoever sent the
message and SHALL NOT be interpreted as instructions to the board, nor drawn
in a way that lets its characters change how the rest of the board appears.

#### Scenario: A thread of several messages

- **WHEN** a thread holds more than one message
- **THEN** its row shows the newest arrival, the sender, the subject, and how many messages there are

#### Scenario: A thread of one

- **WHEN** a thread holds a single message
- **THEN** its row shows the same things, without a count

#### Scenario: A mail row is not mistaken for a task

- **WHEN** the inbox is shown with mail in it
- **THEN** a mail row is marked apart from a task's row, and colour is not what distinguishes them

#### Scenario: A subject with markup characters in it

- **WHEN** a subject contains square brackets or text that reads as markup
- **THEN** every character appears as sent, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A subject too long for its column

- **WHEN** a subject is longer than the room the column has
- **THEN** it is shortened, and no other column is pushed off the screen

### Requirement: What a message says is shown when its row is selected

The board SHALL show what the selected thread's newest message says, where it
shows a selected task's note. A subject alone says a build failed; the message
says which build and what broke, and a queue triaged without that is triaged
by guessing.

The message's own words SHALL be shown, without its subject repeated: the
subject is already the row's title, and showing it again at the head of the
body reads as a mistake.

It SHALL be shown as the text it is. A message is written by somebody else and
SHALL NOT be interpreted as instructions to the board, nor drawn in a way that
lets its characters change how the rest of the board appears.

Where a message carries only HTML, the board SHALL show it as readable text
rather than showing nothing. Notification mail is often HTML alone, so a board
that read only the plain part would be blank for exactly the messages most
worth looking at. Where a message carries both, the plain part SHALL be
preferred, being what the sender wrote for reading as text.

Turning HTML into text SHALL keep the addresses it carries. The markup holds
the address while the words hold only the link's text, so a rendering that
dropped them would leave nothing for the board to open on precisely the mail
most likely to have something to open.

A message with nothing in its body SHALL show nothing there, as a task with no
note does. Moving to another row SHALL show that row's own note or message,
with nothing of the previous one left.

#### Scenario: What a notification says

- **WHEN** a mail row is selected and its newest message has a body
- **THEN** that body is shown where a task's note is shown

#### Scenario: The subject is not repeated

- **WHEN** a mail row is selected
- **THEN** the subject appears as the row's title and not again at the head of the body

#### Scenario: A message written to look like markup

- **WHEN** a message's body contains square brackets or text that reads as markup
- **THEN** every character appears as sent, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A message carrying only HTML

- **WHEN** a mail row is selected whose newest message has no plain part, only HTML
- **THEN** the message is shown as readable text rather than as nothing

#### Scenario: A message carrying both

- **WHEN** a message has a plain part and an HTML part
- **THEN** the plain part is what is shown

#### Scenario: The addresses in HTML survive being made readable

- **WHEN** an HTML-only message carries addresses in its markup
- **THEN** those addresses are among what the row can open

#### Scenario: HTML that will not parse

- **WHEN** a message's HTML is malformed
- **THEN** the row is still shown, with whatever text could be read from it

#### Scenario: A message with an empty body

- **WHEN** a mail row is selected whose newest message has no body
- **THEN** that area is empty, and nothing announces the absence

#### Scenario: Moving off a mail row

- **WHEN** a person selects a task after selecting a mail row
- **THEN** the task's own note is shown, and no part of the message remains

### Requirement: What a mail thread points at can be opened

The board SHALL let a person open what a mail thread points at, by the key
that already opens a task's link, a tracker issue's page and a calendar
event's address.

The candidates SHALL be taken from the thread's newest message rather than
from all of them. A run of notifications about one thing carries one
near-identical address per message — four builds of a job give four console
addresses differing only in a number — and offering every one would ask a
person to choose between things they cannot tell apart.

Where the thread's text names an issue in a configured tracker project, that
issue SHALL be among what can be opened, by the same rule that applies to a
task.

Where more than one thing can be opened, the board SHALL ask which, as it
already does for a task. Where nothing can be, it SHALL say so.

#### Scenario: Opening a notification's link

- **WHEN** a person asks to open a mail row whose newest message carries one address
- **THEN** that address is handed to the operating system

#### Scenario: A run of near-identical addresses

- **WHEN** a thread holds several messages each carrying its own similar address
- **THEN** only the newest message's is offered, rather than one per message

#### Scenario: A thread naming a tracker issue

- **WHEN** a thread's text names an issue in a configured tracker project
- **THEN** that issue's page is among what can be opened

#### Scenario: A thread with nothing to open

- **WHEN** a thread carries no address and names no issue
- **THEN** nothing is opened and the board says so

### Requirement: A mail row cannot be changed from the board

No key that writes SHALL act on a mail row: it can be neither completed,
cancelled, renamed, rescheduled, filed, tagged, reordered nor deleted, and its
note cannot be edited. The board reads the mailbox and does not own it.

Where a person presses such a key on a mail row, the board SHALL say why
nothing happened rather than doing nothing silently.

Opening what the row points at is not a change and SHALL remain available, as
it does for a calendar event and a tracker issue.

#### Scenario: A key that writes is refused

- **WHEN** a person presses any key that would change a task, with a mail row selected
- **THEN** nothing is written, and the board says the row belongs to the mailbox

#### Scenario: Nothing is asked before refusing

- **WHEN** a person presses a key that would gather something first — a date, a name, a confirmation
- **THEN** the board refuses at once, without asking for anything

#### Scenario: Opening is the one key that acts

- **WHEN** a mail row is selected
- **THEN** the key that opens a link acts, and every key that would change it says it is not editable here

#### Scenario: A mail row is not counted among the tasks

- **WHEN** the board reports how many tasks a view holds
- **THEN** mail rows are not counted among them

### Requirement: The mailbox never delays or breaks the board

Reading the mailbox SHALL NOT delay any other view. A day's tasks SHALL appear
without waiting for it, and a mailbox that is slow, missing or unreadable
SHALL NOT keep them off the screen.

A mailbox large enough to be slow to read SHALL NOT make the board
unresponsive while it is read.

#### Scenario: A day does not wait for the mailbox

- **WHEN** a day is opened while the mailbox is being read
- **THEN** the day's tasks are on screen without waiting for it

#### Scenario: An unreadable mailbox leaves the day alone

- **WHEN** the mailbox cannot be read
- **THEN** the day shows its tasks as it always does, and the failure is reported as the mailbox's, not the day's

#### Scenario: A large mailbox does not freeze the board

- **WHEN** the mailbox holds far more messages than a person would read
- **THEN** the board stays responsive while it is read

## MODIFIED Requirements

### Requirement: Inbox view

The board SHALL offer an inbox view listing every unfinished task that has no date, is not deferred, and has no project. A task that has been given a project has already been sorted, so it does not belong in the queue awaiting triage. Finished tasks SHALL be excluded from it, because the store holds far more finished undated tasks than open ones and including them would bury the tasks awaiting triage.

The inbox SHALL additionally hold the mail awaiting a decision, as its own requirement states. It is the same queue: a message not yet decided about and an undated task not yet decided about are alike, and both are worked through at the same cadence.

#### Scenario: Reaching the inbox

- **WHEN** a person asks for the inbox
- **THEN** the board lists the unfinished tasks that have no date, are not deferred, and have no project, together with the mail awaiting a decision, and nothing else

#### Scenario: A dated task is not in the inbox

- **WHEN** a task carries any date
- **THEN** it does not appear in the inbox

#### Scenario: A deferred task is not in the inbox

- **WHEN** an undated task is marked deferred
- **THEN** it appears in the someday view and not in the inbox

#### Scenario: Finished undated tasks stay out

- **WHEN** an undated task has been completed or cancelled
- **THEN** it does not appear in the inbox

#### Scenario: A filed task is not in the inbox

- **WHEN** an undated, undeferred task has a project
- **THEN** it does not appear in the inbox
