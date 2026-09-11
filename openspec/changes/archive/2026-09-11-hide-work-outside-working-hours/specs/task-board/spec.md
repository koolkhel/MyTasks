## ADDED Requirements

### Requirement: The working window

The board SHALL take a working window from its environment: the hours of the
day within which work is shown, and the days of the week the window applies
to. Both SHALL be configured rather than built into the board's source, for
the same reason the work project is -- the hours a particular person works
are theirs, not the board's.

Where no working window is configured, the board SHALL behave exactly as it
does without one: nothing is hidden until the key is pressed. A window SHALL
be something a person turns on, never something they have to turn off.

Where days are not configured and hours are, the window SHALL apply Monday to
Friday. A day outside the window SHALL be outside it for its whole length,
whatever the hours say.

The hours SHALL name a range within one day. A range whose end is not later
than its start SHALL be treated as unreadable rather than wrapped around
midnight. Midnight SHALL be nameable as an end, so that a window may cover the
whole of a day or run to the end of one.

Where a window is configured but cannot be read, the board SHALL say so and
behave as though none were configured. It SHALL NOT guess a window, and SHALL
NOT refuse to start: an unreadable setting costs a person the feature, not
their board.

Where no work project is configured, the window SHALL hide nothing and SHALL
report nothing of its own accord. A clock cannot know which rows are work.

#### Scenario: No window is configured

- **WHEN** the board is opened with no working window configured
- **THEN** every task is shown, whatever the hour or the day, until the key is pressed

#### Scenario: Inside the window

- **WHEN** the board is opened on a configured working day at an hour inside the configured range
- **THEN** the work tasks are shown

#### Scenario: Outside the window by the hour

- **WHEN** the board is opened on a configured working day at an hour after the range ends
- **THEN** the work tasks are hidden without the key being pressed

#### Scenario: Outside the window by the day

- **WHEN** the board is opened at an hour inside the range, on a day the window does not cover
- **THEN** the work tasks are hidden, because a day outside the window is outside it for its whole length

#### Scenario: The days, as a person writes them

- **WHEN** days are configured as a list, a range, or a range that runs round the end of the week
- **THEN** each names the days it reads as naming, whatever the case and spacing, and a word that is not a day makes the setting unreadable

#### Scenario: Weekends are outside the window unless days are configured

- **WHEN** hours are configured and days are not
- **THEN** the window covers Monday to Friday, so a Saturday at midday is outside it

#### Scenario: A window that runs to midnight

- **WHEN** the hours are configured to end at midnight
- **THEN** the last minute of the day is inside the window, and the minute before the start is outside it

#### Scenario: A range that does not run forwards

- **WHEN** the configured hours end no later than they start
- **THEN** the board reports the setting as unreadable and behaves as though no window were configured

#### Scenario: An unreadable window does not stop the board

- **WHEN** a working window is configured in a form the board cannot read
- **THEN** the board opens, says the setting could not be read, and hides nothing until the key is pressed

#### Scenario: A window with no work project

- **WHEN** a working window is configured and no work project is
- **THEN** nothing is hidden and the board says nothing about the window on its own, because there is no set of rows for it to act on

### Requirement: The board crosses the window while it is open

While the board is open it SHALL notice the window being crossed and set the
mode accordingly, with no key pressed. It SHALL notice within one minute of
the crossing.

The board SHALL redraw on account of the window only when the window has been
crossed, or when the boundary it is reporting has changed. A check that finds
the window where it was SHALL change nothing on screen, because a redraw nobody
asked for moves the list under the hand working it.

A boundary can change without a crossing: an evening after the hours end
becomes a weekend outside the working week, both of them hidden. The board
SHALL then correct what it says, rather than give Friday's reason all weekend.

A crossing SHALL remove or restore rows exactly as the key does: the view
SHALL keep its scroll position, and where the selected row is one of the rows
removed the selection SHALL go to the nearest surviving row.

A crossing SHALL write nothing. No task SHALL be altered because the working
day ended.

#### Scenario: The end of the working day

- **WHEN** the board is open showing work and the end of the window passes
- **THEN** the work rows leave the view within a minute, and the board says the clock removed them

#### Scenario: The start of the working day

- **WHEN** the board is open with work hidden by the window and the start of the window passes
- **THEN** the work rows return within a minute

#### Scenario: Between crossings

- **WHEN** the board checks the window and finds it as it was
- **THEN** nothing on screen moves: not the scroll position, not the selection, not a row

#### Scenario: The boundary changes without a crossing

