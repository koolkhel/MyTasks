## MODIFIED Requirements

### Requirement: Inbox view

The board SHALL offer an inbox view listing every unfinished task that has no date, is not deferred, and has no project. A task that has been given a project has already been sorted, so it does not belong in the queue awaiting triage. Finished tasks SHALL be excluded from it, because the store holds far more finished undated tasks than open ones and including them would bury the tasks awaiting triage.

#### Scenario: Reaching the inbox

- **WHEN** a person asks for the inbox
- **THEN** the board lists the unfinished tasks that have no date, are not deferred, and have no project, and nothing else

#### Scenario: A dated task is not in the inbox

- **WHEN** a task carries any date
- **THEN** it does not appear in the inbox

#### Scenario: A deferred task is not in the inbox

- **WHEN** an undated task is marked deferred
- **THEN** it appears in the never view and not in the inbox

#### Scenario: Finished undated tasks stay out

- **WHEN** an undated task has been completed or cancelled
- **THEN** it does not appear in the inbox

#### Scenario: A filed task is not in the inbox

- **WHEN** an undated, undeferred task has a project
- **THEN** it does not appear in the inbox

### Requirement: Never view

The board SHALL offer a never view listing every unfinished task that has no date and is deferred, reachable directly rather than by walking the calendar. Finished tasks SHALL be excluded, for the same reason as the inbox. Unlike the inbox, this view SHALL NOT exclude tasks that have a project: a task set aside deliberately stays visible whether or not it has been filed.

#### Scenario: Reaching never

- **WHEN** a person asks for the never view
- **THEN** the board lists the unfinished undated tasks that are deferred, and nothing else

#### Scenario: Never is not a position on the calendar

- **WHEN** a person moves between calendar days
- **THEN** they never arrive at the never view by doing so

#### Scenario: A filed task still appears in never

- **WHEN** an undated deferred task has a project
- **THEN** it appears in the never view, even though the same task without the deferred flag would be absent from the inbox

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the never view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds. When the inbox is shown and undated filed tasks have been left out of it, the board SHALL also report how many, so that excluding them does not hide their existence.

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

### Requirement: Adding a task follows the shown view

A task added while the inbox is shown SHALL be created with no date, not deferred, and with no project, so that it appears in the inbox it was added from; one added while the never view is shown SHALL be created deferred with no date; one added while a calendar day is shown SHALL be created on that day.

#### Scenario: Adding to the inbox

- **WHEN** a person adds a task while the inbox is shown
- **THEN** the new task has no date, is not deferred, has no project, and appears in the inbox

#### Scenario: Adding to never

- **WHEN** a person adds a task while the never view is shown
- **THEN** the new task is deferred, has no date, and appears in the never view
