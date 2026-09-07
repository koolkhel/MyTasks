## REMOVED Requirements

### Requirement: The tracker block sits above the day and is not ordered

**Reason**: The position this requirement exists to state is reversed by this
change, and two of its scenarios are named for that position — `Above
everything the board manages` and the wording of `Ticking a task does not
disturb the block`, which says the rows stay "before the tasks". A scenario
cannot be renamed inside a modification, so the requirement is replaced rather
than edited, and the replacement carries every rule this one had beyond
placement.

**Migration**: Replaced by `The tracker block sits below the day's unfinished
tasks and is not ordered`, which keeps unchanged: that the block takes no part
in the day's ordering, that its rows are never interleaved with tasks, that it
keeps a stable sequence among themselves, that issues within it are ordered by
configured state and then by key, and that no key which reorders may move a
tracker row. Only where the block sits differs.

### Requirement: Today shows the issues the tracker reports for me

**Reason**: Its first scenario is named `The issues appear above today's
tasks`, which states the position this change reverses, and a scenario cannot
be renamed within a modification. Its name is also the weaker half of what it
says: the requirement is largely about what each row carries and how a state
is rendered, which the name does not mention.

**Migration**: Replaced by `Today shows the tracker's issues, and what each
one is`, which keeps every rule unchanged — the block on today alone, the key
and summary and state each row carries, a state shown as its last word in
lower case, the shared column wide enough for both kinds of label, and two
states ending in the same word still told apart by grouping — and every
scenario, with the one naming the old position renamed and reworded to say
the rows appear among today's tasks.

## ADDED Requirements

### Requirement: The tracker block sits below the day's unfinished tasks and is not ordered

The tracker block SHALL sit after every unfinished task the board manages and
before the first finished or cancelled one. An issue names no hour and no
date, which makes it kin to the day's untimed work rather than to the
appointments and the overdue tasks that lead the day.

Where the day holds no finished task, the block SHALL end the list. Where
every task is finished, the block SHALL lead them. In both cases the rule is
the same one: the block marks where the day's unfinished work ends.

The block SHALL NOT take part in the day's ordering. Its rows SHALL NOT be
interleaved with tasks, SHALL NOT be reordered by anything the day does, and
SHALL keep a stable sequence among themselves.

Within the block, issues SHALL be ordered by their state in the order the
states are configured, and by issue key within a state. Configuring the
states therefore decides which of them leads the block.

No key that reorders SHALL move a tracker row, and the board SHALL say why
rather than doing nothing.

#### Scenario: Below the unfinished work and above the finished

- **WHEN** today holds past-due tasks, tasks due today, finished tasks and tracker issues
- **THEN** every tracker issue is listed after all the unfinished tasks and before every finished one

#### Scenario: Beside the day's untimed work

- **WHEN** today holds tasks that name a time and tasks that name none, together with tracker issues
- **THEN** the block follows the tasks naming no time, with no unfinished task of the day between them

#### Scenario: A day with nothing finished

- **WHEN** today holds tracker issues and no finished or cancelled task
- **THEN** the block ends the list

#### Scenario: A day with everything finished

- **WHEN** every task today is finished or cancelled and the tracker reports issues
- **THEN** the block is listed before all of them

#### Scenario: The configured order of states is the order of the block

- **WHEN** issues are shown in more than one state
- **THEN** they appear grouped in the order the states are configured, and by key within each state

#### Scenario: Ticking a task moves it past the block

- **WHEN** a task is ticked and the day reorders
- **THEN** the ticked task passes below the block, which keeps its own sequence and its place between the unfinished tasks and the finished ones

#### Scenario: Reordering does not reach a tracker row

- **WHEN** a person tries to move a tracker row up or down
- **THEN** the board says the issue lives in the tracker and cannot be reordered here, and nothing changes

### Requirement: Today shows the tracker's issues, and what each one is

Today's view SHALL additionally show the issues assigned to the configured
person that the issue tracker reports as being in any of the configured
states, in a block placed among the tasks the board manages.

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

#### Scenario: The issues appear among today's tasks

- **WHEN** today is displayed and the tracker reports issues for the configured person
- **THEN** each appears as a row among the day's own tasks, showing its key, its summary and its state

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

- **WHEN** the block is shown among the day's tasks
- **THEN** a tracker row is marked differently from a task, without relying on colour to tell them apart
