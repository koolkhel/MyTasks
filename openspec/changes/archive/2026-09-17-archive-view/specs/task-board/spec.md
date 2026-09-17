## ADDED Requirements

### Requirement: The archive view

The board SHALL offer an archive view listing the tasks the store has archived
that are completed or cancelled, ordered by the date the store archived them,
most recently archived first. Two rows carrying the same archive date SHALL be
ordered by title, so that the order does not depend on the order the store
answered in.

A task the store has archived but which is neither completed nor cancelled
SHALL NOT be listed when the archive is read: the view is what was finished,
and the store archives some tasks that never were. Which rows are the archive's
is decided when it is read, and holds until it is read again.

The archive SHALL hold tasks alone. No calendar event, tracker issue or mail
row SHALL be drawn in it, because none of them is a thing the store archives.

The view SHALL be reached by a key of its own, which SHALL work in both
keyboard layouts as every other key does, and SHALL be left by the same keys
that reach the day, the inbox and the someday view.

The tag that marks a task green SHALL NOT reorder the archive. Every row in it
is finished, and the tag already ranks below whether a task is finished, so
recency is what is left to order by.

#### Scenario: Reaching the archive

- **WHEN** a person asks for the archive
- **THEN** the board lists the archived tasks that are completed or cancelled, most recently archived first, and nothing else

#### Scenario: A cancelled task is in the archive

- **WHEN** an archived task was cancelled rather than completed
- **THEN** it appears in the archive

#### Scenario: An archived task that is no longer finished stays out

- **WHEN** the archive is read and a task the store archived is neither completed nor cancelled
- **THEN** it does not appear in the archive

#### Scenario: No other source appears

- **WHEN** the archive is shown and the calendar, the tracker and the mailbox have all answered
- **THEN** no event, issue or mail row is drawn in it

#### Scenario: The order is by archive date

- **WHEN** the archive holds tasks archived on different dates
- **THEN** the most recently archived is listed first and the oldest last

#### Scenario: The order does not depend on the store's answer

- **WHEN** several tasks share one archive date
- **THEN** they are listed in title order, whatever order the store returned them in

#### Scenario: Green does not lift a row in the archive

- **WHEN** the archive holds both tagged and untagged tasks
- **THEN** they are ordered by archive date alone, and the tagged ones are not lifted above the rest

### Requirement: The archive is fetched when it is first asked for, and held while the board is open

The board SHALL NOT fetch the archive as part of starting, nor as part of
showing any other view. It SHALL fetch it when the archive is first asked for,
and SHALL keep what it fetched for as long as the board is open.

The fetch SHALL NOT block the board. Rows SHALL be drawn as they arrive rather
than only when the last of them has, and every other view SHALL go on working
while it runs.

The board SHALL say that the archive is still being fetched for as long as it
is, so that a partial answer is never mistaken for the whole of it, and SHALL
stop saying so when it is complete.

Returning to the archive after leaving it SHALL NOT fetch again. Asking the
board to reload while the archive is shown SHALL fetch it again, replacing what
was held.

Nothing about the archive SHALL be written to disk. What was fetched SHALL be
gone when the board is closed, and opening the board again SHALL hold nothing
until the view is asked for again.

#### Scenario: A session that never asks

- **WHEN** a person uses the board without asking for the archive
- **THEN** nothing about the archive is fetched

#### Scenario: The board stays usable while it fills

- **WHEN** the archive is being fetched
- **THEN** the board goes on answering keys, the rows that have arrived are drawn, and moving to another view shows it

#### Scenario: A partial archive says so

- **WHEN** some of the archive has arrived and the rest has not
- **THEN** the board says it is still being fetched

#### Scenario: The saying stops

- **WHEN** the last of the archive has arrived
- **THEN** the board no longer says it is being fetched, and reports what it holds

#### Scenario: Coming back does not fetch again

- **WHEN** a person leaves the archive for another view and returns to it
- **THEN** what was fetched is shown again and the store is not asked a second time

#### Scenario: A reload fetches it again

