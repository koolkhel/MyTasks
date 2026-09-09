## ADDED Requirements

### Requirement: Messages about one issue fold into one row

Messages that are about the same thing SHALL be shown as one row. A person
reviewing a tracker's notifications is deciding about an issue, not about each
comment on it: the real folders hold 1,056 messages standing for 199 issues,
and a row per message asks the same question five times over.

Two messages SHALL be folded together when both hold true:

- their subjects name the same issue in a configured tracker project, and
- the first address each carries is the same.

Both conditions, not either. The first alone is not enough: in one of the
folders read daily, mail about a merge request names the issue it mentions, so
several unrelated requests cite one issue — folding on the name alone merged
24 of 38 groups wrongly. Requiring that they also point at the same place is
what makes the rule safe, and it validates itself against the data rather than
against a list of folder names somebody has to maintain.

A configured project's key SHALL be what is recognised, not a general pattern
for letters-dash-digits. That pattern also matches a version or a standard,
and the board already has one place that knows which projects count.

Where the rule does not apply, messages SHALL be grouped as they are today, by
the headers that say which message answers which. A folder whose subjects name
no issue SHALL therefore be unchanged by this.

A folded row SHALL report how many messages it stands for, as a row already
does.

#### Scenario: Updates about one issue are one row

- **WHEN** several messages name the same issue in a configured project and carry the same first address
- **THEN** they appear as a single row, reporting how many messages it stands for

#### Scenario: The same issue in unrelated mail is not folded

- **WHEN** two messages name the same issue but carry different first addresses
- **THEN** they remain separate rows

#### Scenario: A general pattern is not mistaken for an issue

- **WHEN** a subject carries letters, a dash and digits that are not a configured project's issue
- **THEN** no folding happens on it

#### Scenario: A folder that names no issues is unaffected

- **WHEN** a folder's subjects name no configured project's issue
- **THEN** its messages are grouped exactly as they were before this

### Requirement: Reviewing a message takes it out of the mailbox

The board SHALL let a person mark the selected mail row reviewed, by the key
that ticks a task, and SHALL then move every message the row stands for to the
account's archive folder.

Moving is what makes a reviewed message not come back. The folder it was in is
mirrored locally; the archive is not. So an archived message has nowhere to
return from, where a flag on a local file only says that one program has seen
it.

The move SHALL be made on the server, addressed by each message's own
identity. Once the archive is confirmed, the messages SHALL be marked read —
the one flag the board sets anywhere, and only on messages it has confirmed
are in the archive. A queue is what has not been dealt with; a reviewed
message the account still calls new is not that, and every other program
reading the account would show it as new mail.

Beyond that move and that flag the board SHALL change nothing about the
account: no message SHALL be deleted, and none SHALL be moved anywhere but
the archive.

Where a row stands for several messages, all of them SHALL be moved. A row
that is one decision must not leave half its mail behind to be decided again.

The board SHALL show the row gone at once and do the moving behind the screen,
as it does for every write it makes.

Promoting a thread to a task SHALL archive it too. One review, one outcome: a
message that became a task has been dealt with as surely as one that was
merely read.

#### Scenario: A reviewed row leaves the inbox

- **WHEN** a person ticks the selected mail row
- **THEN** the row goes at once, and its messages are moved to the archive

#### Scenario: Every message in a folded row is archived

- **WHEN** a row standing for several messages is reviewed
- **THEN** all of them are moved, not only the newest

#### Scenario: Promoting archives as well

- **WHEN** a thread is turned into a task
- **THEN** its messages are archived, and the task is created

#### Scenario: Nothing is deleted, and nothing goes elsewhere

- **WHEN** the board has reviewed and promoted messages
- **THEN** no message has been deleted and none has been moved to any folder but the archive

#### Scenario: A reviewed message is marked read

- **WHEN** a row's messages are confirmed in the archive
- **THEN** they are marked read, in one request, and no flag is set anywhere but the archive

#### Scenario: An unconfirmed archive marks nothing read

- **WHEN** the archive cannot be confirmed
- **THEN** no message has been marked read

