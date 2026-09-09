# task-board Specification

## Purpose
The day-at-a-time terminal view of a person's tasks: it shows the tasks starting on one calendar day, lets them move between days, and lets them act on the selected task. It deliberately exposes a small subset of the upstream task model, leaving richer editing to the SingularityApp clients.

## Requirements

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

### Requirement: A title is shown as readable text

A task's title SHALL be shown as readable text: any link markup stored in it is rendered as the address it points to rather than displayed raw, and any character that the display treats as styling is shown as written.

#### Scenario: A row never shows stored markup

- **WHEN** a task's title holds an HTML anchor
- **THEN** the row shows the readable address and none of the surrounding tags

### Requirement: A past-due row is marked out

A past-due task SHALL show how overdue it is in place of its start time, and SHALL have its title rendered in a colour that sets it apart from the tasks due today.

#### Scenario: A past-due row is set apart

- **WHEN** today's view holds both a past-due task and a task due today
- **THEN** the past-due row shows how overdue it is where the other shows a time, and its title is coloured while the other's is not

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, tagged green before untagged, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally the order a person has set by hand. Where two tasks share even that, they SHALL be ordered by title. Priority SHALL NOT influence the order.

These rules order the tasks. A day may also hold rows that are not tasks — the calendar's events — which take their place among them by when they happen, and are not subject to these rules. Removing every such row from a day SHALL leave the tasks in exactly the order stated here.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and the same manual order, and carry different priorities
- **THEN** they are ordered by title, so the sequence is never arbitrary between them, and their priorities are not consulted

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

#### Scenario: Past-due tasks lead today's own

- **WHEN** today's view holds both past-due tasks and tasks due today, and they are equally tagged
- **THEN** every past-due task is listed above every task due today

#### Scenario: A tagged task due today leads an untagged one past due

- **WHEN** today's view holds a tagged task due today and an untagged task past due
- **THEN** the tagged task is listed first, because the tag ranks above how overdue a task is

#### Scenario: The tasks' order survives the events

- **WHEN** a day holds both events and tasks
- **THEN** disregarding the events leaves the tasks in the same order they would have had alone

### Requirement: The manual order is the last ordering key

The order a person has set by hand SHALL be the last key and never override an earlier one: it decides the sequence among tasks the other keys leave equal, and cannot lift a task above a group it does not belong to. A day's timed tasks therefore stay in ascending start time however they are moved.

#### Scenario: The manual order is what decides between otherwise equal tasks

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot but carry different manual orders
- **THEN** they are ordered by the sequence a person has set, and the title is not consulted

#### Scenario: The manual order cannot override the time of day

- **WHEN** a day holds two timed tasks at different times, whatever manual order they carry
- **THEN** the earlier one is listed first

### Requirement: Past-due tasks are ordered by how overdue they are

Past-due tasks SHALL be ordered by how overdue they are, the most overdue first, whatever manual order they carry. Where some of them are tagged green, they SHALL form two runs — the tagged ones and the rest — each ordered by how overdue its tasks are, since the tag ranks above lateness. Where they sit relative to the tasks due today is decided by the day's ordering keys, not here.

#### Scenario: The most overdue comes first

- **WHEN** today's view holds several past-due tasks, none of them tagged
- **THEN** they are ordered with the longest overdue at the top, whatever manual order they carry

#### Scenario: Tagged and untagged past-due tasks form two runs

- **WHEN** today's view holds past-due tasks of which some are tagged
- **THEN** the tagged ones are listed first, ordered by how overdue they are, and the rest follow ordered the same way

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

A note SHALL be shown as the characters it contains. The area draws its text as markup, so a note is escaped before it is drawn; otherwise a note holding square brackets would lose them on screen while remaining whole in the store, and a person who had just typed them would be told the board had destroyed their work.

The detail area SHALL keep the same height whatever the selected row carries, and whether or not anything is selected at all. Its height SHALL NOT depend on the length of the note. A person stepping down a list is moving through rows whose notes differ from nothing at all to many screens; an area sized to each of them in turn moves the list under the hand that is moving through it, and the row a person is about to press a key on is not where they saw it.

Where the window is too short for that height to leave a usable list, the area SHALL take a share of the height instead. The height is fixed against the *content*, which is what makes the list still; being fixed against the window as well would make a short window unusable.

The area SHALL scroll, so that a note longer than the area can be read in full without leaving the list. Scrolling SHALL be by its own keys and SHALL NOT move the selection: the person is reading the row they have chosen, not choosing another.

While the area holds more than it can show, it SHALL say so. An area that is always the same height gives a person no way to tell a note that ends from one that continues, and a note read as complete when it was cut is worse than one that plainly runs on.

When the selection changes, the area SHALL show the beginning of the newly selected row's note. A note carried over at the offset the last one was read to would open part way through, at a place that means nothing.

#### Scenario: A recurring task with a note

- **WHEN** the selected task recurs and carries a note
- **THEN** the detail area reports that it is recurring and shows the note text, with no mention of priority

#### Scenario: A plain task

- **WHEN** the selected task does not recur, is not pinned, and has neither deadline nor note
- **THEN** the detail area shows no priority line

#### Scenario: A note is shown as written

- **WHEN** the selected task's note contains square brackets or text that reads as markup
- **THEN** every character of it appears, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: The area is the same height whatever the note

- **WHEN** the selection moves between a row with no note, a row with a one-line note, and a row whose note is many times the area's height
- **THEN** the area is the same height each time

#### Scenario: The list does not move under the cursor

- **WHEN** the selection moves down a list of rows whose notes differ in length
- **THEN** the list shows the same number of rows throughout, and no row changes position because of the note being shown

#### Scenario: Nothing selected

- **WHEN** the shown view holds no rows at all
- **THEN** the area is still the same height, showing nothing

#### Scenario: A window too short for the fixed height

- **WHEN** the window is too short for the area's height to leave a usable list
- **THEN** the area takes a share of the window's height instead, and is still the same height whatever the note

#### Scenario: A long note can be read in full

- **WHEN** the selected row's note is longer than the area can show and a person scrolls the area down
- **THEN** the rest of the note is shown, and the selection has not moved

#### Scenario: Scrolling back

- **WHEN** a person scrolls the area down and then up again
- **THEN** the beginning of the note is shown again

#### Scenario: Scrolling a note that fits

- **WHEN** the selected row's note is shorter than the area and a person presses a scrolling key
- **THEN** nothing moves, and the selection has not moved

#### Scenario: There is more below

- **WHEN** the selected row's note is longer than the area can show
- **THEN** the area shows that it holds more than it is showing

#### Scenario: There is nothing more below

- **WHEN** the selected row's note fits in the area
- **THEN** the area shows no such indication

#### Scenario: A new selection starts at the beginning

- **WHEN** a person scrolls part way through one row's note and then selects another row
- **THEN** the beginning of the newly selected row's note is shown

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, scroll the detail area up and down, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

Scrolling the detail area SHALL write nothing and SHALL be offered on every row the board draws, a row from a source included: reading is not a change, and the rows whose notes least often fit are the ones the board does not own.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, project assignment, done for today, note editing and opening a link included

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

#### Scenario: Promoting belongs to a mail row

- **WHEN** a person presses the key that turns a mail thread into a task, with a task selected rather than a mail thread
- **THEN** nothing is created, and the board says what the key is for

#### Scenario: Scrolling the detail area writes nothing

- **WHEN** a person scrolls the detail area on any row, including one from the mailbox, the calendar or the tracker
- **THEN** the area scrolls, nothing is written anywhere, and the row is not refused as unownable

### Requirement: Only opening acts on a tracker issue

Where the selected row is a tracker issue rather than a task, only opening it SHALL do anything; every other action SHALL say the issue is not editable here.

#### Scenario: Only opening works on a tracker issue

- **WHEN** a tracker issue is selected
- **THEN** the key that opens a link opens it, and every action that would change it says it is not editable here

### Requirement: Help lists the available keys

The board SHALL offer an in-app help overlay listing the keys it responds to. The overlay SHALL list only keys the board actually binds, and SHALL NOT advertise a priority action. It SHALL name each key in English only, and SHALL state that the keys work in either keyboard layout without naming the other layout's characters.

#### Scenario: Opening help

- **WHEN** a person opens the help overlay
- **THEN** it lists the movement, day-navigation, and task actions the board supports, with no priority entry

#### Scenario: Help says the keys work in either layout

- **WHEN** a person opens the help overlay
- **THEN** it says the keys work whichever keyboard layout is active, and shows no key spelled in any layout other than English

### Requirement: The board does not write priority

The board SHALL NOT send a priority value in any task it creates or updates, leaving each task's stored priority as whatever other SingularityApp clients set.

#### Scenario: Adding a task

- **WHEN** a person adds a task to the shown day
- **THEN** the created task carries the title and the day's start, and no priority is specified

#### Scenario: Renaming a task

- **WHEN** a person renames the selected task
- **THEN** only the title is submitted, and the task's stored priority is unchanged afterwards

### Requirement: Inbox view

The board SHALL offer an inbox view listing every unfinished task that has no date, is not deferred, and has no project. A task that has been given a project has already been sorted, so it does not belong in the queue awaiting triage. Finished tasks SHALL be excluded from it, because the store holds far more finished undated tasks than open ones and including them would bury the tasks awaiting triage.

The inbox SHALL additionally hold the mail awaiting a decision, as its own requirement states. It is the same queue: a message not yet decided about and an undated task not yet decided about are alike, and both are worked through at the same cadence.

#### Scenario: Reaching the inbox

- **WHEN** a person asks for the inbox
- **THEN** the board lists the unfinished tasks that have no date, are not deferred, and have no project, together with the mail awaiting a decision, and nothing else

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

Within the inbox and the someday view the board SHALL order tasks by, in turn: tagged green before untagged, pinned before unpinned, and then title. Priority SHALL NOT influence the order.

#### Scenario: Undated tasks read alphabetically

- **WHEN** the inbox holds several unpinned tasks, none of them tagged
- **THEN** they are listed in title order

#### Scenario: Pinned tasks lead

- **WHEN** the inbox holds both pinned and unpinned tasks, equally tagged
- **THEN** every pinned task is listed above the unpinned ones

#### Scenario: Tagged tasks lead the pinned ones

- **WHEN** the inbox holds a tagged unpinned task and an untagged pinned task
- **THEN** the tagged one is listed first

### Requirement: The board names the view it is showing

The board SHALL show which of the three views is displayed, naming the inbox and the someday view rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds.

#### Scenario: Showing the inbox

- **WHEN** the inbox is displayed
- **THEN** the board names it as the inbox and reports how many tasks it holds

#### Scenario: Showing a calendar day

- **WHEN** a calendar day is displayed
- **THEN** the board names that day and how it relates to today, as it did before

### Requirement: The board reports what a view is not showing

When the inbox is shown and undated filed tasks have been left out of it, the board SHALL report how many, so that excluding them does not hide their existence. When today is shown and it has gathered past-due tasks, the board SHALL report how many are past due separately from how many are due today.

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

### Requirement: The board reports hidden work and the issues it is tracking

When work tasks are being hidden, the board SHALL report that, alongside whatever else it is reporting about the view. When today is shown and the tracker block holds issues, the board SHALL report how many, counted separately from the tasks it manages, and SHALL NOT name them by any single state, since more than one may be shown.

#### Scenario: Reporting hidden work beside the other counts

- **WHEN** today is displayed with past-due tasks gathered into it and work is being hidden
- **THEN** the board reports the past-due count and the hidden-work count together, and neither replaces the other

#### Scenario: Tracker issues are counted separately

- **WHEN** today is displayed with tracker issues shown
- **THEN** the board reports how many issues it is tracking, and the count of tasks it reports is the number of tasks it manages, not including them

#### Scenario: The count is not named for one state

- **WHEN** issues in more than one state are shown
- **THEN** what the board reports about them does not describe them all as being in any one of those states

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

The focus view SHALL show a note as the characters it contains, by the same rule the detail area follows and for the same reason. The two places a note is shown SHALL agree: a note holding square brackets is a note holding square brackets in both.

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

#### Scenario: A note is shown as written here too

- **WHEN** the selected task's note contains square brackets or text that reads as markup and a person opens the focus view
- **THEN** every character of it appears there, and no styling comes from it
### Requirement: The focus view changes nothing

Opening, viewing, or dismissing the focus view SHALL leave the task exactly as it was, and SHALL send no request that modifies anything. In particular the key that opens the focus view SHALL NOT also tick the task, so a task cannot be completed by looking at it.

#### Scenario: Opening the focus view does not complete the task

- **WHEN** a person opens the focus view on an unfinished task and dismisses it
- **THEN** the task is still unfinished

#### Scenario: No request is sent

- **WHEN** a person opens and dismisses the focus view
- **THEN** the board sends no request that creates, updates, or deletes anything

#### Scenario: Ticking still has its own way in

- **WHEN** a person wants to tick the selected task
- **THEN** an action distinct from the one that opens the focus view does it

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

### Requirement: Gathering what is past due takes more than one query

Gathering these tasks requires more than one query of the API, because the conditions combine conjunctively and asking for both in one query would return only the tasks meeting both. Those queries SHALL be allowed to run at the same time as each other and as the query for the day itself, and the view they produce SHALL NOT depend on the order in which their results arrive. Where any of them fails, the load SHALL be reported as failed rather than presented as a day with some of its tasks missing.

#### Scenario: The order results arrive in does not matter

- **WHEN** today's queries complete in any order relative to one another
- **THEN** the resulting view is the same, in contents, ordering, and past-due count

#### Scenario: One of today's queries fails

- **WHEN** any one of the queries making up today's view fails
- **THEN** the board reports the failure, and does not show a partial day as though it were complete

### Requirement: How overdue a task is

For a past-due task the board SHALL report how long it has been past due, measured from the earliest of its passed start and its passed deadline — the moment it first became late.

#### Scenario: Measured from the start it missed

- **WHEN** a task's start was three days ago and it carries no deadline
- **THEN** the board reports it as three days past due

#### Scenario: Measured from whichever came first

- **WHEN** a task's deadline passed before its start did
- **THEN** the board measures from the deadline, as the earlier of the two

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

### Requirement: Marking a task done for today

The board SHALL let a person mark the selected task as done for today, meaning work happened on it today and it should come up again tomorrow. This SHALL record the day's work against the task wherever the API accepts such a record, and SHALL then schedule the task for tomorrow. It SHALL NOT mark the task finished: a task done for today is still an open task.

#### Scenario: A task being worked on today

- **WHEN** a person marks a task dated today as done for today
- **THEN** the day's work is recorded against the task, the task is scheduled for tomorrow, and it remains unfinished

#### Scenario: It does not finish the task

- **WHEN** a person marks any task as done for today
- **THEN** the task is not completed, not cancelled, and still appears as open on the day it was moved to

#### Scenario: Available from the dateless views

