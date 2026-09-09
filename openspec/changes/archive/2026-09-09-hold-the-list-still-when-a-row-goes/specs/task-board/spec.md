## ADDED Requirements

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

## MODIFIED Requirements

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
