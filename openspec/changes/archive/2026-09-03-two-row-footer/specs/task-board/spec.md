## ADDED Requirements

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
