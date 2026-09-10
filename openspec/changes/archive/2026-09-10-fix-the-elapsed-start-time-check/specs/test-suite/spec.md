## ADDED Requirements

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
