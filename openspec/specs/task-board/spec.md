# task-board Specification

## Purpose
The day-at-a-time terminal view of a person's tasks: it shows the tasks starting on one calendar day, lets them move between days, and lets them act on the selected task. It deliberately exposes a small subset of the upstream task model, leaving richer editing to the SingularityApp clients.

## Requirements

### Requirement: Task row presentation

Each task in the shown day SHALL be presented as a row carrying its completion mark, its start time, its title, and its project name. The title SHALL be shown as readable text: any link markup stored in it is rendered as the address it points to rather than displayed raw, and any character that the display treats as styling is shown as written. A past-due task SHALL instead show how overdue it is in place of its start time, and SHALL have its title rendered in a colour that sets it apart from the tasks due today. Title emphasis SHALL otherwise convey completion state only. The board SHALL NOT vary a title's weight, dimming, or colour according to the task's priority.

#### Scenario: An open task is shown plainly

- **WHEN** the day contains an open task
- **THEN** its title is rendered without emphasis, regardless of the priority stored on that task

#### Scenario: A finished task is struck through

- **WHEN** a task in the day is completed or cancelled
- **THEN** its title is rendered struck through and dimmed

#### Scenario: Two tasks differing only in priority look identical

- **WHEN** the day contains two open tasks whose stored priorities differ
- **THEN** neither row is emphasised relative to the other

#### Scenario: A past-due row is set apart

- **WHEN** today's view holds both a past-due task and a task due today
- **THEN** the past-due row shows how overdue it is where the other shows a time, and its title is coloured while the other's is not

#### Scenario: A row never shows stored markup

- **WHEN** a task's title holds an HTML anchor
- **THEN** the row shows the readable address and none of the surrounding tags

### Requirement: Ordering of tasks within a day

The board SHALL order a day's tasks by, in turn: unfinished before finished, past due before due today, pinned before unpinned, timed before all-day, earlier start time before later, and finally the order a person has set by hand. Where two tasks share even that, they SHALL be ordered by title. Past-due tasks SHALL be ordered among themselves by how overdue they are, the most overdue first. Priority SHALL NOT influence the order.

The manual order SHALL be the last key and never override an earlier one: it decides the sequence among tasks the other keys leave equal, and cannot lift a task above a group it does not belong to. A day's timed tasks therefore stay in ascending start time however they are moved, and past-due tasks stay in most-overdue-first order.

#### Scenario: Timed tasks lead all-day tasks

- **WHEN** a day holds both timed and all-day tasks
- **THEN** every timed task is listed above every all-day task, and the timed ones run in ascending start time

#### Scenario: A tie is broken by title, not priority

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot, and the same manual order, and carry different priorities
- **THEN** they are ordered by title, so the sequence is never arbitrary between them, and their priorities are not consulted

#### Scenario: The manual order is what decides between otherwise equal tasks

- **WHEN** two tasks in the day share a completion state, pinned state, and start slot but carry different manual orders
- **THEN** they are ordered by the sequence a person has set, and the title is not consulted

#### Scenario: The manual order cannot override the time of day

- **WHEN** a day holds two timed tasks at different times, whatever manual order they carry
- **THEN** the earlier one is listed first

#### Scenario: Finished tasks sink

- **WHEN** a day holds a mix of open and completed tasks
- **THEN** the completed ones appear after all open ones

#### Scenario: Past-due tasks lead today's own

- **WHEN** today's view holds both past-due tasks and tasks due today
- **THEN** every past-due task is listed above every task due today

#### Scenario: The most overdue comes first

- **WHEN** today's view holds several past-due tasks
- **THEN** they are ordered with the longest overdue at the top, whatever manual order they carry

### Requirement: Detail of the selected task

The board SHALL show, for the currently selected task, whether it recurs, whether it is pinned, its deadline when it has one, and its note when it has one. The detail SHALL NOT report the task's priority.

#### Scenario: A recurring task with a note

- **WHEN** the selected task recurs and carries a note
- **THEN** the detail area reports that it is recurring and shows the note text, with no mention of priority

#### Scenario: A plain task

- **WHEN** the selected task does not recur, is not pinned, and has neither deadline nor note
- **THEN** the detail area shows no priority line

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, open its link, move it up or down within a calendar day, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, done for today and opening a link included

#### Scenario: Reordering is the one action a day alone offers

- **WHEN** a task is selected in the inbox or the someday view and a person tries to move it up or down
- **THEN** the board reports that reordering applies to calendar days, which is the single exception to every action being available everywhere

#### Scenario: Moving a task and moving the cursor are different keys

- **WHEN** a person presses the key that moves the cursor up or down
- **THEN** no task's stored order changes, and the key that moves the task is a different one

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

### Requirement: The key bar shows every key without clipping

The board SHALL display at all times the keys it responds to and what each one does. The bar SHALL wrap across as many rows as it takes for every entry to be shown in full: no label may be omitted, and none may be cut off part-way through a word. The bar SHALL advertise exactly the keys the board binds, so a binding cannot exist without being shown and the bar cannot name a key that does nothing.

#### Scenario: Every action is advertised

- **WHEN** the board is shown
- **THEN** every key it binds for display appears in the bar, each with its description in full

#### Scenario: A narrow terminal

- **WHEN** the board is shown in a terminal too narrow for the entries to fit on two rows
- **THEN** the bar uses however many rows are needed, and still shows every entry in full

#### Scenario: A wide terminal

- **WHEN** the board is shown in a terminal wide enough for fewer rows
- **THEN** every entry still appears exactly once, with none repeated across rows

