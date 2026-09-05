## ADDED Requirements

### Requirement: Today shows the issues currently in progress

Today's view SHALL additionally show the issues assigned to the configured
person that the issue tracker reports as in progress, in a block below every
task the board manages.

The block SHALL appear on today alone. An issue in progress is what is being
worked on now rather than something scheduled, and showing it under every
date would say it was.

Each row SHALL carry the issue's key and its summary, so that an issue can be
recognised and named without opening it.

#### Scenario: Issues in progress appear under today

- **WHEN** today is displayed and the tracker reports issues in progress for the configured person
- **THEN** each appears as a row below the day's own tasks, showing its key and its summary

#### Scenario: Only today

- **WHEN** any view other than today is displayed
- **THEN** no tracker issue appears in it

#### Scenario: Nothing in progress

- **WHEN** the tracker reports no issue in progress
- **THEN** today's view shows the day's own tasks and no tracker block

#### Scenario: The day's own tasks are unaffected

- **WHEN** tracker issues are shown
- **THEN** the day's own tasks are exactly those it would show without them, in the same order

### Requirement: The tracker block is fixed in place and not ordered

The tracker block SHALL sit after every task the board manages and SHALL NOT
take part in the day's ordering. Its rows SHALL NOT be interleaved with tasks,
SHALL NOT move when tasks are ticked or reordered, and SHALL keep a stable
sequence among themselves.

No key that reorders SHALL move a tracker row, and the board SHALL say why
rather than doing nothing.

#### Scenario: Below everything the board manages

- **WHEN** today holds past-due tasks, tasks due today, finished tasks and tracker issues
- **THEN** every tracker issue is listed after all of them

#### Scenario: Ticking a task does not disturb the block

- **WHEN** a task is ticked and the day reorders
- **THEN** the tracker rows stay where they were, after the tasks, in the same sequence

#### Scenario: Reordering does not reach it

- **WHEN** a person tries to move a tracker row up or down
- **THEN** the board says the issue lives in the tracker and cannot be reordered here, and nothing changes

### Requirement: A tracker issue cannot be changed from the board

No action that writes to a task SHALL act on a tracker issue. Where a person
presses a key that would change one, the board SHALL say the issue lives in
the tracker and is not editable here, and SHALL send nothing.

This SHALL hold for every such action the board offers, including any added
later: the refusal belongs where writes are made, not repeated in each action.

Because nothing is ever written for a tracker issue, there SHALL be nothing
to undo for one.

#### Scenario: Ticking an issue

- **WHEN** a person presses the tick key on a tracker row
- **THEN** the board says the issue is not editable here, nothing is sent, and the row is unchanged

#### Scenario: Every writing action refuses

- **WHEN** a person presses any key that would change a task, with a tracker row selected
- **THEN** each says the issue is not editable here and none sends anything

#### Scenario: Undo has nothing to reverse

- **WHEN** a person presses keys against a tracker row and then presses the undo key
- **THEN** nothing about the issue is reversed, because nothing was ever written

#### Scenario: The day's own tasks stay editable

- **WHEN** tracker issues are shown and a person acts on one of the day's own tasks
- **THEN** that action works exactly as it does without the tracker block

### Requirement: Opening a tracker issue

The board SHALL let a person open the selected tracker issue at its page in
the tracker, handing the address to the operating system, by the same key that
opens a task's link.

#### Scenario: Opening the selected issue

- **WHEN** a person presses the key that opens a link with a tracker row selected
- **THEN** the issue's page in the tracker is opened

#### Scenario: The address identifies the issue

- **WHEN** an issue is opened
- **THEN** the address is that issue's own page, built from the tracker's configured location and the issue's key

#### Scenario: Opening changes nothing

- **WHEN** an issue is opened
- **THEN** nothing about the issue changes and no request is made to change it

### Requirement: Tracker issues count as work

A tracker issue SHALL be treated as belonging to the work project, so that the
key which hides work hides the tracker block too, and the count of what was
hidden includes it.

#### Scenario: Hiding work hides the issues

- **WHEN** work is hidden and today holds tracker issues
- **THEN** they disappear along with the work tasks, and pressing the key again brings them back

#### Scenario: The hidden count includes them

- **WHEN** work is hidden and the board reports how many rows that removed
- **THEN** the tracker issues it removed are included in that count

### Requirement: Which issues are shown is configured, not built in

The assignee, the projects and the state that select the issues SHALL be read
from the environment, so that no login, project name or credential is written
into the board.

Where the tracker is not configured, the board SHALL show no tracker block and
SHALL NOT report a failure: a board with no tracker configured is an ordinary
board, not a broken one.

#### Scenario: A tracker is configured

- **WHEN** the tracker is configured and reachable
- **THEN** the issues it reports for that configuration are shown

#### Scenario: No tracker is configured

- **WHEN** no tracker is configured
- **THEN** today shows only the day's own tasks, and the board reports no tracker failure

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no person, no project and no tracker address, and all of them are discovered at run time

### Requirement: The board works when the tracker cannot be reached

Where the tracker cannot be reached or answers with an error, the day SHALL
load and behave exactly as it does without a tracker, and the board SHALL say
that it could not reach the tracker.

Silence SHALL NOT be acceptable here: an empty block is the ordinary case when
nothing is in progress, so a failure that showed nothing would be
indistinguishable from a quiet day.

Fetching the issues SHALL NOT delay the day's own tasks appearing, and a
tracker failure SHALL NOT be reported as a failure to load the day.

#### Scenario: The tracker is unreachable

- **WHEN** today is displayed and the tracker cannot be reached
- **THEN** the day's own tasks are shown as usual, no tracker block appears, and the board says the tracker could not be reached

#### Scenario: A failure is distinguishable from an empty result

- **WHEN** the tracker cannot be reached and when it reports nothing in progress
- **THEN** the board says something different in each case

#### Scenario: The day does not wait for the tracker

- **WHEN** today is loaded
- **THEN** the day's own tasks appear without waiting for the tracker to answer

#### Scenario: A tracker failure is not a failure to load the day

- **WHEN** the tracker fails
- **THEN** the board does not report that today failed to load, and every task action still works

#### Scenario: The tracker recovers

- **WHEN** the tracker could not be reached and a person reloads the view once it can be
- **THEN** the issues appear and the board stops saying it could not be reached

## MODIFIED Requirements

### Requirement: The board reports what a view is not showing

When the inbox is shown and undated filed tasks have been left out of it, the board SHALL report how many, so that excluding them does not hide their existence. When today is shown and it has gathered past-due tasks, the board SHALL report how many are past due separately from how many are due today. When work tasks are being hidden, the board SHALL report that too, alongside whatever else it is reporting about the view. When today is shown and tracker issues are in progress, the board SHALL report how many, counted separately from the tasks it manages.

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

#### Scenario: Tracker issues are counted separately

- **WHEN** today is displayed with tracker issues in progress
- **THEN** the board reports how many issues are in progress, and the count of tasks it reports is the number of tasks it manages, not including them

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, undo the last write it made, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

Where the selected row is a tracker issue rather than a task, only opening it SHALL do anything; every other action SHALL say the issue is not editable here.

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

#### Scenario: Undoing needs no task selected

- **WHEN** a person presses the undo key
- **THEN** it reverses the last write the board made, whichever task that was and whether or not it is the selected one

#### Scenario: Only opening works on a tracker issue

- **WHEN** a tracker issue is selected
- **THEN** the key that opens a link opens it, and every action that would change it says it is not editable here
