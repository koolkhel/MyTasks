## ADDED Requirements

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
