## ADDED Requirements

### Requirement: A view of every recurring series

The board SHALL offer a view holding every recurring series the account has, and
holding nothing else. A series is a task carrying a repeat; an occurrence the
store generated from one is not a series and SHALL NOT appear here, because it
appears on its own day already and a list mixing the two would be a list of
neither.

The view SHALL be reached by a key of its own, listed in the key bar and in the
help like every other. It is not a day, so day navigation SHALL NOT apply to it,
exactly as it does not apply to the inbox, the someday view or the archive.

The store offers no way to ask for series alone: its task listing has no filter
for a repeat. The view SHALL therefore be gathered by reading the account's
tasks and keeping those that carry one. That reading SHALL happen when the view
is first asked for and SHALL NOT happen again on returning to it; a reload SHALL
drop what is held so that the next asking reads afresh. This is the arrangement
the archive already uses, for the same reason: the fetch is several requests and
a view redrawn from what is held is immediate.

The rows SHALL be drawn as the reading's pages arrive rather than after the last
of them. A view that stays empty while several requests complete is worse than
one that fills.

Rows SHALL be ordered by when each series next comes round, soonest first, so
that the view answers "what is about to happen" before "what exists". A series
with no next occurrence SHALL be ordered after every series that has one.

The reading SHALL ask the store for every occurrence rather than letting it
collapse them. Asked the other way the store pages unreliably: it post-filters
after paging, so rows repeat and rows are missed. The board SHALL NOT depend on
that behaviour anywhere, and the count a series reports of its queued
occurrences depends on seeing them all.

#### Scenario: The view holds the series and not their occurrences

- **WHEN** the account holds recurring series and occurrences those series generated
- **THEN** the view lists every series once and lists no occurrence

#### Scenario: A view for an account with no series

- **WHEN** the account has no recurring task at all
- **THEN** the view is shown, holds no rows, and says it is empty rather than appearing not to have loaded

#### Scenario: Returning to the view does not read again

- **WHEN** the view has been shown and a person leaves it and comes back
- **THEN** the rows are drawn from what was held and the store is not asked again

#### Scenario: A reload reads afresh

- **WHEN** a person asks for a reload while the view is shown
- **THEN** what was held is dropped and the store is read again

#### Scenario: Soonest first

- **WHEN** the view holds series whose next occurrences fall on different days
- **THEN** the one coming round soonest is drawn first, and a series with no next occurrence is drawn after those that have one

#### Scenario: Day navigation does not apply

- **WHEN** a person presses a day-navigation key while the view is shown
- **THEN** the view does not change to a day, as in the board's other views that are not days

### Requirement: What a series row says about its repeat

For the selected series the board SHALL report, beside its note and in the same
area the board already uses for what a row is rather than what it says:

- what the repeat means, in words a person can check against their intention,
- whether the series waits for the current occurrence to be finished before the
  next exists, or produces occurrences regardless,
- how many occurrences are already queued, and the furthest ahead they reach,
- when the series ends, where it ends at all.

The wait-or-stack distinction SHALL be reported in both directions, naming
which one is in force rather than only marking the unusual case. It is the fact
a person most often wants and cannot otherwise discover, and a report that is
silent when a series stacks up cannot be told from a report that failed.

The queued count SHALL be the occurrences the board actually holds for that
series, and the board SHALL NOT infer it from the repeat's arithmetic. A count
derived from the rule would describe what the store ought to have made rather
than what it made.

A series row's own columns SHALL carry the next occurrence where a task's row
carries its start time, and its title and project as every row does. The repeat
SHALL NOT be written into the title column: the row's width belongs to the
title, which is what tells one series from another.

#### Scenario: A repeating series reports its rule and its stacking

- **WHEN** a series repeating weekly is selected
- **THEN** the area says what the repeat means in words and says whether it waits for completion or stacks up

#### Scenario: Waiting and stacking are both named

- **WHEN** one selected series waits for completion and another produces occurrences regardless
- **THEN** each says which of the two it does, and neither is silent about it

#### Scenario: The queued count is what is held

- **WHEN** a series has occurrences queued ahead of it
- **THEN** the area reports how many the board holds for it and how far ahead they reach, not a number worked out from the rule

#### Scenario: A series that never ends

- **WHEN** a selected series has no ending
- **THEN** the area says so rather than reporting an ending it does not have

#### Scenario: The next occurrence is in the row

- **WHEN** a series row is drawn
- **THEN** the column that carries a start time carries the next occurrence, and the title column carries the title alone

### Requirement: A repeat the board cannot read is said to be unreadable

The store documents the repeat as an object with no fields, so its shape is
known to the board only by having been observed. A repeat whose form the board
does not recognise SHALL be reported as one it cannot read, naming the row, and
the row SHALL still be listed with its title and whatever else is readable.

The board SHALL NOT present a guess as a reading. A row claiming a repeat it
inferred would be worse than a row admitting it does not know: the person would
have no reason to check it against the app, which is the one place the truth is.

An unreadable repeat SHALL NOT prevent the view from being drawn, and SHALL NOT
prevent any other series from reporting its own.

#### Scenario: An unfamiliar repeat

- **WHEN** a series carries a repeat in a form the board does not recognise
- **THEN** the row is listed and the area says the repeat cannot be read, naming nothing it has not read

#### Scenario: One unreadable repeat among many

- **WHEN** one series of several carries an unreadable repeat
- **THEN** the view is drawn, that row says so, and every other row reports its own repeat as usual

### Requirement: Nothing is written from the recurring view

Every action that writes to a task SHALL be refused while the recurring view is
shown, and the board SHALL say the view is a reading rather than failing
quietly. Unlike the board's other read-only rows, this is not because the rows
belong to somebody else: a series is the board's own task and the board could
write to it. What is unknown is what such a write would reach. The store
generates occurrences from a series ahead of time, and whether renaming,
rescheduling or ticking a series reaches the occurrences it has already made is
not established. A board that guessed would be editing rows a person cannot see.

The refusal SHALL be decided by the action rather than by the row, as the
archive's is, so that it covers every write the board offers now and every one
added later.

The same task SHALL remain as editable as it ever was on its own day. The
refusal is a property of the view, not of the task.

#### Scenario: A write is refused in the view

- **WHEN** a person presses a key that would change a task while the recurring view is shown
- **THEN** nothing is sent to the store and the board says the view is a reading

#### Scenario: A write added later is refused too

- **WHEN** the board offers a write that did not exist when this view was made
- **THEN** it is refused in this view without that action having to be named

#### Scenario: The same task on its own day

- **WHEN** a series task is shown on the day it is dated, outside the recurring view
- **THEN** every write the board offers on it works as it does on any task

## MODIFIED Requirements

### Requirement: The board names the view it is showing

The board SHALL show which of its views is displayed, naming the inbox, the someday view, the archive and the recurring view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds.

#### Scenario: Showing the inbox

- **WHEN** the inbox is displayed
- **THEN** the board names it as the inbox and reports how many tasks it holds

#### Scenario: Showing a calendar day

- **WHEN** a calendar day is displayed
- **THEN** the board names that day and how it relates to today, as it did before

#### Scenario: Showing the archive

- **WHEN** the archive is displayed
- **THEN** the board names it as the archive and reports how many tasks it holds

#### Scenario: Showing the recurring view

- **WHEN** the recurring view is displayed
- **THEN** the board names it as the recurring view and reports how many series it holds
