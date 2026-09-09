## ADDED Requirements

### Requirement: The board shows whether the mailbox is busy

Reviewing a mail row is the slowest thing the board does — measured at about 13 seconds for a row of one message and 25 seconds a message for a folded one — and reviews are done one at a time, so ticking several leaves the later ones waiting. The board SHALL show whether any of that work is in flight, so that a person can tell whether what they have ticked has landed before they tick more or leave.

The indication SHALL be one cell at the right of the day bar, shown in every view. Mailbox work outstands regardless of which view is being looked at, and whether it is safe to quit is the same question in all of them.

It SHALL distinguish three things:

- that nothing is in flight and nothing has failed,
- that something is in flight,
- that something has failed since the person last asked for a reload.

The in-flight state SHALL be animated. A still mark cannot be told from a stuck one, and these operations last tens of seconds; motion is the information. The animation SHALL run only while work is in flight, and SHALL NOT redraw the list — by the same rule the clock follows, a mark that disturbed the rows above it would cost more than it gave.

The failed state SHALL persist until the person asks for a reload or restarts the board. It SHALL NOT be cleared by a later operation succeeding: a failure among ten reviews would otherwise be painted over before it was seen, which is the fault this exists to fix.

The indication SHALL return to its untroubled state whenever the last operation finishes, whichever way it finished. A mark that stayed busy after the work stopped would tell a person to wait for nothing, which is worse than showing nothing at all.

#### Scenario: Nothing in flight

- **WHEN** no mailbox operation is running and none has failed
- **THEN** the day bar's right cell shows that nothing is outstanding

#### Scenario: An operation running

- **WHEN** a person ticks a mail row and its archiving is under way
- **THEN** the cell shows work in flight, and keeps moving while it lasts

#### Scenario: Several ticked in succession

- **WHEN** a person ticks several mail rows faster than they can be confirmed
- **THEN** the cell shows work in flight until the last of them has finished

#### Scenario: Back to rest

- **WHEN** the last outstanding operation finishes
- **THEN** the cell shows that nothing is outstanding, and stops moving

#### Scenario: Every way an operation can end

- **WHEN** an operation ends by being confirmed, by failing to confirm, by finding the message already archived, by finding it in neither place, by the gateway being unreachable, or by giving up because the board is closing
- **THEN** the cell stops showing that operation as in flight in every one of those cases

#### Scenario: A failure is shown until it is acknowledged

- **WHEN** an operation fails and later operations succeed
- **THEN** the cell still shows that something has failed

#### Scenario: A reload clears it

- **WHEN** a person asks for a reload after a failure
- **THEN** the cell shows that nothing is outstanding again

#### Scenario: The animation does not disturb the list

- **WHEN** the cell is animating while work is in flight
- **THEN** no row is redrawn on account of it, and neither the selected row nor the view's position moves

#### Scenario: Shown in every view

- **WHEN** mailbox work is in flight and a person moves between a day, the inbox and the someday view
- **THEN** the cell is shown in each of them

### Requirement: Quitting asks while the mailbox is busy

Where mailbox work is in flight, quitting SHALL ask first, saying how much is outstanding. Quitting mid-queue abandons the reviews that have not started; nothing is lost, because they moved nothing, but the rows return at the next start and are then indistinguishable from a message the local mirror has not caught up on.

Where nothing is in flight, quitting SHALL NOT ask. A question asked every time is a question that stops being read.

Declining SHALL leave the board exactly as it was, with the work still running.

Nothing here SHALL make a forced end fail: where the board is ended without being asked, an operation part way through SHALL still give up cleanly, as it already does.

#### Scenario: Quitting with work in flight

- **WHEN** a person asks to quit while mail is being archived
- **THEN** the board asks first, saying how much is outstanding

#### Scenario: Declining

- **WHEN** a person declines that question
- **THEN** the board is still running, still showing what it was, and the work is still under way

#### Scenario: Confirming

- **WHEN** a person confirms it
- **THEN** the board ends

#### Scenario: Quitting with nothing in flight

- **WHEN** a person asks to quit and no mailbox work is outstanding
- **THEN** the board ends without asking

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

## MODIFIED Requirements

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

The board SHALL draw no row from anything it wrote itself. Every row comes
from a source, and the account is the record of what has been promoted; the
board SHALL keep no record it reads back, on disk or anywhere else.

A log of what the board did is not such a record. Nothing reads it, no row
depends on it, and deleting it SHALL change nothing the board shows. That is
what makes it safe to keep, and it is required separately.

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

#### Scenario: The log is not a record the board reads

- **WHEN** the board's log of what it did to the mailbox is deleted while the board is not running
- **THEN** the next run shows exactly the rows it would have shown anyway
