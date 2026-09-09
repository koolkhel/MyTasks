## ADDED Requirements

### Requirement: Mail counts as work

A mail row SHALL be treated as work, so that the key which hides work hides it
too, and the count of what was hidden includes it. Every message the board
reads comes from a corporate account, so there is no mail it reads that is not
work.

Every mail row SHALL count, whatever folder it came from and whoever sent it.
This is unconditional, as a tracker issue's is, rather than decided per
account as an event's is: the board reads one account and its folders are all
corporate, so there is nothing for a per-account rule to distinguish. A second
mailbox that was not work would be the reason to make it conditional, and
until there is one, a rule that appeared to choose would be describing a choice
that is not being made.

Mail is shown only in the inbox, and the inbox is the one view where hiding
work removes nothing at all — a task with a project is already outside it. So
hiding work there SHALL leave the inbox's own tasks, which is the whole of what
the key does in that view.

The counts of mail rows and of the messages they stand for SHALL report what
is on screen, so they SHALL fall away while mail is hidden. The board already
undertakes to report how many rows of mail it *is showing*; this is that
undertaking held to when some of them are not.

Hiding mail SHALL change nothing about the account. No message SHALL be moved,
no flag SHALL be set, and the mailbox SHALL NOT be read again because rows
were hidden or shown: the key decides only which of the rows a view already
chose are painted.

#### Scenario: Hiding work hides the mail

- **WHEN** work is hidden and the inbox holds mail
- **THEN** every mail row disappears, and pressing the key again brings them all back

#### Scenario: What is left is the person's own queue

- **WHEN** work is hidden in an inbox holding both mail and undated tasks
- **THEN** the tasks remain and are the whole of the view

#### Scenario: The hidden count includes them

- **WHEN** work is hidden in the inbox and the board reports how many rows that removed
- **THEN** the mail rows it removed are included in that count, so the inbox no longer says it is hiding work without saying how much

#### Scenario: Every mail row counts

- **WHEN** work is hidden and the inbox holds mail from every folder the board reads
- **THEN** no mail row is left behind by folder or by sender

#### Scenario: The counts follow what is shown

- **WHEN** work is hidden in the inbox
- **THEN** the board reports no mail rows and no messages, and reports them again when the key is pressed a second time

#### Scenario: The order comes back unchanged

- **WHEN** a person hides the mail and shows it again
- **THEN** the rows are in the order they were, still below the inbox's tasks

#### Scenario: The account is untouched

- **WHEN** a person hides or shows the mail
- **THEN** no message is moved, no flag is set, and the mailbox is not read again on account of it

## MODIFIED Requirements

### Requirement: Hiding the work tasks

The board SHALL offer a key that hides every task belonging to the work project, and the same key SHALL bring them back. There SHALL be two states and no third.

Hiding SHALL remove rows from the view without changing any task: no write SHALL be made, and nothing SHALL be altered about a task because it was hidden or shown.

Rows the board draws from a source rather than from the task store SHALL be
subject to the same key, on each source's own terms, and SHALL be filtered
where the store's tasks are filtered rather than added to the view afterwards.
A source whose rows are appended after the filtering is a source the key
cannot reach, however the rows are marked.

#### Scenario: Hiding and showing again

- **WHEN** a person presses the key with work tasks in the shown view
- **THEN** those tasks disappear from it, and pressing the key again brings them back exactly as they were

#### Scenario: Nothing is written

- **WHEN** a person hides or shows the work tasks
- **THEN** no request is sent to change a task, and every task is exactly as it was

#### Scenario: A view with no work tasks

- **WHEN** a person hides the work tasks in a view that holds none
- **THEN** the view is unchanged and the board still shows that the mode is on

#### Scenario: The inbox is unaffected

- **WHEN** the mode is on and the inbox is displayed
- **THEN** none of its tasks are hidden, because a task with a project is already outside the inbox

#### Scenario: But the inbox's mail is not

- **WHEN** the mode is on and the inbox is displayed with mail in it
- **THEN** the mail rows are hidden, because all mail is work, so the view is not what it would be with the mode off

#### Scenario: No source is reached only by being marked

- **WHEN** the board draws rows from a source and those rows count as work
- **THEN** they are filtered together with the store's tasks, and no source's rows reach the view past the filter
