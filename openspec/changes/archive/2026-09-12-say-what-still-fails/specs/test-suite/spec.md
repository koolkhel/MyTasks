## MODIFIED Requirements

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

A suite SHALL also account for what the machine itself permits. Belonging to a
group settles which credentials a run needs, not whether the system will
answer: a calendar, a mailbox or a keychain can be configured and still be
refused to the process that asks. Where a check needs such a permission, the
suite SHALL ask the system before asserting, SHALL treat a refusal as a reason
not to run that check rather than as a result from the code under test, and
SHALL say which permission was missing.

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

#### Scenario: A check that needs a permission the machine withholds

- **WHEN** a check needs a permission the system has not granted to the process running the suites
- **THEN** the check is not run, and the suite names the permission that is missing

#### Scenario: A count covers only the checks that ran

- **WHEN** a suite leaves checks unrun for want of a permission
- **THEN** its total counts only the checks it ran, and it reports success when those passed

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

Removing an entry SHALL leave a record of what it said and why it went, so that
a list which is pruned does not become a list which forgets.

A suite SHALL NOT be listed here for checks the machine refuses to let it run.
An entry excusing those checks would excuse a genuine break of them exactly as
readily, which is the thing this list exists not to do.

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

#### Scenario: A removed entry leaves a record

- **WHEN** an entry is removed because the suite it named now passes
- **THEN** what the entry said, and that it went for passing, stay on file

#### Scenario: A permission the machine withholds is not a known failure

- **WHEN** a suite cannot run some of its checks because the system refuses a permission they need
- **THEN** it is not listed as known to fail, and the run reports no failure for it

