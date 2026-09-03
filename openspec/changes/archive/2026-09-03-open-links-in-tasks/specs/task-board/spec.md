## ADDED Requirements

### Requirement: A task's link is recognised and readable

The board SHALL recognise a link written in a task's title, whether stored as an HTML anchor or written as a plain `http` or `https` address. Where a title holds an anchor, the board SHALL show the anchor's readable text in place of the stored markup, so no row or card ever displays raw HTML. The surrounding words of the title SHALL be preserved. An address written without a scheme SHALL be understood as `https`.

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
- **THEN** the first is the task's link, and every one of them is still shown in the title

#### Scenario: Markup characters in a title are shown, not interpreted

- **WHEN** a task's title contains square brackets
- **THEN** they appear in the row exactly as stored, rather than being consumed as styling

### Requirement: Opening a task's link

The board SHALL let a person open the selected task's link, handing the address to the operating system. This SHALL work without a mouse and without depending on the terminal's own capabilities. The board SHALL additionally present the address so that a terminal able to make hyperlinks clickable can do so, but SHALL NOT rely on that for the link to be reachable.

Only `http` and `https` addresses SHALL be opened. A title is ordinary text that happens to be passed to the system opener, so no other scheme may be launched through it.

#### Scenario: Opening the link of the selected task

- **WHEN** a person asks to open the link of a task that has one
- **THEN** the address is handed to the operating system to open

#### Scenario: A task with no link

- **WHEN** a person asks to open the link of a task that has none
- **THEN** nothing is opened and the board says the task has no link

#### Scenario: Nothing is selected

- **WHEN** a person asks to open a link while the shown view holds no tasks
- **THEN** nothing is opened and the board is left as it was

#### Scenario: An address of another kind is refused

- **WHEN** a task's title contains an address whose scheme is neither `http` nor `https`
- **THEN** it is not opened

#### Scenario: Opening a link changes nothing

- **WHEN** a person opens a task's link
- **THEN** the task is not modified and no request that changes anything is sent

#### Scenario: Available wherever a task is selected

- **WHEN** a task with a link is selected in the inbox or in the someday view
- **THEN** its link can be opened just as from a day

## MODIFIED Requirements

### Requirement: Task row presentation

Each task in the shown day SHALL be presented as a row carrying its completion mark, its start time, its title, and its project name. The title SHALL be shown as readable text: any link markup stored in it is rendered as the address it points to rather than displayed raw, and any character that the display treats as styling is shown as written. A past-due task SHALL instead show how overdue it is in place of its start time, and SHALL have its title rendered in a colour that sets it apart from the tasks due today. Title emphasis SHALL otherwise convey completion state only. The board SHALL NOT vary a title's weight, dimming, or colour according to the task's priority.

#### Scenario: An open task is shown plainly

- **WHEN** the day contains an open task
- **THEN** its title is rendered without emphasis, regardless of the priority stored on that task

#### Scenario: A finished task is struck through

- **WHEN** a task in the day is completed or cancelled
- **THEN** its title is rendered struck through and dimmed

#### Scenario: Two tasks differing only in priority look identical

- **WHEN** the day contains two open tasks whose stored priorities differ
- **THEN** neither row is emphasised relative to the other

#### Scenario: A past-due row is set apart

- **WHEN** today's view holds both a past-due task and a task due today
- **THEN** the past-due row shows how overdue it is where the other shows a time, and its title is coloured while the other's is not

#### Scenario: A row never shows stored markup

- **WHEN** a task's title holds an HTML anchor
- **THEN** the row shows the readable address and none of the surrounding tags

### Requirement: Actions available on the selected task

The board SHALL let a person add a task to the shown view, tick and untick the selected task, mark it done for today, cancel it, rename it, assign or clear its date, open its link, and delete it behind a confirmation. The board SHALL NOT offer any action that changes a task's priority.

#### Scenario: No key cycles priority

- **WHEN** a person presses a key that is not bound to one of the offered actions
- **THEN** the selected task's stored priority is left untouched

#### Scenario: Ticking a recurring task

- **WHEN** a person ticks a task that recurs
- **THEN** it is completed the same way any other task is, because ticking never means "done for this occasion"

#### Scenario: Every action is available in every view

- **WHEN** a task is selected in the inbox or in the someday view
- **THEN** the same actions offered in a day view are offered there, date assignment, done for today and opening a link included