### Requirement: An archive is confirmed before a row is retired

The board SHALL confirm an archive before treating the row as gone: the
messages SHALL be absent from the folder they were in and present in the
archive. Both, because a move that removed mail without delivering it is the
one outcome that loses work, and the gateway this speaks to has been found
violating its protocol elsewhere.

Where a message is already absent from its folder, the board SHALL ask the
archive before concluding anything. Found there, the review has already
happened and SHALL be reported as done rather than as an error. Found in
neither, the board SHALL say so: something moved that message, and it was not
the board.

Where the archive cannot be confirmed, the row SHALL come back and the board
SHALL say why. A row retired on an unconfirmed move is a message a person
believes they have dealt with.

Undoing a review SHALL move the messages back to the folder they came from
and SHALL mark them unread again, or the row would return to a queue that no
longer counts it. The board SHALL say that the row returns only once the
mirror next catches up, and SHALL NOT pretend the row is back before it is.

#### Scenario: A confirmed archive retires the row

- **WHEN** the messages are absent from their folder and present in the archive
- **THEN** the row stays gone

#### Scenario: An unconfirmed archive brings the row back

- **WHEN** the archive cannot be confirmed
- **THEN** the row returns and the board says why

#### Scenario: A message already archived

- **WHEN** a message is not in its folder and is found in the archive
- **THEN** the review is reported as already done, not as a failure

#### Scenario: A message in neither place

- **WHEN** a message is in neither its folder nor the archive
- **THEN** the board says so rather than reporting success

#### Scenario: Undoing a review puts the mail back

- **WHEN** a person undoes a review
- **THEN** the messages are moved back to the folder they came from, unread again, and the board says the row returns when the mirror next catches up

### Requirement: The board reads named folders from a directory of maildirs

The board SHALL read messages from the folders named in the environment,
found inside a directory named there too. Reading SHALL make no network call
and need no credentials.

The path SHALL name a directory that holds maildirs, and each named folder
SHALL be one of them: a directory of that name beside the others. This is the
layout the sync tool that fills it writes. The path is not itself a maildir
and the board SHALL NOT try to read it as one.

The board SHALL read the named folders and no others. What wants processing
daily is a few folders rather than every message an account has ever held,
and reading only those is what keeps the queue a queue. Where no folder is
named, the board SHALL show no mail and SHALL NOT report a failure: naming
none is how a person turns mail off.

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

The board SHALL alter nothing in the local mailbox at all: no flag, no name,
no folder, no content. Not even to record that a message has been reviewed —
that is recorded on the server, where it is authoritative, and a message moved
by hand in a mirrored maildir is documented to break the sync that fills it.

Where no mailbox is configured, the board SHALL show no mail and SHALL NOT
report a failure. A board without one is an ordinary board.

Where a mailbox is configured but cannot be read, the board SHALL say so once
and SHALL otherwise carry on: the day's tasks, the tracker and the calendar
SHALL be unaffected.

#### Scenario: Messages are read from the named folders

- **WHEN** a directory of maildirs is configured and folders are named in it
- **THEN** the board reads their messages, and makes no network call to do so

#### Scenario: A folder is a directory beside the others

- **WHEN** a folder is named in the environment
- **THEN** it is found as a directory of that name, not as a dot-prefixed subdirectory

#### Scenario: Only the named folders are read

- **WHEN** the directory holds folders beyond those named
- **THEN** messages from the named folders appear and messages from the others do not

#### Scenario: No folder named means no mail

- **WHEN** a directory is configured but no folder is named
- **THEN** the board shows no mail and reports no failure

#### Scenario: The path is not read as a mailbox itself

- **WHEN** the configured directory holds maildirs but is not one
- **THEN** the board reads the named folders and does not report the directory unreadable

#### Scenario: A folder that does not exist

- **WHEN** a named folder is not in the directory
- **THEN** the board says so rather than showing a queue quietly missing it

#### Scenario: A message already read is not in the queue

- **WHEN** a message in a named folder is marked read
- **THEN** it does not appear, whether it was read here or in another program

