## ADDED Requirements

### Requirement: A published picture of the board is the board itself, on invented data

Every picture published with the board SHALL be taken from the board itself
-- the application running, drawn by its own code -- and never drawn by hand
or assembled. What a picture shows is what the board does.

Every task, event, issue, message, project, tag, account and version in a
published picture SHALL be invented. No name, title, key, address or date
from any real account SHALL reach a picture, and the means of taking a
picture SHALL make that so by construction rather than by care: the board
in a picture SHALL be given a stubbed store and replaced sources, SHALL read
no token and build no client, and SHALL be unable to reach the store, the
calendar, the tracker or a mailbox however it is driven.

Where a picture is taken of the board running in a real terminal, so that the
terminal's own rendering is what is shown, the same SHALL hold for the board
served into that terminal: it is the same invented board, with the same rows,
marks and cursor the picture would otherwise show, and a key pressed in that
window SHALL change nothing anywhere but in the stub. The terminal window
SHALL be one the picture-taking opened for the purpose, told apart from any
other window of the same application by having appeared, not by its title --
the board names its own tab, so two of its windows share a title.

Taking a picture of a real window needs the system's permission to record the
screen, which nothing here can grant. Where it is refused, the picture-taking
SHALL say so and write no picture; a black or empty picture written as if it
were the board would be worse than none.

The pictures SHALL be reproducible by one command from the repository, so
that a new feature can be shown by describing a board and running it.

#### Scenario: A picture is the board, drawn by the board

- **WHEN** a published picture is made
- **THEN** it is produced by running the board on the described data, not composed by any other means

#### Scenario: Nothing real reaches a picture

- **WHEN** the board is run for a picture
- **THEN** its store is a stub, its calendar, tracker and mailbox are replaced, no token is read and no client is built

#### Scenario: A served board is the pictured board

- **WHEN** a board is served into a real terminal for a picture
- **THEN** it holds the same rows, the same marked rows and the same selected row the same picture shows when drawn without a terminal

#### Scenario: Keys in a served window reach nothing

- **WHEN** a key that writes is pressed in a board served for a picture
- **THEN** the change is made in the stub alone and nothing is sent anywhere

#### Scenario: The window is the one that appeared

- **WHEN** a terminal window is opened for a picture while another window of the same terminal is already showing the board
- **THEN** the picture is of the window that appeared, and the other is untouched

#### Scenario: A refused capture writes nothing

- **WHEN** the system refuses to let the screen be recorded
- **THEN** the picture-taking says so, names what would put it right, and writes no picture

#### Scenario: One command remakes the pictures

- **WHEN** the picture-taking is run from the repository
- **THEN** every published picture is produced again from the described boards
