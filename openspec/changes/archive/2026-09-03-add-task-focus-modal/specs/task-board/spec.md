## ADDED Requirements

### Requirement: Focus view of the selected task

The board SHALL offer a focus view of the selected task, showing its title in full without truncation, when it is due, its project when it has one, its deadline when it has one, and its note when it has one. The view SHALL be dismissable, and dismissing it SHALL return to the same view and the same selected task.

#### Scenario: Opening the focus view

- **WHEN** a person opens the focus view on a selected task
- **THEN** the task's whole title is shown, along with when it is due and its project

#### Scenario: A long title is not cut off

- **WHEN** the selected task's title is longer than the width the task list gives it
- **THEN** the focus view shows the title in full, unlike the row it was opened from

#### Scenario: A task with a note and a deadline

- **WHEN** the selected task has a note and a deadline
- **THEN** the focus view shows both

#### Scenario: A task with nothing optional set

- **WHEN** the selected task has no project, no deadline, and no note
- **THEN** the focus view shows its title and when it is due, and omits the parts it has nothing to show for

#### Scenario: Dismissing returns to the board

- **WHEN** a person dismisses the focus view
- **THEN** the board is shown again, in the same view, with the same task still selected

#### Scenario: Available in every view

- **WHEN** a task is selected in the inbox or in the never view
- **THEN** the focus view can be opened on it just as from a day

#### Scenario: Nothing is selected

- **WHEN** a person asks for the focus view while the shown view holds no tasks
- **THEN** no focus view opens and the board is left as it was

### Requirement: The focus view changes nothing

Opening, viewing, or dismissing the focus view SHALL leave the task exactly as it was, and SHALL send no request that modifies anything. In particular the key that opens the focus view SHALL NOT also tick the task, so a task cannot be completed by looking at it.

#### Scenario: Opening the focus view does not complete the task

- **WHEN** a person opens the focus view on an unfinished task and dismisses it
- **THEN** the task is still unfinished

#### Scenario: No request is sent

- **WHEN** a person opens and dismisses the focus view
- **THEN** the board sends no request that creates, updates, or deletes anything

#### Scenario: Ticking still has its own way in

- **WHEN** a person wants to tick the selected task
- **THEN** an action distinct from the one that opens the focus view does it
