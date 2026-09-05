## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Help lists the available keys

The board SHALL offer an in-app help overlay listing the keys it responds to. The overlay SHALL list only keys the board actually binds, and SHALL NOT advertise a priority action. It SHALL name each key in English only, and SHALL state that the keys work in either keyboard layout without naming the other layout's characters.

#### Scenario: Opening help

- **WHEN** a person opens the help overlay
- **THEN** it lists the movement, day-navigation, and task actions the board supports, with no priority entry

#### Scenario: Help says the keys work in either layout

- **WHEN** a person opens the help overlay
- **THEN** it says the keys work whichever keyboard layout is active, and shows no key spelled in any layout other than English

### Requirement: The key bar shows every key without clipping

The board SHALL display at all times the keys it responds to and what each one does. The bar SHALL wrap across as many rows as it takes for every entry to be shown in full: no label may be omitted, and none may be cut off part-way through a word.

The bar SHALL name every action the board offers for display, once each, by the English key a person presses for it. Where an action answers more than one key — an arrow beside a letter, a second key that deletes, or the character the same physical key gives in another layout — the bar SHALL show the one key and not the alternatives, so that offering more ways to reach an action never widens the bar. The bar SHALL NOT name a key that does nothing.

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

#### Scenario: Alternatives do not widen the bar

- **WHEN** an action answers several keys, whether an arrow, a second key, or another layout's character
- **THEN** the bar shows one entry for that action, naming the English key, and the bar is no wider than if the action answered that key alone
