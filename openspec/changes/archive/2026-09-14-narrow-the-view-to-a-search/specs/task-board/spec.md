## ADDED Requirements

### Requirement: Narrowing the view to a search

The board SHALL offer a key that asks for a term, and SHALL then draw only the
rows whose title contains it. Escape SHALL clear the search and bring every
row back.

The term SHALL be matched against the title alone -- a mail row's subject, or
a task's, an event's or a tracker issue's title -- and SHALL NOT be matched
against the sender, the project, the date, or the body of a message. What a
person reads in the title column is what the search answers to.

The term SHALL be matched against the title the row carries rather than the
string drawn in the cell: before the count of messages is appended to a mail
subject, and before the column shortens the title to fit. A word a person can
read on the focus card SHALL NOT be unfindable because the column cut it off.

The match SHALL be a plain substring and SHALL ignore letter case, so that a
subject is found however its sender capitalised it.

Every source the view draws SHALL be narrowed -- the store's tasks, mail
threads, calendar events and tracker issues -- and SHALL be narrowed where the
work filter narrows, rather than being added to the view afterwards. A source
whose rows are appended after the narrowing is a source the key cannot reach,
however the rows are marked.

Narrowing SHALL remove rows from the view without changing any task: no write
SHALL be made, and nothing SHALL be altered about a task because it was drawn
or not drawn.

Where the work filter is also in force, a row SHALL be drawn only if it
survives both, and neither key SHALL clear the other.

Confirming an empty term SHALL be the same as having no search. Cancelling the
prompt SHALL leave whatever search was already in force exactly as it was.

#### Scenario: Finding a thread in a long inbox

- **WHEN** a person searches the inbox for a word that appears in some subjects
- **THEN** only the rows whose subject contains that word are drawn, and the rest are not

#### Scenario: Only the title is matched

- **WHEN** a person searches for a word that appears in a message's sender or body but not in its subject
- **THEN** that row is not drawn, because the search answers to the title alone

#### Scenario: A title the column cut off

- **WHEN** a person searches for a word that is part of a title too long for the column to show
- **THEN** that row is drawn, because the search reads the title the row carries rather than the shortened cell

#### Scenario: The thread count is not part of the subject

- **WHEN** a person searches for the number of messages shown beside a mail subject
- **THEN** that row is drawn only if the number is in the subject itself

#### Scenario: Letter case does not matter

- **WHEN** a person searches with a term whose letters are cased differently from the title
- **THEN** the row is still drawn

#### Scenario: Every source is narrowed, in the view that holds it

- **WHEN** a search is in force in the inbox, which holds the store's tasks and the mailbox's threads, and on today, which holds the store's tasks, the calendar's events and the tracker's issues
- **THEN** rows of every one of those four kinds are drawn only if their title contains the term, no view holding all four at once

#### Scenario: No source is reached only by being marked

- **WHEN** the board draws rows from a source and a search is in force
- **THEN** they are narrowed together with the store's tasks, and no source's rows reach the view past the narrowing

#### Scenario: Nothing is written

- **WHEN** a person starts a search, changes it, or clears it
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: Clearing brings the rows back

- **WHEN** a person presses escape with a search in force
- **THEN** every row the view holds is drawn again, exactly as it was before the search

#### Scenario: Cancelling the prompt changes nothing

- **WHEN** a person opens the prompt with a search already in force and cancels it instead of confirming
- **THEN** the search that was in force is still in force, unchanged

#### Scenario: An empty term is no search

- **WHEN** a person confirms the prompt having typed nothing
- **THEN** the view is drawn as it is with no search at all

#### Scenario: Both filters at once

- **WHEN** the work filter is on and a person searches for a term that some work rows match
- **THEN** those rows are still not drawn, because a row is drawn only if it survives both, and clearing one leaves the other in force

#### Scenario: What is selected after narrowing

- **WHEN** a search is applied or cleared
- **THEN** the selection is on a row that is drawn, or nothing is selected because no row is

### Requirement: How long a search lasts, and where it applies

A search SHALL apply to every view the board shows, so that moving between the
inbox, a calendar day and the someday view does not change what it means. It
SHALL last as long as the board is open or until it is cleared, and no longer:
nothing about it SHALL be written anywhere.

Rows that arrive while a search is in force -- a fetch answering, mail
arriving, the calendar or the tracker replying -- SHALL be narrowed by it like
every other row, so that a search cannot be outrun by a redraw.