- **WHEN** a person asks the board to reload while the archive is shown
- **THEN** the archive is fetched again and what is held is replaced

#### Scenario: Nothing outlives the board

- **WHEN** the board is closed after the archive was fetched and opened again
- **THEN** no file holds the archive, and nothing about it is held until the view is asked for again

### Requirement: The archive is searched whole and drawn in part

The board SHALL draw at most a fixed number of archive rows, chosen so that
redrawing the view stays immediate however much the archive holds. Where more
rows are held than that, the most recently archived SHALL be the ones drawn.

A search SHALL be matched against every row the board holds, not only against
the rows it drew. A row the bound withheld SHALL be findable by searching for
it. Where more rows match than the bound allows, the most recently archived
matches SHALL be the ones drawn.

Where the board reports what the view holds, it SHALL report how many rows the
archive holds as well as how many are drawn, so that a view showing part of the
archive is never indistinguishable from an archive that small.

The bound SHALL apply to what is drawn and to nothing else. It SHALL NOT limit
what is fetched, what is held, what a search reaches, or what the board reports.

#### Scenario: More is held than is drawn

- **WHEN** the archive holds more rows than the bound allows
- **THEN** the most recently archived are drawn, and the board reports both how many it holds and how many are drawn

#### Scenario: A search reaches a row that was not drawn

- **WHEN** a person searches for a word that appears only in a row the bound withheld
- **THEN** that row is drawn

#### Scenario: A search narrower than the bound

- **WHEN** a search matches fewer rows than the bound allows
- **THEN** every match is drawn

#### Scenario: A search wider than the bound

- **WHEN** a search matches more rows than the bound allows
- **THEN** the most recently archived matches are drawn, and the board reports how many matched

#### Scenario: The whole archive is held

- **WHEN** the archive holds more rows than the bound allows and no search is in force
- **THEN** every fetched row is still held, and asking what the board would draw for a search finds them

### Requirement: What can be done to a row in the archive

Two writes SHALL be offered on a row in the archive, and no other: un-ticking
it, which is how a finished task is brought back, and dating it, which is
where it is sent once it is. Both SHALL act on the marked rows where any row
is marked and on the selected one otherwise, as they do everywhere else, and
both SHALL be undoable.

A task brought back SHALL return to the day it carried. The store clears its
archive date when it is un-ticked, and the board SHALL send nothing further.
Where that day has passed, the task SHALL appear on today as past due, as any
unfinished task of a past day does.

A row that has been written to SHALL stay in the archive, drawn as it now is,
until the archive is next read. The row is what a person is looking at when
they decide where to send the task, and taking it away on the un-tick would
leave the second key nothing to act on. Reading the archive again SHALL leave
out a row the store no longer archives.

Every other action that writes to a task -- renaming, editing the note,
cancelling, filing into a project, tagging, marking done for today, deleting
-- SHALL be refused in the archive. The board SHALL say the archive is a
record and name the two things that do change a row here, and SHALL send
nothing. The refusal SHALL be given before anything is announced, so that a
key acting on a marked set never reports a write it did not make.

The refusal SHALL belong to the view and not to the task. A finished task
shown on its own calendar day SHALL stay exactly as editable there as it has
always been.

Marking a row, copying the marked rows, the focus view and opening what a row
points at SHALL go on working in the archive, as they do on every row the
board draws: reading is not a change.

#### Scenario: Un-ticking a row in the archive

- **WHEN** a person presses the tick key on a finished row in the archive
- **THEN** the task is un-ticked in the store, its row stays where it is and is drawn as unfinished, and the task is on its own calendar day

#### Scenario: Un-ticking a marked set

- **WHEN** rows are marked in the archive and the tick key is pressed
- **THEN** every marked task is un-ticked and the board reports how many it brought back

#### Scenario: Dating a row in the archive

- **WHEN** a person dates a row in the archive
- **THEN** the task is given that date in the store and its row stays where it is

#### Scenario: Undo reaches both

