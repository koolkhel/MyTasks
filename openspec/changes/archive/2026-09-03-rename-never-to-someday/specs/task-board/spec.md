## REMOVED Requirements

### Requirement: Never view

**Reason**: The board's "never" mislabelled the API's `deferred` flag, which SingularityApp itself presents as "Someday". Replaced by `Someday view`, which carries the same rules under the name the app uses.
**Migration**: None. A someday task is `start=None, deferred=true`, exactly as a never task was, so no stored task changes and nothing needs rewriting.

## ADDED Requirements

### Requirement: Someday view

The board SHALL offer a someday view listing every unfinished task that has no date and is deferred, reachable directly rather than by walking the calendar. Finished tasks SHALL be excluded, for the same reason as the inbox. Unlike the inbox, this view SHALL NOT exclude tasks that have a project: a task set aside deliberately stays visible whether or not it has been filed.

#### Scenario: Reaching someday

- **WHEN** a person asks for the someday view
- **THEN** the board lists the unfinished undated tasks that are deferred, and nothing else

#### Scenario: Someday is not a position on the calendar

- **WHEN** a person moves between calendar days
- **THEN** they never arrive at the someday view by doing so

#### Scenario: A filed task still appears in someday

- **WHEN** an undated deferred task has a project
- **THEN** it appears in the someday view, even though the same task without the deferred flag would be absent from the inbox

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

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment included

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
- **THEN** it appears in the someday view and not in the inbox

#### Scenario: Finished undated tasks stay out

- **WHEN** an undated task has been completed or cancelled
- **THEN** it does not appear in the inbox

#### Scenario: A filed task is not in the inbox

- **WHEN** an undated, undeferred task has a project
- **THEN** it does not appear in the inbox

### Requirement: Assigning a date to a task

The board SHALL let a person give the selected task a date of today, tomorrow, or a day they name, or send it to someday, or clear its date. Naming a day SHALL accept a `YYYY-MM-DD` value and SHALL reject anything else without changing the task.

#### Scenario: Dating a task from the inbox

- **WHEN** a person assigns today's date to a task selected in the inbox
- **THEN** the task is given that date and no longer appears in the inbox

#### Scenario: Dating a task from a day view

- **WHEN** a person assigns a different day to a task selected in a day view
- **THEN** the task is given that day and no longer appears under the day it was moved from

#### Scenario: Sending a task to never

- **WHEN** a person sends the selected task to someday
- **THEN** the task appears in the someday view and in neither the inbox nor any day

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

Assigning a real date SHALL clear the task's deferred flag, and sending a task to someday SHALL clear its date. The board SHALL NOT leave a task both dated and deferred, a state the underlying API permits but no view of the board would show consistently.

#### Scenario: Dating a task that was set to never

- **WHEN** a person assigns a date to a task currently in the someday view
- **THEN** the task carries that date and is no longer deferred

#### Scenario: Never-ing a task that had a date

- **WHEN** a person sends a dated task to someday
- **THEN** the task is deferred and carries no date

### Requirement: Ordering in the dateless views

Within the inbox and the someday view the board SHALL order tasks by, in turn: pinned before unpinned, and then title. Priority SHALL NOT influence the order.

#### Scenario: Undated tasks read alphabetically

- **WHEN** the inbox holds several unpinned tasks
- **THEN** they are listed in title order

#### Scenario: Pinned tasks lead

- **WHEN** the inbox holds both pinned and unpinned tasks
- **THEN** every pinned task is listed above the unpinned ones

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the someday view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds. When the inbox is shown and undated filed tasks have been left out of it, the board SHALL also report how many, so that excluding them does not hide their existence. When today is shown and it has gathered past-due tasks, the board SHALL report how many are past due separately from how many are due today.

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

### Requirement: Adding a task follows the shown view

A task added while the inbox is shown SHALL be created with no date, not deferred, and with no project, so that it appears in the inbox it was added from; one added while the someday view is shown SHALL be created deferred with no date; one added while a calendar day is shown SHALL be created on that day.

#### Scenario: Adding to the inbox

- **WHEN** a person adds a task while the inbox is shown
- **THEN** the new task has no date, is not deferred, has no project, and appears in the inbox

#### Scenario: Adding to never

- **WHEN** a person adds a task while the someday view is shown
- **THEN** the new task is deferred, has no date, and appears in the someday view

### Requirement: Day navigation applies only to calendar days

Moving to the previous or next day SHALL apply only while a calendar day is shown. While the inbox or the someday view is shown those movements SHALL do nothing, and returning to today SHALL bring back the day view.

#### Scenario: Day movement is inert in a dateless view

- **WHEN** a person asks for the previous or next day while the inbox is shown
- **THEN** the inbox stays displayed

#### Scenario: Returning to today from the inbox

- **WHEN** a person asks for today while the inbox is shown
- **THEN** the board shows today's calendar day

### Requirement: Focus view of the selected task

The board SHALL offer a focus view of the selected task, showing its title in full without truncation, when it is due, its project when it has one, its deadline when it has one, and its note when it has one. The view SHALL be dismissable, and dismissing it SHALL return to the same view and the same selected task.

#### Scenario: Opening the focus view

- **WHEN** a person opens the focus view on a selected task
- **THEN** the task's whole title is shown, along with when it is due and its project

#### Scenario: A long title is not cut off

- **WHEN** the selected task's title is longer than the width the task list gives it
- **THEN** the focus view shows the title in full, unlike the row it was opened from

#### Scenario: A task with a note and a deadline

- **WHEN** the selected task has a note and a deadline
- **THEN** the focus view shows both

#### Scenario: A task with nothing optional set

- **WHEN** the selected task has no project, no deadline, and no note
- **THEN** the focus view shows its title and when it is due, and omits the parts it has nothing to show for

#### Scenario: Dismissing returns to the board

- **WHEN** a person dismisses the focus view
- **THEN** the board is shown again, in the same view, with the same task still selected

#### Scenario: Available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the focus view can be opened on it just as from a day

#### Scenario: Nothing is selected

- **WHEN** a person asks for the focus view while the shown view holds no tasks
- **THEN** no focus view opens and the board is left as it was

### Requirement: Today shows what is past due

Today's view SHALL list, in addition to the tasks that start today, every unfinished task that is past due: one whose start is before today, or whose deadline has already passed. A task that qualifies under both rules SHALL appear once. Deferred tasks SHALL NOT be included, because the someday view exists to set a task aside and returning it to today would defeat that. No limit SHALL be placed on how far back a past-due task may come from.

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
- **THEN** it appears in the someday view and not in today's view

#### Scenario: Only today gathers what is past due

- **WHEN** any calendar day other than today is displayed, whether earlier or later
- **THEN** it shows only the tasks that start on that day, and no past-due tasks from elsewhere

#### Scenario: The dateless views are unaffected

- **WHEN** the inbox or the someday view is displayed
- **THEN** its contents are exactly as they were before, with no past-due tasks added