- **WHEN** a person marks an undated task in the inbox or in the someday view as done for today
- **THEN** the task is scheduled for tomorrow and is no longer deferred, leaving the bucket it was in

#### Scenario: Distinct from finishing a task

- **WHEN** a person finishes a task
- **THEN** an action other than the one that marks it done for today does it, and neither key performs the other's work

### Requirement: The day's work is recorded before the task is rescheduled

The record SHALL be attempted before the task is rescheduled, because the API accepts it only for a task whose start is not in the future and moving the date forward would make the record impossible. Where the API refuses the record — a task with no date, or one already dated far enough ahead — the task SHALL still be scheduled for tomorrow, and the refusal SHALL NOT be reported as a failure.

#### Scenario: A task carried over from an earlier day

- **WHEN** a person marks a past-due task as done for today
- **THEN** the day's work is recorded against it as well, the task is scheduled for tomorrow, and it remains unfinished

### Requirement: The key bar shows every key without clipping

The board SHALL display at all times the keys it responds to and what each one does. The bar SHALL wrap across as many rows as it takes for every entry to be shown in full: no label may be omitted, and none may be cut off part-way through a word.

#### Scenario: A narrow terminal

- **WHEN** the board is shown in a terminal too narrow for the entries to fit on two rows
- **THEN** the bar uses however many rows are needed, and still shows every entry in full

#### Scenario: A wide terminal

- **WHEN** the board is shown in a terminal wide enough for fewer rows
- **THEN** every entry still appears exactly once, with none repeated across rows

#### Scenario: No entry is cut off part-way

- **WHEN** the bar is shown at any width the board can be run at
- **THEN** no entry appears as a partial word

#### Scenario: The task list keeps its room

- **WHEN** the bar occupies more than one row
- **THEN** the task list shrinks to accommodate it rather than being overlapped, and the day header and status line remain visible

### Requirement: The key bar names each action once, by its English key

The bar SHALL name every action the board offers for display, once each, by the English key a person presses for it. Where an action answers more than one key — an arrow beside a letter, a second key that deletes, or the character the same physical key gives in another layout — the bar SHALL show the one key and not the alternatives, so that offering more ways to reach an action never widens the bar. The bar SHALL NOT name a key that does nothing.

The key a person presses is the character on the keycap, not the name the
toolkit gives it. Where those differ, the bar SHALL show the character.

#### Scenario: Every action is advertised

- **WHEN** the board is shown
- **THEN** every key it binds for display appears in the bar, each with its description in full

#### Scenario: Alternatives do not widen the bar

- **WHEN** an action answers several keys, whether an arrow, a second key, or another layout's character
- **THEN** the bar shows one entry for that action, naming the English key, and the bar is no wider than if the action answered that key alone

#### Scenario: The bar and the help overlay agree

- **WHEN** a person compares the bar with the help overlay
- **THEN** every key named in the bar is described in the overlay, and neither names a key the board does not bind

#### Scenario: A key whose name is not its character

- **WHEN** an action answers a key the toolkit names in words rather than by its character — a bracket, a full stop, a question mark
- **THEN** the bar shows the character a person would press, not the toolkit's name for it
### Requirement: A task's link is recognised and readable

The board SHALL recognise a link written in a task's title or in its note, whether stored as an HTML anchor or written as a plain `http` or `https` address. Where a title holds an anchor, the board SHALL show the anchor's readable text in place of the stored markup, so no row or card ever displays raw HTML. The surrounding words of the title SHALL be preserved. An address written without a scheme SHALL be understood as `https`.

The board SHALL also recognise a task's mention of a tracker issue, written as one of the configured tracker projects followed by a number, and SHALL treat that issue's page in the tracker as something the task can open. Only the configured projects SHALL be recognised, so that ordinary text shaped like a key — a version, a standard, a year — is never taken for an issue. Where no tracker is configured, no key SHALL be recognised.

A task's note SHALL be read for the same things its title is read for. A note is where an address is most naturally kept, and a rule that recognised an issue key there but not an address, or the reverse, could not be remembered.

Recognising an issue key SHALL NOT change how a title is drawn. The key is shown as the text it is.

#### Scenario: A title storing an HTML anchor

- **WHEN** a task's title contains an HTML anchor around an address
- **THEN** the title is shown as its readable text with the surrounding words intact, and the stored markup is not displayed

#### Scenario: A title with a plain address

- **WHEN** a task's title contains a plain `https` address and no markup
- **THEN** the title is shown unchanged and that address is recognised as its link

#### Scenario: An address with no scheme

- **WHEN** a task's link is stored without a scheme, as a bare domain
- **THEN** it is understood as an `https` address

#### Scenario: A title with no link

- **WHEN** a task's title contains no address
- **THEN** the title is shown exactly as stored and the task has no link

#### Scenario: A title holding more than one address

- **WHEN** a task's title contains several addresses
- **THEN** all of them are things the task can open, and every one of them is still shown in the title

#### Scenario: Markup characters in a title are shown, not interpreted

- **WHEN** a task's title contains square brackets
- **THEN** they appear in the row exactly as stored, rather than being consumed as styling

#### Scenario: A mention of a tracker issue

- **WHEN** a task's text names one of the configured tracker projects followed by a number
- **THEN** that issue's page in the tracker is something the task can open, and the text is shown as written

#### Scenario: Text that only looks like an issue key

- **WHEN** a task's text holds a word shaped like a project key and a number, whose project is not one of the configured ones
- **THEN** it is not treated as an issue and nothing is offered for it

#### Scenario: An address kept in the note

- **WHEN** a task's note holds an address and its title holds none
- **THEN** the address is something the task can open

#### Scenario: No tracker configured

- **WHEN** no tracker is configured and a task's text names something shaped like an issue key
- **THEN** no issue is recognised, and the task's addresses are unaffected

### Requirement: Opening a task's link

The board SHALL let a person open the selected task's link, handing the address to the operating system. This SHALL work without a mouse and without depending on the terminal's own capabilities. The board SHALL additionally present the address so that a terminal able to make hyperlinks clickable can do so, but SHALL NOT rely on that for the link to be reachable.

Where the task offers more than one thing to open, the board SHALL ask which, as its own requirement states. A person pressing the key SHALL never have to know in advance whether they will be asked.

#### Scenario: Opening the link of the selected task

- **WHEN** a person asks to open the link of a task that has one
- **THEN** the address is handed to the operating system to open

#### Scenario: A task with no link

- **WHEN** a person asks to open the link of a task that has none
- **THEN** nothing is opened and the board says the task has no link

#### Scenario: Nothing is selected

- **WHEN** a person asks to open a link while the shown view holds no tasks
- **THEN** nothing is opened and the board is left as it was

#### Scenario: Opening a link changes nothing

- **WHEN** a person opens a task's link
- **THEN** the task is not modified and no request that changes anything is sent

#### Scenario: Available wherever a task is selected

- **WHEN** a task with a link is selected in the inbox or in the someday view
- **THEN** its link can be opened just as from a day

#### Scenario: Opening an issue named by a task

- **WHEN** a person asks to open the link of a task whose only openable thing is a mention of a tracker issue
- **THEN** that issue's page in the tracker is opened, without a choice being presented

### Requirement: Only web addresses are opened

Only `http` and `https` addresses SHALL be opened. A task's title, a task's
note, an event's location and an event's description are all ordinary text
that happens to be passed to the system opener, so no other scheme may be
launched through any of them.

An issue's page SHALL be built from the tracker's configured location, not
taken from a task's text, so a mention of an issue cannot name an address of
its own.

#### Scenario: An address of another kind is refused

- **WHEN** a task's title contains an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened

#### Scenario: An event's address of another kind is refused

- **WHEN** an event's location or description holds an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened, and the event is treated as carrying no address unless it holds another that may be

#### Scenario: An address of another kind in a note is refused

- **WHEN** a task's note holds an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened, and is not offered as something the task can open

#### Scenario: An issue's address comes from the configuration

- **WHEN** a task mentions a tracker issue
- **THEN** the address opened is built from the tracker's configured location and the issue's key, and nothing in the task's text can change it

### Requirement: The board offers the Turbo C++ themes

The board SHALL offer two themes reproducing the Turbo C++ editor theme: one on a black ground and one on the classic blue. Their ordinary text, selection, error and link colours SHALL be those the editor theme itself declares, not approximations. Where a declared value cannot serve this board, the theme MAY depart from it, and each departure SHALL be recorded with its reason. Both themes SHALL be selectable while the board is running, and the board SHALL start on the black ground.

#### Scenario: Both themes are offered

- **WHEN** the board is running
- **THEN** both the black-ground and the blue Turbo theme are available to choose from, alongside the themes the framework already provides

#### Scenario: The board starts in the dark one

- **WHEN** the board is opened
- **THEN** the black-ground Turbo theme is active

#### Scenario: Switching between them needs no restart

- **WHEN** a person chooses the other Turbo theme while the board is running
- **THEN** the board is redrawn in it immediately

#### Scenario: The colours are the editor theme's own

- **WHEN** either Turbo theme's colours are compared with the editor theme it reproduces
- **THEN** the ordinary text, the selection, the error colour and the link colour are the values that theme declares

#### Scenario: A departure from the source is deliberate

- **WHEN** a theme's colour differs from the value the editor theme declares for that role
- **THEN** the difference is one the board needed — a ground chosen to sit on a black terminal, or a muted colour the source leaves identical to its ordinary text — and not an accident of transcription

### Requirement: A theme keeps the board's distinctions visible

Whatever theme is active, the board SHALL keep apart the things its other requirements rely on being told apart: a past-due title from an ordinary one, muted text from ordinary text, the selected row from the rest, and the text on any bar or panel from the surface behind it. A theme that renders any of these indistinguishable SHALL NOT be offered.

#### Scenario: A past-due title still reads as past due

- **WHEN** today's view holds both a past-due task and one due today, under any offered theme
- **THEN** the two titles are drawn in different colours

#### Scenario: Muted text is still muted

- **WHEN** the board draws muted text — the status line, the project column, the detail strip, the key bar's labels — under any offered theme
- **THEN** it is a different colour from an ordinary task title

#### Scenario: The selected row still stands out

- **WHEN** a row is selected under any offered theme
- **THEN** its background differs from the surrounding rows and its text is legible against that background

#### Scenario: Text on a bar is legible against it

- **WHEN** a theme gives a bar or panel a light background
- **THEN** the text drawn on it is dark rather than light, and the reverse for a dark background

#### Scenario: A link is not mistaken for ordinary text

- **WHEN** a task's title carries a link under any offered theme
- **THEN** the link is drawn differently from the rest of the title

### Requirement: A write shows its outcome before the server confirms it

When a person performs an action that changes a task, the board SHALL apply the expected outcome to the view and repaint it without waiting for the API, then send the request in the background. The board SHALL NOT refetch the view in order to display a write it performed itself: the outcome it already applied stands, reconciled against the server's answer when that arrives.

#### Scenario: Ticking a task

- **WHEN** a person ticks the selected task
- **THEN** the row shows as finished, moves to where finished tasks are ordered, and the view's done count rises, all before the API has answered

#### Scenario: The view is not refetched

- **WHEN** a write succeeds
- **THEN** the board does not re-request the view's tasks in order to show the change

#### Scenario: A slow write is still instant on screen

- **WHEN** a write takes seconds for the API to complete
- **THEN** the screen has already shown the outcome, and the person is not made to wait for it

### Requirement: An applied write carries every consequence the board derives

The repainted view SHALL be the view the person would have seen had the write completed instantly, including every consequence the board derives for itself — a task's position in the ordering, whether it is still shown at all, and the counts the board reports for the view.

#### Scenario: A write that removes a task from the view

- **WHEN** a person assigns another day to a task, marks it done for today, or deletes it
- **THEN** the task leaves the shown view immediately, and the view's counts are adjusted to match

#### Scenario: Past-due status is re-derived, not refetched

- **WHEN** an optimistic write changes whether a shown task is past due
- **THEN** the board re-derives that from the task it now holds, and the past-due count it reports agrees with the rows on screen

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

When a write reorders the view, the selection SHALL be decided by which task it belongs on, never by the row number it previously occupied. Where the selected task has left the view, the selection SHALL move to a task adjacent to where it was.

This matters because completion is the first ordering key, so ticking a task moves it: a selection that stayed on the row index would land on an unrelated task, and the next keypress would act on that task instead.

#### Scenario: A write other than ticking

- **WHEN** a person renames the selected task, or moves it to a day it is already on
- **THEN** the selection is still on that task afterwards

#### Scenario: The selected task leaves the view

- **WHEN** the selected task is deleted, or assigned to another day
- **THEN** the selection moves to a task adjacent to where it was

#### Scenario: The view becomes empty

- **WHEN** the last task in the view leaves it
- **THEN** nothing is selected and the board reports the view as empty

### Requirement: Ticking a task moves the selection on

Ticking a task off SHALL move the selection to the next unfinished task, so that a list can be worked down with one key. Every other write SHALL leave the selection on the task it changed, unticking included — a task brought back is what the person is then looking at.

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

### Requirement: The list stays where it is when it is redrawn

The shown view SHALL keep its scroll position when it is redrawn. A redraw happens for reasons that are nothing to do with the person: a write confirming, mail arriving, the calendar or the tracker answering. A view that moved on each of those would move under the hand that is working it, and the row about to be acted on would not be where it was seen.

Where the selected row leaves the view, the rows below it SHALL move up by one and nothing else on screen SHALL move. The selection SHALL then be on the line the departed row occupied, so that a list is worked down one row at a time in one place rather than chasing the cursor across the screen.

Where a redraw would leave the selected row outside the visible area, the board SHALL bring it into view — and SHALL NOT place it on the last visible line, which leaves a person acting on a row with nothing shown after it. This is the case that ticking a task creates: completion is the first ordering key, so a ticked task moves down among the finished ones while the selection moves to the next unfinished one.

Where the view has become shorter than the position it was scrolled to, the board SHALL show the end of the shorter view rather than an empty area past it.

Changing which view is shown SHALL NOT carry the previous view's position into the new one. A day of six rows entered from row two hundred of the inbox is a different list, and it begins at its beginning.

#### Scenario: Ticking a row leaves the list where it was

- **WHEN** a person ticks the selected row with rows above and below it on screen
- **THEN** the view has not scrolled: the row at the top of the view is the same row it was

#### Scenario: The next row takes the line the ticked one had

- **WHEN** a person ticks the selected row
- **THEN** the row that follows it is selected, on the same line of the screen the ticked row occupied

#### Scenario: Working down a long list

- **WHEN** a person ticks several rows in succession part way down a list far longer than the screen
- **THEN** each press removes one row and moves nothing else, and the selection stays on the same line throughout

#### Scenario: A redraw for another reason

- **WHEN** the view is redrawn because a write confirmed, or because mail, the calendar or the tracker answered, with the selection unchanged
- **THEN** the view has not scrolled

