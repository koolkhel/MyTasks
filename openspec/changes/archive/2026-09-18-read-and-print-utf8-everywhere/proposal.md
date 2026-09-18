## Why

Twenty-two places in `tests/` read a file without saying what encoding it is
in, ten more decode a child process's output the same way, and eighteen suites
print check names that are not ASCII. On a machine whose locale is not UTF-8
-- Windows with cp1251 is the one that was reported -- the first of these fails
on the first non-ASCII byte, the runner itself fails decoding the first suite
that prints a `☑`, and a suite run on its own dies printing its first check.
Fourteen of the reads are of the board's own source, which has 111 lines of
non-ASCII, so under cp1251 they cannot pass by luck. `PYTHONUTF8=1` makes the
whole tier green, which is the proof that nothing is wrong with the code being
checked: the suites depend on a setting the repository neither sets nor names.

The board itself has no such place. The suites promise to pass on a fresh
clone with nothing configured, and a locale is something nobody configures.

## What Changes

- Every text read and write in `tests/` names `encoding="utf-8"`.
- Every `subprocess.run(..., text=True)` in `tests/` names the encoding it
  decodes with, the runner's own included.
- The runner hands its children `PYTHONUTF8=1`, and a suite started on its own
  -- directly or under the test tool -- reconfigures its own standard output to
  UTF-8 first, so the guarantee does not depend on having come through the
  runner. That is the same argument the suites' token already makes: the
  moment somebody narrows a failure down is the moment they run one suite by
  hand.
- A part in a stub suite scans `tests/` for a text open, a `read_text`, a
  `write_text` or a `text=True` without an encoding, so the count stays at
  zero rather than drifting back to twenty-two.
- The fresh-clone promise in the `test-suite` spec says explicitly that the
  machine's locale is one of the things a run must not need.

Recorded assumption: this is locale independence, not a commitment to Windows.
The board's calendar integration is macOS-only and stays so; what changes is
that the self-contained suites no longer fail for a reason unrelated to the
code on any machine whose default encoding is not UTF-8.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite`: "The suites live in the repository" gains locale independence
  for a suite run on its own; "A run needs no credentials by default" gains it
  for the run.

## Impact

- `tests/run.py`, `tests/testtoken.py` (`child_env`), `tests/parts.py`,
  `tests/conftest.py`, and the 22 + 10 sites across the stub, config and store
  tiers and the helpers beside them.
- One new part in a stub suite, the guard.
- No product file is touched; none needs to be.