#### Scenario: Nothing is written to the mailbox

- **WHEN** the board has read the mailbox, and a person has reviewed and promoted messages in it
- **THEN** no message's flags, name, folder or content have changed on disk

#### Scenario: No mailbox configured

- **WHEN** no directory is configured
- **THEN** the board shows no mail and reports no failure

#### Scenario: A mailbox that cannot be read

- **WHEN** a directory is configured but missing, unreadable, or holds no named folder
- **THEN** the board says so once and the rest of the board works as it did

#### Scenario: A message the board cannot make sense of

- **WHEN** one message in a folder cannot be parsed
- **THEN** the others are still shown, and the unreadable one does not take the view down with it

## REMOVED Requirements

### Requirement: The board reads a mailbox from a directory

**Reason**: The path was a maildir with the folders hanging off it as
dot-prefixed subdirectories, and the mailbox's own inbox was read when no
folder was named. The real directory is not a maildir at all — it holds one
per folder, the inbox among them — so reading the path itself reports it
unreadable, and "the mailbox's own inbox" names nothing.

**Migration**: Replaced by "The board reads named folders from a directory of
maildirs". Name every folder to read in `MAIL_FOLDERS`, the inbox included if
it is wanted; naming none now means no mail rather than the inbox alone.

## MODIFIED Requirements

### Requirement: Mail is shown in the inbox

Mail SHALL be shown in the inbox view, which is the board's queue of things
that have arrived and not been decided about. A message needing a decision and
an undated task needing one are the same kind of thing at the same cadence,
and two queues asking that question separately would be worse than one.

Mail SHALL NOT appear among a day's rows. A day holds what has been promised.

The inbox's tasks SHALL lead its mail rows. Mail arrives in far greater
quantity than a person files tasks — some 460 rows against 35 — so putting it
first buries one's own work behind a scroll of somebody else's notifications.
The reasoning that once put mail at the top, that processing should start there
rather than after a scroll, argues for this order once the mail is real.

Mail SHALL NOT take part in the ordering of tasks, and removing every mail row
from the inbox SHALL leave its tasks in precisely the order the rules for
tasks give them.

The inbox SHALL report how many rows of mail it is showing and how many
messages they stand for, beside what it already reports about tasks, so the
size of each queue is visible without counting rows.

#### Scenario: Mail is in the inbox

- **WHEN** a person asks for the inbox and the mailbox holds messages
- **THEN** the rows appear there, below the tasks awaiting triage

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
- **THEN** it reports how many rows of mail and how many messages, beside what it reports about tasks

#### Scenario: An inbox with no mail at all

- **WHEN** no mailbox is configured, or it holds nothing
- **THEN** the inbox is exactly the view it was before, tasks and counts alike

#### Scenario: A person's own work is reachable without scrolling

- **WHEN** the inbox holds far more mail rows than tasks
- **THEN** the tasks are at the top of the view, where the cursor starts

### Requirement: What a mail thread points at can be opened

The board SHALL let a person open what a mail row points at, by the key
that already opens a task's link, a tracker issue's page and a calendar
event's address.

Where the row's messages carry an address with a fragment — an address that
names a place *within* a page — the earliest such address SHALL be what is
offered. A person opening a discussion of thirty comments wants to begin where
they left off and read downward, not to land at the newest remark and scroll
up. Measured on the real folders, the earliest and the latest such address
differ in 75 of 121 folded rows, so this is not a distinction without a
difference.

Where no message in the row carries such an address, the candidates SHALL be
taken from the row's newest message rather than from all of them. A run of
notifications about one thing carries one near-identical address per message —
four builds of a job give four console addresses differing only in a number —
and offering every one would ask a person to choose between things they cannot
tell apart. The folder where that reasoning was formed carries no fragments at
all, so it keeps exactly the behaviour it has.

Where the row's text names an issue in a configured tracker project, that
issue SHALL be among what can be opened, by the same rule that applies to a
task.

Where more than one thing can be opened, the board SHALL ask which, as it
already does for a task. Where nothing can be, it SHALL say so.

#### Scenario: Opening a notification's link

