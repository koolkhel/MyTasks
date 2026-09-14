## REMOVED Requirements

### Requirement: The board reads named folders from a directory of maildirs

**Reason**: The requirement guaranteed that a message already marked read is
not in the queue, and that guarantee is what this change retires. It cannot be
carried into a modification: a scenario asserting that a read message does not
appear is the opposite of what the board must now do, and a requirement holding
both would not say which wins. The requirement returns below under a name
that says what it now guarantees -- every message the folders hold, rather than
the unread ones -- with its other ten scenarios unchanged.

**Migration**: None for anyone reading the board. Messages that were read
without being filed return to the queue -- 525 of them on the account this was
found on -- which is the point rather than a side effect. Nothing is written to
the mail account, no message changes, and a person who wants a message gone
files it, from the board or from their mail client, exactly as before.

## ADDED Requirements

### Requirement: The board reads every message in the named folders

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

Within those folders the board SHALL read every message the folder holds,
whether or not it has been marked read. A queue is what has not been dealt
with, and being filed away is what dealing with a message means: filing moves
it out of the folder, so what the folder still holds is exactly what is
outstanding. The board SHALL NOT consult the read flag to decide what is in
the queue.

A message SHALL therefore leave the queue only by leaving the folder --
reviewed from the board, or moved by hand in whatever program the person reads
mail with. Reading a message SHALL NOT take it out of the queue: a person who
opens a message to see what it is has not decided anything about it, and a
queue that emptied itself on being read would lose the messages most worth
keeping.

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

#### Scenario: A message already read is still in the queue

- **WHEN** a message in a named folder is marked read, here or in another program
- **THEN** it is still shown, because reading it decided nothing about it

#### Scenario: A message filed by hand leaves the queue

- **WHEN** a message is moved out of a named folder by another program
- **THEN** it is no longer shown, the folder no longer holding it

#### Scenario: A message whose flags cannot be read

- **WHEN** a message's flags cannot be read at all
- **THEN** it is shown like any other, an unreadable flag being no reason to withhold a message

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

## MODIFIED Requirements

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

Confirming SHALL cost a number of folder openings that does not grow with the
row. The archive holds everything the account has ever kept and opening it was
measured on this account at about fourteen seconds against about one to search
it, so opening it once per message makes a folded row cost minutes where it
could cost seconds. This is not only a matter of waiting: an operation is
exposed to the line being dropped for as long as it is open, and the failure
that made that concrete happened on a row of seven.

Where a confirmation asks the archive about more than one group of messages —
those just moved, and those that turned out already to be elsewhere — it SHALL
ask in the same opening. They concern one folder and there is no reason to
open it twice.

Undoing a review SHALL move the messages back to the folder they came from,
and SHALL restore each message to the read state it had before the review --
read if it was read, unread if it was not. The read flag records what a person
has looked at, which is theirs rather than the review's; an undo that marked
everything unread would erase it, and one that marked everything read would
invent it. The board SHALL say that the row returns only once the mirror next
catches up, and SHALL NOT pretend the row is back before it is.

An undo SHALL be all or nothing. Where it fails, every message SHALL be left
where it was and the row SHALL NOT come back, rather than some messages
reaching the folder and the rest staying in the archive. A row split across
two places is the state hardest to reason about and the one a person can do
least about; one outcome and one notice is worth more here than salvaging part
of an undo.

#### Scenario: A confirmed archive retires the row

- **WHEN** the messages are absent from their folder and present in the archive
- **THEN** the row stays gone

#### Scenario: An unconfirmed archive brings the row back

- **WHEN** the archive cannot be confirmed
- **THEN** the row returns and the board says why

The economy SHALL be counted in requests to the account, not in any one
protocol's idea of opening a folder. What a row costs SHALL NOT grow with the
number of messages it holds: confirming is one question about a set of
identities, asked once.

#### Scenario: A message already archived

