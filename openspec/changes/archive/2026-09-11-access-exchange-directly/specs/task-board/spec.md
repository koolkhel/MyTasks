## MODIFIED Requirements

### Requirement: An archive is confirmed before a row is retired

The board SHALL confirm an archive before treating the row as gone: the
messages SHALL be absent from the folder they were in and present in the
archive. Both, because a move that removed mail without delivering it is the
one outcome that loses work, and the gateway this speaks to has been found
violating its protocol elsewhere.

Where a message is already absent from its folder, the board SHALL ask the
archive before concluding anything. Found there, the review has already
happened and SHALL be reported as done rather than as an error. Found in
neither, the board SHALL say so: something moved that message, and it was not
the board.

Where the archive cannot be confirmed, the row SHALL come back and the board
SHALL say why. A row retired on an unconfirmed move is a message a person
believes they have dealt with.

Confirming SHALL cost a number of folder openings that does not grow with the
row. The archive holds everything the account has ever kept and opening it was
measured on this account at about fourteen seconds against about one to search
it, so opening it once per message makes a folded row cost minutes where it
could cost seconds. This is not only a matter of waiting: an operation is
exposed to the line being dropped for as long as it is open, and the failure
that made that concrete happened on a row of seven.

Where a confirmation asks the archive about more than one group of messages —
those just moved, and those that turned out already to be elsewhere — it SHALL
ask in the same opening. They concern one folder and there is no reason to
open it twice.

Undoing a review SHALL move the messages back to the folder they came from
and SHALL mark them unread again, or the row would return to a queue that no
longer counts it. The board SHALL say that the row returns only once the
mirror next catches up, and SHALL NOT pretend the row is back before it is.

An undo SHALL be all or nothing. Where it fails, every message SHALL be left
where it was and the row SHALL NOT come back, rather than some messages
reaching the folder and the rest staying in the archive. A row split across
two places is the state hardest to reason about and the one a person can do
least about; one outcome and one notice is worth more here than salvaging part
of an undo.

#### Scenario: A confirmed archive retires the row

- **WHEN** the messages are absent from their folder and present in the archive
- **THEN** the row stays gone

#### Scenario: An unconfirmed archive brings the row back

- **WHEN** the archive cannot be confirmed
- **THEN** the row returns and the board says why

The economy SHALL be counted in requests to the account, not in any one
protocol's idea of opening a folder. What a row costs SHALL NOT grow with the
number of messages it holds: confirming is one question about a set of
identities, asked once.

#### Scenario: A message already archived

- **WHEN** a message is not in its folder and is found in the archive
- **THEN** the review is reported as already done, not as a failure

#### Scenario: A message in neither place

- **WHEN** a message is in neither its folder nor the archive
- **THEN** the board says so rather than reporting success

#### Scenario: Undoing a review puts the mail back

- **WHEN** a person undoes a review
- **THEN** the messages are moved back to the folder they came from, unread again, and the board says the row returns when the mirror next catches up

#### Scenario: Confirming a folded row costs no more openings than a single one

- **WHEN** rows of one message and of many are reviewed
- **THEN** confirming each costs the archive the same number of requests, whatever the row holds

#### Scenario: One opening answers about both groups

- **WHEN** a row holds messages that were moved and messages already elsewhere
- **THEN** one request to the archive answers about both groups

#### Scenario: An undo that fails leaves the row whole

- **WHEN** putting a row back fails part way
- **THEN** none of its messages have reached the folder, all are still in the archive, and the board says the undo failed

#### Scenario: Giving up is still possible while confirming

- **WHEN** the board is ended without being asked while a row is being confirmed
- **THEN** the confirmation gives up cleanly rather than running to the end

### Requirement: The board shows whether the mailbox is busy

Reviewing a mail row reaches across the network to the account, and reviews are done one at a time, so ticking several leaves the later ones waiting. How long one takes depends on the account, the network and how the board reaches it, and SHALL NOT be written into this requirement: the indication exists because the work is not instant, not because it takes any particular number of seconds. The board SHALL show whether any of that work is in flight, so that a person can tell whether what they have ticked has landed before they tick more or leave.