- **WHEN** a person opens the selected mail row and it points at one thing
- **THEN** that thing is opened

#### Scenario: A run of near-identical addresses

- **WHEN** a row stands for several notifications about one thing, none of them carrying a fragment
- **THEN** one address is offered, the newest message's, rather than one per message

#### Scenario: The earliest anchored address wins

- **WHEN** a row's messages carry addresses with fragments
- **THEN** the earliest of them is what is offered

#### Scenario: A row with no anchored address falls through

- **WHEN** no message in the row carries an address with a fragment
- **THEN** the newest message's addresses are offered, as before

#### Scenario: A thread naming a tracker issue

- **WHEN** the row's text names an issue in a configured project
- **THEN** that issue's page is among what can be opened

#### Scenario: A thread with nothing to open

- **WHEN** a row carries no address and names no configured issue
- **THEN** the board says there is nothing to open

### Requirement: A mail row cannot be changed from the board

No key that writes to the task store SHALL act on a mail row: it can be
neither cancelled, renamed, rescheduled, filed, tagged, reordered nor deleted,
and its note cannot be edited. The board does not own the message.

Two keys SHALL act on a mail row, and only these two: the one that opens what
it points at, and the one that ticks it — which reviews the message and takes
it out of the mailbox, as that requirement states. Neither changes the row into
something the board owns; the first reads it and the second files it away.

Where a person presses any other writing key on a mail row, the board SHALL
say why nothing happened rather than doing nothing silently.

#### Scenario: A key that writes is refused

- **WHEN** a person presses a key that renames, reschedules, files, tags, reorders, cancels or deletes, with a mail row selected
- **THEN** nothing is written and the board says the row is not the board's to change

#### Scenario: Nothing is asked before refusing

- **WHEN** such a key would normally ask for a date, a name or a confirmation
- **THEN** the board refuses first and asks nothing

#### Scenario: Opening is the one key that acts

- **WHEN** a person opens what a mail row points at
- **THEN** it opens, because reading is not a change

#### Scenario: Ticking reviews rather than completes

- **WHEN** a person ticks a mail row
- **THEN** the message is reviewed and archived, and no task is completed

#### Scenario: A mail row is not counted among the tasks

- **WHEN** the inbox holds mail and tasks together
- **THEN** the task counts count tasks alone

### Requirement: Promoting takes the thread out of the queue

Promoting SHALL archive every message in the row, by the same means and with
the same confirmation as reviewing one, so that the row leaves the inbox for
the same reason. A queue that cannot be drained from the board is a queue that
will be drained somewhere else, which defeats having it on the board.

Archiving, and marking the archived messages read, SHALL be the only changes
made to the account: no message SHALL be deleted, and none SHALL be moved
anywhere but the archive. Nothing SHALL be written to the local mailbox at
all.

The task SHALL be created before the messages are archived, and a failure to
archive SHALL NOT undo the task. A task whose mail is still in the folder is a
row that appears once more; mail archived with no task made is work lost, and
of the two only the first can be put right by a person who can see what
happened.

Where the archive cannot be reached, the board SHALL say so and SHALL leave
the created task alone.

The board SHALL keep no record of what it has promoted. It holds no state of
its own on disk, every row it draws comes from a source, and the account is
now that record.

#### Scenario: The thread leaves the queue

- **WHEN** a thread is promoted
- **THEN** its messages are archived, and the row is gone from the inbox

#### Scenario: Undoing a promotion returns the thread

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the created task is removed and the messages are moved back to the folder they came from

#### Scenario: Nothing else about the mailbox changes

- **WHEN** a thread has been promoted
- **THEN** no message has been deleted, none has moved anywhere but the archive, no flag has been set outside it, and nothing on disk has changed

#### Scenario: The task survives a mailbox that cannot be written

- **WHEN** the archive cannot be reached and a thread is promoted
- **THEN** the task is still created, and the board says the mail could not be archived

#### Scenario: Nothing is remembered

- **WHEN** a thread has been promoted
- **THEN** the board has written no record of it anywhere but the account itself