#### Scenario: A selection that would fall outside the view

- **WHEN** a redraw leaves the selected row outside the visible area
- **THEN** the board scrolls to show it

#### Scenario: And not against the bottom edge

- **WHEN** the board scrolls to reveal a selected row that had fallen outside the view
- **THEN** the row is not placed on the last visible line

#### Scenario: A view that has become shorter

- **WHEN** the shown view loses most of its rows while scrolled far down
- **THEN** the end of the shorter view is shown, with no empty area past it

#### Scenario: Changing view

- **WHEN** a person is scrolled far down one view and asks for another
- **THEN** the new view starts at its beginning rather than at the position the old one was at

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

### Requirement: Setting the order of a day's tasks by hand

The board SHALL let a person move the selected task up or down within a calendar day, and SHALL store the resulting position on the task so that it survives a reload and is the same order other SingularityApp clients show.

#### Scenario: Moving a task up

- **WHEN** a person moves the selected task up, and the task above it is one the day's other ordering keys allow it to trade with
- **THEN** the two appear in the opposite sequence, every other task stays where it was, only the moved task's stored order changed, and the selection is still on the moved task

#### Scenario: Moving down

- **WHEN** a person moves the selected task down
- **THEN** it comes to sit after the task below it, under the same rules that govern moving up

#### Scenario: The new position is remembered

- **WHEN** a person moves a task and then reloads the view, or leaves the day and comes back
- **THEN** the task is still in the position they moved it to

### Requirement: A move writes one task and no other

Moving SHALL change the stored order of the moved task alone, to a value that places it on the far side of its neighbour and that no other task in the day holds. No other task's stored order SHALL change, so that a move is a single write and cannot be left half applied.

#### Scenario: A failed move changes nothing

- **WHEN** the write that moves a task fails
- **THEN** no task's stored order has changed, because the move was a single write

### Requirement: No two tasks in a day share a stored order

No two tasks in a day SHALL be left sharing a stored order. Where there is no value available between the moved task's destination and the task beyond it, the board SHALL first move that run of tasks into a range of values no task in the day holds, so that the destination exists; such a respacing SHALL preserve the order of the tasks it moves, and SHALL leave every stored order distinct even if only some of its writes are applied.

#### Scenario: No room between the destination and the task beyond it

- **WHEN** a person moves a task to a place where the two tasks it must sit between hold adjacent values with nothing available in between
- **THEN** the move still happens, the tasks keep the sequence they were in apart from the one moved, and every stored order in the day is still distinct

### Requirement: A move may not cross an ordering group

Moving SHALL only carry the task past a neighbour the day's other ordering keys allow it to trade with — one that is equally finished, equally past due, equally pinned, and equally timed at the same start. Where the neighbour in that direction is not such a task, or there is none, the board SHALL report why the task cannot move there and SHALL leave every task's stored order untouched.

#### Scenario: Already at the edge of its group

- **WHEN** a person moves the selected task towards an edge where there is no task it may trade with, whether because the day has none or because the adjacent one is ordered differently
- **THEN** the board reports why it cannot move there, and no task's stored order changes

#### Scenario: An all-day task cannot be lifted above a timed one

- **WHEN** the selected all-day task is the first of the all-day tasks and a timed task sits above it
- **THEN** moving up reports that it cannot pass the timed tasks, and the order is unchanged

#### Scenario: Sequencing a past-due task

- **WHEN** a person wants a past-due task in a particular place in today's sequence and dates it to today
- **THEN** it joins the tasks due today and can be moved among them

### Requirement: Reordering is offered on calendar days only

Reordering SHALL be offered on calendar days only. In the inbox and the someday view the board SHALL report that reordering applies to days rather than silently doing nothing, because those views are not sequences of work and are ordered by title.

#### Scenario: Not offered in the dateless views

- **WHEN** a person tries to move a task in the inbox or the someday view
- **THEN** the board reports that reordering applies to calendar days, and no task's stored order changes

### Requirement: Where a newly added task lands in a day's order

A task added to a calendar day SHALL be placed after every task already in
that day's order, so that adding one does not disturb a sequence a person has
set.

The board SHALL choose the stored order it sends rather than leaving it to
the API's default. The default is the lowest value there is, which would put
each new task at the head of its group and tie it with every other task the
board has added.

#### Scenario: Adding to a day that already has tasks

- **WHEN** a person adds a task to a day whose tasks are in an order they set
- **THEN** the new task appears after the others and none of them moves

#### Scenario: Two tasks added one after another

- **WHEN** a person adds two tasks to the same day in succession
- **THEN** the second appears after the first, rather than the two being tied and ordered by title

#### Scenario: Adding to an empty day

- **WHEN** a person adds a task to a day that has none
- **THEN** the task is created with a stored order the board chose, ready to be moved once the day has others

### Requirement: Keys work in either keyboard layout

Every key the board binds SHALL also answer the character the same physical
key produces in a Russian layout, so that a person presses the key printed on
the keyboard whichever layout is active and need not switch layouts to reach
an action.

A key whose character does not change with the layout SHALL need nothing
further. This covers the arrow keys and the space, enter, escape and
backspace keys.

#### Scenario: Adding a task without switching layout back

- **WHEN** a person adds a task, types a Russian title, confirms it, and presses the add key again while the keyboard is still in a Russian layout
- **THEN** the add prompt opens again, without the layout having to be switched

#### Scenario: Every bound letter answers both layouts

- **WHEN** a person presses any key the board binds to a Latin letter, in a Russian layout
- **THEN** the same action runs as it would in an English layout

#### Scenario: A key that is the same in both layouts

- **WHEN** a person presses space, enter, escape, backspace or an arrow key in a Russian layout
- **THEN** it does what it does in an English layout, needing no separate provision

#### Scenario: Typing a Russian title still types

- **WHEN** a person types a title containing Cyrillic letters that the board also binds to actions
- **THEN** the characters go into the text being typed and no action runs, because a prompt has the keyboard while it is open

### Requirement: Layout coverage reaches the modal keys

Every key a modal binds SHALL work in either layout, in the same way the
board's own keys do. Reordering, choosing a date, and answering a
confirmation SHALL all be reachable without switching layouts.

This matters because the trap is one level in: a person can otherwise open a
dialogue with a key that works and then find no key in it that does.

#### Scenario: Choosing a date

- **WHEN** a person opens the date picker in a Russian layout and presses one of the keys it offers
- **THEN** that choice is taken, as it would be in an English layout

#### Scenario: Answering a confirmation

- **WHEN** a person is asked to confirm a deletion in a Russian layout
- **THEN** both the yes key and the no key answer it

#### Scenario: Closing an overlay

- **WHEN** a person closes the focus card or the help overlay with its close key in a Russian layout
- **THEN** it closes

#### Scenario: No dialogue can be opened but not answered

- **WHEN** any key that opens a dialogue works in a layout
- **THEN** every key that dialogue offers works in that layout too

### Requirement: Hiding the work tasks

The board SHALL offer a key that hides every task belonging to the work project, and the same key SHALL bring them back. There SHALL be two states and no third.

Hiding SHALL remove rows from the view without changing any task: no write SHALL be made, and nothing SHALL be altered about a task because it was hidden or shown.

Rows the board draws from a source rather than from the task store SHALL be
subject to the same key, on each source's own terms, and SHALL be filtered
where the store's tasks are filtered rather than added to the view afterwards.
A source whose rows are appended after the filtering is a source the key
cannot reach, however the rows are marked.

#### Scenario: Hiding and showing again

- **WHEN** a person presses the key with work tasks in the shown view
- **THEN** those tasks disappear from it, and pressing the key again brings them back exactly as they were

#### Scenario: Nothing is written

- **WHEN** a person hides or shows the work tasks
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: A view with no work tasks

- **WHEN** a person hides the work tasks in a view that holds none
- **THEN** the view is unchanged and the board still shows that the mode is on

#### Scenario: The inbox is unaffected

- **WHEN** the mode is on and the inbox is displayed
- **THEN** none of its tasks are hidden, because a task with a project is already outside the inbox

#### Scenario: But the inbox's mail is not

- **WHEN** the mode is on and the inbox is displayed with mail in it
- **THEN** the mail rows are hidden, because all mail is work, so the view is not what it would be with the mode off

#### Scenario: No source is reached only by being marked

- **WHEN** the board draws rows from a source and those rows count as work
- **THEN** they are filtered together with the store's tasks, and no source's rows reach the view past the filter

### Requirement: How long the work filter lasts, and where it applies

The mode SHALL apply to every view the board shows, so that moving between days does not change what the mode means. It SHALL last as long as the board is open and no longer.

#### Scenario: The mode follows the person between views

- **WHEN** a person hides the work tasks and then moves to another day or to the someday view
- **THEN** the work tasks are hidden there too, without the key being pressed again

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

The board SHALL take the identity of the work project from its environment rather than carrying it in its own source, so that a personal project identifier need never enter the repository.

#### Scenario: Configured

- **WHEN** a work project is configured and a person presses the key
- **THEN** the tasks in that project are hidden

#### Scenario: The identifier is not in the source

- **WHEN** the board's source is read
- **THEN** it names no particular project, and the work project is discovered only at run time

### Requirement: A work project that is missing or unknown is reported

Where no work project is configured, the board SHALL say so when the key is pressed, and SHALL NOT silently hide nothing. A missing setting SHALL be distinguishable from a key that does not work.

Where a work project is configured but matches none that exist, the board SHALL say that too. A setting left behind by a renamed or deleted project otherwise looks exactly like a day with no work on it.

#### Scenario: Not configured

- **WHEN** no work project is configured and a person presses the key
- **THEN** the board reports that no work project is set, and no rows are hidden

#### Scenario: Configured with a project that no longer exists

- **WHEN** a work project is configured but no project with that identity exists
- **THEN** the board reports that the configured work project was not found, rather than hiding nothing and appearing to work

### Requirement: Assigning a task to a project

The board SHALL let a person put the selected task in a project, choosing from the projects that exist and showing which project the task is in now.

#### Scenario: The picker says where the task is now

- **WHEN** a person opens the project picker on a task
- **THEN** the project the task is in is shown as such, or it is shown as having none

#### Scenario: Filing from the inbox

- **WHEN** a person files a task selected in the inbox
- **THEN** it leaves the inbox at once, because the inbox holds only tasks with no project

#### Scenario: A filed task can be hidden

- **WHEN** a person files a task under the work project while work is hidden
- **THEN** the task disappears from the view, because it is now work and work is hidden

### Requirement: Filing a task for the first time is confirmed

Assigning a project to a task that has none SHALL be confirmed first. The API accepts only a project identifier and refuses both an empty value and no value, so nothing the board can send will return a task to having no project: the first filing cannot be undone from the board and SHALL be treated like deleting, which is the only other action of that kind.

#### Scenario: Filing a task that has no project

- **WHEN** a person assigns a project to a task that has none
- **THEN** the board asks first, and the task is filed only if the person agrees

#### Scenario: Declining the confirmation

- **WHEN** a person is asked to confirm a first filing and declines
- **THEN** the task keeps having no project, and nothing is sent

### Requirement: Moving between projects, and why a task cannot be un-filed

Moving a task that already has a project SHALL NOT be confirmed, because it gives up nothing that it still has. The board SHALL NOT offer to remove a task from a project, since the API provides no way to do so.

#### Scenario: Moving a task between projects

- **WHEN** a person assigns a project to a task that already has one
- **THEN** the task moves without being asked to confirm

#### Scenario: No way to un-file

- **WHEN** a person looks for a way to remove a task from its project
- **THEN** the board offers none, because the API provides none

### Requirement: Undoing the last write

The board SHALL offer a key that reverses the most recent write it made, then the one before it, and so on back through the session. Where nothing remains to reverse, the board SHALL say so.

An undo SHALL name what it reversed. A person pressing this key does not necessarily know what happened, and being told is most of what they need.

#### Scenario: Undoing a tick

- **WHEN** a person ticks a task and then presses the undo key
- **THEN** the task is unfinished again, and the board names the action it reversed and the task it acted on

#### Scenario: Walking back through several writes

- **WHEN** a person makes three writes and presses the undo key three times
- **THEN** each press reverses the next most recent write, naming it, and all three are reversed

#### Scenario: Nothing left to undo

- **WHEN** a person presses the undo key with nothing left to reverse
- **THEN** the board says so and nothing changes

#### Scenario: Undo does not outlive the board

- **WHEN** a person makes writes, closes the board, and opens it again
- **THEN** there is nothing to undo

### Requirement: Undoing reaches back, and never turns round

An undo SHALL NOT itself become something to undo: pressing the key again SHALL reach further back rather than reinstating what was just reversed.

A write the API refused SHALL NOT be reachable, because it never took effect.

#### Scenario: Pressing undo twice does not turn round

- **WHEN** a person undoes a write and presses the undo key again
- **THEN** the write before it is reversed, not the undo itself

#### Scenario: A refused write is not on the stack

- **WHEN** a write is refused and a person presses the undo key
- **THEN** the refused write is not reversed, because it never happened, and the key reaches past it to the last write that did

### Requirement: What an undo restores

An undo SHALL restore exactly the fields its own write changed, and no others, so that reversing an older write cannot disturb something that has changed since.

Where a single action wrote more than one task, its undo SHALL restore all of them together. One action SHALL be one undo, however many requests it took.

#### Scenario: Only the fields that write changed

- **WHEN** a person renames a task, then something else about that task changes, and the rename is undone
- **THEN** the title returns to what it was and the other change is left alone

#### Scenario: One action that wrote several tasks

- **WHEN** a person moves a task in a run with no numbering room, so that several tasks are written, and then undoes it
- **THEN** one press restores every task that action wrote, and the run is as it was

### Requirement: An undo is a write like any other

An undo SHALL be sent as a write like any other: shown before the API answers, and taken back if the API refuses it.

Where the task an undo would restore no longer exists, the board SHALL say so and move on rather than failing silently.

#### Scenario: An undo shows before it is confirmed

- **WHEN** a person undoes a write
- **THEN** the view shows the restored value before the API has answered

#### Scenario: A refused undo is taken back

- **WHEN** the API refuses an undo
- **THEN** the view returns to what it showed before the undo, and the refusal is reported

#### Scenario: The task is gone

- **WHEN** the task a pending undo refers to no longer exists
- **THEN** the board says so, and that entry is not left waiting to be tried again

### Requirement: What cannot be undone, and how the board says so

An undo SHALL NOT create or destroy a task. Where the most recent write cannot be reversed, the board SHALL name it and say why, rather than doing nothing or appearing to succeed.

Three writes cannot be reversed, and each SHALL be reported in its own terms: deleting a task, because it is gone; filing a task that had no project, because the API refuses every value that would return it to having none; and adding a task, because reversing it would mean deleting, which this key does not do.

#### Scenario: The last write was a deletion

