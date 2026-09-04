## ADDED Requirements

### Requirement: The board offers the Turbo C++ themes

The board SHALL offer two themes reproducing the Turbo C++ editor theme: one on a black ground and one on the classic blue. Their ordinary text, selection, error and link colours SHALL be those the editor theme itself declares, not approximations. Where a declared value cannot serve this board, the theme MAY depart from it, and each departure SHALL be recorded with its reason. Both themes SHALL be selectable while the board is running, and the board SHALL start on the black ground.

#### Scenario: Both themes are offered

- **WHEN** the board is running
- **THEN** both the black-ground and the blue Turbo theme are available to choose from, alongside the themes the framework already provides

#### Scenario: The board starts in the dark one

- **WHEN** the board is opened
- **THEN** the black-ground Turbo theme is active

#### Scenario: Switching between them needs no restart

- **WHEN** a person chooses the other Turbo theme while the board is running
- **THEN** the board is redrawn in it immediately

#### Scenario: The colours are the editor theme's own

- **WHEN** either Turbo theme's colours are compared with the editor theme it reproduces
- **THEN** the ordinary text, the selection, the error colour and the link colour are the values that theme declares

#### Scenario: A departure from the source is deliberate

- **WHEN** a theme's colour differs from the value the editor theme declares for that role
- **THEN** the difference is one the board needed — a ground chosen to sit on a black terminal, or a muted colour the source leaves identical to its ordinary text — and not an accident of transcription

### Requirement: A theme keeps the board's distinctions visible

Whatever theme is active, the board SHALL keep apart the things its other requirements rely on being told apart: a past-due title from an ordinary one, muted text from ordinary text, the selected row from the rest, and the text on any bar or panel from the surface behind it. A theme that renders any of these indistinguishable SHALL NOT be offered.

#### Scenario: A past-due title still reads as past due

- **WHEN** today's view holds both a past-due task and one due today, under any offered theme
- **THEN** the two titles are drawn in different colours

#### Scenario: Muted text is still muted

- **WHEN** the board draws muted text — the status line, the project column, the detail strip, the key bar's labels — under any offered theme
- **THEN** it is a different colour from an ordinary task title

#### Scenario: The selected row still stands out

- **WHEN** a row is selected under any offered theme
- **THEN** its background differs from the surrounding rows and its text is legible against that background

#### Scenario: Text on a bar is legible against it

- **WHEN** a theme gives a bar or panel a light background
- **THEN** the text drawn on it is dark rather than light, and the reverse for a dark background

#### Scenario: A link is not mistaken for ordinary text

- **WHEN** a task's title carries a link under any offered theme
- **THEN** the link is drawn differently from the rest of the title
