## ADDED Requirements

### Requirement: Marking a task done for today

The board SHALL let a person mark the selected task as done for today, meaning work happened on it today and it should come up again tomorrow. This SHALL record the day's work against the task wherever the API accepts such a record, and SHALL then schedule the task for tomorrow. It SHALL NOT mark the task finished: a task done for today is still an open task.

The record SHALL be attempted before the task is rescheduled, because the API accepts it only for a task whose start is not in the future and moving the date forward would make the record impossible. Where the API refuses the record — a task with no date, or one already dated far enough ahead — the task SHALL still be scheduled for tomorrow, and the refusal SHALL NOT be reported as a failure.

#### Scenario: A task being worked on today

- **WHEN** a person marks a task dated today as done for today
- **THEN** the day's work is recorded against the task, the task is scheduled for tomorrow, and it remains unfinished

#### Scenario: A task carried over from an earlier day

- **WHEN** a person marks a past-due task as done for today
- **THEN** the day's work is recorded against it as well, the task is scheduled for tomorrow, and it remains unfinished

#### Scenario: It does not finish the task

- **WHEN** a person marks any task as done for today
- **THEN** the task is not completed, not cancelled, and still appears as open on the day it was moved to

#### Scenario: Available from the dateless views

- **WHEN** a person marks an undated task in the inbox or in the someday view as done for today
- **THEN** the task is scheduled for tomorrow and is no longer deferred, leaving the bucket it was in

#### Scenario: Distinct from finishing a task

- **WHEN** a person finishes a task
- **THEN** an action other than the one that marks it done for today does it, and neither key performs the other's work

## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment and done for today included
