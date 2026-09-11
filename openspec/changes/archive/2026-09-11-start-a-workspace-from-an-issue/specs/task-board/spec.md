## ADDED Requirements

### Requirement: An issue's version

The board SHALL read from each tracker issue the version it is against, taken
from a custom field named in the configuration. Which field carries it SHALL
be configured rather than built in: "the version an issue is against" is a
convention of a particular tracker, and a board that named one field would be
describing somebody's tracker rather than trackers.

Reading it SHALL cost no further request. The board already asks for every
custom field of every issue it fetches, so the version is already arriving.

A field SHALL be read whether it holds one value or several, and several
SHALL be kept in the order the tracker gives them. A field the board keeps
only when it holds a single value is a field that silently disappears the day
somebody adds a second.

Where no version field is configured, no issue SHALL have a version and the
board SHALL say nothing about it. Where a field is configured but an issue
does not carry it, or carries it empty, that issue SHALL have no version --
which is an ordinary state, not an error.

#### Scenario: An issue with one version

- **WHEN** a version field is configured and an issue holds one value in it
- **THEN** the issue carries that version

#### Scenario: An issue with several

- **WHEN** an issue holds several values in the configured field
- **THEN** the issue carries all of them, in the order the tracker gave them

#### Scenario: An issue with none

- **WHEN** an issue does not hold the configured field, or holds it empty
- **THEN** the issue carries no version, and nothing is reported as wrong

#### Scenario: No field is configured

- **WHEN** no version field is configured
- **THEN** no issue carries a version, and the board is otherwise unchanged

#### Scenario: Reading it costs nothing

- **WHEN** the board fetches its issues with a version field configured
- **THEN** it makes the same requests, asking for the same fields, as it does with none configured

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

The program's own output SHALL NOT reach the board's display. A program
started this way writes to the terminal the board is drawing on, and a single
line from it would be painted across the shown view where nothing could take
it back. A program with something to say SHALL have somewhere of its own to
say it.

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

#### Scenario: The board does not wait

- **WHEN** the program has been started
- **THEN** the board is usable at once, and says nothing further about what the program went on to do

### Requirement: What the workspace program is told

The program SHALL be given the issue's key, its tracker project, and the
version that was confirmed, each as a named argument and each exactly once.
These are the three facts the board holds and the program does not; everything
else -- which repositories, which host, which branch, which directory --
belongs to the program and SHALL NOT be expressed by the board.

The key and the project SHALL be the tracker's own values, passed through
unaltered. The version SHALL be whatever was confirmed at the prompt, which
began as the issue's own and may be anything a person typed instead.

A branch name SHALL NOT be sent. The board is told a version; how a version
becomes a branch, or a directory, is the program's own and differs between
the two even for the same version.

#### Scenario: The three arguments

- **WHEN** the program is started
- **THEN** it is given the issue's key, its project and the confirmed version, each named and each once

#### Scenario: The version is the confirmed one

- **WHEN** a person replaced the proposed version before confirming
- **THEN** the program is given the version they typed, not the issue's

#### Scenario: The key and the project are the tracker's

- **WHEN** the program is started
- **THEN** the key and the project are exactly as the tracker gave them

#### Scenario: No branch is named

- **WHEN** the program is started
- **THEN** nothing resembling a branch, a directory or a repository is among its arguments

### Requirement: Nothing but a configured program is run

The program SHALL be named by a configured path and by nothing else. No part
of a task's title, a task's note, an issue's summary or any other text the
board displays SHALL determine what is run.

It SHALL be run as a list of arguments, never as a shell command line. No
shell SHALL be invoked. A version, a project key or an issue key is a value
the tracker holds and somebody typed, and passing one to a shell would make
what it contains a question about the board's safety rather than about the
tracker's data.

This requirement stands beside the one that permits only web addresses to be
opened, and for the same reason: text the board did not author must never
decide what the machine does.

#### Scenario: The program comes from the configuration

- **WHEN** a workspace is started
- **THEN** the program run is the configured one, whatever any row's text says

#### Scenario: No shell is used

- **WHEN** a workspace is started
- **THEN** the program is run directly with a list of arguments, and no shell interprets any part of it

#### Scenario: A value holding shell characters

- **WHEN** an issue's version or project contains characters a shell would treat as syntax
- **THEN** the program receives them as an ordinary argument, and nothing else happens

## MODIFIED Requirements

### Requirement: Only opening acts on a tracker issue

Where the selected row is a tracker issue rather than a task, only the actions
that read it SHALL do anything; every action that would change it SHALL say
the issue is not editable here. The board reports a tracker issue and never
alters one.

Opening the issue and starting a workspace from it are both such actions:
neither sends anything to the tracker, and neither changes the issue.

#### Scenario: Only opening works on a tracker issue

- **WHEN** a tracker issue is selected
- **THEN** the key that opens a link opens it, and every action that would change it says it is not editable here

#### Scenario: Starting a workspace works on one too

- **WHEN** a tracker issue is selected
- **THEN** the key that starts a workspace starts one, and every action that would change the issue still says it is not editable here

#### Scenario: Neither read-only action changes the issue

- **WHEN** a person opens a tracker issue or starts a workspace from it
- **THEN** no request is sent to the tracker, and the issue is exactly as it was
