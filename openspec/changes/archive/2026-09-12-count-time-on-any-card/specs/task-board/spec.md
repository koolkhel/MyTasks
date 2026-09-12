## ADDED Requirements

### Requirement: The card counts the sitting

A card SHALL say, for whatever row it was opened on, the moment it opened and
how long ago that was. It SHALL do so for every row alike -- a task, a tracker
issue, a mail thread, a calendar event -- because the card is where a person is
while they are on something, and no kind of row is exempt from being the thing
somebody is on.

The count SHALL begin when the card opens and SHALL end when it is dismissed.
Opening the card again SHALL begin a new count. Leaving the card is leaving the
thing: a person who has come back has come back to start again, and a count
that carried across the gap would be counting the walk to the kitchen.

No key that opens a card SHALL count differently from any other. In particular
the key that starts a workspace SHALL count because the card it opens counts,
not because that key is special.

What is shown SHALL be time elapsed, and the board SHALL NOT present it as
effort. A card left open overnight, a lunch and a closed laptop all pass
unnoticed, so the count answers "since when" and not "how hard". The wording
SHALL make that plain.

The count SHALL keep up with the clock while the card is open, without a person
doing anything to refresh it.

Nothing about it SHALL be written down or added up. No total SHALL be kept for
a row, for a day, or for anything else, on disk or in memory, and the board
SHALL NOT remember after a card is dismissed that it was ever open. An
accumulated record of time spent is a different undertaking and SHALL NOT be
inferred from this one.

#### Scenario: The card says since when

- **WHEN** a card is opened on any row
- **THEN** it says the time it opened and how long ago that was

#### Scenario: The count keeps up

- **WHEN** a card stays open across a minute boundary
- **THEN** the elapsed time it shows advances without anything being pressed

#### Scenario: Every kind of row counts

- **WHEN** a card is opened on a mail thread or on a calendar event
- **THEN** it counts exactly as it does for a task the board manages

#### Scenario: Coming back starts again

- **WHEN** a card is dismissed and opened again on the same row
- **THEN** the count begins from that moment, not from when it was first opened

#### Scenario: Starting a workspace is no different

- **WHEN** a workspace is started and the card opens on that issue
- **THEN** the count begins then, exactly as it would have had the card been opened by hand

#### Scenario: A second card does not disturb a first

- **WHEN** a card is opened on one row, dismissed, and a card opened on another
- **THEN** the second counts from when it opened, and the board holds nothing about the first

#### Scenario: Nothing is added up

- **WHEN** cards have been opened and dismissed several times
- **THEN** the board holds no total for any row, and nothing on disk records that any card was open

## MODIFIED Requirements

### Requirement: The focus view changes nothing

Opening, viewing, or dismissing the focus view SHALL leave the task exactly as
it was, and SHALL send no request that modifies anything. In particular the key
that opens the focus view SHALL NOT also tick the task, so a task cannot be
completed by looking at it.

The count the card shows is not an exception to this. It is the card's own
reading of the clock, kept while the card is open and gone when it closes: no
request carries it, nothing on the row records it, and a row whose card has
been opened is byte for byte the row it was. A person who opens a card to read
a long title has changed nothing by doing so, however long they leave it open.

#### Scenario: Opening the focus view does not complete the task

- **WHEN** a person opens the focus view on an unfinished task and dismisses it
- **THEN** the task is still unfinished

#### Scenario: No request is sent

- **WHEN** a person opens and dismisses the focus view
- **THEN** the board sends no request that creates, updates, or deletes anything

#### Scenario: Ticking still has its own way in

- **WHEN** a person wants to tick the selected task
- **THEN** an action distinct from the one that opens the focus view does it

#### Scenario: Counting is not a change

- **WHEN** a person leaves a card open on a task for a long time and dismisses it
- **THEN** no request has been sent, and the task is exactly as it was before the card opened

## REMOVED Requirements

### Requirement: The board shows what is being worked on and since when

**Reason**: This change makes every card count its own sitting, on every row,
restarting each time a card opens. That leaves the board's memory of one thing
being worked on with nowhere to show itself -- the card was the only place it
appeared, and the card no longer asks what it says. Four of the seven scenarios
say the opposite of what now holds.
`Another row says nothing` and `One thing at a time` both assert that a card
can say nothing about time.
`Opened by either key` asserts that reaching a card by a second key preserves
the count it already had.
`A restarted board remembers nothing` is about a memory that no longer exists. A requirement cannot be edited into the negation of its own
scenarios, so it is replaced rather than modified.

**Migration**: None for anyone using the board, and nothing stored changes --
the memory being dropped was only ever held while the board ran and was never
written anywhere. What a person sees changes in one direction only: cards that
said nothing about time now say when they opened. Replaced by `The card counts
the sitting`, which keeps unchanged: that the count is time elapsed and never
presented as effort, that it keeps up with the clock unaided, that opening
again restarts it, and that nothing is written down or added up.
