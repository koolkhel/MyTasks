## MODIFIED Requirements

### Requirement: The key bar names each action once, by its English key

The bar SHALL name every action the board offers for display, once each, by the English key a person presses for it. Where an action answers more than one key — an arrow beside a letter, a second key that deletes, or the character the same physical key gives in another layout — the bar SHALL show the one key and not the alternatives, so that offering more ways to reach an action never widens the bar. The bar SHALL NOT name a key that does nothing.

The key a person presses is the character on the keycap, not the name the
toolkit gives it. Where those differ, the bar SHALL show the character. That holds of
the bar as drawn, not only of the entry behind it: a key that is itself a
character the display treats as styling SHALL be drawn as that character and
SHALL NOT be taken for styling. Otherwise the character opens a tag, the bar
shows the tag it failed to close, and the promise above is kept everywhere
except on screen.

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

#### Scenario: A key that is a markup character, as drawn

- **WHEN** the bar is drawn and one of the keys it names is a character the display treats as styling
- **THEN** the row on screen shows that character followed by its label, and no part of the bar's own styling appears as text

## ADDED Requirements

### Requirement: What the board says and what it asks are shown as their characters

The status line and every prompt SHALL show the text they are given as the
characters it contains. Both draw their text as markup, so text the board did
not write SHALL NOT be taken for styling — a task's title above all, which is
quoted inside most of what the board says and asks.

A prompt SHALL include the things it offers to choose between. A project's
name and a label read out of a task or a message are as foreign as a title,
and a list drawn as markup loses them the same way.

This is the rule the rows, the notes and the focus card already follow, said
of the two places that had been left out. It matters most where it is least
visible: a title holding square brackets loses them silently in a prompt,
which asks a person to confirm an action against a name that is not the name
of their task.

#### Scenario: A title that reads as markup, in a prompt

- **WHEN** a person opens a prompt on a task whose title contains square brackets — the date, project or link picker, the note editor, or the confirmation before deleting
- **THEN** the prompt shows the title as written, with every character of it, and applies no styling by it

#### Scenario: A title that reads as markup, in the status line

- **WHEN** the board says something naming a task whose title contains square brackets
- **THEN** the status line shows the title as written and loses no part of it

#### Scenario: A name or a label that reads as markup, among things to choose

- **WHEN** a prompt lists things to choose between and one of them contains square brackets — a project's name, or a label taken from a task or a message
- **THEN** the list shows it as written, with every character of it

#### Scenario: Nothing the board writes itself is altered

- **WHEN** the board says something with no such text in it
- **THEN** the message reads exactly as it did before, and the status line's own error styling still applies
