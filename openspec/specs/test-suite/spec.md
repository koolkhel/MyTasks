# test-suite Specification

## Purpose
The board's own suites, kept in the repository: what each one is allowed to
depend on, how a run decides which of them to execute, and what it does about
a suite that is known to fail. It exists so that "did I break anything" is a
question a fresh clone can answer.

## Requirements

### Requirement: The suites live in the repository

The suites SHALL be kept in the repository alongside the code they check. A
suite that exists only in a working session is evidence that expires: twenty-six
changes have been verified with these and none of that verification survives
the session that ran it.

Each suite SHALL be runnable on its own, SHALL report each thing it checked,
and SHALL exit non-zero when any check fails. Runnable on its own because that
is how a person narrows a failure down; reporting each check because a suite
that says only "failed" sends the reader back to the source to find out what
it was even looking at.

A suite SHALL NOT depend on the path it happens to be stored at, nor on the
path of the code it checks. Both were absolute in every suite before this, and
that alone made them unrunnable anywhere but the machine that wrote them.

#### Scenario: A suite runs by itself

- **WHEN** one suite is run directly
- **THEN** it reports each check it made and exits zero only if all of them passed

#### Scenario: A failing check is visible

- **WHEN** a suite has a check that fails
- **THEN** it names that check and what it got against what it wanted, and exits non-zero

#### Scenario: The checkout can be anywhere

- **WHEN** the repository is checked out at a different path
- **THEN** every suite still finds the code it checks and the fixtures it reads

#### Scenario: Pre-change copies are not kept

- **WHEN** the suites are brought in
- **THEN** the snapshots taken of a suite before one particular change are left behind, and only the current suites are kept

### Requirement: A suite declares what it needs to run

Every suite SHALL declare which of four things it needs: nothing beyond the
repository, the board's own configuration, the real task store, or the issue
tracker. Nothing else about a suite tells a runner whether it can be run here
and now, and guessing from its imports is the kind of inference that quietly
stops being true.

A suite that reads the board's configuration and asserts on it needs that
configuration, even though it calls nothing. Emptying the environment does not
establish otherwise: configuration is found by walking up from the module that
asks for it, and those modules sit beside the file it is kept in — so a suite
can look self-contained under an emptied environment while still reading the
real thing. Only a checkout without that file settles it.

A suite needing nothing beyond the repository SHALL make no network call.
Where it drives the board, it SHALL do so against a substituted store and
substituted sources, so that what it measures is decided entirely by the suite.

#### Scenario: Every suite says what it needs

- **WHEN** the suites are collected
- **THEN** each one is attributed to exactly one of the four groups, and none is unattributed

#### Scenario: Needing configuration is not being self-contained

- **WHEN** a suite reads the board's configuration and asserts on what it finds
- **THEN** it is not in the self-contained group, however it behaves with the environment emptied

#### Scenario: A self-contained suite reaches nothing outside

- **WHEN** a suite that declares it needs nothing is run
- **THEN** it makes no request to the task store, the tracker, the calendar or a mail server

#### Scenario: A self-contained suite is not affected by configuration

- **WHEN** such a suite is run on a machine with a calendar and a mailbox configured
- **THEN** it reads neither, and reports the same result as on a machine with neither

### Requirement: A run needs no credentials by default

A run that is not asked for anything in particular SHALL execute only the
suites that need nothing beyond the repository, and SHALL pass on a checkout
that has no credentials configured at all. The default has to be the run a
person can actually perform; a default that cannot complete is not a default.

The suites needing the task store or the tracker SHALL run only when asked for
explicitly.

Where such a run is asked for and the credentials it needs are absent, the
runner SHALL say so and SHALL NOT start. Starting anyway produces a wall of
failures that say nothing about the code.

#### Scenario: The default run on a bare checkout

- **WHEN** a run is started with nothing asked for, on a checkout with no credentials
- **THEN** the self-contained suites run, none is skipped for want of credentials, and the run passes

#### Scenario: Reaching the store is asked for, not assumed

- **WHEN** a run is started with nothing asked for
- **THEN** no suite that talks to the task store or the tracker is executed

