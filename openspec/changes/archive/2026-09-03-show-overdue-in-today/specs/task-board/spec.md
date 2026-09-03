## ADDED Requirements

### Requirement: Today shows what is past due

Today's view SHALL list, in addition to the tasks that start today, every unfinished task that is past due: one whose start is before today, or whose deadline has already passed. A task that qualifies under both rules SHALL appear once. Deferred tasks SHALL NOT be included, because the never view exists to set a task aside and returning it to today would defeat that. No limit SHALL be placed on how far back a past-due task may come from.

#### Scenario: A task left over from an earlier day

- **WHEN** an unfinished task's start is before today
- **THEN** it appears in today's view

#### Scenario: A task whose deadline has passed

- **WHEN** an unfinished task's deadline is in the past
- **THEN** it appears in today's view, whether its start is in the future, today, or absent

#### Scenario: A task past due by both rules appears once

- **WHEN** an unfinished task's start is before today and its deadline has also passed
- **THEN** it appears exactly once in today's view

#### Scenario: A finished task from an earlier day stays away

- **WHEN** a task from an earlier day has been completed or cancelled
- **THEN** it does not appear in today's view

#### Scenario: A deferred task is never past due

- **WHEN** a deferred task's deadline has passed
- **THEN** it appears in the never view and not in today's view

#### Scenario: Only today gathers what is past due

- **WHEN** any calendar day other than today is displayed, whether earlier or later
- **THEN** it shows only the tasks that start on that day, and no past-due tasks from elsewhere

#### Scenario: The dateless views are unaffected

- **WHEN** the inbox or the never view is displayed
- **THEN** its contents are exactly as they were before, with no past-due tasks added

### Requirement: How overdue a task is

For a past-due task the board SHALL report how long it has been past due, measured from the earliest of its passed start and its passed deadline — the moment it first became late.

#### Scenario: Measured from the start it missed

- **WHEN** a task's start was three days ago and it carries no deadline
- **THEN** the board reports it as three days past due

#### Scenario: Measured from whichever came first

- **WHEN** a task's deadline passed before its start did
- **THEN** the board measures from the deadline, as the earlier of the two

## MODIFIED Requirements

### Requirement: Task row presentation

Each task in the shown day SHALL be presented as a row carrying its completion mark, its start time, its title, and its project name. A past-due task SHALL instead show how overdue it is in place of its start time, and SHALL have its title rendered in a colour that sets it apart from the tasks due today. Title emphasis SHALL otherwise convey completion state only. The board SHALL NOT vary a title's weight, dimming, or colour according to the task's priority.

#### Scenario: An open task is shown plainly

- **WHEN** the day contains an open task
- **THEN** its title is rendered without emphasis, regardless of the priority stored on that task

#### Scenario: A finished task is struck through

- **WHEN** a task in the day is completed or cancelled
- **THEN** its title is rendered struck through and dimmed

#### Scenario: Two tasks differing only in priority look identical

- **WHEN** the day contains two open tasks whose stored priorities differ
- **THEN** neither row is emphasised relative to the other

#### Scenario: A past-due row is set apart

- **WHEN** today's view holds both a past-due task and a task due today
- **THEN** the past-due row shows how overdue it is where the other shows a time, and its title is coloured while the other's is not

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally title. Past-due tasks SHALL be ordered among themselves by how overdue they are, the most overdue first. Priority SHALL NOT influence the order.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and carry different priorities
- **THEN** they are ordered by title

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

#### Scenario: Past-due tasks lead today's own

- **WHEN** today's view holds both past-due tasks and tasks due today
- **THEN** every past-due task is listed above every task due today

#### Scenario: The most overdue comes first

- **WHEN** today's view holds several past-due tasks
- **THEN** they are ordered with the longest overdue at the top

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the never view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds. When the inbox is shown and undated filed tasks have been left out of it, the board SHALL also report how many, so that excluding them does not hide their existence. When today is shown and it has gathered past-due tasks, the board SHALL report how many are past due separately from how many are due today.

#### Scenario: Showing the inbox

- **WHEN** the inbox is displayed
- **THEN** the board names it as the inbox and reports how many tasks it holds

#### Scenario: Showing a calendar day

- **WHEN** a calendar day is displayed
- **THEN** the board names that day and how it relates to today, as it did before

#### Scenario: Reporting what the inbox leaves out

- **WHEN** the inbox is displayed and some unfinished undated undeferred tasks have a project
- **THEN** the board reports how many such tasks were left out, alongside the count of those shown

#### Scenario: Nothing to report

- **WHEN** the inbox is displayed and no unfinished undated undeferred task has a project
- **THEN** the board reports no left-out count

#### Scenario: Reporting what is past due

- **WHEN** today is displayed and past-due tasks have been gathered into it
- **THEN** the board reports how many are past due as well as how many are due today

#### Scenario: Nothing is past due

- **WHEN** today is displayed and no task is past due
- **THEN** the board reports no past-due count
