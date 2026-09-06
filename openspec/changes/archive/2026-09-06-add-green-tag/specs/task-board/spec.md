## ADDED Requirements

### Requirement: Marking a task as green

A key SHALL add the configured tag to the selected task, and the same key
pressed again SHALL remove it, so that the two states are reached by one key
rather than two.

Because the tag can be taken off again, the action SHALL NOT be confirmed and
SHALL be undoable, unlike filing a task into a project, which cannot be
reversed and therefore is confirmed.

The action SHALL be available wherever a task is selected, and SHALL be
refused on a tracker row, which the board does not own.

Where no tag is configured the key SHALL say so rather than do nothing.

#### Scenario: Marking a task

- **WHEN** a person presses the key on an unmarked task
- **THEN** the task carries the tag, and the board shows it as marked without refetching the view

#### Scenario: Pressing the same key again

- **WHEN** a person presses the key on a task already marked
- **THEN** the tag is taken off and the task returns to how it read before

#### Scenario: Marking is not confirmed

- **WHEN** a person marks or unmarks a task
- **THEN** the board asks nothing first, because the action can be reversed

#### Scenario: Marking can be undone

- **WHEN** a person marks a task and then undoes the last write
- **THEN** the tag is taken off again, and the board says what it undid

#### Scenario: A tracker row cannot be marked

- **WHEN** a person presses the key on a tracker row
- **THEN** the board says the issue lives in the tracker and nothing is written

#### Scenario: No tag is configured

- **WHEN** no tag is configured and a person presses the key
- **THEN** the board says no tag is configured and nothing is written

### Requirement: Taking the mark off is made to stick

Where the store accepts a write that removes the tag and does not apply it —
answering as though it had — the board SHALL make the removal reliable rather
than report a state the store does not hold. A board that shows a task
unmarked while it is still marked where the tasks are kept is worse than a
board that takes a moment longer.

A removal that follows closely on another tag write to the same task SHALL be
held back until it can be relied on. A removal that follows no recent tag
write SHALL NOT be held back: taking the mark off a task marked at some
earlier time is the ordinary case and SHALL go at once.

Holding a write back SHALL NOT hold the board back. The row SHALL lose its
rail immediately, as every other write shows its outcome immediately, and the
board SHALL remain usable throughout, reporting the write as still in flight
the way it reports any other.

#### Scenario: Marking and then unmarking

- **WHEN** a person marks a task and takes the mark off again moments later
- **THEN** the task ends unmarked both on screen and where the tasks are kept

#### Scenario: Taking off a mark set earlier

- **WHEN** a person unmarks a task that was not marked during this sitting
- **THEN** the write is sent at once, with nothing held back

#### Scenario: The board does not wait with it

- **WHEN** a removal is being held back
- **THEN** the row has already lost its rail, the board answers every key, and the write is reported as still in flight

### Requirement: A green task is marked by a rail, not by colour

A task carrying the tag SHALL be marked in the margin, before everything else
on its row, by a rail that no other row carries. The mark SHALL NOT rely on
colour to be seen, and the colour the tag itself carries SHALL be ignored: a
person may not be able to tell the board's colours apart.

Where marked tasks are next to one another their rails SHALL join into one
unbroken bar, so that a run of them reads as a single block rather than as
several separate marks.

The tag's name SHALL NOT be printed on the row. The rail says which tasks are
marked, and the row's width is better spent on the task.

#### Scenario: A marked task is distinguishable

- **WHEN** a view holds both marked and unmarked tasks
- **THEN** every marked task carries the rail and no unmarked task does, and they can be told apart with colour disregarded

#### Scenario: Adjacent marked tasks read as one block

- **WHEN** several marked tasks are listed one after another
- **THEN** their rails join into a single unbroken bar down the margin

#### Scenario: The tag is not named on the row

- **WHEN** a marked task is shown
- **THEN** its row does not print the tag's name

#### Scenario: The rail is shown in every view

- **WHEN** a marked task appears on a calendar day, in the inbox or in the someday view
- **THEN** it carries the rail in each of them

### Requirement: Green tasks lead every view

A task carrying the tag SHALL be ordered before every task that does not, in
every view, ranking below only whether a task is finished. Marking a task is
therefore how a person says it comes first, which is what the tag is for.

This SHALL rank above how overdue a task is: an unfinished marked task leads
an unmarked one however overdue the unmarked one has become. A person who
marks a task is saying it outranks the job's backlog, and a rule that let
lateness win would say the opposite.