#### Scenario: Asked for without the credentials to do it

- **WHEN** a run against the task store is asked for and no credentials are configured
- **THEN** the runner says which are missing and runs nothing, rather than reporting failures

### Requirement: A run against a real service is paced and tells throttling apart from failure

A run of the suites that talk to the task store SHALL leave a gap between
them, and SHALL NOT run them concurrently with one another. Run back to back
they exhaust the store's quota: it answers with a throttle error and goes on
doing so for tens of minutes, after which every remaining suite fails for a
reason that has nothing to do with the code.

The runner SHALL count the throttle errors a run produced and SHALL report
that count alongside the results. A run that was throttled SHALL be reported
as inconclusive rather than as a set of failures — a failure that is really a
quota is the most expensive kind of false signal this project has, having once
sent a whole verification pass to be re-done.

#### Scenario: Live suites are spaced apart

- **WHEN** a run against the task store executes more than one suite
- **THEN** they run one at a time with a gap between them

#### Scenario: Throttling is counted and named

- **WHEN** the store answers a suite with a throttle error
- **THEN** the run reports how many throttle errors it saw, distinctly from the checks that failed

#### Scenario: A throttled run is not a verdict

- **WHEN** a run ends having seen throttle errors
- **THEN** it says the result is inconclusive and says what to do about it, rather than presenting the failures as findings

### Requirement: A run against the real store uses a token of its own

Where the account provides a second token for the suites, a run against the
task store SHALL use it, and SHALL NOT use the token the board itself uses. A
full run can exhaust the account's quota; when it does, it SHALL be the
suites' quota it exhausts, leaving the board a person is actually working in
still able to answer.

The suites SHALL NOT read that token themselves. They SHALL be launched with
it in place of the ordinary one, so that what they exercise is the same code
path a real run takes and the product knows nothing of a test token.

Where no such token is configured, a run SHALL proceed with the one that is,
so that a checkout with a single token still works.

A run SHALL say which of the two it used, identified without disclosing it.

#### Scenario: The suites' token is preferred

- **WHEN** a run against the task store is started and a token for the suites is configured
- **THEN** the suites are launched with it, and the board's own token is not used

#### Scenario: The product knows nothing about it

- **WHEN** a suite reads the token it was given
- **THEN** it finds it where any run would, and no product code refers to a token meant for tests

#### Scenario: One token is enough

- **WHEN** no token for the suites is configured
- **THEN** the run proceeds with the configured one rather than refusing

#### Scenario: The run says which it used

- **WHEN** a run against the task store finishes
- **THEN** it reports which of the two tokens it used, without printing the token

### Requirement: A run against the real store leaves nothing behind

A suite that creates anything in the task store SHALL name it so that it is
recognisable as a test's, and SHALL remove it even when the suite fails part
way through.

After a run against the store, the runner SHALL check for anything left behind
and SHALL report what it finds. A suite that crashes leaves a task on the
account, and a task left there is not merely untidy: it shows up in a later
run as a change to the board that no code made, which reads as a regression.

#### Scenario: What a suite creates, it removes

- **WHEN** a suite that creates tasks finishes, whether it passed or failed
- **THEN** the tasks it created are gone from the account

#### Scenario: A crash still cleans up

- **WHEN** a suite raises part way through, after creating a task
- **THEN** the task is still removed

#### Scenario: What was left behind is reported

- **WHEN** a run against the store has finished
- **THEN** anything recognisable as a test's that remains on the account is reported

### Requirement: A suite known to fail is recorded with the reason

A suite that fails for a reason predating the work in hand SHALL be listed as
known to fail, with a one-line reason, and SHALL NOT make the run report
failure. Otherwise every run starts red, and a red run cannot answer the one
question the suites exist to answer.

The list SHALL be kept honest in both directions: a listed suite that starts
passing SHALL be reported, so that the list is pruned rather than accumulating
entries nobody has revisited.

A suite SHALL NOT be listed merely because it is inconvenient. The reason
recorded SHALL say what is known about the failure, including when the answer
is that it has not been diagnosed.

#### Scenario: A known failure does not fail the run