- **WHEN** a person deletes a task and presses the undo key
- **THEN** the board says a deletion cannot be undone, and no task is created

#### Scenario: The last write was a first filing

- **WHEN** a person files a task that had no project and presses the undo key
- **THEN** the board says the filing cannot be undone, and the task keeps its project

#### Scenario: The last write was an addition

- **WHEN** a person adds a task and presses the undo key
- **THEN** the board says adding cannot be undone and suggests deleting the task instead, and the task is not deleted

#### Scenario: Undo never destroys

- **WHEN** a person presses the undo key any number of times
- **THEN** no task is ever deleted by it

### Requirement: Undo and confirmation cover the same set

Each write that cannot be undone is already confirmed before it happens. What cannot be undone is what the board asks about, and the two SHALL stay in step: an action added later that cannot be undone SHALL be confirmed, and one that can be undone SHALL NOT need confirming.

#### Scenario: Moving between projects can be undone

- **WHEN** a person moves a task that already had a project to another one and presses the undo key
- **THEN** the task returns to its previous project, because a project it can return to still exists

### Requirement: Undoing done for today is partial, and says so

Marking a task done for today does two things: it records that work happened,
and it moves the task to tomorrow. Undoing it SHALL restore the date, and
SHALL say that the record of the day's work remains, because the API offers
no way to withdraw it.

The board SHALL NOT imply the action was fully reversed.

#### Scenario: Undoing done for today

- **WHEN** a person marks a task done for today and then undoes it
- **THEN** the task returns to the date it was on, and the board says the record of the day's work could not be withdrawn

#### Scenario: The task is where it was

- **WHEN** the date is restored by an undo
- **THEN** the task appears in the view it was in before, not the one it was moved to

### Requirement: The tracker block sits below the day's unfinished tasks and is not ordered

The tracker block SHALL sit after every unfinished task the board manages and
before the first finished or cancelled one. An issue names no hour and no
date, which makes it kin to the day's untimed work rather than to the
appointments and the overdue tasks that lead the day.

Where the day holds no finished task, the block SHALL end the list. Where
every task is finished, the block SHALL lead them. In both cases the rule is
the same one: the block marks where the day's unfinished work ends.

The block SHALL NOT take part in the day's ordering. Its rows SHALL NOT be
interleaved with tasks, SHALL NOT be reordered by anything the day does, and
SHALL keep a stable sequence among themselves.

Within the block, issues SHALL be ordered by their state in the order the
states are configured, and by issue key within a state. Configuring the
states therefore decides which of them leads the block.

No key that reorders SHALL move a tracker row, and the board SHALL say why
rather than doing nothing.

#### Scenario: Below the unfinished work and above the finished

- **WHEN** today holds past-due tasks, tasks due today, finished tasks and tracker issues
- **THEN** every tracker issue is listed after all the unfinished tasks and before every finished one

#### Scenario: Beside the day's untimed work

- **WHEN** today holds tasks that name a time and tasks that name none, together with tracker issues
- **THEN** the block follows the tasks naming no time, with no unfinished task of the day between them

#### Scenario: A day with nothing finished

- **WHEN** today holds tracker issues and no finished or cancelled task
- **THEN** the block ends the list

#### Scenario: A day with everything finished

- **WHEN** every task today is finished or cancelled and the tracker reports issues
- **THEN** the block is listed before all of them

#### Scenario: The configured order of states is the order of the block

- **WHEN** issues are shown in more than one state
- **THEN** they appear grouped in the order the states are configured, and by key within each state

#### Scenario: Ticking a task moves it past the block

- **WHEN** a task is ticked and the day reorders
- **THEN** the ticked task passes below the block, which keeps its own sequence and its place between the unfinished tasks and the finished ones

#### Scenario: Reordering does not reach a tracker row

- **WHEN** a person tries to move a tracker row up or down
- **THEN** the board says the issue lives in the tracker and cannot be reordered here, and nothing changes

### Requirement: Today shows the tracker's issues, and what each one is

Today's view SHALL additionally show the issues assigned to the configured
person that the issue tracker reports as being in any of the configured
states, in a block placed among the tasks the board manages.

The block SHALL appear on today alone. An issue the tracker reports as being
worked on or waiting on review is current rather than scheduled, and showing
it under every date would say it was.

Each row SHALL carry the issue's key and its summary, so that an issue can be
recognised and named without opening it, and the state the tracker reports it
in, so that issues in different states can be told apart. Where more than one
state is shown, which state an issue is in SHALL be visible without opening it.

A state SHALL be shown as its last word, in lower case. The tracker names its
states in its own phrasing, where the leading words are often shared between
them and the last word is the one that carries the meaning; showing the whole
phrase would need a column too wide to spend on a label that repeats down the
block. Lower case is what every other label in the same column already uses,
so the case a state happens to be written in does not show through.

The column carrying the state SHALL be wide enough for a state label and for
the labels the board's own tasks put in the same column, so that neither kind
is cut.

Two configured states MAY end in the same word. Where they do, their rows are
still told apart by the block's grouping, which follows the configured order
of the states.

#### Scenario: The issues appear among today's tasks

- **WHEN** today is displayed and the tracker reports issues for the configured person
- **THEN** each appears as a row among the day's own tasks, showing its key, its summary and its state

#### Scenario: More than one state at once

- **WHEN** the configured states are more than one and the tracker reports issues in several of them
- **THEN** all of them appear, and each row says which state its issue is in

#### Scenario: A state of more than one word

- **WHEN** a configured state is named with several words
- **THEN** the row shows its last word alone, whether the words that precede it are shared with another state or not

#### Scenario: However the tracker capitalises a state

- **WHEN** configured states differ from each other in how they are capitalised
- **THEN** every state on the board reads in lower case, and no row's state differs in case from another's

#### Scenario: Nothing in the shared column is cut

- **WHEN** today shows tracker rows and the day's own tasks together
- **THEN** every state reads in full, and so does every label the day's own tasks put in the same column

#### Scenario: Two states ending in the same word

- **WHEN** two configured states end in the same word
- **THEN** their rows read alike but still appear in separate groups, in the configured order of the states

#### Scenario: Only today

- **WHEN** any view other than today is displayed
- **THEN** no tracker issue appears in it

#### Scenario: Nothing to show

- **WHEN** the tracker reports no issue in any configured state
- **THEN** today's view shows the day's own tasks and no tracker block

#### Scenario: The day's own tasks are unaffected

- **WHEN** tracker issues are shown
- **THEN** the day's own tasks are exactly those it would show without them, in the same order

#### Scenario: A tracker row is distinguishable from a task

- **WHEN** the block is shown among the day's tasks
- **THEN** a tracker row is marked differently from a task, without relying on colour to tell them apart

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

The assignee, the projects and the states that select the issues SHALL be read
from the environment, so that no login, project name or credential is written
into the board. More than one state SHALL be configurable, and their order
SHALL be the order the block is grouped in.

Where the tracker is not configured, the board SHALL show no tracker block and
SHALL NOT report a failure: a board with no tracker configured is an ordinary
board, not a broken one.

#### Scenario: A tracker is configured

- **WHEN** the tracker is configured and reachable
- **THEN** the issues it reports for that configuration are shown

#### Scenario: Several states are configured

- **WHEN** more than one state is configured
- **THEN** issues in any of them are shown, and none in any other state is

#### Scenario: No tracker is configured

- **WHEN** no tracker is configured
- **THEN** today shows only the day's own tasks, and the board reports no tracker failure

#### Scenario: Configured with a state that no longer exists

- **WHEN** a configured state matches no issue
- **THEN** it simply contributes nothing, and the issues in the other configured states still appear

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no person, no project, no state and no tracker address, and all of them are discovered at run time

### Requirement: The board works when the tracker cannot be reached

Where the tracker cannot be reached or answers with an error, the day SHALL load and behave exactly as it does without a tracker, and the board SHALL say that it could not reach the tracker.

Silence SHALL NOT be acceptable here: an empty block is the ordinary case when nothing is in progress, so a failure that showed nothing would be indistinguishable from a quiet day.

#### Scenario: The tracker is unreachable

- **WHEN** today is displayed and the tracker cannot be reached
- **THEN** the day's own tasks are shown as usual, no tracker block appears, and the board says the tracker could not be reached

#### Scenario: A failure is distinguishable from an empty result

- **WHEN** the tracker cannot be reached and when it reports nothing in progress
- **THEN** the board says something different in each case

#### Scenario: The tracker recovers

- **WHEN** the tracker could not be reached and a person reloads the view once it can be
- **THEN** the issues appear and the board stops saying it could not be reached

### Requirement: The tracker never delays or breaks the day

Fetching the issues SHALL NOT delay the day's own tasks appearing, and a tracker failure SHALL NOT be reported as a failure to load the day.

#### Scenario: The day does not wait for the tracker

- **WHEN** today is loaded
- **THEN** the day's own tasks appear without waiting for the tracker to answer

#### Scenario: A tracker failure is not a failure to load the day

- **WHEN** the tracker fails
- **THEN** the board does not report that today failed to load, and every task action still works

### Requirement: Marking a task as green

A key SHALL add the configured tag to the selected task, and the same key
pressed again SHALL remove it, so that the two states are reached by one key
rather than two.

Because the tag can be taken off again, the action SHALL NOT be confirmed and
SHALL be undoable, unlike filing a task into a project, which cannot be
reversed and therefore is confirmed.

The action SHALL be available wherever a task is selected, and SHALL be
refused on a tracker row, which the board does not own.

Where no tag is configured the key SHALL say so rather than do nothing.

#### Scenario: Marking a task

- **WHEN** a person presses the key on an unmarked task
- **THEN** the task carries the tag, and the board shows it as marked without refetching the view

#### Scenario: Pressing the same key again

- **WHEN** a person presses the key on a task already marked
- **THEN** the tag is taken off and the task returns to how it read before

#### Scenario: Marking is not confirmed

- **WHEN** a person marks or unmarks a task
- **THEN** the board asks nothing first, because the action can be reversed

#### Scenario: Marking can be undone

- **WHEN** a person marks a task and then undoes the last write
- **THEN** the tag is taken off again, and the board says what it undid

#### Scenario: A tracker row cannot be marked

- **WHEN** a person presses the key on a tracker row
- **THEN** the board says the issue lives in the tracker and nothing is written

#### Scenario: No tag is configured

- **WHEN** no tag is configured and a person presses the key
- **THEN** the board says no tag is configured and nothing is written

### Requirement: Taking the mark off is made to stick

Where the store accepts a write that removes the tag and does not apply it —
answering as though it had — the board SHALL make the removal reliable rather
than report a state the store does not hold. A board that shows a task
unmarked while it is still marked where the tasks are kept is worse than a
board that takes a moment longer.

A removal that follows closely on another tag write to the same task SHALL be
held back until it can be relied on. A removal that follows no recent tag
write SHALL NOT be held back: taking the mark off a task marked at some
earlier time is the ordinary case and SHALL go at once.

Holding a write back SHALL NOT hold the board back. The row SHALL lose its
rail immediately, as every other write shows its outcome immediately, and the
board SHALL remain usable throughout, reporting the write as still in flight
the way it reports any other.

#### Scenario: Marking and then unmarking

- **WHEN** a person marks a task and takes the mark off again moments later
- **THEN** the task ends unmarked both on screen and where the tasks are kept

#### Scenario: Taking off a mark set earlier

- **WHEN** a person unmarks a task that was not marked during this sitting
- **THEN** the write is sent at once, with nothing held back

#### Scenario: The board does not wait with it

- **WHEN** a removal is being held back
- **THEN** the row has already lost its rail, the board answers every key, and the write is reported as still in flight

### Requirement: A green task is marked by a star, not by colour

A task carrying the tag SHALL be marked in the margin, before everything else
on its row, by a star that no other row carries. The mark SHALL NOT rely on
colour to be seen, and the colour the tag itself carries SHALL be ignored: a
person may not be able to tell the board's colours apart.

The mark SHALL occupy one cell in every locale, so that the columns beside it
line up wherever the board is run. It stands alone on its row: adjacent
marked tasks read as several marks, not as one joined shape.

The tag's name SHALL NOT be printed on the row. The star says which tasks are
marked, and the row's width is better spent on the task.

#### Scenario: A marked task is distinguishable

- **WHEN** a view holds both marked and unmarked tasks
- **THEN** every marked task carries the star and no unmarked task does, and they can be told apart with colour disregarded

#### Scenario: The mark is one cell wide

- **WHEN** the board is run in any locale
- **THEN** the mark takes one cell, and the columns beside it line up as they would with no mark at all

#### Scenario: Adjacent marked tasks

- **WHEN** several marked tasks are listed one after another
- **THEN** each carries its own star, and they are not required to form a continuous shape

#### Scenario: The tag is not named on the row

- **WHEN** a marked task is shown
- **THEN** its row does not print the tag's name

#### Scenario: The star is shown in every view

- **WHEN** a marked task appears on a calendar day, in the inbox or in the someday view
- **THEN** it carries the star in each of them

### Requirement: Green tasks lead every view

A task carrying the tag SHALL be ordered before every task that does not, in
every view, ranking below only whether a task is finished. Marking a task is
therefore how a person says it comes first, which is what the tag is for.

This SHALL rank above how overdue a task is: an unfinished marked task leads
an unmarked one however overdue the unmarked one has become. A person who
marks a task is saying it outranks the job's backlog, and a rule that let
lateness win would say the opposite.

A finished task SHALL still sink whether it is marked or not, so that the
rail never lifts completed work above what is still to do.

#### Scenario: Marked tasks come first

- **WHEN** a view holds both marked and unmarked unfinished tasks
- **THEN** every marked one is listed above every unmarked one

#### Scenario: Marked outranks overdue

- **WHEN** a marked task is due today and an unmarked task is long past due
- **THEN** the marked task is listed first

#### Scenario: A finished marked task still sinks

- **WHEN** a marked task is finished and unmarked tasks are still open
- **THEN** the finished marked task is listed after the open ones

#### Scenario: A move cannot cross the rail

- **WHEN** a person tries to move an unmarked task above a marked one
- **THEN** it stops at the edge, as it does at any other ordering group

### Requirement: The board reports how many green tasks it is showing

When a view holds tasks carrying the tag, the board SHALL report how many,
beside the counts it already reports rather than instead of any of them. The
count SHALL NOT replace the number of tasks the view holds.

#### Scenario: The count appears beside the others

- **WHEN** a view holds marked tasks, past-due tasks and finished tasks
- **THEN** the board reports all of those counts together, and none replaces another

#### Scenario: Nothing marked

- **WHEN** a view holds no marked task
- **THEN** the board reports no count for them

### Requirement: Which tag counts as green is configured, not built in

The tag SHALL be named in the environment by its identifier, so that no tag
name or identifier is written into the board's source.

