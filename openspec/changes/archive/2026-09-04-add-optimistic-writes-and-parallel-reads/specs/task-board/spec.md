## ADDED Requirements

### Requirement: A write shows its outcome before the server confirms it

When a person performs an action that changes a task, the board SHALL apply
the expected outcome to the view and repaint it without waiting for the API,
then send the request in the background. The board SHALL NOT refetch the view
in order to display a write it performed itself: the outcome it already
applied stands, reconciled against the server's answer when that arrives.

The repainted view SHALL be the view the person would have seen had the write
completed instantly, including every consequence the board derives for itself
— a task's position in the ordering, whether it is still shown at all, and the
counts the board reports for the view.

#### Scenario: Ticking a task

- **WHEN** a person ticks the selected task
- **THEN** the row shows as finished, moves to where finished tasks are ordered, and the view's done count rises, all before the API has answered

#### Scenario: The view is not refetched

- **WHEN** a write succeeds
- **THEN** the board does not re-request the view's tasks in order to show the change

#### Scenario: A write that removes a task from the view

- **WHEN** a person assigns another day to a task, marks it done for today, or deletes it
- **THEN** the task leaves the shown view immediately, and the view's counts are adjusted to match

#### Scenario: Past-due status is re-derived, not refetched

- **WHEN** an optimistic write changes whether a shown task is past due
- **THEN** the board re-derives that from the task it now holds, and the past-due count it reports agrees with the rows on screen

#### Scenario: A slow write is still instant on screen

- **WHEN** a write takes seconds for the API to complete
- **THEN** the screen has already shown the outcome, and the person is not made to wait for it

### Requirement: A rejected write is undone

Where the API refuses a write, the board SHALL restore what it showed before
applying the write and SHALL report the failure. It SHALL NOT keep on screen a
change the server did not accept, and SHALL NOT leave the failure unreported.

A refusal the board already treats as acceptable SHALL remain acceptable: the
record refused when marking a task done for today is not a failure, and does
not undo anything.

#### Scenario: The API refuses a write

- **WHEN** a write the board has already shown is refused
- **THEN** the view returns to what it showed before that write, and the refusal is reported

#### Scenario: One write fails among several

- **WHEN** several writes are in flight and one is refused
- **THEN** only that write's effect is undone, and the others stand

#### Scenario: An accepted refusal undoes nothing

- **WHEN** the record of a day's work is refused for a task being marked done for today
- **THEN** nothing is undone, no failure is reported, and the task is still scheduled for tomorrow

### Requirement: The cursor never lands on a task by accident

When a write reorders the view, the selection SHALL be decided by which task
it belongs on, never by the row number it previously occupied. Where the
selected task has left the view, the selection SHALL move to a task adjacent
to where it was.

This matters because completion is the first ordering key, so ticking a task
moves it: a selection that stayed on the row index would land on an unrelated
task, and the next keypress would act on that task instead.

Ticking a task off SHALL move the selection to the next unfinished task, so
that a list can be worked down with one key. Every other write SHALL leave
the selection on the task it changed, unticking included — a task brought
back is what the person is then looking at.

#### Scenario: Ticking moves on to the next unfinished task

- **WHEN** a person ticks a task that is not the last unfinished one
- **THEN** the ticked task moves to where finished tasks are ordered, and the selection is on the next unfinished task

#### Scenario: Ticking the last unfinished task

- **WHEN** a person ticks the only unfinished task left
- **THEN** the selection stays on a task that is still shown, and no keypress is left pointing at nothing

#### Scenario: Working down a list

- **WHEN** a person presses the tick key several times in succession, faster than the API answers
- **THEN** a different task is ticked by each press, and every press acts on the task that was visibly selected when it was made

#### Scenario: Unticking keeps the task selected

- **WHEN** a person unticks a task
- **THEN** the selection stays on that task as it moves back among the unfinished ones

#### Scenario: A write other than ticking

- **WHEN** a person renames the selected task, or moves it to a day it is already on
- **THEN** the selection is still on that task afterwards

#### Scenario: The selected task leaves the view

- **WHEN** the selected task is deleted, or assigned to another day
- **THEN** the selection moves to a task adjacent to where it was

#### Scenario: The view becomes empty

- **WHEN** the last task in the view leaves it
- **THEN** nothing is selected and the board reports the view as empty

### Requirement: Keypresses during a write are not lost

The board SHALL accept an action while an earlier write is still in flight.
It SHALL NOT discard the keypress silently.

Writes to different tasks SHALL be allowed to proceed at the same time.
Writes to the same task SHALL reach the API in the order the person performed
them, so that a later action on a task cannot be overtaken by an earlier one.

#### Scenario: Ticking several tasks quickly

- **WHEN** a person ticks three tasks faster than the API answers
- **THEN** all three writes reach the API, and none of the keypresses is dropped

#### Scenario: Two actions on the same task

- **WHEN** a person renames a task and then immediately cancels it
- **THEN** the API receives the rename before the cancellation

#### Scenario: Nothing is silently swallowed

- **WHEN** the board cannot carry out an action
- **THEN** it says so, rather than appearing to ignore the key

### Requirement: A refresh does not revert a write in flight

When the board reloads a view — because a person asked it to, or because it
navigated — it SHALL NOT replace a task whose write has not yet been
confirmed with the server's older copy of that task. The write the person
performed SHALL remain visible until it is confirmed or refused.

#### Scenario: A refresh arrives mid-write

- **WHEN** a person ticks a task and asks for a refresh before the tick is confirmed
- **THEN** the refreshed view still shows the task as ticked, rather than reverting it

#### Scenario: Confirmed writes accept the server's copy

- **WHEN** a refresh arrives and no write is in flight
- **THEN** the view is replaced by what the server reports, as it was before

## MODIFIED Requirements

### Requirement: Today shows what is past due

Today's view SHALL list, in addition to the tasks that start today, every unfinished task that is past due: one whose start is before today, or whose deadline has already passed. A task that qualifies under both rules SHALL appear once. Deferred tasks SHALL NOT be included, because the someday view exists to set a task aside and returning it to today would defeat that. No limit SHALL be placed on how far back a past-due task may come from.

Gathering these tasks requires more than one query of the API, because the
conditions combine conjunctively and asking for both in one query would return
only the tasks meeting both. Those queries SHALL be allowed to run at the same
time as each other and as the query for the day itself, and the view they
produce SHALL NOT depend on the order in which their results arrive. Where any
of them fails, the load SHALL be reported as failed rather than presented as a
day with some of its tasks missing.

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

#### Scenario: The order results arrive in does not matter

- **WHEN** today's queries complete in any order relative to one another
- **THEN** the resulting view is the same, in contents, ordering, and past-due count

#### Scenario: One of today's queries fails

- **WHEN** any one of the queries making up today's view fails
- **THEN** the board reports the failure, and does not show a partial day as though it were complete
