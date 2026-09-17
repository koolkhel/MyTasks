## ADDED Requirements

### Requirement: A suite's parts are declared, and each one is addressable

A suite SHALL declare the parts it is made of in one place, as a list the
runner can read without executing the suite's own driving code. That
declaration SHALL be the only list: a part the suite defines and leaves out of
it does not run, and nothing else decides what runs.

Each declared part SHALL be run and reported on its own, SHALL be selectable
by its name from outside the file it lives in, and SHALL be re-runnable by
itself. A part is where a person actually looks -- it is one situation, set up
and checked -- and a suite that can only be addressed whole makes the smallest
failure cost the largest run.

The parts SHALL run in the order the suite declares them. Several of them
share state the suite set up before any of them ran, and reordering would
change what they are checking without saying so.

Leaving a part out of the declaration SHALL be visible in what the suite
reports, not silent. The count of checks a suite ran is what makes it visible:
a part that no longer runs takes its checks with it, so the count falls.

#### Scenario: Each part is reported by itself

- **WHEN** a suite runs
- **THEN** each of its declared parts is reported as having passed or failed, named, rather than the suite reporting only one result for the file

#### Scenario: A part can be named from outside

- **WHEN** a person asks for one part of one suite by name
- **THEN** that part runs and the rest of the suite does not

#### Scenario: A failing part is re-runnable alone

- **WHEN** a part fails
- **THEN** it can be run again by itself, without running the parts that passed

#### Scenario: The declaration is the only list

- **WHEN** a suite defines a part and does not declare it
- **THEN** that part does not run, and the suite's count of checks is lower than when it was declared

#### Scenario: Declared order is the order that runs

- **WHEN** a suite's parts are run
- **THEN** they run in the order the suite declares them

## MODIFIED Requirements

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

Running a suite on its own SHALL run exactly the parts it declares, in that
order, and SHALL report the same checks as a run through the runner. Two ways
of starting the same suite that cover different parts would make the pair of
them evidence for nothing.

Reading a suite SHALL NOT run it. A suite that acts merely on being loaded
cannot be looked at by anything -- not by a runner collecting its parts, not by
a person importing it to try one function by hand -- without its whole body
executing and the process being exited underneath them.

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

#### Scenario: Loading a suite runs nothing

- **WHEN** a suite is loaded without being asked to run
- **THEN** none of its parts runs, no check is made, and the process that loaded it is still running afterwards

#### Scenario: Both ways of running a suite agree

- **WHEN** one suite is run directly and the same suite is run through the runner
- **THEN** both run the same parts and report the same number of checks

### Requirement: A run needs no credentials by default

A run that is not asked for anything in particular SHALL execute only the
suites that need nothing beyond the repository, and SHALL pass on a checkout
that has no credentials configured at all. The default has to be the run a
person can actually perform; a default that cannot complete is not a default.

This SHALL hold for every way a run can be started, not only the runner's own
command. Where the tool the runner uses underneath can also be invoked
directly, invoking it with nothing asked for SHALL still reach only the
self-contained suites. A second entry point that defaults to reaching a real
account is the same accident as no default at all, arrived at by typing four
letters.

The suites needing the task store or the tracker SHALL run only when asked for
explicitly.

Where such a run is asked for and the credentials it needs are absent, the
runner SHALL say so and SHALL NOT start. Starting anyway produces a wall of
failures that say nothing about the code.

Where what the runner needs installed is absent, it SHALL say what to install
and SHALL NOT start. A missing dependency reported as a failure to import
reads, to the person who just cloned this, exactly like a broken suite.

#### Scenario: The default run on a bare checkout

- **WHEN** a run is started with nothing asked for, on a checkout with no credentials
- **THEN** the self-contained suites run, none is skipped for want of credentials, and the run passes

#### Scenario: Reaching the store is asked for, not assumed

- **WHEN** a run is started with nothing asked for
- **THEN** no suite that talks to the task store or the tracker is executed

#### Scenario: Asked for without the credentials to do it

- **WHEN** a run against the task store is asked for and no credentials are configured
- **THEN** the runner says which are missing and runs nothing, rather than reporting failures

#### Scenario: The underlying tool defaults the same way

- **WHEN** the test tool the runner uses is invoked directly at the repository, with nothing asked for
- **THEN** it runs only the self-contained suites, and no suite that talks to the task store, the tracker or a mail account is collected

#### Scenario: What the runner needs is not installed

- **WHEN** a run is started on a checkout where the test tool is not installed
- **THEN** the runner names what to install and runs nothing, rather than failing on an import

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
