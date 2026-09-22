## MODIFIED Requirements

### Requirement: Which calendar accounts are read is configured, not built in

What is read SHALL be named in the environment, and which of it counts as work
SHALL be named there too. No account name, and no calendar name, SHALL appear
in the board's source.

A configured entry SHALL name either a source account or a single calendar. An
entry naming an account SHALL read every calendar that account holds; an entry
naming a calendar SHALL read that calendar alone; an entry that happens to name
both SHALL read both. The account is not always the grain a person needs -- a
calendar worth putting on the board often sits in a source holding others that
are not -- and an account-only configuration can neither express that nor tell
the person it cannot.

Only what the entries name SHALL be read. A machine's calendar holds a great
deal that has nothing to do with a working day, and showing all of it would
bury what matters.

Where nothing is configured, the board SHALL show no events and SHALL NOT
report a failure: a board with no calendar configured is an ordinary board.

Where a configured entry names nothing on the machine, the board SHALL say so,
naming the entry that matched nothing, and SHALL still show the events of every
entry that did match. That report SHALL stand until the entry matches or is
removed, in the way the board's other standing reports do, so that a day known
to be incomplete says so for as long as it is. Withdrawing the whole calendar
over one entry spends every event a person had in order to report one name, and
presents a correctable name as the calendar being unreadable.

#### Scenario: Only the named accounts are shown

- **WHEN** accounts are configured and the machine holds others besides
- **THEN** only events from the named accounts appear

#### Scenario: An entry naming a calendar reads that calendar

- **WHEN** an entry names a calendar rather than the account it sits in
- **THEN** that calendar's events appear

#### Scenario: Naming a calendar does not bring in the rest of its account

- **WHEN** an entry names one calendar of an account holding several, and no entry names that account
- **THEN** only that calendar's events appear, and the account's other calendars are not read

#### Scenario: An entry naming an account reads every calendar in it

- **WHEN** an entry names an account holding several calendars
- **THEN** events from all of them appear

#### Scenario: A name belonging to both is read as both

- **WHEN** an entry names something that is the title of an account and also the title of a calendar elsewhere
- **THEN** both are read

#### Scenario: No calendar is configured

- **WHEN** no entry is configured
- **THEN** no event is shown, and the board reports no failure

#### Scenario: A configured account is missing

- **WHEN** one configured entry names nothing on the machine and the others match
- **THEN** the board says that entry was not found, and the events of the entries that matched are still shown

#### Scenario: The report of an unmatched entry stands

- **WHEN** an entry matches nothing and the view is refreshed for some other reason
- **THEN** the board is still saying that entry was not found

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source is read
- **THEN** it names no account and no calendar, and both are discovered at run time

### Requirement: Work events are hidden with the rest of the work

An event SHALL be treated as work when what is configured as work names either
the account the event came from or the calendar it sits in, so that the key
which hides work hides it too, and the count of what was hidden includes it. An
event that what is configured as work does not name SHALL NOT be hidden by that
key.

What counts as work SHALL be matched the same way the entries selecting
calendars are matched. A name good enough to read a calendar by but not good
enough to recognise that calendar's events as work would leave the board
hiding nothing while appearing to be configured.

#### Scenario: Hiding work hides the work account's events

- **WHEN** work is hidden and the day holds events from the work account
- **THEN** they disappear along with the work tasks, and pressing the key again brings them back

#### Scenario: Hiding work hides the events of a calendar named as work

- **WHEN** what is configured as work names a calendar rather than an account, and the day holds that calendar's events
- **THEN** they disappear along with the work tasks, and pressing the key again brings them back

#### Scenario: Personal events are not hidden

- **WHEN** work is hidden and the day holds events from an account that is not work
- **THEN** those events stay

#### Scenario: The hidden count includes them

- **WHEN** work is hidden and the board reports how many rows that removed
- **THEN** the work events it removed are included in that count
