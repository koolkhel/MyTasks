## ADDED Requirements

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

The priority SHALL NOT change the order of the block, which stays grouped by
state as it is. Where the tracker words one priority in more than one way, the
board SHALL show the same letter for all of them.

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

- **WHEN** issues of several priorities are shown
- **THEN** they appear in the order they would have without priorities being shown, grouped by state

#### Scenario: Nothing else about the row changes

- **WHEN** a tracker row shows a priority
- **THEN** its key, its summary and its state read exactly as they would without it

#### Scenario: A task's row is untouched

- **WHEN** the day shows the board's own tasks alongside tracker issues
- **THEN** what a task shows in the leftmost column is exactly what it showed before

#### Scenario: Still nothing can be changed

- **WHEN** a person acts on a tracker row showing a priority
- **THEN** the row refuses every write it refused before, and offers no way to change the priority
