## MODIFIED Requirements

### Requirement: A run says what it did

A run SHALL report which group of suites it executed, how many suites passed
and failed, which were known failures, and how many throttle errors it saw. A
run whose output has to be interpreted before it can be believed is a run that
will be believed wrongly.

A run SHALL also report, for each suite, how many checks it made and how many
of those passed. That count is what tells a reader the suite is still the size
it was: a suite reporting a pass over fewer checks than it used to has lost
part of itself, and nothing else in a green run would say so.

Where a suite fails, the run SHALL make it possible to re-run that suite
alone. Where a part of a suite fails, the run SHALL name that part, so that it
too can be re-run alone.

A run SHALL tell a suite whose checks failed from a suite whose process ended
in failure while every check it made passed. The second is marked as a crash,
not as a failure: a part that raised after its last check, or a part that made
none, is a different kind of fault -- more often the harness, a timing or a
shutdown than the board -- and a reader shown a full count of passing checks
beside a plain failure mark is shown a contradiction and left to resolve it.

For a crash the run SHALL say what raised: the part, and the exception's own
last line, taken from what the test process printed. It SHALL say so on the
suite's line and again where the run lists what failed, so that a crash is
never reported as a bare mark over a count that says nothing went wrong.

The verdict SHALL still come from the process. A suite that crashed after its
checks has failed, whatever its checks say, and a run that called it a pass
would be a run hiding the one fault its checks could not have caught.

#### Scenario: The summary covers the run

- **WHEN** a run finishes
- **THEN** it reports the group it ran, the counts of passed and failed suites, the known failures, and the throttle count

#### Scenario: A failure can be reproduced on its own

- **WHEN** a suite fails in a run
- **THEN** the run identifies it well enough to be run again by itself

#### Scenario: Each suite's size is reported

- **WHEN** a run finishes
- **THEN** each suite's line says how many checks it made and how many passed

#### Scenario: A failing part is named

- **WHEN** a part of a suite fails in a run
- **THEN** the run names the part, and not only the suite it is in

#### Scenario: A part that fell over after its checks

- **WHEN** a suite's process exits in failure and every check the suite made passed
- **THEN** the run marks the suite as crashed rather than failed, and does not report it as passing

#### Scenario: The cause is named

- **WHEN** a suite is marked as crashed
- **THEN** the suite's line and the run's list of failures both name the part that raised and the exception's last line

#### Scenario: A failed check is still a failure

- **WHEN** a suite's process exits in failure and at least one check it made failed
- **THEN** the run marks it as failed, as before, and names the failing checks

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

How a suite failed SHALL be recorded in a way that tells a failed check from a
crash. A suite whose process failed while every check passed SHALL be
described by the exception that ended it, never as a count of failed checks:
a count of zero describes nothing, and an entry carrying it would match any
later crash of any kind.

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

#### Scenario: A crash after the checks is described by its exception

- **WHEN** a suite listed as known to fail crashed after every check it made passed
- **THEN** its recorded signature names the exception, and a later run that fails a check instead is reported as failing differently
