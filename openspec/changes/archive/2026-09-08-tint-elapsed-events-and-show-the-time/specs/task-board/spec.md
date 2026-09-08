## ADDED Requirements

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