- **WHEN** a run includes a suite listed as known to fail, and it fails as listed
- **THEN** the run reports it as known and still reports overall success

#### Scenario: The reason is there to read

- **WHEN** a suite is listed as known to fail
- **THEN** a one-line reason is recorded with it

#### Scenario: A known failure that has been fixed

- **WHEN** a suite listed as known to fail passes
- **THEN** the run says so, so the entry can be removed

#### Scenario: A known failure that fails differently

- **WHEN** a suite listed as known to fail fails in a way the entry does not describe
- **THEN** the run reports it rather than absorbing it into the known entry

### Requirement: Nothing about a real account or a real person enters the repository

The suites and their fixtures SHALL contain no real identifier: no issue key
from a real tracker project, no project code, no address, no credential. One
such key was removed from this repository's history with a history rewrite and
SHALL NOT return, and it is present in several of these suites as they stand.

A value a suite must match because the account really returns it is not an
identifier of that class and MAY remain — a tag's title, for instance. The
test is what the value discloses, not where it came from: a project code names
an employer, where a colour word names a colour. Loosening a live suite's
assertion to avoid holding such a value would trade a real check for no gain
in privacy.

Fixtures SHALL be synthetic and SHALL keep only the properties the code under
test turns on — non-ASCII text, duplicate titles, characters that are awkward
in a filename, an empty body, a message already marked read. Where a fixture
was generated, the generator SHALL be kept with it so its provenance can be
checked.

Anything a run produces that describes a real account — a captured view of the
board, a recorded baseline — SHALL be excluded from the repository rather than
relied upon to be deleted by hand.

#### Scenario: No real identifier is committed

- **WHEN** the suites and fixtures are added
- **THEN** none contains a real tracker key, project code, address or credential

#### Scenario: The scrubbed key does not return

- **WHEN** the repository is searched for the key removed by the history rewrite
- **THEN** it is not found in any committed file

#### Scenario: A generated fixture keeps its generator

- **WHEN** a fixture was produced by a script
- **THEN** that script is committed with it, and re-running it reproduces a fixture with the same properties

#### Scenario: A captured view of the board is not committed

- **WHEN** a run records the board's state or a baseline to compare against
- **THEN** it is written where the repository excludes it

### Requirement: A suite never writes to the fixture it reads

A suite SHALL work on its own copy of any fixture it might write to, made for
that run. The board can now change a mailbox, and a suite that pointed it at
the committed fixture rewrote the very data every other mail suite measures
against — silently, and only noticed because the fixture was checked
afterwards.

After a run, the committed fixtures SHALL be unchanged.

#### Scenario: The fixture is copied, not used in place

- **WHEN** a suite exercises behaviour that writes to a mailbox
- **THEN** it works on a copy made for that run

#### Scenario: The committed fixture survives the run

- **WHEN** the whole suite set has run
- **THEN** every committed fixture file is byte-for-byte what it was before

#### Scenario: One suite cannot disturb another

- **WHEN** two suites that read the same fixture run in the same session
- **THEN** neither sees changes made by the other

### Requirement: A run says what it did

A run SHALL report which group of suites it executed, how many suites passed
and failed, which were known failures, and how many throttle errors it saw. A
run whose output has to be interpreted before it can be believed is a run that
will be believed wrongly.

Where a suite fails, the run SHALL make it possible to re-run that suite alone.

#### Scenario: The summary covers the run

- **WHEN** a run finishes
- **THEN** it reports the group it ran, the counts of passed and failed suites, the known failures, and the throttle count

#### Scenario: A failure can be reproduced on its own

- **WHEN** a suite fails in a run
- **THEN** the run identifies it well enough to be run again by itself

### Requirement: A suite's result does not depend on when it runs

A suite SHALL answer about the code, not about the moment it ran. Given
unchanged code, a run at any hour of any day SHALL reach the same verdict as a
run at any other. A suite that passes in the morning and fails at midnight has
reported nothing about the change in hand, and the time it takes to work that
out is spent twice: once suspecting the change, once clearing it.