A finished task SHALL still sink whether it is marked or not, so that the
rail never lifts completed work above what is still to do.

#### Scenario: Marked tasks come first

- **WHEN** a view holds both marked and unmarked unfinished tasks
- **THEN** every marked one is listed above every unmarked one

#### Scenario: Marked outranks overdue

- **WHEN** a marked task is due today and an unmarked task is long past due
- **THEN** the marked task is listed first

#### Scenario: A finished marked task still sinks

- **WHEN** a marked task is finished and unmarked tasks are still open
- **THEN** the finished marked task is listed after the open ones

#### Scenario: A move cannot cross the rail

- **WHEN** a person tries to move an unmarked task above a marked one
- **THEN** it stops at the edge, as it does at any other ordering group

### Requirement: The board reports how many green tasks it is showing

When a view holds tasks carrying the tag, the board SHALL report how many,
beside the counts it already reports rather than instead of any of them. The
count SHALL NOT replace the number of tasks the view holds.

#### Scenario: The count appears beside the others

- **WHEN** a view holds marked tasks, past-due tasks and finished tasks
- **THEN** the board reports all of those counts together, and none replaces another

#### Scenario: Nothing marked

- **WHEN** a view holds no marked task
- **THEN** the board reports no count for them

### Requirement: Which tag counts as green is configured, not built in

The tag SHALL be named in the environment by its identifier, so that no tag
name or identifier is written into the board's source.

The board SHALL read the tag back and confirm what the identifier resolves
to, rather than trusting it. Where the identifier resolves to nothing, the
board SHALL say so and SHALL leave every other part of the view working: a
board with no tag configured, or with one configured wrongly, is an ordinary
board rather than a broken one.

#### Scenario: A tag is configured

- **WHEN** a tag is configured and its identifier resolves
- **THEN** tasks carrying it are marked and ordered first

#### Scenario: No tag is configured

- **WHEN** no tag is configured
- **THEN** no task is marked, the ordering is what it would be without the tag, and the board reports no failure

#### Scenario: The identifier resolves to nothing

- **WHEN** a tag is configured but its identifier names no tag
- **THEN** the board says the configured tag was not found, and every other part of the view still works

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no tag and no tag identifier, and both are discovered at run time

## MODIFIED Requirements

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, tagged green before untagged, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally the order a person has set by hand. Where two tasks share even that, they SHALL be ordered by title. Priority SHALL NOT influence the order.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and the same manual order, and carry different priorities
- **THEN** they are ordered by title, so the sequence is never arbitrary between them, and their priorities are not consulted

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

#### Scenario: Past-due tasks lead today's own

- **WHEN** today's view holds both past-due tasks and tasks due today, and they are equally tagged
- **THEN** every past-due task is listed above every task due today

#### Scenario: A tagged task due today leads an untagged one past due

- **WHEN** today's view holds a tagged task due today and an untagged task past due
- **THEN** the tagged task is listed first, because the tag ranks above how overdue a task is

### Requirement: Past-due tasks are ordered by how overdue they are

Past-due tasks SHALL be ordered by how overdue they are, the most overdue first, whatever manual order they carry. Where some of them are tagged green, they SHALL form two runs — the tagged ones and the rest — each ordered by how overdue its tasks are, since the tag ranks above lateness. Where they sit relative to the tasks due today is decided by the day's ordering keys, not here.

#### Scenario: The most overdue comes first

- **WHEN** today's view holds several past-due tasks, none of them tagged
- **THEN** they are ordered with the longest overdue at the top, whatever manual order they carry

#### Scenario: Tagged and untagged past-due tasks form two runs

- **WHEN** today's view holds past-due tasks of which some are tagged
- **THEN** the tagged ones are listed first, ordered by how overdue they are, and the rest follow ordered the same way

### Requirement: Ordering in the dateless views

Within the inbox and the someday view the board SHALL order tasks by, in turn: tagged green before untagged, pinned before unpinned, and then title. Priority SHALL NOT influence the order.

#### Scenario: Undated tasks read alphabetically

- **WHEN** the inbox holds several unpinned tasks, none of them tagged
- **THEN** they are listed in title order

#### Scenario: Pinned tasks lead

- **WHEN** the inbox holds both pinned and unpinned tasks, equally tagged
- **THEN** every pinned task is listed above the unpinned ones

#### Scenario: Tagged tasks lead the pinned ones

- **WHEN** the inbox holds a tagged unpinned task and an untagged pinned task
- **THEN** the tagged one is listed first
