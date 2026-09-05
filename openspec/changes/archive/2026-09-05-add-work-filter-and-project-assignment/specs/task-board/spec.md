## ADDED Requirements

### Requirement: Hiding the work tasks

The board SHALL offer a key that hides every task belonging to the work
project, and the same key SHALL bring them back. There SHALL be two states
and no third.

The mode SHALL apply to every view the board shows, so that moving between
days does not change what the mode means. It SHALL last as long as the board
is open and no longer.

Hiding SHALL remove rows from the view without changing any task: no write
SHALL be made, and nothing SHALL be altered about a task because it was
hidden or shown.

#### Scenario: Hiding and showing again

- **WHEN** a person presses the key with work tasks in the shown view
- **THEN** those tasks disappear from it, and pressing the key again brings them back exactly as they were

#### Scenario: The mode follows the person between views

- **WHEN** a person hides the work tasks and then moves to another day or to the someday view
- **THEN** the work tasks are hidden there too, without the key being pressed again

#### Scenario: Nothing is written

- **WHEN** a person hides or shows the work tasks
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: A view with no work tasks

- **WHEN** a person hides the work tasks in a view that holds none
- **THEN** the view is unchanged and the board still shows that the mode is on

#### Scenario: The inbox is unaffected

- **WHEN** the mode is on and the inbox is displayed
- **THEN** its contents are exactly what they would be with the mode off, because a task with a project is already outside the inbox

#### Scenario: The mode does not outlive the board

- **WHEN** a person hides the work tasks, closes the board, and opens it again
- **THEN** every task is shown

### Requirement: The board says when it is hiding work

When work tasks are being hidden, the board SHALL say so where it already
reports what the shown view holds, and SHALL report how many rows the mode
removed. A view that is quietly shorter than expected SHALL NOT be
indistinguishable from a day with less on it.

Where the mode is off, the board SHALL say nothing about it.

#### Scenario: The mode is on and hides something

- **WHEN** the mode is on and the shown view holds work tasks
- **THEN** the board reports that work is hidden and how many rows that removed, alongside the counts it already reports

#### Scenario: The mode is on and hides nothing

- **WHEN** the mode is on and the shown view holds no work task
- **THEN** the board still reports that work is hidden, so that the mode is never invisible

#### Scenario: The mode is off

- **WHEN** the mode is off
- **THEN** the board reports nothing about hidden work

#### Scenario: The counts still add up

- **WHEN** the mode is on and the board reports how many tasks the view holds
- **THEN** that count is the number of rows shown, and the hidden count is reported separately, as the inbox already does for the tasks it withholds

### Requirement: Which project counts as work is configured, not built in

The board SHALL take the identity of the work project from its environment
rather than carrying it in its own source, so that a personal project
identifier need never enter the repository.

Where no work project is configured, the board SHALL say so when the key is
pressed, and SHALL NOT silently hide nothing. A missing setting SHALL be
distinguishable from a key that does not work.

Where a work project is configured but matches none that exist, the board
SHALL say that too. A setting left behind by a renamed or deleted project
otherwise looks exactly like a day with no work on it.

#### Scenario: Configured

- **WHEN** a work project is configured and a person presses the key
- **THEN** the tasks in that project are hidden

#### Scenario: Not configured

- **WHEN** no work project is configured and a person presses the key
- **THEN** the board reports that no work project is set, and no rows are hidden

#### Scenario: Configured with a project that no longer exists

- **WHEN** a work project is configured but no project with that identity exists
- **THEN** the board reports that the configured work project was not found, rather than hiding nothing and appearing to work

#### Scenario: The identifier is not in the source

- **WHEN** the board's source is read
- **THEN** it names no particular project, and the work project is discovered only at run time

### Requirement: Assigning a task to a project

The board SHALL let a person put the selected task in a project, choosing
from the projects that exist and showing which project the task is in now.

Assigning a project to a task that has none SHALL be confirmed first. The API
accepts only a project identifier and refuses both an empty value and no
value, so nothing the board can send will return a task to having no project:
the first filing cannot be undone from the board and SHALL be treated like
deleting, which is the only other action of that kind.

Moving a task that already has a project SHALL NOT be confirmed, because it
gives up nothing that it still has.

The board SHALL NOT offer to remove a task from a project, since it cannot.

#### Scenario: Filing a task that has no project

- **WHEN** a person assigns a project to a task that has none
- **THEN** the board asks first, and the task is filed only if the person agrees

#### Scenario: Declining the confirmation

- **WHEN** a person is asked to confirm a first filing and declines
- **THEN** the task keeps having no project, and nothing is sent

#### Scenario: Moving a task between projects

- **WHEN** a person assigns a project to a task that already has one
- **THEN** the task moves without being asked to confirm

#### Scenario: The picker says where the task is now

- **WHEN** a person opens the project picker on a task
- **THEN** the project the task is in is shown as such, or it is shown as having none

#### Scenario: No way to un-file

- **WHEN** a person looks for a way to remove a task from its project
- **THEN** the board offers none, because the API provides none

#### Scenario: Filing from the inbox

- **WHEN** a person files a task selected in the inbox
- **THEN** it leaves the inbox at once, because the inbox holds only tasks with no project

#### Scenario: A filed task can be hidden

- **WHEN** a person files a task under the work project while work is hidden
- **THEN** the task disappears from the view, because it is now work and work is hidden

## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, project assignment, done for today and opening a link included

#### Scenario: Reordering is the one action a day alone offers

- **WHEN** a task is selected in the inbox or the someday view and a person tries to move it up or down
- **THEN** the board reports that reordering applies to calendar days, which is the single exception to every action being available everywhere

#### Scenario: Moving a task and moving the cursor are different keys

- **WHEN** a person presses the key that moves the cursor up or down
- **THEN** no task's stored order changes, and the key that moves the task is a different one

#### Scenario: Assigning a project and hiding work are different keys

- **WHEN** a person presses the key that hides the work tasks
- **THEN** no task is assigned to a project, and the key that assigns one is a different one

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the someday view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds. When the inbox is shown and undated filed tasks have been left out of it, the board SHALL also report how many, so that excluding them does not hide their existence. When today is shown and it has gathered past-due tasks, the board SHALL report how many are past due separately from how many are due today. When work tasks are being hidden, the board SHALL report that too, alongside whatever else it is reporting about the view.

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

#### Scenario: Reporting hidden work beside the other counts

- **WHEN** today is displayed with past-due tasks gathered into it and work is being hidden
- **THEN** the board reports the past-due count and the hidden-work count together, and neither replaces the other