Where a suite builds a fixture from the present — an event under way, a task
past due, a day already over — that fixture SHALL be correct at every hour it
could be built at. It SHALL NOT be clamped or trimmed to a legal range in a way
that changes what it means: an event meant to span the present becomes an event
already over when its end is clipped back past the present, and the suite then
asserts the opposite of what it set out to.

Where a position in time genuinely cannot exist at the moment of the run, the
suite SHALL skip that case rather than build something standing in for it. At
midnight nothing has ended today; in the last hour nothing is still to come.
Skipping what cannot exist is honest; approximating it is how a fixture comes
to claim one thing and be another.

A suite SHALL NOT assert a threshold against text whose length the product
derives from the current date or time. A day name and a month name are of
different lengths on different days, so a check that a line is too long to fit
something beside it is a check on the calendar. Such a check SHALL instead
measure what the product produced and assert the behaviour either side of the
boundary, which is both independent of the date and a stronger statement than
sampling one width.

This kind of dependence SHALL be assumed not to be findable by searching the
suites: the suite that had it contained no date handling of any kind, the
length it depended on being computed by the product. So a suite exercising a
limit SHALL demonstrate that it holds away from the moment of the run, rather
than that it holds now.

#### Scenario: The same verdict whenever it is run

- **WHEN** a suite is run at different hours of different days with the code unchanged
- **THEN** it reaches the same verdict every time

#### Scenario: A fixture built from the present means what it says

- **WHEN** a suite builds an event, task or day defined by its position relative to now
- **THEN** that position is correct at every hour the fixture could be built at, and is not clipped into meaning something else

#### Scenario: A position that cannot exist is skipped, not approximated

- **WHEN** the moment of the run admits no example of the position a case needs
- **THEN** the case is skipped rather than built from something that only resembles it

#### Scenario: A limit is not asserted against the calendar

- **WHEN** a suite checks behaviour at a limit on text the product laid out from the current date or time
- **THEN** it measures that text and asserts the behaviour either side of the limit, rather than assuming a width that only holds on some days

#### Scenario: The limit is shown to hold away from now

- **WHEN** a suite checks behaviour that depends on the present
- **THEN** it shows that behaviour holding at moments other than the one it is running in

### Requirement: An expectation is taken from the fixture it is about

Where a suite asserts something about a fixture it built, the expected value
SHALL be derived from that fixture rather than computed a second time beside
it. Two expressions of one value, kept in step by hand, drift the moment the
fixture changes — and they drift silently, because nothing connects them.

This is not about the clock. It holds for any fixture a suite builds and then
makes a claim about: a mailbox, a task, a row, a width. Wherever the expected
value can be read off the thing under test, it SHALL be, so that changing the
fixture changes the expectation with it and a stale assertion is impossible
rather than merely unlikely.

Where a value genuinely cannot be read back — the suite is asserting a
constant the product should produce, and reading it from the product would
assert nothing — the constant SHALL be written plainly rather than
reconstructed from the same arithmetic the fixture used. Recomputing the
fixture's own arithmetic is neither a constant nor a derivation; it is a copy
that looks like a check.

Where a suite demonstrates that behaviour holds away from the moment of the
run, that demonstration SHALL cover every assertion the suite makes about the
fixture, not one property chosen from among them. A sweep that judges a row's
shading while the same row's other cells go unchecked will pass over an
expectation that has been wrong since the fixture changed.

#### Scenario: The expected value comes from the fixture

- **WHEN** a suite asserts a property of a fixture it built
- **THEN** the value it expects is read from that fixture rather than computed separately from the same inputs

#### Scenario: Changing the fixture cannot strand an assertion

- **WHEN** a fixture a suite builds is changed
- **THEN** every assertion about it either follows the change or fails, and none silently keeps describing what the fixture used to be

#### Scenario: A constant is written, not reconstructed

- **WHEN** a suite asserts a constant the product is expected to produce
- **THEN** it states that constant rather than rebuilding it from the arithmetic the fixture was built with

#### Scenario: A demonstration covers what the suite asserts

- **WHEN** a suite shows that behaviour holds at moments other than the one it is running in
- **THEN** that demonstration covers every assertion the suite makes about the fixture, not a single property of it
