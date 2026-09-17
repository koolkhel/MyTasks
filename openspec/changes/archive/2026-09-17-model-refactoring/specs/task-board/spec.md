## ADDED Requirements

### Requirement: What the board draws is decided without a terminal

Given the board's state -- the tasks it has fetched, the writes it has in
flight, the day or bucket being shown, the marks, the search, the work filter,
and what the calendar, the tracker and the mailbox last answered -- what the
board would draw SHALL be answerable without starting a user interface. That
answer SHALL cover the rows and their order, the text of every cell, the status
line, the counts the status line reports, and which of the marks survive.

The board SHALL put on screen exactly that answer, rather than computing the
same thing a second time on its way to the screen. Two expressions of what a
row says, kept in step by hand, drift the moment one of them is edited, and
they drift silently: nothing connects them.

Deciding what to draw SHALL NOT consult the screen. It SHALL NOT read a widget,
require a terminal, or depend on a user interface having been started. Where a
decision genuinely needs a measurement only the screen can supply -- how wide
the title column came out, which row the cursor was on, how far the view was
scrolled -- that measurement SHALL be given to the decision as a value, and the
decision SHALL answer from it rather than fetch it.

This is a constraint on where the answer comes from, not on what it says.
Everything this specification requires the board to draw -- how a row is
presented, how the day is ordered, where events and issues fall, what each
source contributes to the counts, and where the list sits after a redraw --
holds exactly as written.

#### Scenario: What would be drawn, asked without a screen

- **WHEN** the board's state is given and no user interface has been started
- **THEN** the rows, their order, every cell's text, the status line and its counts are answered

#### Scenario: The screen shows the answer, not a second opinion

- **WHEN** the board draws itself
- **THEN** every cell on screen is the text that answer gave, and no cell is composed on the way to the screen

#### Scenario: Deciding reaches no widget

- **WHEN** what to draw is being decided
- **THEN** nothing is read from a widget, and the decision completes on a machine with no terminal at all

#### Scenario: A measurement from the screen is given, not fetched

- **WHEN** what to draw depends on the width a column came out at, the row the cursor was on, or how far the view was scrolled
- **THEN** those are supplied to the decision as values, and the decision answers from what it was given
