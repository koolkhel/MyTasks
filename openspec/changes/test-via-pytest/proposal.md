## Why

The suites answer "did I break anything" well, and they answer nothing smaller
than a whole suite. A run addresses a file; a failure is re-run as a file; a
file that takes 70 seconds is re-run whole to look at one check. The 52
self-contained suites hold 199 named parts between them -- `folding`,
`rewinding`, `the_text_still_lands` -- and none of them can be named from
outside the file it lives in.

There is a second, quieter reason. A part is a function the suite's own tail
happens to call. Nothing checks that the tail calls all of them, so a part can
be written, left out of the list, and never run, and the suite goes on
reporting a number that looks like a full pass. That hazard is real: a scan of
the tiers found 40 group-style functions and had to read each tail by hand to
establish that none was orphaned. Collecting parts from a declaration makes
the list the only list there is.

This was explored first and the recommendation was against migrating: the
runner carries protocol -- throttle verdicts, signature-matched known
failures, tier preflight, leftover scans -- that pytest has nowhere to put.
The scope here answers that. The runner keeps all of it and gains pytest
underneath, and only the tier that needs no credentials moves.

## What Changes

- Each of the 52 self-contained suites declares its parts in one place, as
  `PARTS`, and drives them through a shared runner in the harness instead of
  its own hand-written tail. **No check is rewritten.** All 1,649 of them keep
  their wording, their `got`/`want` reporting and their accumulation into the
  suite's own `ok` list.
- 47 of those suites currently run themselves at import and call `sys.exit`
  in module scope. Their driving moves behind a `__main__` guard, so importing
  a suite no longer runs it -- the precondition for anything collecting them.
- A collector in `tests/conftest.py` turns each declared part into one pytest
  item, so a part is addressable by name (`-k rewinding`), re-runnable on its
  own, and reported pass or fail individually.
- `tests/run.py` runs each self-contained suite as `pytest <file>`, still one
  process per suite. Its tier preflight, 25-second pacing, throttle counting,
  inconclusive verdict, known-failure signatures and leftover scan are
  untouched, and it still reports `N/M checks passed` per suite.
- A `pytest.ini` confines collection to the self-contained tier, so typing
  bare `pytest` in the repository cannot start a suite that talks to the real
  store, tracker or mail account.
- `pytest` is added to `requirements.txt`; the runner says what to install if
  it is missing rather than failing with an import error.

Not in this change, deliberately:

- **The live tiers.** The store, tracker, config and gateway suites keep
  running exactly as they do today. They are where the quota protocol lives
  and where a mistake costs a spent quota; they move once this tier has proved
  the approach.
- **Parallel execution.** Measured while exploring this: the self-contained
  tier is 12.1 minutes sequential and 140 seconds at six at a time, 5.2x, with
  all 52 green and the fixture tree byte-identical afterwards. It is the
  larger prize and it needs no pytest at all, which is exactly why it is
  separate -- changing how suites are collected and how many run at once in
  one change would leave neither verifiable.
- **Any product code.** This change touches no file the board runs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite`: a suite gains a declared list of its parts, and each part is
  separately reported and separately runnable; the runner's summary gains the
  ability to name a failing part rather than only a failing file; the default
  run must hold for every way a run can now be started, including the test
  tool's own command, and must say what to install rather than fail obscurely.

## Impact

- **Code**: 52 suites in `tests/stub/` (tails only), `tests/harness.py`,
  `tests/run.py`, new `tests/conftest.py` and `pytest.ini`,
  `requirements.txt`. No product module.
- **Dependencies**: adds `pytest`. The board itself does not import it.
- **Risk**: converting 52 tails by hand can drop a part, and a dropped part
  reads as a pass. The instrument against it is the per-suite check count:
  every suite's `N/M checks passed` must be identical before and after, all 52
  of them, and the tier total with it.
- **Unaffected**: the live tiers, the pacing, the throttle verdict, the
  known-failure list, the leftover scan, and every check's wording.
