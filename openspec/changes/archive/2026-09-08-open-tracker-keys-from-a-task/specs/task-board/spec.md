## ADDED Requirements

### Requirement: Choosing among several things a task can open

Where the selected task offers more than one thing to open, the board SHALL
ask which one, rather than choosing on a person's behalf. Silently opening the
first leaves the others unreachable and gives no sign that they exist.

The choices SHALL be offered in the order they appear in the task — its title
first, then its note — so that their order needs no rule to be predictable.
Each SHALL be readable enough to be told apart: an issue by its key, an
address by the address.

Leaving without choosing SHALL open nothing and write nothing. Choosing SHALL
open exactly the one chosen.

Where the task offers exactly one thing, it SHALL be opened directly and no
choice SHALL be presented. Where it offers none, the board SHALL say the task
has no link.

#### Scenario: A task offering an issue and an address

- **WHEN** a person asks to open the link of a task whose text holds both a tracker issue key and a web address
- **THEN** the board asks which to open, listing both

#### Scenario: A task offering several addresses

- **WHEN** a person asks to open the link of a task whose text holds more than one web address
- **THEN** the board asks which to open, rather than opening the first

#### Scenario: The order they are offered in

- **WHEN** a task holds one thing to open in its title and another in its note
- **THEN** the one from the title is offered first

#### Scenario: Choosing one

- **WHEN** a person chooses one of the offered items
- **THEN** that one is opened and no other is

#### Scenario: Leaving the choice

- **WHEN** a person leaves the choice without choosing
- **THEN** nothing is opened, and the task is unchanged

#### Scenario: Only one thing to open

- **WHEN** a task offers exactly one thing to open
- **THEN** it is opened at once and nothing is asked

## MODIFIED Requirements

### Requirement: A task's link is recognised and readable

The board SHALL recognise a link written in a task's title or in its note, whether stored as an HTML anchor or written as a plain `http` or `https` address. Where a title holds an anchor, the board SHALL show the anchor's readable text in place of the stored markup, so no row or card ever displays raw HTML. The surrounding words of the title SHALL be preserved. An address written without a scheme SHALL be understood as `https`.

The board SHALL also recognise a task's mention of a tracker issue, written as one of the configured tracker projects followed by a number, and SHALL treat that issue's page in the tracker as something the task can open. Only the configured projects SHALL be recognised, so that ordinary text shaped like a key — a version, a standard, a year — is never taken for an issue. Where no tracker is configured, no key SHALL be recognised.

A task's note SHALL be read for the same things its title is read for. A note is where an address is most naturally kept, and a rule that recognised an issue key there but not an address, or the reverse, could not be remembered.

Recognising an issue key SHALL NOT change how a title is drawn. The key is shown as the text it is.

#### Scenario: A title storing an HTML anchor

- **WHEN** a task's title contains an HTML anchor around an address
- **THEN** the title is shown as its readable text with the surrounding words intact, and the stored markup is not displayed

#### Scenario: A title with a plain address

- **WHEN** a task's title contains a plain `https` address and no markup
- **THEN** the title is shown unchanged and that address is recognised as its link

#### Scenario: An address with no scheme

- **WHEN** a task's link is stored without a scheme, as a bare domain
- **THEN** it is understood as an `https` address

#### Scenario: A title with no link

- **WHEN** a task's title contains no address
- **THEN** the title is shown exactly as stored and the task has no link

#### Scenario: A title holding more than one address

- **WHEN** a task's title contains several addresses
- **THEN** all of them are things the task can open, and every one of them is still shown in the title

#### Scenario: Markup characters in a title are shown, not interpreted

- **WHEN** a task's title contains square brackets
- **THEN** they appear in the row exactly as stored, rather than being consumed as styling

#### Scenario: A mention of a tracker issue

- **WHEN** a task's text names one of the configured tracker projects followed by a number
- **THEN** that issue's page in the tracker is something the task can open, and the text is shown as written

#### Scenario: Text that only looks like an issue key

- **WHEN** a task's text holds a word shaped like a project key and a number, whose project is not one of the configured ones
- **THEN** it is not treated as an issue and nothing is offered for it

#### Scenario: An address kept in the note

- **WHEN** a task's note holds an address and its title holds none
- **THEN** the address is something the task can open

#### Scenario: No tracker configured

- **WHEN** no tracker is configured and a task's text names something shaped like an issue key
- **THEN** no issue is recognised, and the task's addresses are unaffected

### Requirement: Opening a task's link

The board SHALL let a person open the selected task's link, handing the address to the operating system. This SHALL work without a mouse and without depending on the terminal's own capabilities. The board SHALL additionally present the address so that a terminal able to make hyperlinks clickable can do so, but SHALL NOT rely on that for the link to be reachable.

Where the task offers more than one thing to open, the board SHALL ask which, as its own requirement states. A person pressing the key SHALL never have to know in advance whether they will be asked.

#### Scenario: Opening the link of the selected task

- **WHEN** a person asks to open the link of a task that has one
- **THEN** the address is handed to the operating system to open

#### Scenario: A task with no link

- **WHEN** a person asks to open the link of a task that has none
- **THEN** nothing is opened and the board says the task has no link

#### Scenario: Nothing is selected

- **WHEN** a person asks to open a link while the shown view holds no tasks
- **THEN** nothing is opened and the board is left as it was

#### Scenario: Opening a link changes nothing

- **WHEN** a person opens a task's link
- **THEN** the task is not modified and no request that changes anything is sent

#### Scenario: Available wherever a task is selected

- **WHEN** a task with a link is selected in the inbox or in the someday view
- **THEN** its link can be opened just as from a day

#### Scenario: Opening an issue named by a task

- **WHEN** a person asks to open the link of a task whose only openable thing is a mention of a tracker issue
- **THEN** that issue's page in the tracker is opened, without a choice being presented

### Requirement: Only web addresses are opened

Only `http` and `https` addresses SHALL be opened. A task's title, a task's
note, an event's location and an event's description are all ordinary text
that happens to be passed to the system opener, so no other scheme may be
launched through any of them.

An issue's page SHALL be built from the tracker's configured location, not
taken from a task's text, so a mention of an issue cannot name an address of
its own.

#### Scenario: An address of another kind is refused

- **WHEN** a task's title contains an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened

#### Scenario: An event's address of another kind is refused

- **WHEN** an event's location or description holds an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened, and the event is treated as carrying no address unless it holds another that may be

#### Scenario: An address of another kind in a note is refused

- **WHEN** a task's note holds an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened, and is not offered as something the task can open

#### Scenario: An issue's address comes from the configuration

- **WHEN** a task mentions a tracker issue
- **THEN** the address opened is built from the tracker's configured location and the issue's key, and nothing in the task's text can change it