The board SHALL read the tag back and confirm what the identifier resolves
to, rather than trusting it. Where the identifier resolves to nothing, the
board SHALL say so and SHALL leave every other part of the view working: a
board with no tag configured, or with one configured wrongly, is an ordinary
board rather than a broken one.

#### Scenario: A tag is configured

- **WHEN** a tag is configured and its identifier resolves
- **THEN** tasks carrying it are marked and ordered first

#### Scenario: No tag is configured

- **WHEN** no tag is configured
- **THEN** no task is marked, the ordering is what it would be without the tag, and the board reports no failure

#### Scenario: The identifier resolves to nothing

- **WHEN** a tag is configured but its identifier names no tag
- **THEN** the board says the configured tag was not found, and every other part of the view still works

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no tag and no tag identifier, and both are discovered at run time

### Requirement: The prompt shows enough of a title to read it

The prompt that adds and renames a task SHALL be wide enough that the great
majority of a person's titles are visible in full while being typed. A person
editing a title they cannot see is guessing at what they are changing.

The prompt SHALL take its width independently of the board's other
dialogues, so that widening it does not stretch a short question, a
confirmation or a picker that reads better narrow.

Where the terminal is too narrow for that width, the prompt SHALL narrow to
fit rather than overflow, and SHALL never be narrower than the terminal can
show.

#### Scenario: A long title is visible while it is typed

- **WHEN** a person adds or renames a task with a title longer than the board's other dialogues would show
- **THEN** the prompt shows it without the beginning scrolling out of view

#### Scenario: The other dialogues are unchanged

- **WHEN** a confirmation, a date picker, a project picker, the focus view or the help overlay is shown
- **THEN** each is exactly as wide as it was before the prompt was widened

#### Scenario: A narrow terminal

- **WHEN** the board runs in a terminal narrower than the prompt's preferred width
- **THEN** the prompt narrows to fit within the terminal, and nothing is drawn outside it

#### Scenario: A title longer than any width

- **WHEN** a title is longer than even the widened prompt can show
- **THEN** the prompt still accepts and returns the whole title, showing as much of it as fits

### Requirement: The board names its terminal tab, and gives the name back

While the board is running, it SHALL ask the terminal to name the tab or
window it occupies, so that the tab holding the board can be found among
others without opening it.

The name SHALL be fixed rather than describing the day shown, the counts, or
the view. A name that changes as work is done is noise where a tab bar is
scanned rather than read, and a fixed name is what makes the tab findable.

When the board exits it SHALL restore the title the terminal had before,
rather than leaving its own name behind or blanking the title. The board is
opened and quit often, and a tab left permanently misnamed is worse than one
that was never named.

The title SHALL be restored however the board exits, including when it exits
by failing. A crash SHALL NOT be the reason a terminal keeps the wrong name.

The board SHALL write nothing when its output is not a terminal, so that a
run whose output is piped or redirected stays free of control sequences.

Where the terminal cannot restore a previous title, the board SHALL still name
the tab while it runs: naming that outlives the board is a smaller fault than
never naming it, and the shell's next prompt commonly replaces the title in
any case.

#### Scenario: The tab is named while the board runs

- **WHEN** the board is started in a terminal
- **THEN** the tab or window it occupies is named for the board

#### Scenario: The name does not change as work is done

- **WHEN** tasks are ticked, added, reordered, or the shown view is changed
- **THEN** the name stays exactly as it was

#### Scenario: Quitting gives the title back

- **WHEN** a person quits the board
- **THEN** the terminal shows the title it had before the board was started

#### Scenario: Failing gives the title back too

- **WHEN** the board exits because of an error rather than being quit
- **THEN** the title is still restored

#### Scenario: Output that is not a terminal

- **WHEN** the board's output is piped or redirected rather than shown in a terminal
- **THEN** nothing is written to name the tab, and the output carries no control sequences

#### Scenario: A terminal that cannot restore the previous title

- **WHEN** the terminal does not support putting a previous title back
- **THEN** the tab is still named while the board runs, and the board does not fail on account of it

### Requirement: The board fits its columns to the terminal

The task list SHALL fit within the terminal it is drawn in, rather than
growing to the width of its longest title and leaving the columns beyond it
off the screen. A person SHALL be able to see every column of a row without
scrolling sideways.

The column holding a task's title SHALL take the width the other columns
leave, so that a wider terminal gives the title more room and a narrower one
gives it less. The widths SHALL follow the terminal as it is resized, not
only as it was when the board started.

Where a title is longer than the width it is given, the board SHALL shorten
it and SHALL show that it has been shortened, so that a person can tell a
title that ends from one that continues. The same SHALL hold for any other
column that must shorten what it shows: no column may cut text and leave it
looking whole.

Shortening a title SHALL NOT damage how it reads. A title carries a link, a
colour when the task is past due, and a strike when it is finished; each
SHALL survive being shortened, and none may appear as raw markup.

The title SHALL NOT be shortened below a width at which it can still be
recognised. Where the terminal is too narrow to give it that much, the board
SHALL keep the minimum and let the list scroll, rather than reducing the
title to something unreadable.

Shortening SHALL be by ending the text early, not by wrapping it onto
further lines: a row is one line, and stays one line.

#### Scenario: A long title no longer pushes the other columns away

- **WHEN** a view holds a task whose title is far longer than the terminal is wide
- **THEN** every column of that row is visible without scrolling sideways

#### Scenario: A shortened title says so

- **WHEN** a title is longer than the room the column gives it
- **THEN** the row shows as much as fits followed by a mark that says the title continues

#### Scenario: A title that fits is untouched

- **WHEN** a title is shorter than the room the column gives it
- **THEN** it is shown in full, with no mark added

#### Scenario: Shortening keeps a title readable

- **WHEN** a shortened title carries a link, or belongs to a past-due task, or belongs to a finished one
- **THEN** the link still opens, the colour and the strike still apply, and no markup is shown as text

#### Scenario: Another column that must shorten

- **WHEN** any other column holds text longer than its width
- **THEN** it too shows that the text was shortened rather than appearing to end where it was cut

#### Scenario: The terminal is resized

- **WHEN** the terminal is made wider or narrower while the board is open
- **THEN** the title column takes the new room, and titles are shortened or shown in full to match

#### Scenario: A terminal too narrow for everything

- **WHEN** the terminal is too narrow to give the title its minimum width
- **THEN** the title keeps that minimum and the list scrolls, rather than the title shrinking further

#### Scenario: A row stays one line

- **WHEN** a title is too long for its column
- **THEN** the row occupies one line, and no part of the title appears on another

### Requirement: The day shows what the calendar holds for it

The board SHALL show, alongside the tasks for the day being viewed, the events
the machine's calendar holds for that same day. Moving to another day SHALL
show that day's events instead: unlike the tracker's issues, which are what is
being worked on now whatever day is shown, an event belongs to a date.

An event SHALL be shown with the time it starts and what it is called, so that
it can be recognised without opening anything. A row SHALL be distinguishable
from a task at a glance, without relying on colour.

Events that repeat SHALL appear on every day they fall on, not only on the day
the repetition was first set. Most of a calendar is repetition, and one that
showed only the first occurrence would be worse than none.

#### Scenario: Today's events appear with today's tasks

- **WHEN** today is shown and the calendar holds events for today
- **THEN** each appears as a row, showing when it starts and what it is called

#### Scenario: Another day shows that day's events

- **WHEN** a person moves to another day
- **THEN** the events shown are that day's, and the previous day's are gone

#### Scenario: A repeating event appears on every day it falls on

- **WHEN** an event repeats and the day being viewed is one it falls on, but not the day it began
- **THEN** it still appears on that day

#### Scenario: A day with no events

- **WHEN** the calendar holds nothing for the day being viewed
- **THEN** the day shows its tasks alone, and nothing announces the absence

#### Scenario: An event is distinguishable from a task

- **WHEN** a day holds both events and tasks
- **THEN** an event's row is marked apart from a task's, and colour is not what distinguishes them

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

### Requirement: An event cannot be changed from the board

No key that writes SHALL act on an event: it can be neither completed,
uncompleted, cancelled, renamed, rescheduled, filed, tagged, reordered nor
deleted. The board reads the calendar and does not own it, and a change shown
here that the calendar never made would be worse than no change at all.

Where a person presses such a key on an event, the board SHALL say why nothing
happened rather than doing nothing silently.

Opening the event's address is not a change and SHALL remain available, as it
does for a tracker issue: reading the calendar includes following what it
points at.

#### Scenario: A key that writes is refused

- **WHEN** a person presses any key that would change a task, with an event selected
- **THEN** nothing is written, and the board says the event belongs to the calendar

#### Scenario: An event is not counted among the tasks

- **WHEN** the board reports how many tasks a day holds
- **THEN** events are not counted among them

#### Scenario: Moving does not reach an event

- **WHEN** a person tries to reorder with an event selected
- **THEN** nothing moves, and the board says why

#### Scenario: Opening is the one key that acts

- **WHEN** an event is selected
- **THEN** the key that opens a link opens its address, and every key that would change it says it is not editable here

### Requirement: Work events are hidden with the rest of the work

An event from the account whose events count as work SHALL be treated as work,
so that the key which hides work hides it too, and the count of what was
hidden includes it. An event from any other configured account SHALL NOT be
hidden by that key.

#### Scenario: Hiding work hides the work account's events

- **WHEN** work is hidden and the day holds events from the work account
- **THEN** they disappear along with the work tasks, and pressing the key again brings them back

#### Scenario: Personal events are not hidden

- **WHEN** work is hidden and the day holds events from an account that is not work
- **THEN** those events stay

#### Scenario: The hidden count includes them

- **WHEN** work is hidden and the board reports how many rows that removed
- **THEN** the work events it removed are included in that count

### Requirement: Which calendar accounts are read is configured, not built in

The accounts whose events are shown SHALL be named in the environment, and
which of them counts as work SHALL be named there too. No account name, and
no calendar name, SHALL appear in the board's source.

Only the named accounts SHALL be read. A machine's calendar holds a great deal
that has nothing to do with a working day, and showing all of it would bury
what matters.

Where no account is configured, the board SHALL show no events and SHALL NOT
report a failure: a board with no calendar configured is an ordinary board.

Where a configured account does not exist, the board SHALL say so rather than
showing an empty day that looks like a free one.

#### Scenario: Only the named accounts are shown

- **WHEN** accounts are configured and the machine holds others besides
- **THEN** only events from the named accounts appear

#### Scenario: No calendar is configured

- **WHEN** no account is configured
- **THEN** no event is shown, and the board reports no failure

#### Scenario: A configured account is missing

- **WHEN** a configured account names nothing on the machine
- **THEN** the board says that account was not found

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no account and no calendar, and both are discovered at run time

### Requirement: The board works when the calendar cannot be read

Reading the calendar needs a permission granted outside the board, which may
be refused, withdrawn, or granted only in part. In any of those cases the
board SHALL show the day's tasks as it always does and SHALL say once that the
calendar could not be read, naming what would put it right.

A permission granted only in part SHALL be treated as no permission rather
than as success: it reads as though it worked while returning nothing, and a
day wrongly showing no events looks exactly like a free one.

The calendar SHALL NOT delay the day. The tasks SHALL appear without waiting
for it, and a calendar that is slow or unavailable SHALL NOT keep them off the
screen.

#### Scenario: Permission is refused

- **WHEN** the board cannot read the calendar because permission was not granted
- **THEN** the day's tasks appear as usual and the board says the calendar could not be read

#### Scenario: Permission granted only in part

- **WHEN** permission allows adding to the calendar but not reading it
- **THEN** the board treats that as unreadable and says so, rather than showing a day with no events

#### Scenario: The day does not wait

- **WHEN** the calendar is slow to answer
- **THEN** the day's tasks are already on screen, and the events join when they arrive

#### Scenario: Recovering without a restart

- **WHEN** the calendar becomes readable again and the view is refreshed
- **THEN** the events appear and the message about not reading it is gone

### Requirement: Opening an event's link

The board SHALL let a person open the web address an event carries, handing it
to the operating system, by the same key that opens a task's link and a
tracker issue's page. A meeting is joined at the moment it starts, and an
address that has to be copied out of another application is an address that
arrives late.

The address SHALL be sought in the event's location first and in its
description second, because a calendar system may put it in either and the
board cannot know which. The first address that may be opened SHALL be the one
opened.

Where an event carries no address, the board SHALL say so and name the row an
event rather than a task.

Opening SHALL change nothing: no calendar is written, and the event is left
exactly as it was.

#### Scenario: Opening the address of the selected event

- **WHEN** a person presses the key that opens a link with an event selected, and that event carries an address
- **THEN** the address is handed to the operating system to open

#### Scenario: The address is found wherever the calendar put it

- **WHEN** an event holds its address in its location, or holds it only in its description
- **THEN** it is opened either way

#### Scenario: The location is preferred where both hold one

- **WHEN** an event holds an address in both its location and its description
- **THEN** the one in the location is opened

#### Scenario: An event with no address

- **WHEN** a person presses that key with an event selected that carries no address
- **THEN** nothing is opened, and the board says the event has no link

#### Scenario: Opening an event changes nothing

- **WHEN** an event's address is opened
- **THEN** nothing about the event changes, and nothing is written to the calendar or to the task store

### Requirement: The description of a selected event is shown

The board SHALL show the selected event's description where it shows a
selected task's note, so that what a meeting is for can be read without
leaving the board or opening the calendar.

An event with no description SHALL show nothing there, exactly as a task with
no note does. The description SHALL be shown whether or not the event carries
an address.

A description SHALL be shown as the text it is. It is written by whoever made
the event and SHALL NOT be interpreted as instructions to the board, nor drawn
in a way that lets its characters change how the rest of the board appears.

#### Scenario: An event with a description

- **WHEN** an event carrying a description is selected
- **THEN** the description is shown in the same area that shows a task's note

#### Scenario: An event with no description

- **WHEN** an event carrying no description is selected
- **THEN** that area is empty, and nothing announces the absence

#### Scenario: A description is shown for an event with no address

- **WHEN** an event carries a description but no address
- **THEN** the description is still shown

#### Scenario: Moving off the event clears it

- **WHEN** a person selects a task after selecting an event
- **THEN** the area shows that task's own note, and no part of the event's description remains

### Requirement: Editing a task's note

The board SHALL let a person edit the selected task's note without leaving the
board. The editor SHALL open holding the note's current text, or empty where
the task has none, and SHALL accept text of several lines.

Saving SHALL store what was written and show it at once, by the same path
every other write takes, so that it can be undone and so that a failure is
reported the way any other failed write is. Leaving without saving SHALL write
nothing.

Saving text that differs in no way from the note already stored SHALL write
nothing, because a write that changes nothing still spends a request and still
occupies the undo history.

Saving an empty note SHALL clear it. A cleared note SHALL be restorable by
undo, like any other write.

The board SHALL NOT require the editor's keys to be typed in any one keyboard
layout, as it does not for any other key it binds.