- **WHEN** a message is not in its folder and is found in the archive
- **THEN** the review is reported as already done, not as a failure

#### Scenario: A message in neither place

- **WHEN** a message is in neither its folder nor the archive
- **THEN** the board says so rather than reporting success

#### Scenario: Undoing a review puts the mail back

- **WHEN** a person undoes a review
- **THEN** the messages are moved back to the folder they came from, each with the read state it had before the review, and the board says the row returns when the mirror next catches up

#### Scenario: Undoing does not unread what a person had read

- **WHEN** a person undoes a review of a thread whose messages they had already read elsewhere
- **THEN** those messages are read afterwards, the undo having restored what was there rather than clearing it

#### Scenario: Undoing a thread read in part

- **WHEN** a thread holds both read and unread messages and its review is undone
- **THEN** each message is left as it was before the review, the two groups being restored separately

#### Scenario: Confirming a folded row costs no more openings than a single one

- **WHEN** rows of one message and of many are reviewed
- **THEN** confirming each costs the archive the same number of requests, whatever the row holds

#### Scenario: One opening answers about both groups

- **WHEN** a row holds messages that were moved and messages already elsewhere
- **THEN** one request to the archive answers about both groups

#### Scenario: An undo that fails leaves the row whole

- **WHEN** putting a row back fails part way
- **THEN** none of its messages have reached the folder, all are still in the archive, and the board says the undo failed

#### Scenario: Giving up is still possible while confirming

- **WHEN** the board is ended without being asked while a row is being confirmed
- **THEN** the confirmation gives up cleanly rather than running to the end

### Requirement: The board logs what it does to the mailbox

The board SHALL write a log of every operation it performs on the mail account: what was attempted, on which folder, how many messages, how long it took, and how it ended. The mailbox is the one place the board changes something it cannot change back on its own, and a failure there is announced in a notice that the next notice replaces — so what happened SHALL be recoverable afterwards rather than only at the moment it happened.

The log SHALL be a file, off screen. The board SHALL NOT offer a view of it: it is for reading after the fact with whatever a person reads files with.

Each entry SHALL carry the time in a form that sorts and is unambiguous, a level saying whether the entry is ordinary, a warning, or a failure, and one line saying what happened. Successful operations SHALL be logged as well as failures, so that the sequence and the timings can be read, not only the faults.

The log SHALL record message identities, folder names, counts and durations. It SHALL NOT record a subject, a sender, or any part of a message's body: the file is durable and sits outside the mail store, and an identity is both what the gateway addresses a message by and what a person would search on.

Writing the log SHALL be best-effort. A log that cannot be written — a missing directory, a full disk, a permission — SHALL NOT change what the board does or fail an operation. Losing a log entry is a smaller harm than losing a review.

The log SHALL NOT be committable: it holds identities and folder names from a real account, and the repository is a place that gets shared.

#### Scenario: An operation is logged

- **WHEN** a mail row is reviewed and confirmed
- **THEN** the log holds an entry saying what was attempted and one saying how it ended, each with a time, a level and a duration

#### Scenario: An operation names the messages it acted on

- **WHEN** an operation on the mail account succeeds
- **THEN** the log names the identity of every message it acted on, so that what became of one message is answerable from the log alone rather than only from the account

#### Scenario: A failure is logged

- **WHEN** an archive cannot be confirmed
- **THEN** the log holds an entry marked as a failure, saying which folder and how many messages, and why

#### Scenario: Nothing identifying is written

- **WHEN** any operation is logged
- **THEN** the entry holds no subject, no sender and no part of any message body

#### Scenario: A log that cannot be written

- **WHEN** the log cannot be written at all
- **THEN** every operation behaves exactly as it would have, and nothing is reported to the person about the log

#### Scenario: The log is not committable

- **WHEN** the repository is inspected for what it would commit
- **THEN** the log is excluded, and no entry from it is in anything tracked
