## ADDED Requirements

### Requirement: Setting the order of a day's tasks by hand

The board SHALL let a person move the selected task up or down within a
calendar day, and SHALL store the resulting position on the task so that it
survives a reload and is the same order other SingularityApp clients show.

Moving SHALL change the stored order of the moved task alone, to a value
that places it on the far side of its neighbour and that no other task in
the day holds. No other task's stored order SHALL change, so that a move
is a single write and cannot be left half applied.

No two tasks in a day SHALL be left sharing a stored order. Where there is
no value available between the moved task's destination and the task beyond
it, the board SHALL first move that run of tasks into a range of values no
task in the day holds, so that the destination exists; such a renumbering
SHALL preserve the order of the tasks it renumbers, and SHALL leave every
stored order distinct even if only some of its writes are applied.

Moving SHALL only exchange the task with a neighbour the day's other ordering
keys allow it to trade with — one that is equally finished, equally past due,
equally pinned, and equally timed at the same start. Where the neighbour in
that direction is not such a task, or there is none, the board SHALL report
why the task cannot move there and SHALL leave every task's stored order
untouched.

Reordering SHALL be offered on calendar days only. In the inbox and the
someday view the board SHALL report that reordering applies to days rather
than silently doing nothing, because those views are not sequences of work
and are ordered by title.

#### Scenario: Moving a task up

- **WHEN** a person moves the selected task up, and the task above it is one the day's other ordering keys allow it to trade with
- **THEN** the two appear in the opposite sequence, every other task stays where it was, only the moved task's stored order changed, and the selection is still on the moved task

#### Scenario: The new position is remembered

- **WHEN** a person moves a task and then reloads the view, or leaves the day and comes back
- **THEN** the task is still in the position they moved it to

#### Scenario: Moving down

- **WHEN** a person moves the selected task down
- **THEN** it comes to sit after the task below it, under the same rules that govern moving up

#### Scenario: Already at the edge of its group

- **WHEN** a person moves the selected task towards an edge where there is no task it may trade with, whether because the day has none or because the adjacent one is ordered differently
- **THEN** the board reports why it cannot move there, and no task's stored order changes

#### Scenario: An all-day task cannot be lifted above a timed one

- **WHEN** the selected all-day task is the first of the all-day tasks and a timed task sits above it
- **THEN** moving up reports that it cannot pass the timed tasks, and the order is unchanged

#### Scenario: A failed move changes nothing

- **WHEN** the write that moves a task fails
- **THEN** no task's stored order has changed, because the move was a single write

#### Scenario: No room between the destination and the task beyond it

- **WHEN** a person moves a task to a place where the two tasks it must sit between hold adjacent values with nothing available in between
- **THEN** the move still happens, the tasks keep the sequence they were in apart from the one moved, and every stored order in the day is still distinct

#### Scenario: Not offered in the dateless views

- **WHEN** a person tries to move a task in the inbox or the someday view
- **THEN** the board reports that reordering applies to calendar days, and no task's stored order changes

#### Scenario: Sequencing a past-due task

- **WHEN** a person wants a past-due task in a particular place in today's sequence and dates it to today
- **THEN** it joins the tasks due today and can be moved among them

### Requirement: Where a newly added task lands in a day's order

A task added to a calendar day SHALL be placed after every task already in
that day's order, so that adding one does not disturb a sequence a person has
set.

The board SHALL choose the stored order it sends rather than leaving it to
the API's default. The default is the lowest value there is, which would put
each new task at the head of its group and tie it with every other task the
board has added.

#### Scenario: Adding to a day that already has tasks

- **WHEN** a person adds a task to a day whose tasks are in an order they set
- **THEN** the new task appears after the others and none of them moves

#### Scenario: Two tasks added one after another

- **WHEN** a person adds two tasks to the same day in succession
- **THEN** the second appears after the first, rather than the two being tied and ordered by title

#### Scenario: Adding to an empty day

- **WHEN** a person adds a task to a day that has none
- **THEN** the task is created with a stored order the board chose, ready to be moved once the day has others

## MODIFIED Requirements

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally the order a person has set by hand. Where two tasks share even that, they SHALL be ordered by title. Past-due tasks SHALL be ordered among themselves by how overdue they are, the most overdue first. Priority SHALL NOT influence the order.

The manual order SHALL be the last key and never override an earlier one: it decides the sequence among tasks the other keys leave equal, and cannot lift a task above a group it does not belong to. A day's timed tasks therefore stay in ascending start time however they are moved, and past-due tasks stay in most-overdue-first order.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and the same manual order, and carry different priorities
- **THEN** they are ordered by title, so the sequence is never arbitrary between them, and their priorities are not consulted

#### Scenario: The manual order is what decides between otherwise equal tasks

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot but carry different manual orders
- **THEN** they are ordered by the sequence a person has set, and the title is not consulted

#### Scenario: The manual order cannot override the time of day

- **WHEN** a day holds two timed tasks at different times, whatever manual order they carry
- **THEN** the earlier one is listed first

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

#### Scenario: Past-due tasks lead today's own

- **WHEN** today's view holds both past-due tasks and tasks due today
- **THEN** every past-due task is listed above every task due today

#### Scenario: The most overdue comes first

- **WHEN** today's view holds several past-due tasks
- **THEN** they are ordered with the longest overdue at the top, whatever manual order they carry

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, open its link, move it up or down within a calendar day, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, done for today and opening a link included

#### Scenario: Reordering is the one action a day alone offers

- **WHEN** a task is selected in the inbox or the someday view and a person tries to move it up or down
- **THEN** the board reports that reordering applies to calendar days, which is the single exception to every action being available everywhere

#### Scenario: Moving a task and moving the cursor are different keys

- **WHEN** a person presses the key that moves the cursor up or down
- **THEN** no task's stored order changes, and the key that moves the task is a different one
