## ADDED Requirements

### Requirement: An issue's urgency is read as the tracker's own order

The board SHALL read, for each tracker issue, the position the tracker lists
its priority at -- the tracker's own ordering of the values it defines --
alongside the priority's name, on the request the board already makes for its
issues. Reading it SHALL cost no further request.

The board SHALL hold no list of priorities and no order of its own for them.
Which priority is more urgent than which is the tracker's to say, in the
order it lists them; a priority the tracker renames, adds or moves SHALL sort
correctly here with no change to the board. This is the same rule by which
the letter on the row is the first letter of the tracker's own word rather
than one the board chose.

Where the tracker holds no priority for an issue, that issue SHALL have no
position, and SHALL be placed after every issue that has one.

Where issues come from projects whose priorities the tracker defines in
different sets, each issue's position SHALL be read from its own set, and the
board SHALL NOT attempt to reconcile the sets. Within one set the order is
exact; across sets it is whatever the tracker gave, and the order of states
and then of keys is what keeps issues of like urgency in a stable place.

#### Scenario: The position comes with the name

- **WHEN** the tracker's issues are fetched
- **THEN** each issue's priority position arrives with its name on the same request, and no further request is made

#### Scenario: A renamed priority still sorts

- **WHEN** the tracker renames a priority without moving it
- **THEN** issues carrying it sort exactly as before, with no change to the board

#### Scenario: A reordered priority sorts where the tracker put it

- **WHEN** the tracker moves a priority to a different position in its list
- **THEN** issues carrying it sort at the new position on the next fetch

#### Scenario: No priority, no position

- **WHEN** an issue carries no priority
- **THEN** it has no position and is placed after every issue that has one

#### Scenario: Positions from different sets are not reconciled

- **WHEN** two issues from different projects carry priorities at the same position in their own sets
- **THEN** they are treated as equally urgent, and the configured order of states and then the key decide their order

## MODIFIED Requirements

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

Within the block, issues SHALL be ordered by how urgent the tracker calls
them, most urgent first; within one priority by their state in the order the
states are configured; and within one state by issue key. An issue the
tracker holds no priority for SHALL follow every issue that has one.
Configuring the states therefore decides which of them leads among issues of
like urgency, and the tracker's own ordering of its priorities decides the
rest.

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

- **WHEN** issues of one priority are shown in more than one state
- **THEN** they appear grouped in the order the states are configured, and by key within each state

#### Scenario: The most urgent leads

- **WHEN** issues of different priorities are shown, whatever their states
- **THEN** the block lists them most urgent first, in the order the tracker itself lists its priorities

#### Scenario: An issue without a priority goes last

- **WHEN** an issue the tracker holds no priority for is shown among issues that have one
- **THEN** it is listed after all of them

#### Scenario: Ticking a task moves it past the block

- **WHEN** a task is ticked and the day reorders
- **THEN** the ticked task passes below the block, which keeps its own sequence and its place between the unfinished tasks and the finished ones

#### Scenario: Reordering does not reach a tracker row

- **WHEN** a person tries to move a tracker row up or down
- **THEN** the board says the issue lives in the tracker and cannot be reordered here, and nothing changes

### Requirement: A tracker row says how urgent the tracker calls it

A tracker row SHALL show the priority the tracker holds for its issue, as a
single letter, in the leftmost column. The block says what is being worked on
now; which of it is urgent is the next thing a person needs and currently
requires opening each issue to learn.

The letter SHALL be the first letter of the name the tracker itself gives that
priority, so that the board holds no list of priorities in its own source and
a priority the tracker renames needs no change here. This is what the board
already does with a state, where it keeps the last word of the tracker's own
phrasing rather than enumerating the states it expects.

Two of the tracker's priorities MAY begin with the same letter, and where they
do the board SHALL still tell them apart. The pair in question is the most
urgent and the least, so a row read wrongly is read as its opposite. The
letter SHALL be upper case for every priority except the least urgent, which
SHALL be lower case: the same letter said quietly, which keeps each letter
meaning what a person reading the tracker expects and does not pretend the two
names begin differently.

The priority SHALL NOT be conveyed by colour. The board already undertakes to
distinguish a tracker row from a task without relying on colour, and the same
reason applies more strongly here: the tracker gives the same priority
different colours in different definitions, so a colour would say two things
and settle neither.

The priority SHALL order the block, most urgent first, as the block's own
requirement states; the letter on the row and the position in the block are
two readings of the same value the tracker holds. Where the tracker words one
priority in more than one way, the board SHALL show the same letter for all
of them.

Where the tracker holds no priority for an issue, the row SHALL show nothing
in that place rather than standing in for the absence.

Showing the priority SHALL NOT make it changeable. A tracker row refuses every
write, and reporting one more of its fields SHALL add no way to alter it.

The leftmost column SHALL keep its existing meaning for the board's own tasks.
Nothing a task shows there is displaced.

#### Scenario: An issue's priority is on its row

- **WHEN** today shows a tracker issue for which the tracker holds a priority
- **THEN** its row carries one letter standing for that priority, in the leftmost column

#### Scenario: The letter is the tracker's own word

- **WHEN** the tracker names a priority
- **THEN** the letter shown is the first letter of that name, not of a name the board chose for it

#### Scenario: The two priorities that share a letter

- **WHEN** rows are shown for the most urgent priority and for the least, and the tracker's names for them begin with the same letter
- **THEN** the two rows can be told apart, the least urgent reading in lower case and the most urgent in upper

#### Scenario: The same priority worded differently

- **WHEN** the tracker words one priority differently in two places
- **THEN** both rows show the same letter

#### Scenario: An issue with no priority

- **WHEN** the tracker holds no priority for a shown issue
- **THEN** that place on its row is empty

#### Scenario: Colour says nothing

- **WHEN** priorities are shown
- **THEN** which priority a row carries is legible without colour, and no two priorities are distinguished by colour alone

#### Scenario: The block is ordered as before

- **WHEN** issues of one priority are shown
- **THEN** they keep the order they always had -- the configured order of states, then key -- and only issues of differing priority are placed by it

#### Scenario: Nothing else about the row changes

- **WHEN** a tracker row shows a priority
- **THEN** its key, its summary and its state read exactly as they would without it

#### Scenario: A task's row is untouched

- **WHEN** the day shows the board's own tasks alongside tracker issues
- **THEN** what a task shows in the leftmost column is exactly what it showed before

#### Scenario: Still nothing can be changed

- **WHEN** a person acts on a tracker row showing a priority
- **THEN** the row refuses every write it refused before, and offers no way to change the priority
