## ADDED Requirements

### Requirement: A mail row says when its issue is already done

Where a mail row is about an issue in a tracker, and the tracker has marked
that issue done, the board SHALL say so on the row. An issue that is finished
needs no decision, and a queue that shows it exactly like one still being
argued over makes a person open the tracker to tell them apart.

The board SHALL read this from the notification itself and SHALL NOT ask the
tracker. Reading mail needs no network and no credentials, and that SHALL
remain true: a board whose tracker is unreachable, or that has none configured
at all, SHALL mark its rows exactly as one that can reach it.

The fact SHALL be taken from how the notification presents the issue it is
about, rather than from any wording it contains. The states an issue moves
through are named in whatever language and vocabulary the tracker's own
workflow uses, and a board matching those names would be tied to that wording
and would fall silent the day somebody edited it.

Done SHALL mean what the tracker means by it, including an issue that has been
closed without being fixed. Neither kind wants attention again, which is the
whole of what the mark is for.

The newest message in the row SHALL decide, being the most recent word on the
issue and the message the row already shows. Where a row's mail carries no such
presentation at all -- a notification from something that is not the tracker, a
message with no issue in it -- the row SHALL simply not be marked, and SHALL
NOT be reported as a fault.

The mark SHALL say what the last notification said. Where an issue is reopened
and no further notification arrives, the row SHALL go on showing what it was
last told; the board SHALL NOT claim to know the tracker's present state.

#### Scenario: A row whose issue is done

- **WHEN** the newest message in a mail row presents its issue as done
- **THEN** the row says so

#### Scenario: A row whose issue is not done

- **WHEN** the newest message in a mail row presents its issue as unfinished
- **THEN** the row does not say it is done

#### Scenario: The newest message decides

- **WHEN** a row's older messages present the issue as unfinished and its newest presents it as done
- **THEN** the row says it is done, the newest message being the most recent word on it

#### Scenario: An issue closed without being fixed

- **WHEN** an issue is closed as one that will not be fixed, and the tracker marks it done
- **THEN** the row says it is done, because it wants no more attention either

#### Scenario: Nothing is asked of the tracker

- **WHEN** rows are drawn for mail about issues
- **THEN** no request is made to the tracker, and the rows are marked the same whether a tracker is configured, unreachable, or absent

#### Scenario: Mail that is not about an issue

- **WHEN** a mail row's messages carry no issue presentation at all
- **THEN** the row is not marked and nothing is reported as having failed

#### Scenario: No state name is read

- **WHEN** the board decides whether a row's issue is done
- **THEN** it reads how the issue is presented rather than any state name, so that renaming a state in the tracker's workflow changes nothing here

#### Scenario: The mark is as old as the last notification

- **WHEN** an issue is reopened in the tracker and no further notification arrives
- **THEN** the row still says what the last notification said, the board never having asked the tracker anything

## MODIFIED Requirements

### Requirement: What a mail row shows

A mail row SHALL show when its newest message arrived, who it is from, what it
is about, and — where the thread holds more than one message — how many.

The row SHALL be distinguishable from a task at a glance, and not by colour
alone, as a calendar event's row and a tracker issue's row already are.

Where a sender or a subject is longer than its column, it SHALL be shortened
rather than pushing the row's other columns off the screen.

A subject SHALL be shown as the text it is. It is written by whoever sent the
message and SHALL NOT be interpreted as instructions to the board, nor drawn
in a way that lets its characters change how the rest of the board appears.

Where a row's issue has been marked done by its tracker, the row SHALL show
that, in the way the board already shows a task that is finished rather than in
a way of its own. A person reads one list, and a second vocabulary for "this is
finished" would be a second thing to learn.

#### Scenario: A thread of several messages

- **WHEN** a thread holds more than one message
- **THEN** its row shows the newest arrival, the sender, the subject, and how many messages there are

#### Scenario: A thread of one

- **WHEN** a thread holds a single message
- **THEN** its row shows the same things, without a count

#### Scenario: A mail row is not mistaken for a task

- **WHEN** the inbox is shown with mail in it
- **THEN** a mail row is marked apart from a task's row, and colour is not what distinguishes them

#### Scenario: A subject with markup characters in it

- **WHEN** a subject contains square brackets or text that reads as markup
- **THEN** every character appears as sent, no styling is applied by it, and the rest of the board is drawn as it was

#### Scenario: A subject too long for its column

- **WHEN** a subject is longer than the room the column has
- **THEN** it is shortened, and no other column is pushed off the screen

#### Scenario: A row whose issue is done is drawn as done

- **WHEN** a mail row's issue has been marked done
- **THEN** the row is drawn the way the board draws a finished task, and is still readable as a mail row

#### Scenario: A row whose issue is not done is drawn as before

- **WHEN** a mail row's issue has not been marked done
- **THEN** the row is drawn exactly as it was
