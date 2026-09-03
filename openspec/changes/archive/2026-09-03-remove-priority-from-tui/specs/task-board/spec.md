## Purpose

The day-at-a-time terminal view of a person's tasks: it shows the tasks starting on one calendar day, lets them move between days, and lets them act on the selected task. It deliberately exposes a small subset of the upstream task model, leaving richer editing to the SingularityApp clients.

## ADDED Requirements

### Requirement: Task row presentation

Each task in the shown day SHALL be presented as a row carrying its completion mark, its start time, its title, and its project name. Title emphasis SHALL convey completion state only. The board SHALL NOT vary a title's weight, dimming, or colour according to the task's priority.

#### Scenario: An open task is shown plainly

- **WHEN** the day contains an open task
- **THEN** its title is rendered without emphasis, regardless of the priority stored on that task

#### Scenario: A finished task is struck through

- **WHEN** a task in the day is completed or cancelled
- **THEN** its title is rendered struck through and dimmed

#### Scenario: Two tasks differing only in priority look identical

- **WHEN** the day contains two open tasks whose stored priorities differ
- **THEN** neither row is emphasised relative to the other

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, pinned before unpinned, timed before all-day, earlier start time before later, and finally title. Priority SHALL NOT influence the order.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and carry different priorities
- **THEN** they are ordered by title

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

#### Scenario: A recurring task with a note

- **WHEN** the selected task recurs and carries a note
- **THEN** the detail area reports that it is recurring and shows the note text, with no mention of priority

#### Scenario: A plain task

- **WHEN** the selected task does not recur, is not pinned, and has neither deadline nor note
- **THEN** the detail area shows no priority line

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown day, tick and untick the selected task, cancel it, rename it, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** only the shown day's occurrence is completed and the series continues

### Requirement: Help lists the available keys

The board SHALL offer an in-app help overlay listing the keys it responds to. The overlay SHALL list only keys the board actually binds, and SHALL NOT advertise a priority action.

#### Scenario: Opening help

- **WHEN** a person opens the help overlay
- **THEN** it lists the movement, day-navigation, and task actions the board supports, with no priority entry

### Requirement: The board does not write priority

The board SHALL NOT send a priority value in any task it creates or updates, leaving each task's stored priority as whatever other SingularityApp clients set.

#### Scenario: Adding a task

- **WHEN** a person adds a task to the shown day
- **THEN** the created task carries the title and the day's start, and no priority is specified

#### Scenario: Renaming a task

- **WHEN** a person renames the selected task
- **THEN** only the title is submitted, and the task's stored priority is unchanged afterwards
