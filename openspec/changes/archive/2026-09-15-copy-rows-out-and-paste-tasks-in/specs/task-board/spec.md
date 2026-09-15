## ADDED Requirements

### Requirement: Marking rows to copy them

The board SHALL offer a key that marks the row under the cursor, and that
unmarks it when it is pressed again on a row already marked. Marking SHALL
write nothing anywhere.

Marking SHALL be offered on every row the board draws, the mailbox's, the
calendar's and the tracker's included, for the same reason reading one is:
copying a row does not change it, and a day is most worth copying whole.

What is marked SHALL be the row itself rather than the line it occupies. A row
that moves because the view was redrawn, because a write landed, or because
the person went to another view SHALL keep its mark. Marks SHALL last as long
as the board is open or until they are cleared, and nothing about them SHALL
be written anywhere.

Marks SHALL follow the person between views, so that rows gathered from the
inbox, a calendar day and the someday view can be copied in one go.

The board SHALL forget the mark on a row it no longer holds, so that a task
deleted or a message filed elsewhere cannot leave behind a mark that can
neither be seen nor cleared.

A marked row SHALL be drawn so that it can be told apart both from an unmarked
row and from the selected one. The cursor is where a person is; a mark is what
they chose; the two are different things and SHALL NOT look like one.

#### Scenario: Marking and unmarking the same row

- **WHEN** a person presses the marking key on a row and then presses it again on that same row
- **THEN** the row is marked and then unmarked, and nothing is written either time

#### Scenario: A mark survives the view being redrawn

- **WHEN** rows are marked and a write lands, a fetch answers, or the mailbox adds rows, so that the view is rebuilt and the rows move
- **THEN** the same rows are still marked, and no row that was not marked has become marked

#### Scenario: Marks gathered from several views

- **WHEN** a person marks rows in the inbox, moves to a calendar day and marks more, and then moves to the someday view
- **THEN** every row marked in every one of those views is still marked

#### Scenario: A row the board does not own can be marked

- **WHEN** a person marks a mail row, a calendar event or a tracker issue
- **THEN** the row is marked, nothing is written, and it is not refused as unownable

#### Scenario: A mark on a row that is no longer there

- **WHEN** a marked task is deleted, or a marked message leaves the folder the board reads
- **THEN** the mark is forgotten with the row, and the count of marked rows no longer counts it

#### Scenario: The cursor and a mark are different

- **WHEN** a person marks a row and then moves the cursor to another row
- **THEN** the first row is still marked, the cursor is on the second, and the two are drawn differently

### Requirement: Copying the marked rows as text

The board SHALL offer a key that puts the marked rows on the system clipboard
as markdown, one line for each row, so that they can be pasted into any
editor.

An unfinished task SHALL be written with an empty box, a finished one with a
ticked box, and a cancelled one with a ticked box and its title struck
through. Cancelled is a third state and markdown has two boxes; striking the
title is what keeps it from being read back as an ordinary finished task. A
row the board does not own carries no tick state of its own and SHALL be
written as unfinished.

The title SHALL be written as the row carries it rather than as the column
drew it: before it was shortened to fit, and before a count of messages was
appended to a mail subject.

The lines SHALL be in the order the rows were marked. Marks may be gathered
from views that share no ordering, so the order of marking is the only one
that is defined wherever the rows came from.

Every marked row SHALL be copied, including one a search or the work filter is
hiding at the time. A mark is on a row rather than on a drawn line, and the
board says how many rows are marked, so a row copied while hidden is not a row
copied in secret.

The board SHALL say what it copied. Pressing the key with nothing marked SHALL
say so and SHALL leave the clipboard alone, rather than replacing whatever the
person had with nothing.

#### Scenario: The three states of a task

- **WHEN** an unfinished task, a finished task and a cancelled task are marked and copied
- **THEN** the unfinished one carries an empty box, the finished one a ticked box, and the cancelled one a ticked box with its title struck through

#### Scenario: A row from a source copies as unfinished

- **WHEN** a mail row, a calendar event or a tracker issue is marked and copied
- **THEN** its line carries the row's title and an empty box, because such a row has no tick state of its own

#### Scenario: The title is the one the row carries

- **WHEN** a row whose title the column shortened, or a mail row drawn with a count of messages beside its subject, is marked and copied
- **THEN** the copied line carries the whole title without the shortening and without the count

