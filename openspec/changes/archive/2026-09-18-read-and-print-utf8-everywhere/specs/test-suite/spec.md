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

A suite SHALL NOT depend on the machine's default text encoding either. Every
file it reads or writes as text SHALL name its encoding, every child process
whose output it decodes SHALL be decoded with a named encoding, and what a
suite prints SHALL be written as UTF-8 whether it is started on its own, under
the test tool, or through the runner. Fourteen suites read the board's own
source, which is not ASCII; on a machine whose locale is not UTF-8 they failed
on the first byte, and the runner failed decoding the first suite that printed
a mark. A suite that passes only where an environment variable happens to be
set is a suite that passes by accident.

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

#### Scenario: A suite does not need a UTF-8 locale

- **WHEN** a suite is run on its own on a machine whose default text encoding is not UTF-8, with no encoding-related environment variable set
- **THEN** it reads the files it reads, prints every check it makes, and reports the same result as on a UTF-8 machine

#### Scenario: No text is read without saying how

- **WHEN** the suites and the helpers beside them are inspected
- **THEN** every text open, text read, text write and decoded child process names its encoding, and a part exists that fails when one does not

### Requirement: A run needs no credentials by default

A run that is not asked for anything in particular SHALL execute only the
suites that need nothing beyond the repository, and SHALL pass on a checkout
that has no credentials configured at all -- and no particular locale: the
machine's default text encoding SHALL NOT decide whether the run passes. The
default has to be the run a person can actually perform; a default that
cannot complete is not a default, and nobody configures a locale to run tests.

The runner SHALL decode what its suites print as UTF-8 and SHALL start each
of them so that they print UTF-8, rather than relying on the machine to have
been told to.

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

#### Scenario: The default run on a machine that is not UTF-8

- **WHEN** a run is started with nothing asked for, on a checkout whose machine default encoding is not UTF-8 and with no encoding-related environment variable set
- **THEN** the runner reads every suite's output, every self-contained suite runs and prints its checks, and the run passes exactly as it does on a UTF-8 machine
