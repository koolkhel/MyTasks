## ADDED Requirements

### Requirement: The day shows what the calendar holds for it

The board SHALL show, alongside the tasks for the day being viewed, the events
the machine's calendar holds for that same day. Moving to another day SHALL
show that day's events instead: unlike the tracker's issues, which are what is
being worked on now whatever day is shown, an event belongs to a date.

An event SHALL be shown with the time it starts and what it is called, so that
it can be recognised without opening anything. A row SHALL be distinguishable
from a task at a glance, without relying on colour.

Events that repeat SHALL appear on every day they fall on, not only on the day
the repetition was first set. Most of a calendar is repetition, and one that
showed only the first occurrence would be worse than none.

#### Scenario: Today's events appear with today's tasks

- **WHEN** today is shown and the calendar holds events for today
- **THEN** each appears as a row, showing when it starts and what it is called

#### Scenario: Another day shows that day's events

- **WHEN** a person moves to another day
- **THEN** the events shown are that day's, and the previous day's are gone

#### Scenario: A repeating event appears on every day it falls on

- **WHEN** an event repeats and the day being viewed is one it falls on, but not the day it began
- **THEN** it still appears on that day

#### Scenario: A day with no events

- **WHEN** the calendar holds nothing for the day being viewed
- **THEN** the day shows its tasks alone, and nothing announces the absence

#### Scenario: An event is distinguishable from a task

- **WHEN** a day holds both events and tasks
- **THEN** an event's row is marked apart from a task's, and colour is not what distinguishes them

### Requirement: Events fall in the day in the order they happen

An event SHALL be ordered among the day's rows by when it starts, so that the
day reads in the order it will be lived. An event at nine and a task at eleven
SHALL appear in that order.

An event lasting the whole day SHALL be placed above the rows that happen at a
time, because it describes the day rather than a moment within it.

An event SHALL NOT be subject to the rules that order tasks against one
another: it is neither finished nor unfinished, neither past due nor due, is
never tagged, and carries no hand-set order. Those rules SHALL continue to
order the tasks exactly as they did.

#### Scenario: An event and a task read in the order they happen

- **WHEN** a day holds an event starting before a timed task
- **THEN** the event is listed above it, and a later event below it

#### Scenario: An all-day event leads the day

- **WHEN** a day holds an all-day event and rows that happen at a time
- **THEN** the all-day event is above them

#### Scenario: The tasks keep their own order

- **WHEN** events are shown among a day's tasks
- **THEN** the tasks are ordered among themselves exactly as they would be without the events

### Requirement: An event cannot be changed from the board

No key that writes SHALL act on an event: it can be neither completed,
uncompleted, cancelled, renamed, rescheduled, filed, tagged, reordered nor
deleted. The board reads the calendar and does not own it, and a change shown
here that the calendar never made would be worse than no change at all.

Where a person presses such a key on an event, the board SHALL say why nothing
happened rather than doing nothing silently.

#### Scenario: A key that writes is refused

- **WHEN** a person presses any key that would change a task, with an event selected
- **THEN** nothing is written, and the board says the event belongs to the calendar

#### Scenario: An event is not counted among the tasks

- **WHEN** the board reports how many tasks a day holds
- **THEN** events are not counted among them

#### Scenario: Moving does not reach an event

- **WHEN** a person tries to reorder with an event selected
- **THEN** nothing moves, and the board says why

### Requirement: Work events are hidden with the rest of the work

An event from the account whose events count as work SHALL be treated as work,
so that the key which hides work hides it too, and the count of what was
hidden includes it. An event from any other configured account SHALL NOT be
hidden by that key.

#### Scenario: Hiding work hides the work account's events

- **WHEN** work is hidden and the day holds events from the work account
- **THEN** they disappear along with the work tasks, and pressing the key again brings them back

#### Scenario: Personal events are not hidden

- **WHEN** work is hidden and the day holds events from an account that is not work
- **THEN** those events stay

#### Scenario: The hidden count includes them

- **WHEN** work is hidden and the board reports how many rows that removed
- **THEN** the work events it removed are included in that count

### Requirement: Which calendar accounts are read is configured, not built in

The accounts whose events are shown SHALL be named in the environment, and
which of them counts as work SHALL be named there too. No account name, and
no calendar name, SHALL appear in the board's source.

Only the named accounts SHALL be read. A machine's calendar holds a great deal
that has nothing to do with a working day, and showing all of it would bury
what matters.

Where no account is configured, the board SHALL show no events and SHALL NOT
report a failure: a board with no calendar configured is an ordinary board.

Where a configured account does not exist, the board SHALL say so rather than
showing an empty day that looks like a free one.

#### Scenario: Only the named accounts are shown

- **WHEN** accounts are configured and the machine holds others besides
- **THEN** only events from the named accounts appear

#### Scenario: No calendar is configured

- **WHEN** no account is configured
- **THEN** no event is shown, and the board reports no failure

#### Scenario: A configured account is missing

- **WHEN** a configured account names nothing on the machine
- **THEN** the board says that account was not found

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no account and no calendar, and both are discovered at run time

### Requirement: The board works when the calendar cannot be read

Reading the calendar needs a permission granted outside the board, which may
be refused, withdrawn, or granted only in part. In any of those cases the
board SHALL show the day's tasks as it always does and SHALL say once that the
calendar could not be read, naming what would put it right.

A permission granted only in part SHALL be treated as no permission rather
than as success: it reads as though it worked while returning nothing, and a
day wrongly showing no events looks exactly like a free one.

The calendar SHALL NOT delay the day. The tasks SHALL appear without waiting
for it, and a calendar that is slow or unavailable SHALL NOT keep them off the
screen.

#### Scenario: Permission is refused

- **WHEN** the board cannot read the calendar because permission was not granted
- **THEN** the day's tasks appear as usual and the board says the calendar could not be read

#### Scenario: Permission granted only in part

- **WHEN** permission allows adding to the calendar but not reading it
- **THEN** the board treats that as unreadable and says so, rather than showing a day with no events

#### Scenario: The day does not wait

- **WHEN** the calendar is slow to answer
- **THEN** the day's tasks are already on screen, and the events join when they arrive

#### Scenario: Recovering without a restart

- **WHEN** the calendar becomes readable again and the view is refreshed
- **THEN** the events appear and the message about not reading it is gone

## MODIFIED Requirements

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, tagged green before untagged, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally the order a person has set by hand. Where two tasks share even that, they SHALL be ordered by title. Priority SHALL NOT influence the order.

These rules order the tasks. A day may also hold rows that are not tasks — the calendar's events — which take their place among them by when they happen, and are not subject to these rules. Removing every such row from a day SHALL leave the tasks in exactly the order stated here.

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

#### Scenario: The tasks' order survives the events

- **WHEN** a day holds both events and tasks
- **THEN** disregarding the events leaves the tasks in the same order they would have had alone