#### Scenario: Editing a note that exists

- **WHEN** a person opens the editor on a task carrying a note
- **THEN** the editor holds that note's text, and saving stores what was written

#### Scenario: Writing a note where there was none

- **WHEN** a person opens the editor on a task with no note and writes something
- **THEN** the editor was empty, and saving gives the task that note

#### Scenario: A note of several lines

- **WHEN** a person writes a note of more than one line and saves it
- **THEN** every line is stored, and reopening the editor shows them all

#### Scenario: Leaving without saving

- **WHEN** a person opens the editor, changes the text, and leaves without saving
- **THEN** the note is unchanged and nothing was written

#### Scenario: Saving what has not changed

- **WHEN** a person opens the editor and saves without having changed the text
- **THEN** nothing is written

#### Scenario: Clearing a note

- **WHEN** a person empties the editor and saves
- **THEN** the task carries no note, and undo brings the old one back

#### Scenario: The note survives the round trip

- **WHEN** a note is saved and read back from the store
- **THEN** its text is exactly what was written, including its line breaks and any non-ASCII characters

### Requirement: A note the board cannot represent is not rewritten

Where a note carries formatting the board does not represent — styled runs,
line kinds, or anything embedded that is not text — the board SHALL decline to
edit it and SHALL say why.

The board edits a note as text. Saving one of these would mean storing the text
and discarding everything else, and a person who cannot see what was lost
cannot know to object. Declining is worse than editing and better than
destroying.

#### Scenario: A formatted note is refused

- **WHEN** a person opens the editor on a note carrying formatting the board does not represent
- **THEN** the editor does not open, nothing is written, and the board says the note cannot be edited here

#### Scenario: An ordinary note is not refused

- **WHEN** a person opens the editor on a note that is text alone
- **THEN** it opens normally

### Requirement: Only a task's note can be edited

The key that edits a note SHALL act on tasks alone. On a calendar event or a
tracker issue it SHALL refuse at once and say the row is not the board's,
opening nothing — as every other key that would change such a row does.

#### Scenario: An event's description is not editable

- **WHEN** a person presses the note key with an event selected
- **THEN** no editor opens, nothing is written, and the board says the event belongs to the calendar

#### Scenario: A tracker issue's note is not editable

- **WHEN** a person presses the note key with a tracker issue selected
- **THEN** no editor opens, nothing is written, and the board says the issue lives in the tracker
### Requirement: Choosing among several things a task can open

Where the selected task offers more than one thing to open, the board SHALL
ask which one, rather than choosing on a person's behalf. Silently opening the
first leaves the others unreachable and gives no sign that they exist.

The choices SHALL be offered in the order they appear in the task — its title
first, then its note — so that their order needs no rule to be predictable.
Each SHALL be readable enough to be told apart: an issue by its key, an
address by the address.

Leaving without choosing SHALL open nothing and write nothing. Choosing SHALL
open exactly the one chosen.

Where the task offers exactly one thing, it SHALL be opened directly and no
choice SHALL be presented. Where it offers none, the board SHALL say the task
has no link.

#### Scenario: A task offering an issue and an address

- **WHEN** a person asks to open the link of a task whose text holds both a tracker issue key and a web address
- **THEN** the board asks which to open, listing both

#### Scenario: A task offering several addresses

- **WHEN** a person asks to open the link of a task whose text holds more than one web address
- **THEN** the board asks which to open, rather than opening the first

#### Scenario: The order they are offered in

- **WHEN** a task holds one thing to open in its title and another in its note
- **THEN** the one from the title is offered first

#### Scenario: Choosing one

- **WHEN** a person chooses one of the offered items
- **THEN** that one is opened and no other is

#### Scenario: Leaving the choice

- **WHEN** a person leaves the choice without choosing
- **THEN** nothing is opened, and the task is unchanged

#### Scenario: Only one thing to open

- **WHEN** a task offers exactly one thing to open
- **THEN** it is opened at once and nothing is asked
### Requirement: The board shows the current time

The board SHALL show the current time, at the right of its own header, and
SHALL keep it current while it runs. The day's events are read against the
hour, and a board that shows a date but no time withholds the one number
needed to read them.

The time SHALL be shown to the minute. Seconds would move on their own several
times a second in the corner of the eye, for a precision no decision on this
board needs, and every other time the board shows is to the minute.

Keeping the time current SHALL NOT redraw the list. A clock that disturbed the
rows it sits above would cost more than it gave.

#### Scenario: The time is on screen

- **WHEN** the board is running
- **THEN** the current time is shown at the right of its header

#### Scenario: It keeps up

- **WHEN** a minute passes while the board is open
- **THEN** the time shown has followed it

#### Scenario: To the minute

- **WHEN** the time is shown
- **THEN** it reads as hours and minutes, with no seconds

#### Scenario: The list is left alone

- **WHEN** the clock advances
- **THEN** no row is redrawn on account of it, and neither the selected row nor the cursor moves

### Requirement: An event that has ended is shown as past

An event whose end has passed SHALL be drawn receded from the rows still
ahead, so that a day can be read as what is left of it.

The boundary SHALL be the event's end, not its start. An event that has begun
and not ended is one there is still a chance of joining, and showing it as
past would say there was not.

Receded SHALL NOT be expressed as a colour alone. The row cursor replaces a
cell's colour, so a hue is absent exactly when a row is selected — which is
why a past-due task carries its age as well as its colour. Whatever expresses
this SHALL survive being selected.

An event that has ended SHALL keep everything else about its row: its mark,
the time it starts, what it is called, and the calendar it came from. It is
receded, not hidden and not struck out; nothing about it has been completed.

This SHALL hold on whatever day is shown, judged against the current time
rather than against the instant the day was loaded. On a day already past,
every event has ended; on a day to come, none has.

The board SHALL keep this true as time passes, redrawing when the set of ended
events changes. It SHALL NOT redraw when that set is unchanged, and SHALL NOT
fetch anything to decide it.

#### Scenario: An event that is over

- **WHEN** today holds an event whose end has passed
- **THEN** its row is drawn receded from the events still to come

#### Scenario: An event under way

- **WHEN** today holds an event that has started and not yet ended
- **THEN** it is not shown as past, because there is still a chance of joining it

#### Scenario: An event still to come

- **WHEN** today holds an event that has not started
- **THEN** it is drawn as an ordinary event

#### Scenario: Selected and still legible

- **WHEN** an event that has ended is the selected row
- **THEN** it is still distinguishable from the events still to come

#### Scenario: Nothing else about the row changes

- **WHEN** an event has ended
- **THEN** its mark, its start time, its name and its calendar are shown as they are for any other event, and it is neither hidden nor struck out

#### Scenario: A day already behind

- **WHEN** a day earlier than today is shown
- **THEN** every event on it is shown as past

#### Scenario: A day still ahead

- **WHEN** a day later than today is shown
- **THEN** no event on it is shown as past

#### Scenario: The hour passes while the board is open

- **WHEN** an event's end passes while the board is open
- **THEN** its row becomes receded without the day being fetched again

#### Scenario: Nothing changes, nothing is redrawn

- **WHEN** time passes and no event's end has been crossed
- **THEN** no row is redrawn, and the selected row is where it was
### Requirement: The board reads named folders from a directory of maildirs

The board SHALL read messages from the folders named in the environment,
found inside a directory named there too. Reading SHALL make no network call
and need no credentials.

The path SHALL name a directory that holds maildirs, and each named folder
SHALL be one of them: a directory of that name beside the others. This is the
layout the sync tool that fills it writes. The path is not itself a maildir
and the board SHALL NOT try to read it as one.

The board SHALL read the named folders and no others. What wants processing
daily is a few folders rather than every message an account has ever held,
and reading only those is what keeps the queue a queue. Where no folder is
named, the board SHALL show no mail and SHALL NOT report a failure: naming
none is how a person turns mail off.

Within those folders the board SHALL read the messages not yet marked read.
A queue is what has not been dealt with; a message already read has been dealt
with, whether here or in the program the person reads mail with, and showing
it again would make the queue a list of everything instead.

Where a named folder does not exist, the board SHALL say so rather than
passing over it in silence: an empty queue and a misspelt folder look
identical on screen and mean opposite things.

How mail arrives in that directory SHALL NOT be the board's concern. A sync
tool, a mail client, an export — whichever a person uses, and whichever they
change to, the board reads the same directory. This is why the directory is
the boundary rather than a protocol.

The board SHALL alter nothing in the local mailbox at all: no flag, no name,
no folder, no content. Not even to record that a message has been reviewed —
that is recorded on the server, where it is authoritative, and a message moved
by hand in a mirrored maildir is documented to break the sync that fills it.

Where no mailbox is configured, the board SHALL show no mail and SHALL NOT
report a failure. A board without one is an ordinary board.

Where a mailbox is configured but cannot be read, the board SHALL say so once
and SHALL otherwise carry on: the day's tasks, the tracker and the calendar
SHALL be unaffected.

#### Scenario: Messages are read from the named folders

- **WHEN** a directory of maildirs is configured and folders are named in it
- **THEN** the board reads their messages, and makes no network call to do so

#### Scenario: A folder is a directory beside the others

- **WHEN** a folder is named in the environment
- **THEN** it is found as a directory of that name, not as a dot-prefixed subdirectory

#### Scenario: Only the named folders are read

- **WHEN** the directory holds folders beyond those named
- **THEN** messages from the named folders appear and messages from the others do not

#### Scenario: No folder named means no mail

- **WHEN** a directory is configured but no folder is named
- **THEN** the board shows no mail and reports no failure

#### Scenario: The path is not read as a mailbox itself

- **WHEN** the configured directory holds maildirs but is not one
- **THEN** the board reads the named folders and does not report the directory unreadable

#### Scenario: A folder that does not exist

- **WHEN** a named folder is not in the directory
- **THEN** the board says so rather than showing a queue quietly missing it

#### Scenario: A message already read is not in the queue

- **WHEN** a message in a named folder is marked read
- **THEN** it does not appear, whether it was read here or in another program

#### Scenario: Nothing is written to the mailbox

- **WHEN** the board has read the mailbox, and a person has reviewed and promoted messages in it
- **THEN** no message's flags, name, folder or content have changed on disk

#### Scenario: No mailbox configured

- **WHEN** no directory is configured
- **THEN** the board shows no mail and reports no failure

#### Scenario: A mailbox that cannot be read

- **WHEN** a directory is configured but missing, unreadable, or holds no named folder
- **THEN** the board says so once and the rest of the board works as it did

#### Scenario: A message the board cannot make sense of

- **WHEN** one message in a folder cannot be parsed
- **THEN** the others are still shown, and the unreadable one does not take the view down with it

### Requirement: Messages are grouped into threads

Messages SHALL be grouped into threads, and a thread SHALL be one row. A
notification system sends one message per event, so a view of messages is a
feed; a view of threads is a list a person can read.

Grouping SHALL follow the headers that exist for it, each message being joined
to the one it answers, and a chain being followed to its start.

Grouping SHALL NOT fall back to matching subjects. Unrelated messages share a
subject often — a digest, a recurring report — and merging those would hide
messages rather than tidy them. A message whose headers place it in no thread
SHALL be a thread of its own.

A thread SHALL be ordered among the others by its newest message, so that what
moved most recently reads first.

#### Scenario: A run of notifications about one thing

- **WHEN** a mailbox holds several messages that answer one another
- **THEN** they appear as a single row, not as one row each

#### Scenario: A message that answers nothing

- **WHEN** a message's headers place it in no thread
- **THEN** it appears as a row of its own

#### Scenario: Two unrelated messages sharing a subject

- **WHEN** two messages share a subject but neither answers the other
- **THEN** they remain separate rows

#### Scenario: The newest decides where a thread sits

- **WHEN** several threads are shown
- **THEN** they are ordered by the arrival of each thread's newest message, newest first

### Requirement: Messages about one issue fold into one row

Messages that are about the same thing SHALL be shown as one row. A person
reviewing a tracker's notifications is deciding about an issue, not about each
comment on it: the real folders hold 1,056 messages standing for 199 issues,
and a row per message asks the same question five times over.

Two messages SHALL be folded together when both hold true:

- their subjects name the same issue in a configured tracker project, and
- the first address each carries is the same.

Both conditions, not either. The first alone is not enough: in one of the
folders read daily, mail about a merge request names the issue it mentions, so
several unrelated requests cite one issue — folding on the name alone merged
24 of 38 groups wrongly. Requiring that they also point at the same place is
what makes the rule safe, and it validates itself against the data rather than
against a list of folder names somebody has to maintain.

A configured project's key SHALL be what is recognised, not a general pattern
for letters-dash-digits. That pattern also matches a version or a standard,
and the board already has one place that knows which projects count.

Where the rule does not apply, messages SHALL be grouped as they are today, by
the headers that say which message answers which. A folder whose subjects name
no issue SHALL therefore be unchanged by this.

A folded row SHALL report how many messages it stands for, as a row already
does.

#### Scenario: Updates about one issue are one row

- **WHEN** several messages name the same issue in a configured project and carry the same first address
- **THEN** they appear as a single row, reporting how many messages it stands for

#### Scenario: The same issue in unrelated mail is not folded

- **WHEN** two messages name the same issue but carry different first addresses
- **THEN** they remain separate rows

#### Scenario: A general pattern is not mistaken for an issue

- **WHEN** a subject carries letters, a dash and digits that are not a configured project's issue
- **THEN** no folding happens on it

#### Scenario: A folder that names no issues is unaffected

- **WHEN** a folder's subjects name no configured project's issue
- **THEN** its messages are grouped exactly as they were before this

### Requirement: Mail is shown in the inbox

Mail SHALL be shown in the inbox view, which is the board's queue of things
that have arrived and not been decided about. A message needing a decision and
an undated task needing one are the same kind of thing at the same cadence,
and two queues asking that question separately would be worse than one.

Mail SHALL NOT appear among a day's rows. A day holds what has been promised.

The inbox's tasks SHALL lead its mail rows. Mail arrives in far greater
quantity than a person files tasks — some 460 rows against 35 — so putting it
first buries one's own work behind a scroll of somebody else's notifications.
The reasoning that once put mail at the top, that processing should start there
rather than after a scroll, argues for this order once the mail is real.

Mail SHALL NOT take part in the ordering of tasks, and removing every mail row
from the inbox SHALL leave its tasks in precisely the order the rules for
tasks give them.

The inbox SHALL report how many rows of mail it is showing and how many
messages they stand for, beside what it already reports about tasks, so the
size of each queue is visible without counting rows.

#### Scenario: Mail is in the inbox

- **WHEN** a person asks for the inbox and the mailbox holds messages
- **THEN** the rows appear there, below the tasks awaiting triage

#### Scenario: A day holds no mail

- **WHEN** any day is shown
- **THEN** no mail row appears in it

#### Scenario: Someday holds no mail