- **WHEN** an evening outside the hours becomes a day outside the working week, the work hidden throughout
- **THEN** the work stays hidden, no row moves, and the board now names the day rather than the hour

#### Scenario: A crossing with a work row selected

- **WHEN** the window is crossed while a work row is selected
- **THEN** the view keeps its scroll position and the selection is on the nearest surviving row, as it is when the key removes the selected row

#### Scenario: A crossing changes nothing about a task

- **WHEN** the window is crossed with work tasks in the shown view
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: The window is crossed in another view

- **WHEN** the window is crossed while a view other than today is shown
- **THEN** the mode changes there too, because the mode applies to every view the board shows

## MODIFIED Requirements

### Requirement: Hiding the work tasks

The board SHALL offer a key that hides every task belonging to the work project, and the same key SHALL bring them back. There SHALL be two states and no third.

Where a working window is configured, the mode SHALL also be set by the clock:
outside the window it is on, inside it is off, from the moment the board opens.
The key SHALL still offer two states and no third -- pressing it sets the mode
to the opposite of whatever is in force, whether the clock or an earlier press
put it there. There SHALL be no key and no state meaning "follow the clock
again": the window's next crossing restores that by itself.

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

#### Scenario: Opening outside the window

- **WHEN** a person opens the board outside the configured working window
- **THEN** the work tasks are already hidden, with no key pressed

#### Scenario: The key still flips what the clock set

- **WHEN** the clock has hidden the work and a person presses the key
- **THEN** the work tasks are shown, and pressing the key again hides them: the key has the same two states it always had

### Requirement: How long the work filter lasts, and where it applies

The mode SHALL apply to every view the board shows, so that moving between days does not change what the mode means. It SHALL last as long as the board is open and no longer.

Where a working window is configured, a press SHALL last until the window is
next crossed, and SHALL then lapse, leaving the clock's answer in force.

Where a press disagreed with the clock, its lapse SHALL NOT change what is
shown: it falls at the crossing where the clock comes to say what the press
already said, so nothing moves because a press expired.

Where a press left the mode where the clock already had it, the crossing SHALL
act as though no key had been pressed at all. Pressing the key twice SHALL
leave a person in the same position as pressing it none.

Where no working window is configured, a press SHALL last as long as the board
is open, there being no crossing for it to lapse at.

#### Scenario: The mode follows the person between views

- **WHEN** a person hides the work tasks and then moves to another day or to the someday view
- **THEN** the work tasks are hidden there too, without the key being pressed again

#### Scenario: The mode does not outlive the board

- **WHEN** a person hides the work tasks, closes the board, and opens it again
- **THEN** every task is shown, or hidden because the window says so, and never because of the earlier press

#### Scenario: A press to see work in the evening

- **WHEN** a person presses the key after the window has closed to bring the work back, and the window's start then passes
- **THEN** the work is still shown and nothing on screen has moved: the press lapsed into the same answer the clock gives

#### Scenario: A press to hide work during the day

- **WHEN** a person presses the key inside the window to hide the work, and the window's end then passes
- **THEN** the work is still hidden and nothing on screen has moved

#### Scenario: Pressed twice, back where the clock had it

- **WHEN** a person presses the key twice outside the window, ending with the work hidden as the clock had it, and the window's start then passes
- **THEN** the work returns as it would have without either press

#### Scenario: A press lapses only at a crossing

- **WHEN** a person presses the key and the window is not crossed
- **THEN** the mode stays as they left it, however long they leave it

#### Scenario: With no window, a press lasts the session

- **WHEN** no working window is configured and a person hides the work tasks
- **THEN** they stay hidden until the key is pressed again or the board is closed

### Requirement: The board says when it is hiding work

When work tasks are being hidden, the board SHALL say so where it already
reports what the shown view holds, and SHALL report how many rows the mode
removed. A view that is quietly shorter than expected SHALL NOT be
indistinguishable from a day with less on it.

Where the clock is hiding the work rather than a person's press, the board
SHALL say which boundary is doing it -- the hour or the day -- alongside the
count. A board that shortened itself SHALL NOT be indistinguishable from one a
person shortened.

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

#### Scenario: The hour hid it

- **WHEN** work is hidden because the hour is outside the window
- **THEN** the board says so, naming the hour the window ends, alongside the count it already reports

#### Scenario: The day hid it

- **WHEN** work is hidden because the day is outside the window
- **THEN** the board says the day is outside the working week, alongside the count

#### Scenario: A person hid it

- **WHEN** work is hidden by a press inside the window
- **THEN** the board reports the count as it always has and names no boundary, because none is doing it
