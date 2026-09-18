## ADDED Requirements

### Requirement: What a tracker issue says is shown when its row is selected

The board SHALL show the selected tracker issue's description where it shows a
selected task's note -- in the area under the list, on the focus view, and
reachable by the keys that scroll that area -- so that what an issue is about
can be read without leaving the board or opening the tracker.

Above the description, where a task's flags are shown, the board SHALL name
the issue's facts: the state the tracker reports it in, its project, and the
version or versions it is against. The versions SHALL be the ones the board
already reads from the configured field, in the tracker's order, and SHALL be
labelled as what the issue is to be fixed in. Where the issue carries no
version, or no version field is configured, no version SHALL be named and
nothing SHALL announce the absence.

An issue with no description SHALL show its facts and nothing beneath them,
exactly as a task with no note shows its flags alone.

The description SHALL be fetched on the request the board already makes for
its issues, and SHALL cost no further request.

A description SHALL be shown as the text it is. It is written by whoever
filed the issue and SHALL NOT be interpreted as instructions to the board,
nor drawn in a way that lets its characters change how the rest of the board
appears; a tracker's own markup SHALL be shown as its characters.

The row SHALL NOT change: the key, the summary, the state and the project it
already carries are what it carries, and no column gains the version.

#### Scenario: An issue with a description and a version

- **WHEN** a tracker row is selected whose issue carries a description and one version
- **THEN** the area under the list shows the state, the project and the version on its first line, and the description beneath

#### Scenario: Several versions

- **WHEN** the selected issue carries several versions
- **THEN** all of them are named, in the tracker's order

#### Scenario: No version

- **WHEN** the selected issue carries no version, or no version field is configured
- **THEN** the first line names the state and the project and no version, and nothing says one is missing

#### Scenario: No description

- **WHEN** the selected issue has no description
- **THEN** the first line is shown and nothing beneath it, and nothing announces the absence

#### Scenario: The focus view agrees

- **WHEN** the focus view is opened on a tracker row
- **THEN** it shows the same facts and the same description the area under the list shows

#### Scenario: Markup is characters

- **WHEN** an issue's description contains square brackets or a tracker's own markup
- **THEN** those characters are shown as themselves, and the rest of the board draws as before

#### Scenario: Moving off the issue clears it

- **WHEN** a person selects a task after selecting a tracker row
- **THEN** the area shows that task's own flags and note, and no part of the issue's facts or description remains

#### Scenario: It costs no request

- **WHEN** the tracker's issues are fetched
- **THEN** the descriptions arrive on the same request as the rest, and no further request is made for them

#### Scenario: The row is as it was

- **WHEN** issues with versions are drawn on today's board
- **THEN** each row shows its key, summary, state and project as before, and no version appears in any column