The indication SHALL be one cell at the right of the day bar, shown in every view. Mailbox work outstands regardless of which view is being looked at, and whether it is safe to quit is the same question in all of them.

It SHALL distinguish three things:

- that nothing is in flight and nothing has failed,
- that something is in flight,
- that something has failed since the person last asked for a reload.

The in-flight state SHALL be animated. A still mark cannot be told from a stuck one, and these operations last tens of seconds; motion is the information. The animation SHALL run only while work is in flight, and SHALL NOT redraw the list — by the same rule the clock follows, a mark that disturbed the rows above it would cost more than it gave.

The failed state SHALL persist until the person asks for a reload or restarts the board. It SHALL NOT be cleared by a later operation succeeding: a failure among ten reviews would otherwise be painted over before it was seen, which is the fault this exists to fix.

The indication SHALL return to its untroubled state whenever the last operation finishes, whichever way it finished. A mark that stayed busy after the work stopped would tell a person to wait for nothing, which is worse than showing nothing at all.

#### Scenario: Nothing in flight

- **WHEN** no mailbox operation is running and none has failed
- **THEN** the day bar's right cell shows that nothing is outstanding

#### Scenario: An operation running

- **WHEN** a person ticks a mail row and its archiving is under way
- **THEN** the cell shows work in flight, and keeps moving while it lasts

#### Scenario: Several ticked in succession

- **WHEN** a person ticks several mail rows faster than they can be confirmed
- **THEN** the cell shows work in flight until the last of them has finished

#### Scenario: Back to rest

- **WHEN** the last outstanding operation finishes
- **THEN** the cell shows that nothing is outstanding, and stops moving

#### Scenario: Every way an operation can end

- **WHEN** an operation ends by being confirmed, by failing to confirm, by finding the message already archived, by finding it in neither place, by the gateway being unreachable, or by giving up because the board is closing
- **THEN** the cell stops showing that operation as in flight in every one of those cases

#### Scenario: A failure is shown until it is acknowledged

- **WHEN** an operation fails and later operations succeed
- **THEN** the cell still shows that something has failed

#### Scenario: A reload clears it

- **WHEN** a person asks for a reload after a failure
- **THEN** the cell shows that nothing is outstanding again

#### Scenario: The animation does not disturb the list

- **WHEN** the cell is animating while work is in flight
- **THEN** no row is redrawn on account of it, and neither the selected row nor the view's position moves

#### Scenario: Shown in every view

- **WHEN** mailbox work is in flight and a person moves between a day, the inbox and the someday view
- **THEN** the cell is shown in each of them

## ADDED Requirements

### Requirement: How the mail account is reached is configured

The address of the service the board talks to, and the identity it presents,
SHALL be read from the environment. No address, mailbox name or credential
SHALL appear in the board's source, so that a corporate account is not
described by a repository that can be published.

The credential SHALL be asked for at the moment it is needed, by a configured
command, rather than held from the moment the board starts. A board that never
reviews anything SHALL never ask for it.

Where nothing is configured, the board SHALL go on reading mail and SHALL
refuse to review it, saying which of the two it cannot do. Reading and writing
are configured separately and either may be set up alone.

#### Scenario: Configured

- **WHEN** the address and the identity are configured and a row is reviewed
- **THEN** the board reaches the account and reviews the row

#### Scenario: Nothing configured

- **WHEN** no address is configured and a row is reviewed
- **THEN** nothing is sent anywhere, no message moves, and the board says the mailbox cannot be written to

#### Scenario: The credential cannot be fetched

- **WHEN** the configured command for the credential fails or answers nothing
- **THEN** the board reports the account as unreachable, and no message has moved

#### Scenario: Nothing identifying is in the source

- **WHEN** the board's source and its specification are read
- **THEN** neither names an address, a mailbox, a folder of a real account, or a credential
