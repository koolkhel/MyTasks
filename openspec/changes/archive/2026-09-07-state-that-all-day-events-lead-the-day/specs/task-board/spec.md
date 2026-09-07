## MODIFIED Requirements

### Requirement: Events fall in the day in the order they happen

An event SHALL be ordered among the day's rows by when it starts, so that the
day reads in the order it will be lived. An event at nine and a task at eleven
SHALL appear in that order, and this SHALL hold whatever else the day holds.

An event lasting the whole day SHALL lead the day, above every other row it
holds -- above the past-due tasks, above the day's own tasks that name no
time, and above the tracker block. It describes the whole day rather than a
moment within it, so nothing that happens inside the day outranks it. Where a
day holds more than one, they SHALL keep a stable order among themselves.

An event SHALL be placed by the same ordering the tasks are placed by, standing
in it as what an event is: not finished, not tagged, not past due, not pinned,
and happening at its own hour. So a past-due task SHALL be listed above an
event, a finished task SHALL be listed below one, and an event SHALL fall
beside the tasks that share its hour.

An event SHALL NOT acquire the properties that ordering reads. It is never
finished, never tagged, never past due, never pinned, and carries no hand-set
order; it is placed relative to rows that have those properties without
gaining any of them.

The tasks SHALL continue to be ordered among themselves exactly as they are
without any event present. Removing every event from a day SHALL leave the
tasks in precisely the order the rules for tasks give them.

#### Scenario: An event and a task read in the order they happen

- **WHEN** a day holds an event starting before a timed task
- **THEN** the event is listed above it, and a later event below it

#### Scenario: A past-due task is not pushed below an event

- **WHEN** a day holds a past-due task that names no time, and an event later in the day
- **THEN** the past-due task is listed above the event, and the event is not lifted to the top of the day

#### Scenario: An event falls beside the task sharing its hour

- **WHEN** a day holds a task and an event that start at the same time, and also holds a past-due task and a task earlier in the day
- **THEN** the event and the task sharing its hour are adjacent, below the past-due task and below the earlier one

#### Scenario: A finished task stays below an event

- **WHEN** a day holds a completed task whose time is earlier than an event's
- **THEN** the completed task is listed below the event, because finishing sinks a row whatever hour it names

#### Scenario: An all-day event leads the day

- **WHEN** a day holds an all-day event and rows that happen at a time
- **THEN** the all-day event is above them

#### Scenario: An all-day event leads the past-due tasks too

- **WHEN** a day holds an all-day event and tasks that are past due
- **THEN** the all-day event is above every one of them

#### Scenario: An all-day event leads the day's own untimed tasks

- **WHEN** a day holds an all-day event and the day's own tasks that name no time
- **THEN** the all-day event is above them, and they are not mixed together

#### Scenario: An all-day event leads the tracker block

- **WHEN** today holds an all-day event and the tracker reports issues
- **THEN** the all-day event is above the block

#### Scenario: More than one all-day event

- **WHEN** a day holds several all-day events
- **THEN** all of them lead the day, in a stable order among themselves

#### Scenario: The tasks keep their own order

- **WHEN** events are shown among a day's tasks
- **THEN** the tasks are ordered among themselves exactly as they would be without the events

#### Scenario: The tasks keep their order on a crowded day

- **WHEN** a day holds events together with past-due, tagged, pinned, timed, untimed and finished tasks
- **THEN** disregarding the events leaves those tasks in exactly the order they would have had alone
