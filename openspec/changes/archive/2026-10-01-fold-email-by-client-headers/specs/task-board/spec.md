## MODIFIED Requirements

### Requirement: Messages about one issue fold into one row

Messages that are about the same thing SHALL be shown as one row. A person
reviewing a notification system's mail is deciding about the thing it concerns,
not about each event on it: the real folders hold 977 messages standing for 150
issues, 81 merge requests and a handful of build jobs, and a row per message
asks the same question many times over.

What a message is about SHALL be taken from what its sender declares, in the
headers it sets for the purpose, and SHALL NOT be read out of the message's
text. A sender that generates a notification knows what it is about and says
so; anything the board recovers from the words is a guess at a fact it was
already told.

This is not only tidier, it is safer, and the data says so. 234 of those
messages name an issue in their text while carrying no header from the tracker,
because they are review and build mail quoting an issue in passing. Those are
exactly the messages that merged 24 of 38 groups wrongly when the text was
trusted. A declaration only the tracker makes cannot pick them up at all, so
the compound rule that was needed to survive them is no longer needed.

Three senders SHALL be folded, each by its own declaration:

- tracker notifications, by the issue the tracker names, one row per issue;
- code-review notifications, by the review system's project and merge-request
  identifiers taken together, one row per merge request. Neither alone
  identifies a merge request, since the number restarts in every project;
- build notifications, by the job the build server names, one row per job.

Where a message carries no such declaration, it SHALL be grouped as it is
today, by the headers that say which message answers which. A sender that
declares nothing SHALL be unaffected by this requirement.

A folded row SHALL report how many messages it stands for, as a row already
does.

Folding SHALL NOT hide a message. Every message read SHALL appear in exactly
one row, so that a row's count and the mailbox agree. Deciding that a message
is not worth showing is a separate matter, specified separately, and applies to
build mail alone.

#### Scenario: Updates about one issue are one row

- **WHEN** several messages carry the same tracker issue declaration
- **THEN** they appear as a single row, reporting how many messages it stands for

#### Scenario: The same issue in unrelated mail is not folded

- **WHEN** a review or build message names an issue in its text but carries no tracker declaration
- **THEN** it is not folded with that issue's own notifications

#### Scenario: A general pattern is not mistaken for an issue

- **WHEN** a subject carries letters, a dash and digits that no sender has declared an issue
- **THEN** no folding happens on it, the text being read for nothing

#### Scenario: A folder that names no issues is unaffected

- **WHEN** a folder holds messages carrying none of these declarations
- **THEN** its messages are grouped by the headers that say which answers which, exactly as before

#### Scenario: One row per merge request

- **WHEN** several messages concern the same merge request
- **THEN** they appear as a single row

#### Scenario: Merge requests numbered alike in different projects

- **WHEN** two merge requests in different projects carry the same number
- **THEN** they remain separate rows

#### Scenario: One row per build job

- **WHEN** several build messages name the same job
- **THEN** they appear as a single row

#### Scenario: Every message shown is in exactly one row

- **WHEN** the mailbox is drawn
- **THEN** each message read appears in one row, and the rows' counts sum to the number of messages read

## ADDED Requirements

### Requirement: A build notification is kept only where the build failed

A build server reports every outcome, and most outcomes are not news. The board
SHALL keep a build notification only where the build failed, and SHALL leave
the rest out of the mailbox view entirely.

A succeeded build SHALL be left out. Nothing is asked of a person by a build
that worked, and a queue holding it spends attention to reach the one that did
not.

A build that was stopped before it finished SHALL also be left out. Stopping a
build is somebody withdrawing a job they started, often because they started it
wrongly, and it leaves nothing to fix.

The outcome SHALL be taken from what the build server declares, not from the
message's wording. A board matching words would be tied to one server's
phrasing and one language, and would fall silent the day either changed.

Where every message about a job is left out, that job SHALL have no row. A row
standing for nothing a person needs is the thing this removes.

This SHALL apply to build notifications alone. A message from any other sender
SHALL be shown whatever it reports, because no other sender here declares an
outcome the board can judge.

#### Scenario: A failed build is kept

- **WHEN** a build notification declares that the build failed
- **THEN** it appears, folded into its job's row

#### Scenario: A succeeded build is left out

- **WHEN** a build notification declares that the build succeeded
- **THEN** it does not appear, and does not count towards any row

#### Scenario: A stopped build is left out

- **WHEN** a build notification declares that the build was stopped before finishing
- **THEN** it does not appear, and does not count towards any row

#### Scenario: A job with nothing but successes has no row

- **WHEN** every message about a job reports a success or a stopped build
- **THEN** no row stands for that job

#### Scenario: A job with both keeps only the failures

- **WHEN** a job has messages reporting successes and messages reporting failures
- **THEN** its row stands for the failures alone and reports how many it holds

#### Scenario: Only build mail is judged this way

- **WHEN** a message from another sender reports an outcome of its own
- **THEN** it is shown regardless of what it reports