- **WHEN** the someday view is shown
- **THEN** no mail row appears in it

#### Scenario: The inbox's tasks keep their own order

- **WHEN** the inbox holds mail and tasks together
- **THEN** disregarding the mail leaves the tasks in exactly the order they would have had alone

#### Scenario: Both queues are counted

- **WHEN** the inbox is shown with mail and tasks in it
- **THEN** it reports how many rows of mail and how many messages, beside what it reports about tasks

#### Scenario: An inbox with no mail at all

- **WHEN** no mailbox is configured, or it holds nothing
- **THEN** the inbox is exactly the view it was before, tasks and counts alike

#### Scenario: A person's own work is reachable without scrolling

- **WHEN** the inbox holds far more mail rows than tasks
- **THEN** the tasks are at the top of the view, where the cursor starts

### Requirement: What a mail row shows

A mail row SHALL show when its newest message arrived, who it is from, what it
is about, and — where the thread holds more than one message — how many.

The row SHALL be distinguishable from a task at a glance, and not by colour
alone, as a calendar event's row and a tracker issue's row already are.

Where a sender or a subject is longer than its column, it SHALL be shortened
rather than pushing the row's other columns off the screen.

A subject SHALL be shown as the text it is. It is written by whoever sent the
message and SHALL NOT be interpreted as instructions to the board, nor drawn
in a way that lets its characters change how the rest of the board appears.

#### Scenario: A thread of several messages

- **WHEN** a thread holds more than one message
- **THEN** its row shows the newest arrival, the sender, the subject, and how many messages there are

#### Scenario: A thread of one

- **WHEN** a thread holds a single message
- **THEN** its row shows the same things, without a count

#### Scenario: A mail row is not mistaken for a task

- **WHEN** the inbox is shown with mail in it
- **THEN** a mail row is marked apart from a task's row, and colour is not what distinguishes them

#### Scenario: A subject with markup characters in it

- **WHEN** a subject contains square brackets or text that reads as markup
- **THEN** every character appears as sent, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A subject too long for its column

- **WHEN** a subject is longer than the room the column has
- **THEN** it is shortened, and no other column is pushed off the screen

### Requirement: What a message says is shown when its row is selected

The board SHALL show what the selected thread's newest message says, where it
shows a selected task's note. A subject alone says a build failed; the message
says which build and what broke, and a queue triaged without that is triaged
by guessing.

The message's own words SHALL be shown, without its subject repeated: the
subject is already the row's title, and showing it again at the head of the
body reads as a mistake.

It SHALL be shown as the text it is. A message is written by somebody else and
SHALL NOT be interpreted as instructions to the board, nor drawn in a way that
lets its characters change how the rest of the board appears.

Where a message carries only HTML, the board SHALL show it as readable text
rather than showing nothing. Notification mail is often HTML alone, so a board
that read only the plain part would be blank for exactly the messages most
worth looking at. Where a message carries both, the plain part SHALL be
preferred, being what the sender wrote for reading as text.

Turning HTML into text SHALL keep the addresses it carries. The markup holds
the address while the words hold only the link's text, so a rendering that
dropped them would leave nothing for the board to open on precisely the mail
most likely to have something to open.

A message with nothing in its body SHALL show nothing there, as a task with no
note does. Moving to another row SHALL show that row's own note or message,
with nothing of the previous one left.

#### Scenario: What a notification says

- **WHEN** a mail row is selected and its newest message has a body
- **THEN** that body is shown where a task's note is shown

#### Scenario: The subject is not repeated

- **WHEN** a mail row is selected
- **THEN** the subject appears as the row's title and not again at the head of the body

#### Scenario: A message written to look like markup

- **WHEN** a message's body contains square brackets or text that reads as markup
- **THEN** every character appears as sent, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A message carrying only HTML

- **WHEN** a mail row is selected whose newest message has no plain part, only HTML
- **THEN** the message is shown as readable text rather than as nothing

#### Scenario: A message carrying both

- **WHEN** a message has a plain part and an HTML part
- **THEN** the plain part is what is shown

#### Scenario: The addresses in HTML survive being made readable

- **WHEN** an HTML-only message carries addresses in its markup
- **THEN** those addresses are among what the row can open

#### Scenario: HTML that will not parse

- **WHEN** a message's HTML is malformed
- **THEN** the row is still shown, with whatever text could be read from it

#### Scenario: A message with an empty body

- **WHEN** a mail row is selected whose newest message has no body
- **THEN** that area is empty, and nothing announces the absence

#### Scenario: Moving off a mail row

- **WHEN** a person selects a task after selecting a mail row
- **THEN** the task's own note is shown, and no part of the message remains

### Requirement: What a mail thread points at can be opened

The board SHALL let a person open what a mail row points at, by the key
that already opens a task's link, a tracker issue's page and a calendar
event's address.

Where the row's messages carry an address with a fragment — an address that
names a place *within* a page — the earliest such address SHALL be what is
offered. A person opening a discussion of thirty comments wants to begin where
they left off and read downward, not to land at the newest remark and scroll
up. Measured on the real folders, the earliest and the latest such address
differ in 75 of 121 folded rows, so this is not a distinction without a
difference.

Where no message in the row carries such an address, the candidates SHALL be
taken from the row's newest message rather than from all of them. A run of
notifications about one thing carries one near-identical address per message —
four builds of a job give four console addresses differing only in a number —
and offering every one would ask a person to choose between things they cannot
tell apart. The folder where that reasoning was formed carries no fragments at
all, so it keeps exactly the behaviour it has.

Where the row's text names an issue in a configured tracker project, that
issue SHALL be among what can be opened, by the same rule that applies to a
task.

Where more than one thing can be opened, the board SHALL ask which, as it
already does for a task. Where nothing can be, it SHALL say so.

#### Scenario: Opening a notification's link

- **WHEN** a person opens the selected mail row and it points at one thing
- **THEN** that thing is opened

#### Scenario: A run of near-identical addresses

- **WHEN** a row stands for several notifications about one thing, none of them carrying a fragment
- **THEN** one address is offered, the newest message's, rather than one per message

#### Scenario: The earliest anchored address wins

- **WHEN** a row's messages carry addresses with fragments
- **THEN** the earliest of them is what is offered

#### Scenario: A row with no anchored address falls through

- **WHEN** no message in the row carries an address with a fragment
- **THEN** the newest message's addresses are offered, as before

#### Scenario: A thread naming a tracker issue

- **WHEN** the row's text names an issue in a configured project
- **THEN** that issue's page is among what can be opened

#### Scenario: A thread with nothing to open

- **WHEN** a row carries no address and names no configured issue
- **THEN** the board says there is nothing to open

### Requirement: A mail row cannot be changed from the board

No key that writes to the task store SHALL act on a mail row: it can be
neither cancelled, renamed, rescheduled, filed, tagged, reordered nor deleted,
and its note cannot be edited. The board does not own the message.

Two keys SHALL act on a mail row, and only these two: the one that opens what
it points at, and the one that ticks it — which reviews the message and takes
it out of the mailbox, as that requirement states. Neither changes the row into
something the board owns; the first reads it and the second files it away.

Where a person presses any other writing key on a mail row, the board SHALL
say why nothing happened rather than doing nothing silently.

#### Scenario: A key that writes is refused

- **WHEN** a person presses a key that renames, reschedules, files, tags, reorders, cancels or deletes, with a mail row selected
- **THEN** nothing is written and the board says the row is not the board's to change

#### Scenario: Nothing is asked before refusing

- **WHEN** such a key would normally ask for a date, a name or a confirmation
- **THEN** the board refuses first and asks nothing

#### Scenario: Opening is the one key that acts

- **WHEN** a person opens what a mail row points at
- **THEN** it opens, because reading is not a change

#### Scenario: Ticking reviews rather than completes

- **WHEN** a person ticks a mail row
- **THEN** the message is reviewed and archived, and no task is completed

#### Scenario: A mail row is not counted among the tasks

- **WHEN** the inbox holds mail and tasks together
- **THEN** the task counts count tasks alone

### Requirement: The mailbox never delays or breaks the board

Reading the mailbox SHALL NOT delay any other view. A day's tasks SHALL appear
without waiting for it, and a mailbox that is slow, missing or unreadable
SHALL NOT keep them off the screen.

A mailbox large enough to be slow to read SHALL NOT make the board
unresponsive while it is read.

Acting on the mailbox SHALL NOT break the board either. An operation on the
account SHALL fail in exactly one way as far as the board is concerned: the
operation is reported as having failed, and the session continues. A
connection lost part way through — the gateway closing the line mid-command,
a socket error, anything the protocol underneath can raise — SHALL be that
same failure, and SHALL NOT end the session. It is the most likely way an
operation on this account fails, not an exceptional one: an operation stays
open for tens of seconds, and the longer it is open the better its chance of
being cut.

Where an operation fails after part of its work has been done, the board SHALL
report the failure rather than the part that succeeded, and SHALL NOT undo
what was confirmed. Half a review is a row a person must look at again, which
they can do; mail moved with no record of it is work lost, which they cannot.

#### Scenario: A day does not wait for the mailbox

- **WHEN** a day is opened while the mailbox is being read
- **THEN** the day's tasks are on screen without waiting for it

#### Scenario: An unreadable mailbox leaves the day alone

- **WHEN** the mailbox cannot be read
- **THEN** the day shows its tasks as it always does, and the failure is reported as the mailbox's, not the day's

#### Scenario: A large mailbox does not freeze the board

- **WHEN** the mailbox holds far more messages than a person would read
- **THEN** the board stays responsive while it is read

#### Scenario: A connection lost part way through a review

- **WHEN** the connection is lost part way through reviewing a row
- **THEN** the row returns to the queue, the failure is reported as the mailbox's, the log records it with the folder and how long it took, and the board is still running

#### Scenario: A connection lost part way through an undo

- **WHEN** the connection is lost part way through putting a reviewed row back
- **THEN** the failure is reported, the log records it, and the board is still running

#### Scenario: What was already done stays done

- **WHEN** some of a row's messages have been archived and confirmed and then the connection is lost
- **THEN** those messages stay archived, the row is reported as failed, and nothing is moved back to make the report tidy
### Requirement: A mail thread can be turned into a task

The board SHALL let a person turn the selected mail thread into a task on
today, so that a message which turns out to be work joins the day's
commitments rather than being remembered.

The task SHALL be titled from what the thread is about. A title a person did
not choose is better than no task, and it can be renamed by the key that
renames any task.

The task SHALL be created the way every task the board creates is created:
shown at once, sent behind the screen, reversible by undo, and reported if it
fails. Promoting SHALL NOT be a special path through the board's writing.

Promoting SHALL act on a mail thread alone. On any other row the board SHALL
say so and create nothing.

#### Scenario: A thread becomes a task

- **WHEN** a person promotes the selected mail thread
- **THEN** a task appears on today, titled from what the thread is about

#### Scenario: It is shown before the store has answered

- **WHEN** a thread is promoted
- **THEN** the task is on screen without waiting for the store, as any added task is

#### Scenario: Promoting can be undone

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the task is removed, and the board says what it reversed

#### Scenario: A failed promotion is reported

- **WHEN** promoting is refused by the store
- **THEN** the board says so, and does not leave a task on screen that does not exist

#### Scenario: Promoting acts on mail alone

- **WHEN** a person presses the key on a task, a calendar event or a tracker issue
- **THEN** nothing is created, and the board says what the key is for

### Requirement: Reviewing a message takes it out of the mailbox

The board SHALL let a person mark the selected mail row reviewed, by the key
that ticks a task, and SHALL then move every message the row stands for to the
account's archive folder.

Moving is what makes a reviewed message not come back. The folder it was in is
mirrored locally; the archive is not. So an archived message has nowhere to
return from, where a flag on a local file only says that one program has seen
it.

The move SHALL be made on the server, addressed by each message's own
identity. Once the archive is confirmed, the messages SHALL be marked read —
the one flag the board sets anywhere, and only on messages it has confirmed
are in the archive. A queue is what has not been dealt with; a reviewed
message the account still calls new is not that, and every other program
reading the account would show it as new mail.

Beyond that move and that flag the board SHALL change nothing about the
account: no message SHALL be deleted, and none SHALL be moved anywhere but
the archive.

Where a row stands for several messages, all of them SHALL be moved. A row
that is one decision must not leave half its mail behind to be decided again.

The board SHALL show the row gone at once and do the moving behind the screen,
as it does for every write it makes.

Promoting a thread to a task SHALL archive it too. One review, one outcome: a
message that became a task has been dealt with as surely as one that was
merely read.

#### Scenario: A reviewed row leaves the inbox

- **WHEN** a person ticks the selected mail row
- **THEN** the row goes at once, and its messages are moved to the archive

#### Scenario: Every message in a folded row is archived

- **WHEN** a row standing for several messages is reviewed
- **THEN** all of them are moved, not only the newest

#### Scenario: Promoting archives as well

- **WHEN** a thread is turned into a task
- **THEN** its messages are archived, and the task is created

#### Scenario: Nothing is deleted, and nothing goes elsewhere

- **WHEN** the board has reviewed and promoted messages
- **THEN** no message has been deleted and none has been moved to any folder but the archive

#### Scenario: A reviewed message is marked read

- **WHEN** a row's messages are confirmed in the archive
- **THEN** they are marked read, in one request, and no flag is set anywhere but the archive

#### Scenario: An unconfirmed archive marks nothing read

- **WHEN** the archive cannot be confirmed
- **THEN** no message has been marked read

### Requirement: An archive is confirmed before a row is retired

The board SHALL confirm an archive before treating the row as gone: the
messages SHALL be absent from the folder they were in and present in the
archive. Both, because a move that removed mail without delivering it is the
one outcome that loses work, and the gateway this speaks to has been found
violating its protocol elsewhere.

Where a message is already absent from its folder, the board SHALL ask the
archive before concluding anything. Found there, the review has already
happened and SHALL be reported as done rather than as an error. Found in
neither, the board SHALL say so: something moved that message, and it was not
the board.

Where the archive cannot be confirmed, the row SHALL come back and the board
SHALL say why. A row retired on an unconfirmed move is a message a person
believes they have dealt with.

Undoing a review SHALL move the messages back to the folder they came from
and SHALL mark them unread again, or the row would return to a queue that no
longer counts it. The board SHALL say that the row returns only once the
mirror next catches up, and SHALL NOT pretend the row is back before it is.

#### Scenario: A confirmed archive retires the row

- **WHEN** the messages are absent from their folder and present in the archive
- **THEN** the row stays gone

#### Scenario: An unconfirmed archive brings the row back

- **WHEN** the archive cannot be confirmed
- **THEN** the row returns and the board says why

#### Scenario: A message already archived

- **WHEN** a message is not in its folder and is found in the archive
- **THEN** the review is reported as already done, not as a failure

#### Scenario: A message in neither place

