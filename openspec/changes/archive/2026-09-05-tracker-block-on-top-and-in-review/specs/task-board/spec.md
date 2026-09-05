## RENAMED Requirements

- FROM: `### Requirement: The board reports hidden work and issues in progress`
- TO: `### Requirement: The board reports hidden work and the issues it is tracking`

## REMOVED Requirements

### Requirement: The tracker block is fixed in place and not ordered

**Reason**: The block moved from below the day's tasks to above them, so its
scenario asserting that every issue is listed *below* everything the board
manages is now false rather than merely reworded. Its replacement states the
same two guarantees -- fixed in place, and taking no part in the day's
ordering -- for the block's new position, and adds the ordering the states
now need.

**Migration**: None for anyone using the board. The replacement requirement,
`The tracker block sits above the day and is not ordered`, covers everything
this one did.

### Requirement: Today shows the issues currently in progress

**Reason**: The block no longer shows only what the tracker calls in
progress, and no longer sits below the day's tasks, so both its name and two
of its scenarios -- one asserting issues appear under the day's own tasks,
one asserting what happens when nothing is in progress -- say something the
board no longer does.

**Migration**: None for anyone using the board. The replacement requirement,
`Today shows the issues the tracker reports for me`, covers everything this
one did and states what the block now shows.

## ADDED Requirements

### Requirement: Today shows the issues the tracker reports for me

Today's view SHALL additionally show the issues assigned to the configured
person that the issue tracker reports as being in any of the configured
states, in a block above every task the board manages.

The block SHALL appear on today alone. An issue the tracker reports as being
worked on or waiting on review is current rather than scheduled, and showing
it under every date would say it was.

Each row SHALL carry the issue's key and its summary, so that an issue can be
recognised and named without opening it, and the state the tracker reports it
in, so that issues in different states can be told apart. Where more than one
state is shown, which state an issue is in SHALL be visible without opening it.

#### Scenario: The issues appear above today's tasks

- **WHEN** today is displayed and the tracker reports issues for the configured person
- **THEN** each appears as a row above the day's own tasks, showing its key, its summary and its state

#### Scenario: More than one state at once

- **WHEN** the configured states are more than one and the tracker reports issues in several of them
- **THEN** all of them appear, and each row says which state its issue is in

#### Scenario: Only today

- **WHEN** any view other than today is displayed
- **THEN** no tracker issue appears in it

#### Scenario: Nothing to show

- **WHEN** the tracker reports no issue in any configured state
- **THEN** today's view shows the day's own tasks and no tracker block

#### Scenario: The day's own tasks are unaffected

- **WHEN** tracker issues are shown
- **THEN** the day's own tasks are exactly those it would show without them, in the same order

#### Scenario: A tracker row is distinguishable from a task

- **WHEN** the block is shown above the day's tasks
- **THEN** a tracker row is marked differently from a task, without relying on colour to tell them apart

### Requirement: The tracker block sits above the day and is not ordered

The tracker block SHALL sit before every task the board manages and SHALL NOT
take part in the day's ordering. Its rows SHALL NOT be interleaved with tasks,
SHALL NOT move when tasks are ticked or reordered, and SHALL keep a stable
sequence among themselves.

Within the block, issues SHALL be ordered by their state in the order the
states are configured, and by issue key within a state. Configuring the
states therefore decides which of them leads the block.

No key that reorders SHALL move a tracker row, and the board SHALL say why
rather than doing nothing.

#### Scenario: Above everything the board manages

- **WHEN** today holds past-due tasks, tasks due today, finished tasks and tracker issues
- **THEN** every tracker issue is listed before all of them

#### Scenario: The configured order of states is the order of the block

- **WHEN** issues are shown in more than one state
- **THEN** they appear grouped in the order the states are configured, and by key within each state

#### Scenario: Ticking a task does not disturb the block

- **WHEN** a task is ticked and the day reorders
- **THEN** the tracker rows stay where they were, before the tasks, in the same sequence

#### Scenario: Reordering does not reach a tracker row

- **WHEN** a person tries to move a tracker row up or down
- **THEN** the board says the issue lives in the tracker and cannot be reordered here, and nothing changes

## MODIFIED Requirements

### Requirement: Which issues are shown is configured, not built in

The assignee, the projects and the states that select the issues SHALL be read
from the environment, so that no login, project name or credential is written
into the board. More than one state SHALL be configurable, and their order
SHALL be the order the block is grouped in.

Where the tracker is not configured, the board SHALL show no tracker block and
SHALL NOT report a failure: a board with no tracker configured is an ordinary
board, not a broken one.

#### Scenario: A tracker is configured

- **WHEN** the tracker is configured and reachable
- **THEN** the issues it reports for that configuration are shown

#### Scenario: Several states are configured

- **WHEN** more than one state is configured
- **THEN** issues in any of them are shown, and none in any other state is

#### Scenario: No tracker is configured

- **WHEN** no tracker is configured
- **THEN** today shows only the day's own tasks, and the board reports no tracker failure

#### Scenario: Configured with a state that no longer exists

- **WHEN** a configured state matches no issue
- **THEN** it simply contributes nothing, and the issues in the other configured states still appear

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no person, no project, no state and no tracker address, and all of them are discovered at run time

### Requirement: The board reports hidden work and the issues it is tracking

When work tasks are being hidden, the board SHALL report that, alongside whatever else it is reporting about the view. When today is shown and the tracker block holds issues, the board SHALL report how many, counted separately from the tasks it manages, and SHALL NOT name them by any single state, since more than one may be shown.

#### Scenario: Reporting hidden work beside the other counts

- **WHEN** today is displayed with past-due tasks gathered into it and work is being hidden
- **THEN** the board reports the past-due count and the hidden-work count together, and neither replaces the other

#### Scenario: Tracker issues are counted separately

- **WHEN** today is displayed with tracker issues shown
- **THEN** the board reports how many issues it is tracking, and the count of tasks it reports is the number of tasks it manages, not including them

#### Scenario: The count is not named for one state

- **WHEN** issues in more than one state are shown
- **THEN** what the board reports about them does not describe them all as being in any one of those states