#### Scenario: No entry is cut off part-way

- **WHEN** the bar is shown at any width the board can be run at
- **THEN** no entry appears as a partial word

#### Scenario: The bar and the help overlay agree

- **WHEN** a person compares the bar with the help overlay
- **THEN** every key named in the bar is described in the overlay, and neither names a key the board does not bind

#### Scenario: The task list keeps its room

- **WHEN** the bar occupies more than one row
- **THEN** the task list shrinks to accommodate it rather than being overlapped, and the day header and status line remain visible

### Requirement: A task's link is recognised and readable

The board SHALL recognise a link written in a task's title, whether stored as an HTML anchor or written as a plain `http` or `https` address. Where a title holds an anchor, the board SHALL show the anchor's readable text in place of the stored markup, so no row or card ever displays raw HTML. The surrounding words of the title SHALL be preserved. An address written without a scheme SHALL be understood as `https`.

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
- **THEN** the first is the task's link, and every one of them is still shown in the title

#### Scenario: Markup characters in a title are shown, not interpreted

- **WHEN** a task's title contains square brackets
- **THEN** they appear in the row exactly as stored, rather than being consumed as styling

### Requirement: Opening a task's link

The board SHALL let a person open the selected task's link, handing the address to the operating system. This SHALL work without a mouse and without depending on the terminal's own capabilities. The board SHALL additionally present the address so that a terminal able to make hyperlinks clickable can do so, but SHALL NOT rely on that for the link to be reachable.

Only `http` and `https` addresses SHALL be opened. A title is ordinary text that happens to be passed to the system opener, so no other scheme may be launched through it.

#### Scenario: Opening the link of the selected task

- **WHEN** a person asks to open the link of a task that has one
- **THEN** the address is handed to the operating system to open

#### Scenario: A task with no link

- **WHEN** a person asks to open the link of a task that has none
- **THEN** nothing is opened and the board says the task has no link

#### Scenario: Nothing is selected

- **WHEN** a person asks to open a link while the shown view holds no tasks
- **THEN** nothing is opened and the board is left as it was

#### Scenario: An address of another kind is refused

- **WHEN** a task's title contains an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened

#### Scenario: Opening a link changes nothing

- **WHEN** a person opens a task's link
- **THEN** the task is not modified and no request that changes anything is sent

#### Scenario: Available wherever a task is selected

- **WHEN** a task with a link is selected in the inbox or in the someday view
- **THEN** its link can be opened just as from a day

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

### Requirement: Setting the order of a day's tasks by hand

The board SHALL let a person move the selected task up or down within a
calendar day, and SHALL store the resulting position on the task so that it
survives a reload and is the same order other SingularityApp clients show.

Moving SHALL change the stored order of the moved task alone, to a value
that places it on the far side of its neighbour and that no other task in
the day holds. No other task's stored order SHALL change, so that a move
is a single write and cannot be left half applied.

No two tasks in a day SHALL be left sharing a stored order. Where there is
no value available between the moved task's destination and the task beyond
it, the board SHALL first move that run of tasks into a range of values no
task in the day holds, so that the destination exists; such a renumbering
SHALL preserve the order of the tasks it renumbers, and SHALL leave every
stored order distinct even if only some of its writes are applied.

Moving SHALL only exchange the task with a neighbour the day's other ordering
keys allow it to trade with — one that is equally finished, equally past due,
equally pinned, and equally timed at the same start. Where the neighbour in
that direction is not such a task, or there is none, the board SHALL report
why the task cannot move there and SHALL leave every task's stored order
untouched.

Reordering SHALL be offered on calendar days only. In the inbox and the
someday view the board SHALL report that reordering applies to days rather
than silently doing nothing, because those views are not sequences of work
and are ordered by title.

#### Scenario: Moving a task up

- **WHEN** a person moves the selected task up, and the task above it is one the day's other ordering keys allow it to trade with
- **THEN** the two appear in the opposite sequence, every other task stays where it was, only the moved task's stored order changed, and the selection is still on the moved task

#### Scenario: The new position is remembered

- **WHEN** a person moves a task and then reloads the view, or leaves the day and comes back
- **THEN** the task is still in the position they moved it to

#### Scenario: Moving down

- **WHEN** a person moves the selected task down
- **THEN** it comes to sit after the task below it, under the same rules that govern moving up

#### Scenario: Already at the edge of its group

- **WHEN** a person moves the selected task towards an edge where there is no task it may trade with, whether because the day has none or because the adjacent one is ordered differently
- **THEN** the board reports why it cannot move there, and no task's stored order changes

#### Scenario: An all-day task cannot be lifted above a timed one

- **WHEN** the selected all-day task is the first of the all-day tasks and a timed task sits above it
- **THEN** moving up reports that it cannot pass the timed tasks, and the order is unchanged

#### Scenario: A failed move changes nothing

- **WHEN** the write that moves a task fails
- **THEN** no task's stored order has changed, because the move was a single write

#### Scenario: No room between the destination and the task beyond it

- **WHEN** a person moves a task to a place where the two tasks it must sit between hold adjacent values with nothing available in between
- **THEN** the move still happens, the tasks keep the sequence they were in apart from the one moved, and every stored order in the day is still distinct

#### Scenario: Not offered in the dateless views

- **WHEN** a person tries to move a task in the inbox or the someday view
- **THEN** the board reports that reordering applies to calendar days, and no task's stored order changes

#### Scenario: Sequencing a past-due task

- **WHEN** a person wants a past-due task in a particular place in today's sequence and dates it to today
- **THEN** it joins the tasks due today and can be moved among them

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