#### Scenario: The search follows the person between views

- **WHEN** a person searches in the inbox and then moves to a calendar day or the someday view
- **THEN** that view is narrowed by the same term, without the key being pressed again

#### Scenario: Rows arriving are narrowed too

- **WHEN** a fetch, the mailbox, the calendar or the tracker adds rows to a view while a search is in force
- **THEN** those rows are drawn only if their title contains the term

#### Scenario: It lasts no longer than the board

- **WHEN** a person searches, leaves the board, and opens it again
- **THEN** no search is in force and every row is drawn

### Requirement: The board says when a search is narrowing the view

When a search is in force, the board SHALL say so where it already reports
what the shown view holds, and SHALL report how many rows the search removed.
A view that is quietly shorter than expected SHALL NOT be indistinguishable
from a day with less on it.

The board SHALL say so even when the search removes nothing, so that a search
matching everything is never invisible, and even when it removes every row, so
that an empty view is never indistinguishable from a board that has failed.

The board SHALL say which term is in force, so that a person returning to the
board after a while is told what it is doing rather than left to remember.

Where no search is in force, the board SHALL say nothing about it.

The counts the board already reports SHALL go on naming the number of rows
shown, with the removed count reported separately, as it already does for
hidden work and for the tasks the inbox withholds.

#### Scenario: A search that hides something

- **WHEN** a search is in force and the shown view holds rows that do not match
- **THEN** the board reports the term and how many rows it removed, alongside the counts it already reports

#### Scenario: A search that hides nothing

- **WHEN** a search is in force and every row in the shown view matches it
- **THEN** the board still reports that a search is in force, so that it is never invisible

#### Scenario: A search that hides everything

- **WHEN** a search is in force and no row in the shown view matches it
- **THEN** the view is empty and the board reports the term, so that the empty view is explained rather than looking like a failure

#### Scenario: No search

- **WHEN** no search is in force
- **THEN** the board reports nothing about one

#### Scenario: The counts still add up

- **WHEN** a search is in force and the board reports how many rows the view holds
- **THEN** that count is the number of rows shown, and the removed count is reported separately

#### Scenario: Both filters are reported

- **WHEN** a search is in force and work is being hidden as well
- **THEN** the board reports both, and neither replaces the other
## MODIFIED Requirements

### Requirement: Keys work in either keyboard layout

Every key the board binds SHALL also answer the character the same physical
key produces in a Russian layout, so that a person presses the key printed on
the keyboard whichever layout is active and need not switch layouts to reach
an action.

A key whose character does not change with the layout SHALL need nothing
further. This covers the arrow keys and the space, enter, escape and
backspace keys.

Where the character a key produces in a Russian layout is already bound to
another action, the board SHALL NOT take it from the action that has it. The
newcomer SHALL instead be given a second key whose Russian character is free,
so that the action is reachable in either layout without any action losing the
key a person already knows. No two actions SHALL answer the same key in either
layout.

Where an action carries a second key for that reason, the board SHALL name the
action by the key it is usually known as, so that what is printed in the help
and on the key bar is the gesture rather than the workaround.

#### Scenario: Adding a task without switching layout back

- **WHEN** a person adds a task, types a Russian title, confirms it, and presses the add key again while the keyboard is still in a Russian layout
- **THEN** the add prompt opens again, without the layout having to be switched

#### Scenario: Every bound letter answers both layouts

- **WHEN** a person presses any key the board binds to a Latin letter, in a Russian layout
- **THEN** the same action runs as it would in an English layout

#### Scenario: A key that is the same in both layouts

- **WHEN** a person presses space, enter, escape, backspace or an arrow key in a Russian layout
- **THEN** it does what it does in an English layout, needing no separate provision

#### Scenario: Typing a Russian title still types

- **WHEN** a person types a title containing Cyrillic letters that the board also binds to actions
- **THEN** the characters go into the text being typed and no action runs, because a prompt has the keyboard while it is open

#### Scenario: A key whose Russian character is already spoken for

- **WHEN** the board binds a key whose Russian character another action already answers
- **THEN** that other action keeps its key unchanged, and the new action answers a second key as well, so it can be reached in either layout

#### Scenario: No two actions answer one key

- **WHEN** every key the board binds is listed, in both layouts
- **THEN** no key appears twice, and no action has been left reachable in only one layout
