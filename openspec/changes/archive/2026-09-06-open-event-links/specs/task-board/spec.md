## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Only web addresses are opened

Only `http` and `https` addresses SHALL be opened. A title, an event's
location and an event's description are all ordinary text that happens to be
passed to the system opener, so no other scheme may be launched through any of
them.

#### Scenario: An address of another kind is refused

- **WHEN** a task's title contains an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened

#### Scenario: An event's address of another kind is refused

- **WHEN** an event's location or description holds an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened, and the event is treated as carrying no address unless it holds another that may be