- **WHEN** a person un-ticks or dates a row in the archive and then presses undo
- **THEN** that write is reversed, as any other write is

#### Scenario: Reading again leaves brought-back rows out

- **WHEN** a task was brought back from the archive and the archive is reloaded
- **THEN** that task is no longer listed

#### Scenario: Every other writing action refuses

- **WHEN** a person presses any other key that would change a task while the archive is shown
- **THEN** each says that only un-ticking and dating change a row here, and none sends anything

#### Scenario: A marked set is refused before it is reported

- **WHEN** rows are marked in the archive and a refused key is pressed
- **THEN** the board says the refusal and does not report having acted on the set

#### Scenario: The same task on its own day is editable

- **WHEN** a person moves from the archive to the calendar day a finished task belongs to and acts on it there
- **THEN** that action works exactly as it does without the archive having been opened

#### Scenario: Reading is still offered

- **WHEN** a person marks rows in the archive, copies them, opens the focus view and opens what a row points at
- **THEN** each works, nothing is sent to change anything, and no row is refused

### Requirement: What a row in the archive shows

A row in the archive SHALL show the date the store archived it where a row
elsewhere shows its time of day, and SHALL otherwise be drawn as a finished
task is drawn in any other view: the mark that tells completed from cancelled,
the title struck through, and the project it was filed in.

The board SHALL name that date as when the task was archived rather than as
when it was completed. The store archives most tasks at the moment they are
ticked but sweeps the rest at the turn of the day, so the two are not the same
date for every row, and the board SHALL NOT state as completion a date the
store does not hold as one.

#### Scenario: The date is shown

- **WHEN** a row is drawn in the archive
- **THEN** the date the store archived it is shown in the column that shows a time of day elsewhere

#### Scenario: Completed and cancelled are still told apart

- **WHEN** the archive holds both a completed and a cancelled task
- **THEN** each carries the mark it carries in every other view, and both are struck through

#### Scenario: The date is called what it is

- **WHEN** the board labels the archive's date, in the view or in the focus view
- **THEN** it names it as when the task was archived, not as when it was completed

### Requirement: The board works when the archive cannot be read

Where the archive cannot be fetched, the board SHALL say so and SHALL stay
usable. The failure SHALL NOT surface as any other view failing, SHALL NOT
prevent moving to another view, and SHALL NOT be retried on its own.

Asking for the archive again, or asking the board to reload while it is shown,
SHALL try again.

#### Scenario: The store refuses the archive

- **WHEN** the archive is asked for and the store answers with an error
- **THEN** the board says the archive could not be read and goes on answering keys

#### Scenario: The other views are unaffected

- **WHEN** the archive could not be read and a person moves to a calendar day
- **THEN** that day loads exactly as it does when the archive was never asked for

#### Scenario: Asking again retries

- **WHEN** the archive could not be read and a person asks for it again
- **THEN** the board tries to fetch it again

## MODIFIED Requirements

### Requirement: The board names the view it is showing

The board SHALL show which of the four views is displayed, naming the inbox, the someday view and the archive rather than presenting them as dates, and SHALL keep reporting how many tasks the view holds.

#### Scenario: Showing the inbox

- **WHEN** the inbox is displayed
- **THEN** the board names it as the inbox and reports how many tasks it holds

#### Scenario: Showing a calendar day

- **WHEN** a calendar day is displayed
- **THEN** the board names that day and how it relates to today, as it did before

#### Scenario: Showing the archive

- **WHEN** the archive is displayed
- **THEN** the board names it as the archive and reports how many tasks it holds

### Requirement: Adding a task follows the shown view

A task added while the inbox is shown SHALL be created with no date, not deferred, and with no project, so that it appears in the inbox it was added from; one added while the someday view is shown SHALL be created deferred with no date; one added while a calendar day is shown SHALL be created on that day.

The archive SHALL take no addition. It is a record of what is already finished
and holds no place a new task could be created into, so the key SHALL create
nothing there and the board SHALL say what it is for.

#### Scenario: Adding to the inbox

