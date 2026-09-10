## ADDED Requirements

### Requirement: The board records what it said to the mailbox

The board SHALL write down every request it makes to the mail account: when it
was made, which command it was, which folder it concerned, how many messages or
which message it named, how long it took, and how it ended. The log of what the
board *did* records an operation and its outcome; this records the conversation
underneath it, which is what a person needs when the question is not whether
something failed but where.

Recording SHALL be always on. It SHALL NOT wait to be switched on, because the
fault it exists for cannot be reproduced on demand: a gateway drops a line
when it drops one, and a trace that has to be turned on first is a trace that
was off.

Each request's duration SHALL be recorded, and it SHALL be the load-bearing
field. A command's identity says what was attempted; its duration is what says
whether the account was healthy, slowing, or already gone — and it is the one
thing that cannot be reconstructed afterwards.

A request that failed SHALL be recorded as such, with what it failed with, so
that the last line before a session ends is the request that ended it.

The trace SHALL be written to its own file, one for each day it records, kept
beside the log of what the board did. Two reasons, both about being able to
read either: the trace is far larger than that log — a full pass of the
mailbox measures thousands of lines against a log of hundreds — and a fault is
looked for by the day it happened on, which a file named for its day answers
directly. Old days SHALL be removable without touching the current one.

The trace SHALL NOT contain a subject, a sender, or any part of a message's
body. This SHALL hold structurally rather than by inspection of each line: the
board SHALL make no request that fetches a header or a body, so no such text
can reach the trace to be filtered out of it.

The trace SHALL NOT contain a credential. The request that carries one SHALL
remain outside the traced path, so that a password is not written and then
masked but never seen.

Writing the trace SHALL be best-effort. A trace that cannot be written — no
directory, no room, no permission — SHALL NOT change what the board does, SHALL
NOT fail an operation, and SHALL NOT be reported to the person: losing a line
is a smaller harm than losing the work it was describing.

The board SHALL NOT read the trace back. No row SHALL depend on it and deleting
it SHALL change nothing the board shows, which is the condition on keeping it
at all. It SHALL NOT be committable: it holds a real account's folder names and
message identities.

Recording SHALL cost no request. The board SHALL ask the account for nothing on
account of the trace, and SHALL make the same requests it would have made
without it.

#### Scenario: Every request is written down

- **WHEN** the board acts on the mail account
- **THEN** each request it makes appears in the trace, naming the command and the folder it concerned

#### Scenario: How long each took

- **WHEN** a request completes
- **THEN** its duration is recorded with it

#### Scenario: The request that ended a session

- **WHEN** a request fails
- **THEN** it is recorded as having failed, with what it failed with, and it is the last request recorded for that operation

#### Scenario: A day at a time

- **WHEN** the board records requests on two different days
- **THEN** each day's are in a file named for that day, and removing one day's leaves the other untouched

#### Scenario: Nothing was switched on

- **WHEN** the board acts on the mail account without anybody having asked for a trace
- **THEN** the requests are recorded anyway

#### Scenario: No message text can appear

- **WHEN** the whole trace of any operation is read
- **THEN** it holds no subject, no sender and no part of a body, because no request the board makes asks for any

#### Scenario: No credential can appear

- **WHEN** the whole trace of any operation is read
- **THEN** it holds no password, the request that carries one not being among those recorded

#### Scenario: A trace that cannot be written

- **WHEN** the trace cannot be written at all
- **THEN** every operation behaves exactly as it would have, and nothing about the trace is reported to the person

#### Scenario: Nothing depends on it

- **WHEN** the trace is deleted while the board is not running
- **THEN** the next run shows exactly the rows it would have shown anyway

#### Scenario: It is not committable

- **WHEN** the repository is inspected for what it would commit
- **THEN** no trace file is included, and no line from one is in anything tracked

#### Scenario: It costs the account nothing

- **WHEN** an operation is performed with the trace being written
- **THEN** the requests made to the account are exactly those that would have been made without it
