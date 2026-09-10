## Context

See proposal.md — Why. What the code actually says:

- One expectation is stale, at `t_elapsed.py:173`:
  `check("it keeps its start time", cell(app, "over", 2), f"{(h-2)%24:02d}:00")`.
  Everything else hour-derived in that file is fixture *construction*, not an
  assertion — checked by searching the file for arithmetic on the hour.
- `positions` asserts six things about the *over* row: that it is receded, and
  then its mark, its start time, its name, its calendar, and that it is not
  struck out. The stale one is among the five that follow the comment
  "nothing else about the row changed".
- The hour sweep added by the previous change judges only whether each of the
  three positions is receded. It builds the same fixtures, at every hour, and
  never looks at the other five cells — which is why it swept twenty-four
  hours past a broken expectation without noticing.
- The fixture the expectation is about is `before_now(title, h)`, which is
  `ev(title, 0, h)`. Its start is midnight at every hour it can be built at,
  so the correct expectation today is `00:00` — but writing `00:00` would be
  the same mistake in a shorter form.

## Goals / Non-Goals

**Goals:**

- The expectation and the fixture cannot disagree, by construction.
- The sweep covers what the suite asserts, so this class fails at the hour it
  is wrong rather than at the hour someone runs.

**Non-Goals:**

- Rewriting `positions` or the other blocks. Their fixtures are correct; one
  assertion about one of them is not.
- Recording either suite in the known-failure list. It stops failing.
- Any product change. The board is right about the row; the suite was wrong
  about the fixture.
- A general sweep tool. The previous change declined one for reasons that
  still hold, and this failure is more evidence for that position rather than
  against it: a sweep existed and did not catch this, because the gap was in
  what the sweep *looked at*.

## Decisions

### The expectation is read off the event, not written as a constant

The case keeps a reference to the event it built and asserts
`f"{over.start:%H:%M}"` against the cell. Not `"00:00"`, which is the right
answer today and would be the same defect the moment the fixture changes
again — a value maintained in parallel, correct until it is not.

The alternative was to leave the arithmetic and correct it to `0`. That
restores the check and preserves exactly the property that broke it: two
places computing one value.

There is a narrow case where reading the value back would assert nothing —
where the point is that the *product* produces some constant. That is not
this: the label the board draws for an event's start is under test, and the
event's own start is the independent thing to compare it against.

### The sweep judges every assertion, not one property

`every_hour` builds the three positions for each hour and presently asks only
whether the board recedes each. It gains the rest of what `positions` claims
about a row: the mark, the start label read from the event, the title, the
calendar, and the absence of a strike.

That is what makes this class of failure loud. The previous change proved the
fixtures *mean* the right thing at every hour, and proved the board *draws*
the right shading — but a suite's claim about a fixture is broader than
either, and the sweep is the only place that exercises all twenty-four hours.

Rejected: leaving the sweep alone and trusting that the one stale expectation
was the only one. It was, this time — the file was searched. Trusting that
next time is how this one survived a change whose subject was suites lying
about the clock.

### The requirement is written for fixtures, not for clocks

Nothing about the defect was temporal. An expectation computed beside a
fixture instead of from it will drift whenever the fixture changes, whether
the fixture is an event, a mailbox, a row or a width. So the new requirement
sits beside the clock one rather than inside it, and says what it is really
about.

## Risks / Trade-offs

- **The widened sweep runs twenty-four boards with more assertions each** →
  the sweep already builds those boards; adding cell comparisons to each costs
  no additional board and no additional hour.
- **Reading the expectation off the fixture can assert a tautology** → only
  where the fixture and the product compute the same value the same way. Here
  they do not: the suite supplies a datetime and the board formats a label
  from it, so the comparison still tests the formatting. Named in the
  requirement so the distinction is not lost.
- **The new requirement could be read as banning every literal in a suite** →
  it says the opposite for a genuine constant, and gives the test: a constant
  is written plainly, and what is forbidden is rebuilding the fixture's own
  arithmetic. Worth keeping in view when it is next cited.
- **`positions` and the sweep now assert overlapping things** → deliberate.
  `positions` is the readable statement of what a row shows; the sweep is the
  same statement made at every hour. The overlap is the point, and the cost is
  one duplicated list of expectations, which the fix keeps in one helper so it
  is not two lists to maintain.
