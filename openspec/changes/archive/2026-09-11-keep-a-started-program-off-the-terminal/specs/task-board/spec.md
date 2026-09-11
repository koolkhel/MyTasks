## MODIFIED Requirements

### Requirement: Starting a workspace from an issue

The board SHALL offer a key that starts work on the selected tracker issue by
running one configured program. The board SHALL NOT check anything out, reach
any host, or know what a repository is: it runs the program and reports
whether it could be started.

The key SHALL act only on a tracker row. A task that merely mentions an
issue's key SHALL NOT offer it, because the board holds no issue behind such a
mention and so knows neither its project nor its version.

The board SHALL always ask which version to work at, proposing the issue's own
as the answer. It SHALL be an answer a person may replace, not a choice among
the versions the issue names: the version an issue is recorded against is
where a problem was found or is due, which is not always the version somebody
is about to work in. Where the issue names several, the first SHALL be
proposed; where it names none, the prompt SHALL open empty.

Leaving the prompt, or confirming it empty, SHALL start nothing. A workspace
SHALL therefore always be started at some version, which is what makes the
prompt the place the decision is made rather than a confirmation of one
already taken.

Where no program is configured, the board SHALL say so. Where the program
cannot be started -- it is not there, or is not runnable -- the board SHALL
say that, distinguishably from having started it. The board SHALL NOT wait
for the program, nor report what it does afterwards: what happens next is
visible where the program puts it.

The program SHALL NOT be able to reach the board's terminal at all, in either
direction. It SHALL be started detached from it -- in a session of its own,
with no controlling terminal -- rather than merely having its streams sent
elsewhere.

Both directions matter, and the second is the one that bites. A line the
program printed would be painted across the shown view with nothing able to
take it back. But a program that opens the controlling terminal can also make
it answer, and what a terminal answers arrives in the same queue a person's
typing arrives in: the board reads it as keys, and acts on them. Sending the
program's three streams elsewhere does not prevent either, because a child can
open the terminal directly and bypass every stream it inherited.

A program with something to say SHALL have somewhere of its own to say it.

Starting a workspace SHALL write nothing. No request SHALL be sent to the
tracker or to the task store, and nothing about the issue SHALL change.

#### Scenario: Starting from a tracker row

- **WHEN** a person presses the key on a tracker row with a program configured
- **THEN** the program is started and the board says so

#### Scenario: The row is not a tracker issue

- **WHEN** a person presses the key on a task, a calendar row or a mail row
- **THEN** nothing is started, and the board says the key is for a tracker issue

#### Scenario: No program is configured

- **WHEN** a person presses the key with no program configured
- **THEN** nothing is started, and the board says no workspace program is set

#### Scenario: The program cannot be started

- **WHEN** the configured program does not exist or cannot be run
- **THEN** the board says it could not be started, in terms distinguishable from having started it

#### Scenario: The issue's version is proposed

- **WHEN** a person presses the key on an issue with a version
- **THEN** the board asks which version to work at, with the issue's own already filled in

#### Scenario: Accepting the proposal

- **WHEN** a person confirms the proposed version unchanged
- **THEN** the program is started at that version

#### Scenario: Working at another version

- **WHEN** a person replaces the proposed version with a different one
- **THEN** the program is started at the one they typed, and the issue is unchanged

#### Scenario: An issue with several versions

- **WHEN** a person presses the key on an issue naming more than one version
- **THEN** the first is proposed, and the others neither replace it nor are offered as a list

#### Scenario: An issue with no version

- **WHEN** a person presses the key on an issue naming no version
- **THEN** the board asks all the same, with nothing filled in

#### Scenario: Leaving the prompt

- **WHEN** a person is asked which version and leaves, or confirms it empty
- **THEN** nothing is started

#### Scenario: Nothing is written

- **WHEN** a person starts a workspace
- **THEN** no request is sent to the tracker or to the task store, and the issue is exactly as it was

#### Scenario: The program cannot write on the board

- **WHEN** the started program writes to its output or its errors
- **THEN** none of it appears on the shown view, whatever the program prints and however much

#### Scenario: The program cannot reach the terminal itself

- **WHEN** the started program opens the controlling terminal rather than using the streams it was given
- **THEN** there is none for it to open, so nothing it does there can be drawn on the board

#### Scenario: The board cannot be typed into by what it starts

- **WHEN** the started program causes the terminal to send anything back
- **THEN** none of it reaches the board, and no action runs that nobody pressed a key for

#### Scenario: The board does not wait

- **WHEN** the program has been started
- **THEN** the board is usable at once, and says nothing further about what the program went on to do