#### Scenario: The order is the order of marking

- **WHEN** rows are marked in one order and copied
- **THEN** the lines are in the order the rows were marked, whatever order the views drew them in

#### Scenario: A marked row a filter is hiding

- **WHEN** a row is marked and a search or the work filter then hides it, and the person copies
- **THEN** that row is copied with the rest, and the count of marked rows had said it was there

#### Scenario: Copying with nothing marked

- **WHEN** a person presses the copying key with no row marked
- **THEN** the board says nothing is marked, and whatever was on the clipboard is still there

### Requirement: The clipboard program is started like every other program

Reaching the clipboard SHALL start a program named by the board and by
nothing else. No part of a task's title, a message's subject or any other
text the board displays SHALL determine what is run or be passed to it as an
argument -- the text being copied goes to the program's input, never to its
command line.

It SHALL be started by the one path this board starts anything by, and SHALL
therefore be detached from the board's terminal in a session of its own, with
its output going nowhere the view can be reached from. A second way of
starting a program is a second place for those rules to be forgotten.

Its input SHALL be the board's to give: either nothing, or exactly the text
being copied, handed over and then closed so the program can finish. It SHALL
NOT be left to read the terminal the board is drawn on.

Where no such program is on the machine, the board SHALL carry on rather than
fail: the escape sequence may have carried the text anyway, and a machine
without the program is an ordinary machine.

#### Scenario: The text goes to the program's input

- **WHEN** marked rows are copied
- **THEN** the program is run with no argument taken from any row, and the text reaches it on its input

#### Scenario: Only one way to start a program

- **WHEN** the board's own source is read
- **THEN** there is exactly one place in it that starts a process, and the clipboard goes through that place

#### Scenario: No such program on this machine

- **WHEN** the clipboard program cannot be started
- **THEN** the copy is not reported as having failed, because the other route may have carried it

### Requirement: The board says how many rows are marked

While any row is marked the board SHALL say how many, where it already reports
what a view is not showing. A mark that cannot be seen -- on a row in another
view, or on one a filter is hiding -- SHALL still be counted there, because
the count is the only place such a mark is visible at all.

When no row is marked the board SHALL say nothing about marks, so that the
report is about something a person did rather than a permanent fixture.

#### Scenario: The count is shown while rows are marked

- **WHEN** rows are marked, in this view or another
- **THEN** the board reports how many rows are marked, alongside what it already says the view is not showing

#### Scenario: Nothing marked, nothing said

- **WHEN** no row is marked
- **THEN** the board says nothing about marked rows

### Requirement: Pasted lines become tasks in the shown view

Text pasted into the board SHALL add one task for each line it holds. The
tasks SHALL land in the view on screen by the same rules the add key follows:
undated in the inbox, deferred in the someday view, and on the shown day
otherwise.

Pasting SHALL need no key of the board's own. The terminal delivers pasted
text to the application, and a person pasting into a task board means to put
tasks on it.

Lines that are empty or hold nothing but whitespace SHALL be passed over
rather than becoming tasks with no title. A paste that holds a single line
SHALL add a single task, by the same rules.

#### Scenario: Several lines become several tasks

- **WHEN** a person pastes several lines into the board
- **THEN** one task is added for each line, in the order the lines were in

#### Scenario: The tasks land in the view on screen

- **WHEN** a person pastes into the inbox, into the someday view, and onto a calendar day
- **THEN** the tasks are undated, deferred, and dated to that day, matching what the add key would have done in each

#### Scenario: Blank lines are not tasks

- **WHEN** a pasted block holds blank lines between its lines, or ends with one
- **THEN** no task is added for them

#### Scenario: A single line

- **WHEN** a person pastes text holding one line
- **THEN** one task is added, in the view on screen

### Requirement: What a pasted line is read as

A pasted line SHALL be read as a task's title with its list decoration
removed: any leading whitespace, then a bullet -- a hyphen, an asterisk or a
plus -- or a number followed by a full stop or a bracket, and then a markdown
checkbox where one follows. A line carrying no decoration at all SHALL be read
as a title in full.

A checkbox SHALL be read rather than merely removed. A ticked box SHALL make
the task finished, whatever letter case the tick was written in; an empty box
SHALL leave it unfinished. Rows copied out of the board and pasted straight
back SHALL come back as they left.

