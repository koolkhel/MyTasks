## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, cancel it, rename it, assign or clear its date, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** only the shown day's occurrence is completed and the series continues

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the never view
- **THEN** the same actions offered in a day view are offered there, date assignment included

## ADDED Requirements

### Requirement: Inbox view

The board SHALL offer an inbox view listing every unfinished task that has no date and is not deferred. Finished tasks SHALL be excluded from it, because the store holds far more finished undated tasks than open ones and including them would bury the tasks awaiting triage.

#### Scenario: Reaching the inbox

- **WHEN** a person asks for the inbox
- **THEN** the board lists the unfinished tasks that have no date and are not deferred, and nothing else

#### Scenario: A dated task is not in the inbox

- **WHEN** a task carries any date
- **THEN** it does not appear in the inbox

#### Scenario: A deferred task is not in the inbox

- **WHEN** an undated task is marked deferred
- **THEN** it appears in the never view and not in the inbox

#### Scenario: Finished undated tasks stay out

- **WHEN** an undated task has been completed or cancelled
- **THEN** it does not appear in the inbox

### Requirement: Never view

The board SHALL offer a never view listing every unfinished task that has no date and is deferred, reachable directly rather than by walking the calendar. Finished tasks SHALL be excluded, for the same reason as the inbox.

#### Scenario: Reaching never

- **WHEN** a person asks for the never view
- **THEN** the board lists the unfinished undated tasks that are deferred, and nothing else

#### Scenario: Never is not a position on the calendar

- **WHEN** a person moves between calendar days
- **THEN** they never arrive at the never view by doing so

### Requirement: Assigning a date to a task

The board SHALL let a person give the selected task a date of today, tomorrow, or a day they name, or send it to never, or clear its date. Naming a day SHALL accept a `YYYY-MM-DD` value and SHALL reject anything else without changing the task.

#### Scenario: Dating a task from the inbox

- **WHEN** a person assigns today's date to a task selected in the inbox
- **THEN** the task is given that date and no longer appears in the inbox

#### Scenario: Dating a task from a day view

- **WHEN** a person assigns a different day to a task selected in a day view
- **THEN** the task is given that day and no longer appears under the day it was moved from

#### Scenario: Sending a task to never

- **WHEN** a person sends the selected task to never
- **THEN** the task appears in the never view and in neither the inbox nor any day

#### Scenario: Clearing a date returns a task to the inbox

- **WHEN** a person clears the date of a dated task
- **THEN** the task appears in the inbox

#### Scenario: A malformed date is refused

- **WHEN** a person names a day that is not a valid `YYYY-MM-DD` date
- **THEN** the board reports the problem and the task's date is unchanged

#### Scenario: Cancelling the picker changes nothing

- **WHEN** a person opens date assignment and then abandons it
- **THEN** the task's date and deferred flag are both unchanged

### Requirement: A task is either dated or deferred, never both

Assigning a real date SHALL clear the task's deferred flag, and sending a task to never SHALL clear its date. The board SHALL NOT leave a task both dated and deferred, a state the underlying API permits but no view of the board would show consistently.

#### Scenario: Dating a task that was set to never

- **WHEN** a person assigns a date to a task currently in the never view
- **THEN** the task carries that date and is no longer deferred

#### Scenario: Never-ing a task that had a date

- **WHEN** a person sends a dated task to never
- **THEN** the task is deferred and carries no date

### Requirement: Ordering in the dateless views

Within the inbox and the never view the board SHALL order tasks by, in turn: pinned before unpinned, and then title. Priority SHALL NOT influence the order.

#### Scenario: Undated tasks read alphabetically

- **WHEN** the inbox holds several unpinned tasks
- **THEN** they are listed in title order

#### Scenario: Pinned tasks lead

- **WHEN** the inbox holds both pinned and unpinned tasks
- **THEN** every pinned task is listed above the unpinned ones

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the never view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds.

#### Scenario: Showing the inbox

- **WHEN** the inbox is displayed
- **THEN** the board names it as the inbox and reports how many tasks it holds

#### Scenario: Showing a calendar day

- **WHEN** a calendar day is displayed
- **THEN** the board names that day and how it relates to today, as it did before

### Requirement: Adding a task follows the shown view

A task added while the inbox is shown SHALL be created with no date and not deferred; one added while the never view is shown SHALL be created deferred with no date; one added while a calendar day is shown SHALL be created on that day.

#### Scenario: Adding to the inbox

- **WHEN** a person adds a task while the inbox is shown
- **THEN** the new task has no date, is not deferred, and appears in the inbox

#### Scenario: Adding to never

- **WHEN** a person adds a task while the never view is shown
- **THEN** the new task is deferred, has no date, and appears in the never view

### Requirement: Day navigation applies only to calendar days

Moving to the previous or next day SHALL apply only while a calendar day is shown. While the inbox or the never view is shown those movements SHALL do nothing, and returning to today SHALL bring back the day view.

#### Scenario: Day movement is inert in a dateless view

- **WHEN** a person asks for the previous or next day while the inbox is shown
- **THEN** the inbox stays displayed

#### Scenario: Returning to today from the inbox

- **WHEN** a person asks for today while the inbox is shown
- **THEN** the board shows today's calendar day