- **WHEN** a person adds a task while the inbox is shown
- **THEN** the new task has no date, is not deferred, has no project, and appears in the inbox

#### Scenario: Adding to never

- **WHEN** a person adds a task while the someday view is shown
- **THEN** the new task is deferred, has no date, and appears in the someday view

#### Scenario: Adding while the archive is shown

- **WHEN** a person adds a task while the archive is shown
- **THEN** no task is created and the board says what the key is for

### Requirement: Day navigation applies only to calendar days

Moving to the previous or next day SHALL apply only while a calendar day is shown. While the inbox, the someday view or the archive is shown those movements SHALL do nothing, and returning to today SHALL bring back the day view.

#### Scenario: Day movement is inert in a dateless view

- **WHEN** a person asks for the previous or next day while the inbox is shown
- **THEN** the inbox stays displayed

#### Scenario: Returning to today from the inbox

- **WHEN** a person asks for today while the inbox is shown
- **THEN** the board shows today's calendar day

#### Scenario: Day movement is inert in the archive

- **WHEN** a person asks for the previous or next day while the archive is shown
- **THEN** the archive stays displayed

#### Scenario: Returning to today from the archive

- **WHEN** a person asks for today while the archive is shown
- **THEN** the board shows today's calendar day

### Requirement: How long a search lasts, and where it applies

A search SHALL apply to every view the board shows, so that moving between the
inbox, a calendar day, the someday view and the archive does not change what
it means. It
SHALL last as long as the board is open or until it is cleared, and no longer:
nothing about it SHALL be written anywhere.

Rows that arrive while a search is in force -- a fetch answering, mail
arriving, the calendar or the tracker replying -- SHALL be narrowed by it like
every other row, so that a search cannot be outrun by a redraw.

#### Scenario: The search follows the person between views

- **WHEN** a person searches in the inbox and then moves to a calendar day, the someday view or the archive
- **THEN** that view is narrowed by the same term, without the key being pressed again

#### Scenario: Rows arriving are narrowed too

- **WHEN** a fetch, the mailbox, the calendar or the tracker adds rows to a view while a search is in force
- **THEN** those rows are drawn only if their title contains the term

#### Scenario: It lasts no longer than the board

- **WHEN** a person searches, leaves the board, and opens it again
- **THEN** no search is in force and every row is drawn

#### Scenario: A term set in the archive applies outside it

- **WHEN** a person searches while the archive is shown and then moves to a calendar day
- **THEN** that day is narrowed by the same term, without the key being pressed again

### Requirement: Actions available on the selected task, or on the marked rows

Every action below SHALL act on the marked rows where any row is marked, and
on the selected one otherwise. Where rows are marked the selected row SHALL
take no part: a mark is a choice somebody made, and the cursor is only where
they happen to be standing.

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, scroll the detail area up and down, mark any row and copy every marked row as text, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

Scrolling the detail area, marking a row and copying the marked rows SHALL write nothing and SHALL be offered on every row the board draws, a row from a source included: reading is not a change, and the rows whose notes least often fit are the ones the board does not own.

In the archive two writes are offered -- un-ticking and dating -- and no
other, as that view's own requirement states. Every action that writes nothing
SHALL be offered there as it is everywhere else.

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
- **THEN** the board reports that reordering applies to calendar days, which is the one action a calendar day offers and the dateless views do not; the archive, which offers two writes and refuses the rest, is covered by its own requirement

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

#### Scenario: Marking and copying write nothing

- **WHEN** a person marks rows on any view, including rows from the mailbox, the calendar or the tracker, and copies them
- **THEN** no request is sent to change anything, and every task, message, event and issue is exactly as it was

#### Scenario: A write key with rows marked

- **WHEN** rows are marked and a person presses a key that writes to a task, with the cursor on a row that is not marked
- **THEN** the marked rows are written and the row under the cursor is not

#### Scenario: A write key with nothing marked

- **WHEN** no row is marked and a person presses a key that writes to a task
- **THEN** it acts on the selected row, exactly as it does with marking never used