A pair of tildes wrapping the whole of what is left SHALL be removed too,
but only from a line whose box was ticked: that is the only line the board
writes them on, a cancelled task being the one thing it strikes through.
A title that is itself wrapped in tildes SHALL keep them on any other line,
because no line the board writes could have looked like that one.
The task SHALL come back finished rather than cancelled: markdown has two
boxes and this board has three states, and the direction that cannot be
carried is the one coming in.

Nothing else in a line SHALL be interpreted. Whatever else the editor left
there -- a tag, a date, a note of its own -- SHALL stay in the title.
Interpreting it would mean guessing, and a guess that is wrong puts words in a
person's task that they did not write and cannot see were changed.

#### Scenario: Bullets of every kind

- **WHEN** lines beginning with a hyphen, an asterisk, a plus, "1." and "1)" are pasted
- **THEN** each becomes a task whose title is the text after the bullet, with the bullet gone

#### Scenario: Indented lines

- **WHEN** pasted lines are indented, with tabs or with spaces, as an outliner nests them
- **THEN** each becomes a task whose title is the text alone, the indentation gone, because the board has no nesting to put it in

#### Scenario: A ticked box makes a finished task

- **WHEN** a line carrying a ticked checkbox is pasted
- **THEN** the task it adds is already finished, and one carrying an empty box is not

#### Scenario: A title that is itself struck through

- **WHEN** an unfinished line whose title is wrapped in tildes is pasted
- **THEN** the task added keeps the tildes in its title, because the board never writes them on an unticked line

#### Scenario: A cancelled row pasted back

- **WHEN** the line the board writes for a cancelled task is pasted back into it
- **THEN** the task added carries the title without the tildes, and is finished

#### Scenario: A line with no decoration

- **WHEN** a line that begins with a letter is pasted
- **THEN** the whole line is the task's title

#### Scenario: Out and straight back

- **WHEN** marked rows are copied and the copied text is pasted back into the board
- **THEN** the tasks added carry the same titles and the same finished-or-not state as the rows that were copied, a cancelled row coming back as a finished task with its title intact and no tildes left in it

#### Scenario: Nothing else is interpreted

- **WHEN** a pasted line carries text an editor of its own uses, such as a trailing tag or a date in brackets
- **THEN** that text is part of the task's title, unchanged

### Requirement: A paste is one action and one undo

However many tasks a paste added, undoing it SHALL remove every one of them
and SHALL say how many it removed. A paste is one thing a person did and
SHALL be one thing to reverse; undoing it a line at a time would be as much
work as the paste saved.

An undo that deletes is otherwise refused on this board. It is allowed here
for the reason it is allowed for a promoted mail thread: the same action
created the tasks, they hold nothing but what it put there, and nothing else
can have come to depend on them in the time since.

#### Scenario: Undoing a paste of several lines

- **WHEN** a person pastes several lines and then presses the undo key once
- **THEN** every task the paste added is gone, the board says how many it removed, and no other task is touched

#### Scenario: Undo reaches past the paste

- **WHEN** a person undoes a paste and presses the undo key again
- **THEN** the write before the paste is reversed, rather than the paste being reversed a second time

### Requirement: A paste of many lines reaches the store whole

The board SHALL add every line of a paste however many it held, and SHALL do
so in a way the store accepts. A paste is the one action on this board that
makes many tasks at once, and a store that refuses some of them because too
many arrived together would lose work a person can see on screen and believes
is saved.

Where a task cannot be created, the board SHALL say which line failed and
SHALL take its row off the screen, rather than leaving a row standing for a
task that was never made.

#### Scenario: A long paste

- **WHEN** a person pastes a block of many lines
- **THEN** a task is created for every line, and none is lost to the number that were sent

#### Scenario: A line the store refuses

- **WHEN** the store refuses one of the tasks a paste is creating
- **THEN** the board says so and that row leaves the screen, while the tasks that were created stay

### Requirement: A multi-line paste into the title prompt is not silently cut

Where a person pastes several lines while a prompt for a title is open, the
board SHALL NOT keep the first line, discard the rest, and say nothing. Losing
the greater part of what somebody pasted, with no sign that anything is
missing, is worse than either accepting it or refusing it.

#### Scenario: Several lines pasted into the prompt for a new task

- **WHEN** a person opens the prompt for a new task's title and pastes several lines into it
- **THEN** the lines are not silently reduced to the first one

### Requirement: What cannot be undone, and what an undo may destroy

