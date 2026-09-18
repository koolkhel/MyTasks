## ADDED Requirements

### Requirement: The launcher says when the terminal cannot be asked for the calendar

Where a calendar account is configured, the launcher SHALL check, before the
board starts, whether the application the terminal belongs to is one the
system will ask on behalf of, and whether the system has already answered.
Where the application declares no reason to want the calendar, or the system
has refused or granted only in part, the launcher SHALL print what it found
and the command that puts it right.

The launcher SHALL then start the board whatever it found. The board is
required to work without the calendar, and a launcher that refused to start
over the calendar would break that from the other side.

Where no calendar account is configured, the launcher SHALL NOT check, and
SHALL print nothing about the calendar. Where the check is not applicable --
the command-line listing, or a machine that is not a Mac -- it SHALL be
skipped the same way.

#### Scenario: A terminal that cannot be asked

- **WHEN** the board is started through the launcher, a calendar account is configured, and the terminal declares no reason to want the calendar
- **THEN** the launcher prints which application the terminal is, that the system will not ask on its behalf, and the fix command, and then starts the board

#### Scenario: A terminal already allowed

- **WHEN** the board is started through the launcher and the system has granted the terminal full access
- **THEN** the launcher prints nothing about the calendar and starts the board

#### Scenario: No calendar configured

- **WHEN** the board is started through the launcher with no calendar account configured
- **THEN** no check is made and nothing about the calendar is printed

#### Scenario: The board starts regardless

- **WHEN** the launcher's check finds the terminal cannot be asked
- **THEN** the board still starts, exactly as it does when the check finds nothing

### Requirement: A helper makes the terminal one the system will ask about

The board SHALL ship a helper that, run from inside a terminal, says which
application that terminal is, whether its Info.plist declares a reason to
want the calendar, how it is signed, and what the system currently answers
for it -- and that says plainly when the answer it reports belongs to a
different application than the one asked about.

Asked to fix, the helper SHALL add the calendar usage keys to the
application's Info.plist, keep a copy of the original beside it, re-sign the
application ad hoc, and clear any answer the system remembered for it -- and
SHALL do so only for an application that is unsigned or already ad-hoc
signed. An application carrying a developer signature SHALL be refused, with
the reason: editing its plist would break that signature, and replacing it
with an ad-hoc one is worse than the problem. An application the system has
already granted SHALL be left alone.

The helper SHALL make no change unless asked to fix, and SHALL ask before
changing anything unless told not to. It SHALL then say that the terminal
must be quit and started again, since the system reads the plist when the
request is made and the running application is the old one.

Asked for the calendar with the keys in place, the helper SHALL make the same
request the board makes, so that the system's prompt appears for that
application, and SHALL report the answer in the system's own terms.

#### Scenario: The diagnosis

- **WHEN** the helper is run in a terminal whose application declares no calendar key
- **THEN** it names the application, says it declares none and that the system will not ask on its behalf, reports how it is signed, and says to run the fix

#### Scenario: Fixing an unsigned terminal

- **WHEN** the helper is asked to fix an unsigned or ad-hoc-signed application
- **THEN** it keeps a copy of the plist, adds both keys, re-signs ad hoc, clears the remembered answer, and says to quit and restart the terminal

#### Scenario: A signed terminal is refused

- **WHEN** the helper is asked to fix an application that carries a developer signature
- **THEN** it changes nothing and says why

#### Scenario: Nothing is changed without asking

- **WHEN** the helper is run without being asked to fix, or is asked to fix and the person declines
- **THEN** no file is changed and nothing is re-signed or cleared

#### Scenario: An allowed terminal is left alone

- **WHEN** the helper is run in a terminal the system has already granted full access
- **THEN** it reports that and changes nothing

#### Scenario: Asked about a different terminal

- **WHEN** the helper is pointed at an application other than the one it runs in
- **THEN** it says the system's answer it reports is for the terminal it runs in, not for that application

#### Scenario: The request is the board's own

- **WHEN** the helper is run in a terminal that declares a key and has not yet been asked
- **THEN** the system's prompt appears for that terminal, and the helper reports the answer

## MODIFIED Requirements

### Requirement: The board works when the calendar cannot be read

Reading the calendar needs a permission granted outside the board, which may
be refused, withdrawn, or granted only in part. In any of those cases the
board SHALL show the day's tasks as it always does and SHALL say once that the
calendar could not be read, naming what would put it right.

A permission granted only in part SHALL be treated as no permission rather
than as success: it reads as though it worked while returning nothing, and a
day wrongly showing no events looks exactly like a free one.

Where the request could not be made at all -- the system refuses to ask on
behalf of an application that declares no reason to want the calendar, and
the terminal the board runs in is such an application -- the board SHALL say
so, naming that application and the helper that puts it right. This is the
one case where Privacy & Security cannot help, since the application never
appears there, and a message that named nothing left a person to guess at
the least obvious of the remedies.

The calendar SHALL NOT delay the day. The tasks SHALL appear without waiting
for it, and a calendar that is slow or unavailable SHALL NOT keep them off the
screen.

#### Scenario: Permission is refused

- **WHEN** the board cannot read the calendar because permission was not granted
- **THEN** the day's tasks appear as usual and the board says the calendar could not be read

#### Scenario: Permission granted only in part

- **WHEN** permission allows adding to the calendar but not reading it
- **THEN** the board treats that as unreadable and says so, rather than showing a day with no events

#### Scenario: The day does not wait

- **WHEN** the calendar is slow to answer
- **THEN** the day's tasks are already on screen, and the events join when they arrive

#### Scenario: Recovering without a restart

- **WHEN** the calendar becomes readable again and the view is refreshed
- **THEN** the events appear and the message about not reading it is gone

#### Scenario: The terminal cannot be asked

- **WHEN** the board cannot read the calendar because the application it runs in declares no reason to want it, so the system never asked
- **THEN** the day's tasks appear as usual and the board names that application and the helper that makes it one the system will ask about