- **WHEN** a message is in neither its folder nor the archive
- **THEN** the board says so rather than reporting success

#### Scenario: Undoing a review puts the mail back

- **WHEN** a person undoes a review
- **THEN** the messages are moved back to the folder they came from, unread again, and the board says the row returns when the mirror next catches up

### Requirement: A promoted task carries the message it came from

The created task SHALL carry, in its note, what the thread's newest message
said and the identity of that message.

What it said, because a task reading "Build failure" is a reminder where one
that still holds the message is the work — and because the addresses a
notification carries are in its own text, so the key that opens a task's link
reaches the build, the merge request or the issue through the note without
anything further being extracted.

The identity, so that the message this task came from can still be found in
the mailbox afterwards. It is what makes the task traceable to its origin
rather than merely descriptive of it.

Where the message said nothing, the task SHALL still be created, carrying the
identity alone. The decision that something is work does not depend on there
being anything to read.

The note SHALL be written in the form the board already writes notes, so that
the key which edits a note can edit this one, and SHALL be shown as the
characters it contains.

#### Scenario: The note carries the message and the identity

- **WHEN** a thread whose newest message has a body is promoted
- **THEN** the created task's note holds that body and the identity of the message

#### Scenario: The task opens what the message pointed at

- **WHEN** a promoted task is selected and the key that opens a link is pressed
- **THEN** the thing the message pointed at is opened, found in the note

#### Scenario: A message that said nothing

- **WHEN** a thread whose newest message has an empty body is promoted
- **THEN** the task is still created, with a note carrying the identity alone

#### Scenario: The note can be edited afterwards

- **WHEN** a person edits the note of a promoted task
- **THEN** it opens in the editor holding what was written, like any other note

#### Scenario: A message written to look like markup

- **WHEN** a promoted message's body contains square brackets or text that reads as markup
- **THEN** the task's note shows every character as sent, applies no styling by it, and leaves the rest of the board as it was

### Requirement: Promoting takes the thread out of the queue

Promoting SHALL archive every message in the row, by the same means and with
the same confirmation as reviewing one, so that the row leaves the inbox for
the same reason. A queue that cannot be drained from the board is a queue that
will be drained somewhere else, which defeats having it on the board.

Archiving, and marking the archived messages read, SHALL be the only changes
made to the account: no message SHALL be deleted, and none SHALL be moved
anywhere but the archive. Nothing SHALL be written to the local mailbox at
all.

The task SHALL be created before the messages are archived, and a failure to
archive SHALL NOT undo the task. A task whose mail is still in the folder is a
row that appears once more; mail archived with no task made is work lost, and
of the two only the first can be put right by a person who can see what
happened.

Where the archive cannot be reached, the board SHALL say so and SHALL leave
the created task alone.

The board SHALL draw no row from anything it wrote itself. Every row comes
from a source, and the account is the record of what has been promoted; the
board SHALL keep no record it reads back, on disk or anywhere else.

A log of what the board did is not such a record. Nothing reads it, no row
depends on it, and deleting it SHALL change nothing the board shows. That is
what makes it safe to keep, and it is required separately.

#### Scenario: The thread leaves the queue

- **WHEN** a thread is promoted
- **THEN** its messages are archived, and the row is gone from the inbox

#### Scenario: Undoing a promotion returns the thread

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the created task is removed and the messages are moved back to the folder they came from

#### Scenario: Nothing else about the mailbox changes

- **WHEN** a thread has been promoted
- **THEN** no message has been deleted, none has moved anywhere but the archive, no flag has been set outside it, and nothing on disk has changed

#### Scenario: The task survives a mailbox that cannot be written

- **WHEN** the archive cannot be reached and a thread is promoted
- **THEN** the task is still created, and the board says the mail could not be archived

#### Scenario: Nothing is remembered

- **WHEN** a thread has been promoted
- **THEN** the board has written no record of it anywhere but the account itself

#### Scenario: The log is not a record the board reads

- **WHEN** the board's log of what it did to the mailbox is deleted while the board is not running
- **THEN** the next run shows exactly the rows it would have shown anyway

### Requirement: The board shows whether the mailbox is busy

Reviewing a mail row is the slowest thing the board does — measured at about 13 seconds for a row of one message and 25 seconds a message for a folded one — and reviews are done one at a time, so ticking several leaves the later ones waiting. The board SHALL show whether any of that work is in flight, so that a person can tell whether what they have ticked has landed before they tick more or leave.

The indication SHALL be one cell at the right of the day bar, shown in every view. Mailbox work outstands regardless of which view is being looked at, and whether it is safe to quit is the same question in all of them.

It SHALL distinguish three things:

- that nothing is in flight and nothing has failed,
- that something is in flight,
- that something has failed since the person last asked for a reload.

The in-flight state SHALL be animated. A still mark cannot be told from a stuck one, and these operations last tens of seconds; motion is the information. The animation SHALL run only while work is in flight, and SHALL NOT redraw the list — by the same rule the clock follows, a mark that disturbed the rows above it would cost more than it gave.

The failed state SHALL persist until the person asks for a reload or restarts the board. It SHALL NOT be cleared by a later operation succeeding: a failure among ten reviews would otherwise be painted over before it was seen, which is the fault this exists to fix.

The indication SHALL return to its untroubled state whenever the last operation finishes, whichever way it finished. A mark that stayed busy after the work stopped would tell a person to wait for nothing, which is worse than showing nothing at all.

#### Scenario: Nothing in flight

- **WHEN** no mailbox operation is running and none has failed
- **THEN** the day bar's right cell shows that nothing is outstanding

#### Scenario: An operation running

- **WHEN** a person ticks a mail row and its archiving is under way
- **THEN** the cell shows work in flight, and keeps moving while it lasts

#### Scenario: Several ticked in succession

- **WHEN** a person ticks several mail rows faster than they can be confirmed
- **THEN** the cell shows work in flight until the last of them has finished

#### Scenario: Back to rest

- **WHEN** the last outstanding operation finishes
- **THEN** the cell shows that nothing is outstanding, and stops moving

#### Scenario: Every way an operation can end

- **WHEN** an operation ends by being confirmed, by failing to confirm, by finding the message already archived, by finding it in neither place, by the gateway being unreachable, or by giving up because the board is closing
- **THEN** the cell stops showing that operation as in flight in every one of those cases

#### Scenario: A failure is shown until it is acknowledged

- **WHEN** an operation fails and later operations succeed
- **THEN** the cell still shows that something has failed

#### Scenario: A reload clears it

- **WHEN** a person asks for a reload after a failure
- **THEN** the cell shows that nothing is outstanding again

#### Scenario: The animation does not disturb the list

- **WHEN** the cell is animating while work is in flight
- **THEN** no row is redrawn on account of it, and neither the selected row nor the view's position moves

#### Scenario: Shown in every view

- **WHEN** mailbox work is in flight and a person moves between a day, the inbox and the someday view
- **THEN** the cell is shown in each of them

### Requirement: Quitting asks while the mailbox is busy

Where mailbox work is in flight, quitting SHALL ask first, saying how much is outstanding. Quitting mid-queue abandons the reviews that have not started; nothing is lost, because they moved nothing, but the rows return at the next start and are then indistinguishable from a message the local mirror has not caught up on.

Where nothing is in flight, quitting SHALL NOT ask. A question asked every time is a question that stops being read.

Declining SHALL leave the board exactly as it was, with the work still running.

Nothing here SHALL make a forced end fail: where the board is ended without being asked, an operation part way through SHALL still give up cleanly, as it already does.

#### Scenario: Quitting with work in flight

- **WHEN** a person asks to quit while mail is being archived
- **THEN** the board asks first, saying how much is outstanding

#### Scenario: Declining

- **WHEN** a person declines that question
- **THEN** the board is still running, still showing what it was, and the work is still under way

#### Scenario: Confirming

- **WHEN** a person confirms it
- **THEN** the board ends

#### Scenario: Quitting with nothing in flight

- **WHEN** a person asks to quit and no mailbox work is outstanding
- **THEN** the board ends without asking

### Requirement: The board logs what it does to the mailbox

The board SHALL write a log of every operation it performs on the mail account: what was attempted, on which folder, how many messages, how long it took, and how it ended. The mailbox is the one place the board changes something it cannot change back on its own, and a failure there is announced in a notice that the next notice replaces — so what happened SHALL be recoverable afterwards rather than only at the moment it happened.

The log SHALL be a file, off screen. The board SHALL NOT offer a view of it: it is for reading after the fact with whatever a person reads files with.

Each entry SHALL carry the time in a form that sorts and is unambiguous, a level saying whether the entry is ordinary, a warning, or a failure, and one line saying what happened. Successful operations SHALL be logged as well as failures, so that the sequence and the timings can be read, not only the faults.

The log SHALL record message identities, folder names, counts and durations. It SHALL NOT record a subject, a sender, or any part of a message's body: the file is durable and sits outside the mail store, and an identity is both what the gateway addresses a message by and what a person would search on.

Writing the log SHALL be best-effort. A log that cannot be written — a missing directory, a full disk, a permission — SHALL NOT change what the board does or fail an operation. Losing a log entry is a smaller harm than losing a review.

The log SHALL NOT be committable: it holds identities and folder names from a real account, and the repository is a place that gets shared.

#### Scenario: An operation is logged

- **WHEN** a mail row is reviewed and confirmed
- **THEN** the log holds an entry saying what was attempted and one saying how it ended, each with a time, a level and a duration

#### Scenario: A failure is logged

- **WHEN** an archive cannot be confirmed
- **THEN** the log holds an entry marked as a failure, saying which folder and how many messages, and why

#### Scenario: Nothing identifying is written

- **WHEN** any operation is logged
- **THEN** the entry holds no subject, no sender and no part of any message body

#### Scenario: A log that cannot be written

- **WHEN** the log cannot be written at all
- **THEN** every operation behaves exactly as it would have, and nothing is reported to the person about the log

#### Scenario: The log is not committable

- **WHEN** the repository is inspected for what it would commit
- **THEN** the log is excluded, and no entry from it is in anything tracked

### Requirement: An unhandled failure leaves a file behind

Where a failure the board does not handle ends the session, the board SHALL
write that failure to a file before it goes. A traceback printed to the
terminal survives only as long as the scrollback and only if someone thought
to save it; the board acts on a real mail account over a gateway that drops
connections, so the evidence of a failure SHALL outlive the session that
produced it.

The file SHALL sit in the same directory as the log of what the board does to
the mailbox, and SHALL be written on the same best-effort terms: a file that
cannot be written SHALL NOT change how the session ends, and SHALL NOT be
reported to the person as a second failure on top of the first.

Each failure SHALL get its own file, named so that the files sort by when they
happened and one failure never overwrites another. A person who crashed twice
SHALL be able to read both.

The file SHALL carry the whole failure: the exception, every frame of the
traceback, and the values held in those frames. This is deliberately more
than the mailbox log records — that log SHALL NOT hold a subject, a sender or
any part of a body, and this file SHALL be expected to hold all three, because
a frame in the middle of a review holds the messages being reviewed. The two
files answer different questions. The log says what the board did and is read
routinely; this file says why the board stopped and is read once, by someone
who has already lost the session and should not also have to reproduce it.

Because it holds message text, the crash file SHALL NOT be committable. This
is not a convenience it inherits from sitting beside the log: it is the
condition on which the file is allowed to hold what it holds.

The board SHALL still end the session. A failure it did not anticipate is
evidence of a defect, not a state to keep working in, and a board that carries
on after one cannot be trusted about what it did to the account afterwards.

#### Scenario: A failure is written down

- **WHEN** a failure the board does not handle ends the session
- **THEN** a file in the mailbox log's directory holds the exception and the traceback that produced it

#### Scenario: The session still ends

- **WHEN** a failure the board does not handle occurs
- **THEN** the session ends, as it would have without the file being written

#### Scenario: One failure does not overwrite another

- **WHEN** two sessions end in unhandled failures
- **THEN** there are two files, and the order they happened in can be read from their names

#### Scenario: The frames are kept

- **WHEN** a review is part way through and the session ends in an unhandled failure
- **THEN** the file holds the values the frames were holding, including the messages being reviewed

#### Scenario: The crash file is not committable

- **WHEN** the repository is inspected for what it would commit
- **THEN** no crash file is included, and no part of one is in anything tracked

#### Scenario: A crash file that cannot be written

- **WHEN** the crash file cannot be written at all
- **THEN** the session ends exactly as it would have, and nothing about the file is reported to the person

### Requirement: Mail counts as work

A mail row SHALL be treated as work, so that the key which hides work hides it
too, and the count of what was hidden includes it. Every message the board
reads comes from a corporate account, so there is no mail it reads that is not
work.

Every mail row SHALL count, whatever folder it came from and whoever sent it.
This is unconditional, as a tracker issue's is, rather than decided per
account as an event's is: the board reads one account and its folders are all
corporate, so there is nothing for a per-account rule to distinguish. A second
mailbox that was not work would be the reason to make it conditional, and
until there is one, a rule that appeared to choose would be describing a choice
that is not being made.

Mail is shown only in the inbox, and the inbox is the one view where hiding
work removes nothing at all — a task with a project is already outside it. So
hiding work there SHALL leave the inbox's own tasks, which is the whole of what
the key does in that view.

The counts of mail rows and of the messages they stand for SHALL report what
is on screen, so they SHALL fall away while mail is hidden. The board already
undertakes to report how many rows of mail it *is showing*; this is that
undertaking held to when some of them are not.

Hiding mail SHALL change nothing about the account. No message SHALL be moved,
no flag SHALL be set, and the mailbox SHALL NOT be read again because rows
were hidden or shown: the key decides only which of the rows a view already
chose are painted.

#### Scenario: Hiding work hides the mail

- **WHEN** work is hidden and the inbox holds mail
- **THEN** every mail row disappears, and pressing the key again brings them all back

#### Scenario: What is left is the person's own queue

- **WHEN** work is hidden in an inbox holding both mail and undated tasks
- **THEN** the tasks remain and are the whole of the view

#### Scenario: The hidden count includes them

- **WHEN** work is hidden in the inbox and the board reports how many rows that removed
- **THEN** the mail rows it removed are included in that count, so the inbox no longer says it is hiding work without saying how much

#### Scenario: Every mail row counts

- **WHEN** work is hidden and the inbox holds mail from every folder the board reads
- **THEN** no mail row is left behind by folder or by sender

#### Scenario: The counts follow what is shown

- **WHEN** work is hidden in the inbox
- **THEN** the board reports no mail rows and no messages, and reports them again when the key is pressed a second time

#### Scenario: The order comes back unchanged

- **WHEN** a person hides the mail and shows it again
- **THEN** the rows are in the order they were, still below the inbox's tasks

#### Scenario: The account is untouched

- **WHEN** a person hides or shows the mail
- **THEN** no message is moved, no flag is set, and the mailbox is not read again on account of it