An undo SHALL NOT create a task. It SHALL NOT destroy a task either, except
where the action being undone is the action that created that task and carries
its own reversal; then removing what it made is the whole of the reversal, and
leaving the task behind would be the failure.

Where the most recent write cannot be reversed, the board SHALL name it and
say why, rather than doing nothing or appearing to succeed.

Three writes cannot be reversed, and each SHALL be reported in its own terms:
deleting a task, because it is gone; filing a task that had no project,
because the API refuses every value that would return it to having none; and
adding a task with the add key, because there is nothing to put back and the
board does not delete on that person's behalf a task they typed out.

#### Scenario: The last write was a deletion

- **WHEN** a person deletes a task and presses the undo key
- **THEN** the board says a deletion cannot be undone, and no task is created

#### Scenario: The last write was a first filing

- **WHEN** a person files a task that had no project and presses the undo key
- **THEN** the board says the filing cannot be undone, and the task keeps its project

#### Scenario: The last write was an addition

- **WHEN** a person adds a task with the add key and presses the undo key
- **THEN** the board says adding cannot be undone and suggests deleting the task instead, and the task is not deleted

#### Scenario: Undo destroys only what the same action made

- **WHEN** a person presses the undo key any number of times
- **THEN** no task is deleted by it except one created by the very action being undone, and no task that existed before that action is ever deleted

## MODIFIED Requirements

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, edit its note, assign or clear its date, assign it to a project, open its link, move it up or down within a calendar day, scroll the detail area up and down, mark any row and copy every marked row as text, undo the last write it made, delete it behind a confirmation, and turn a mail thread into a task on today. The board SHALL NOT offer any action that changes a task's priority.

Scrolling the detail area, marking a row and copying the marked rows SHALL write nothing and SHALL be offered on every row the board draws, a row from a source included: reading is not a change, and the rows whose notes least often fit are the ones the board does not own.

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

#### Scenario: Marking and copying write nothing

- **WHEN** a person marks rows on any view, including rows from the mailbox, the calendar or the tracker, and copies them
- **THEN** no request is sent to change anything, and every task, message, event and issue is exactly as it was

### Requirement: Where a newly added task lands in a day's order

A task added to a calendar day SHALL be placed after every task already in
that day's order, so that adding one does not disturb a sequence a person has
set.

The board SHALL choose the stored order it sends rather than leaving it to
the API's default. The default is the lowest value there is, which would put
each new task at the head of its group and tie it with every other task the
board has added.

Where one action adds several tasks at once, each SHALL be given a place of
its own past the last. Reading the day's last place once and sending it with
every task would tie them all with each other, and the sequence a person
gave would be lost to an ordering by title.

#### Scenario: Adding to a day that already has tasks

- **WHEN** a person adds a task to a day whose tasks are in an order they set
- **THEN** the new task appears after the others and none of them moves

#### Scenario: Two tasks added one after another

- **WHEN** a person adds two tasks to the same day in succession
- **THEN** the second appears after the first, rather than the two being tied and ordered by title

#### Scenario: Adding to an empty day

- **WHEN** a person adds a task to a day that has none
- **THEN** the task is created with a stored order the board chose, ready to be moved once the day has others

#### Scenario: Several tasks added in one action

- **WHEN** a person adds several tasks to a day in a single action
- **THEN** they appear after the day's existing tasks, in the order they were given, none of them tied with another

### Requirement: A rejected write is undone

Where the API refuses a write, the board SHALL restore what it showed before
applying the write and SHALL report the failure. It SHALL NOT keep on screen a
change the server did not accept, and SHALL NOT leave the failure unreported.

The report SHALL name what the refused write was about. One action can write
many tasks -- a paste makes one for every line it held -- and a report saying
only what kind of write failed leaves a person unable to tell which of forty
rows the store would not take.

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

#### Scenario: The report names the task

- **WHEN** a write is refused
- **THEN** the report names the task it was about, as well as what kind of write it was and what the store said

### Requirement: Narrowing the view to a search

The board SHALL offer a key that asks for a term, and SHALL then draw only the
rows whose title contains it. Escape SHALL clear the search and bring every
row back, and SHALL clear any marked rows along with it. Escape is this
board's one answer to “never mind”, and having it mean that for one of the
two things a person set and not the other would be a trap.

