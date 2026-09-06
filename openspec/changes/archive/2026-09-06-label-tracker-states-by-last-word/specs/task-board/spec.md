## MODIFIED Requirements

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

A state SHALL be shown as its last word, in lower case. The tracker names its
states in its own phrasing, where the leading words are often shared between
them and the last word is the one that carries the meaning; showing the whole
phrase would need a column too wide to spend on a label that repeats down the
block. Lower case is what every other label in the same column already uses,
so the case a state happens to be written in does not show through.

The column carrying the state SHALL be wide enough for a state label and for
the labels the board's own tasks put in the same column, so that neither kind
is cut.

Two configured states MAY end in the same word. Where they do, their rows are
still told apart by the block's grouping, which follows the configured order
of the states.

#### Scenario: The issues appear above today's tasks

- **WHEN** today is displayed and the tracker reports issues for the configured person
- **THEN** each appears as a row above the day's own tasks, showing its key, its summary and its state

#### Scenario: More than one state at once

- **WHEN** the configured states are more than one and the tracker reports issues in several of them
- **THEN** all of them appear, and each row says which state its issue is in

#### Scenario: A state of more than one word

- **WHEN** a configured state is named with several words
- **THEN** the row shows its last word alone, whether the words that precede it are shared with another state or not

#### Scenario: However the tracker capitalises a state

- **WHEN** configured states differ from each other in how they are capitalised
- **THEN** every state on the board reads in lower case, and no row's state differs in case from another's

#### Scenario: Nothing in the shared column is cut

- **WHEN** today shows tracker rows and the day's own tasks together
- **THEN** every state reads in full, and so does every label the day's own tasks put in the same column

#### Scenario: Two states ending in the same word

- **WHEN** two configured states end in the same word
- **THEN** their rows read alike but still appear in separate groups, in the configured order of the states

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
