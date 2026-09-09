## ADDED Requirements

### Requirement: An unhandled failure leaves a file behind

Where a failure the board does not handle ends the session, the board SHALL
write that failure to a file before it goes. A traceback printed to the
terminal survives only as long as the scrollback and only if someone thought
to save it; the board acts on a real mail account over a gateway that drops
connections, so the evidence of a failure SHALL outlive the session that
produced it.

The file SHALL sit in the same directory as the log of what the board does to
the mailbox, and SHALL be written on the same best-effort terms: a file that
cannot be written SHALL NOT change how the session ends, and SHALL NOT be
reported to the person as a second failure on top of the first.

Each failure SHALL get its own file, named so that the files sort by when they
happened and one failure never overwrites another. A person who crashed twice
SHALL be able to read both.

The file SHALL carry the whole failure: the exception, every frame of the
traceback, and the values held in those frames. This is deliberately more
than the mailbox log records — that log SHALL NOT hold a subject, a sender or
any part of a body, and this file SHALL be expected to hold all three, because
a frame in the middle of a review holds the messages being reviewed. The two
files answer different questions. The log says what the board did and is read
routinely; this file says why the board stopped and is read once, by someone
who has already lost the session and should not also have to reproduce it.

Because it holds message text, the crash file SHALL NOT be committable. This
is not a convenience it inherits from sitting beside the log: it is the
condition on which the file is allowed to hold what it holds.

The board SHALL still end the session. A failure it did not anticipate is
evidence of a defect, not a state to keep working in, and a board that carries
on after one cannot be trusted about what it did to the account afterwards.

#### Scenario: A failure is written down

- **WHEN** a failure the board does not handle ends the session
- **THEN** a file in the mailbox log's directory holds the exception and the traceback that produced it

#### Scenario: The session still ends

- **WHEN** a failure the board does not handle occurs
- **THEN** the session ends, as it would have without the file being written

#### Scenario: One failure does not overwrite another

- **WHEN** two sessions end in unhandled failures
- **THEN** there are two files, and the order they happened in can be read from their names

#### Scenario: The frames are kept

- **WHEN** a review is part way through and the session ends in an unhandled failure
- **THEN** the file holds the values the frames were holding, including the messages being reviewed

#### Scenario: The crash file is not committable

- **WHEN** the repository is inspected for what it would commit
- **THEN** no crash file is included, and no part of one is in anything tracked

#### Scenario: A crash file that cannot be written

- **WHEN** the crash file cannot be written at all
- **THEN** the session ends exactly as it would have, and nothing about the file is reported to the person

## MODIFIED Requirements

### Requirement: The mailbox never delays or breaks the board

Reading the mailbox SHALL NOT delay any other view. A day's tasks SHALL appear
without waiting for it, and a mailbox that is slow, missing or unreadable
SHALL NOT keep them off the screen.

A mailbox large enough to be slow to read SHALL NOT make the board
unresponsive while it is read.

Acting on the mailbox SHALL NOT break the board either. An operation on the
account SHALL fail in exactly one way as far as the board is concerned: the
operation is reported as having failed, and the session continues. A
connection lost part way through — the gateway closing the line mid-command,
a socket error, anything the protocol underneath can raise — SHALL be that
same failure, and SHALL NOT end the session. It is the most likely way an
operation on this account fails, not an exceptional one: an operation stays
open for tens of seconds, and the longer it is open the better its chance of
being cut.

Where an operation fails after part of its work has been done, the board SHALL
report the failure rather than the part that succeeded, and SHALL NOT undo
what was confirmed. Half a review is a row a person must look at again, which
they can do; mail moved with no record of it is work lost, which they cannot.

#### Scenario: A day does not wait for the mailbox

- **WHEN** a day is opened while the mailbox is being read
- **THEN** the day's tasks are on screen without waiting for it

#### Scenario: An unreadable mailbox leaves the day alone

- **WHEN** the mailbox cannot be read
- **THEN** the day shows its tasks as it always does, and the failure is reported as the mailbox's, not the day's

#### Scenario: A large mailbox does not freeze the board

- **WHEN** the mailbox holds far more messages than a person would read
- **THEN** the board stays responsive while it is read

#### Scenario: A connection lost part way through a review

- **WHEN** the connection is lost part way through reviewing a row
- **THEN** the row returns to the queue, the failure is reported as the mailbox's, the log records it with the folder and how long it took, and the board is still running

#### Scenario: A connection lost part way through an undo

- **WHEN** the connection is lost part way through putting a reviewed row back
- **THEN** the failure is reported, the log records it, and the board is still running

#### Scenario: What was already done stays done

- **WHEN** some of a row's messages have been archived and confirmed and then the connection is lost
- **THEN** those messages stay archived, the row is reported as failed, and nothing is moved back to make the report tidy