The term SHALL be matched against the title alone -- a mail row's subject, or
a task's, an event's or a tracker issue's title -- and SHALL NOT be matched
against the sender, the project, the date, or the body of a message. What a
person reads in the title column is what the search answers to.

The term SHALL be matched against the title the row carries rather than the
string drawn in the cell: before the count of messages is appended to a mail
subject, and before the column shortens the title to fit. A word a person can
read on the focus card SHALL NOT be unfindable because the column cut it off.

The match SHALL be a plain substring and SHALL ignore letter case, so that a
subject is found however its sender capitalised it.

Every source the view draws SHALL be narrowed -- the store's tasks, mail
threads, calendar events and tracker issues -- and SHALL be narrowed where the
work filter narrows, rather than being added to the view afterwards. A source
whose rows are appended after the narrowing is a source the key cannot reach,
however the rows are marked.

Narrowing SHALL remove rows from the view without changing any task: no write
SHALL be made, and nothing SHALL be altered about a task because it was drawn
or not drawn.

Where the work filter is also in force, a row SHALL be drawn only if it
survives both, and neither key SHALL clear the other.

Confirming an empty term SHALL be the same as having no search. Cancelling the
prompt SHALL leave whatever search was already in force exactly as it was.

#### Scenario: Finding a thread in a long inbox

- **WHEN** a person searches the inbox for a word that appears in some subjects
- **THEN** only the rows whose subject contains that word are drawn, and the rest are not

#### Scenario: Only the title is matched

- **WHEN** a person searches for a word that appears in a message's sender or body but not in its subject
- **THEN** that row is not drawn, because the search answers to the title alone

#### Scenario: A title the column cut off

- **WHEN** a person searches for a word that is part of a title too long for the column to show
- **THEN** that row is drawn, because the search reads the title the row carries rather than the shortened cell

#### Scenario: The thread count is not part of the subject

- **WHEN** a person searches for the number of messages shown beside a mail subject
- **THEN** that row is drawn only if the number is in the subject itself

#### Scenario: Letter case does not matter

- **WHEN** a person searches with a term whose letters are cased differently from the title
- **THEN** the row is still drawn

#### Scenario: Every source is narrowed, in the view that holds it

- **WHEN** a search is in force in the inbox, which holds the store's tasks and the mailbox's threads, and on today, which holds the store's tasks, the calendar's events and the tracker's issues
- **THEN** rows of every one of those four kinds are drawn only if their title contains the term, no view holding all four at once

#### Scenario: No source is reached only by being marked

- **WHEN** the board draws rows from a source and a search is in force
- **THEN** they are narrowed together with the store's tasks, and no source's rows reach the view past the narrowing

#### Scenario: Nothing is written

- **WHEN** a person starts a search, changes it, or clears it
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: Clearing brings the rows back

- **WHEN** a person presses escape with a search in force
- **THEN** every row the view holds is drawn again, exactly as it was before the search

#### Scenario: Cancelling the prompt changes nothing

- **WHEN** a person opens the prompt with a search already in force and cancels it instead of confirming
- **THEN** the search that was in force is still in force, unchanged

#### Scenario: An empty term is no search

- **WHEN** a person confirms the prompt having typed nothing
- **THEN** the view is drawn as it is with no search at all

#### Scenario: Both filters at once

- **WHEN** the work filter is on and a person searches for a term that some work rows match
- **THEN** those rows are still not drawn, because a row is drawn only if it survives both, and clearing one leaves the other in force

#### Scenario: What is selected after narrowing

- **WHEN** a search is applied or cleared
- **THEN** the selection is on a row that is drawn, or nothing is selected because no row is

#### Scenario: Escape clears the marks along with the search

- **WHEN** a person has rows marked and a search in force, and presses escape
- **THEN** every row is drawn again and no row is marked, both cleared by the one press

## REMOVED Requirements

### Requirement: What cannot be undone, and how the board says so

**Reason**: Its blanket guarantee that an undo never deletes a task was
already untrue when it was written. Undoing a promoted mail thread removes the
task the promotion created, which the mail requirement states plainly, so the
spec held two rules that could not both be kept. Undoing a paste needs the
same reversal, for the same reason, which makes the contradiction load-bearing
rather than dormant.

**Migration**: Reissued as *What cannot be undone, and what an undo may
destroy*, which keeps every case the old requirement covered and states the
exception the board already relies on: an undo may remove a task only where
the action it is reversing is the action that created it.
