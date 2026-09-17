## Context

See proposal.md — Why. What follows is the shape of the 52 suites this has to
work on, measured rather than assumed.

Every one of them has the same anatomy:

```
  ok = []                       module-level list of booleans
  def check(name, got, want)    30 suites -- prints "  ok  <name>" / "  FAIL"
  def chk(label, cond, extra)   the other 22 -- prints "  [PASS] <label>"
  def board(...)  settle(...)   helpers: build an app, pump it, read a cell
  async def folding(): ...      the parts: one situation, set up and checked
  ...
  for fn in (folding, ...):     the tail: drives them, in module scope
      asyncio.run(fn())
  print(f"{sum(ok)}/{len(ok)} checks passed")
  sys.exit(0 if all(ok) else 1)
```

Four facts from that shape decide the design:

1. **The parts have no naming convention.** They are prose — `folding`,
   `rewinding`, `the_text_still_lands`, `one_height` — and they sit beside
   helpers that look identical (`board`, `settle`, `select`, `rows`). Only the
   tail's tuple says which is which. 199 are named in a tuple today; 371
   functions are defined in total.
2. **47 of 52 drive themselves in module scope**, with no `__main__` guard, and
   call `sys.exit` there. Importing one runs it and ends the process.
3. **9 suites check at module level too** — `t_gateway` (141 checks) and
   `t_mail` (65) are flat scripts with no part structure at all.
4. **The suites mutate global state at import.** The harness replaces the
   configuration loaders of `singularity`, `ical`, `mail`, `gateway` and
   `journal`; individual suites replace `ical.fetch`, `journal.PATH` and the
   workspace launcher. 45 build Textual apps, 20 run threads with gates.

The runner also parses what a suite prints: `tests/run.py` greps the output
for check lines, matches `N/M checks passed` for the per-suite summary, and
`known_failures.signature()` counts the lines containing `FAIL` to decide
whether a listed failure is still the one that was recorded.

## Goals / Non-Goals

**Goals:**

- One addressable, separately reported unit per part, without renaming a part
  or rewriting a check.
- Everything `tests/run.py` reports today keeps working byte-for-byte in form:
  the per-suite check counts, the tier summary, the throttle verdict, the
  known-failure signatures.
- A suite still runs as `python tests/stub/t_x.py`, and runs the same parts
  that way as it does under the runner.

**Non-Goals:**

- Teaching pytest the live tiers' protocol. The store, tracker, config and
  gateway suites are launched exactly as they are now.
- Running suites concurrently (see proposal.md — What Changes).
- Sharing one check helper across the suites. 52 local copies in two dialects
  is duplication worth removing one day, and doing it here would put 1,649
  call sites in the diff of a change whose whole verification is that no check
  moved.

## Decisions

### The unit is a part, declared as `PARTS`

Each suite ends with a tuple naming its parts, and drives them through one
shared helper:

```python
PARTS = (t_hours, t_days, t_opens, t_moment, ...)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
```

`run_parts` lives in `tests/harness.py`, calls a part directly or through
`asyncio.run` depending on what it is, prints the `N/M checks passed` line and
returns 0 or 1 — which is what the 52 hand-written tails do today, once.

*Alternative rejected: rename every part to `test_*` and let pytest collect by
convention.* It renames 199 functions, and since nothing distinguishes a part
from a helper by name, each of the 371 functions has to be classified by hand
anyway — the same reading, with a worse result: the names stop being prose.

*Alternative rejected: `python_functions` glob in pytest.ini.* There is no
glob that separates `folding` from `settle`.

### A custom collector, not pytest-asyncio

`tests/conftest.py` collects a suite file by importing the module and yielding
one item per entry in `PARTS`. Each item runs its part the way the suite runs
it today: called if it is an ordinary function, `asyncio.run(part())` if it is
a coroutine function.

This matters more than it looks. Textual's `run_test()` is entered inside the
part, and today each part gets a fresh event loop from its own `asyncio.run`.
pytest-asyncio would supply a loop from the plugin instead, changing the
lifetime of the loop the app under test lives in. The suites are the
instrument; the migration must not alter what the instrument measures. It also
means one fewer dependency.

### Pass or fail is read off the suite's own `ok` list

The item notes `len(ok)` before the part and inspects the new entries after.
Any `False` fails that item, and the failure message names the part and how
many of its checks failed.

So **no check is rewritten**, and every check in a part still runs even after
an earlier one fails. That is better than the trade-off named when this was
scoped ("a group's first failing check stops that group") and it is worth
saying why it is worth keeping: counting how many checks fail is an instrument
this project uses. Verifying that a rule is not vacuous means neutering the
rule and counting the failures it causes — 53 checks for one recent change, 12
for another. Hard `assert` per check would stop each part at its first
failure, and that count would stop meaning anything.

*Alternative rejected: convert all 1,649 checks to `assert`.* It is the
idiomatic pytest shape, and it costs the got/want reporting, the
failing-check counts, and a diff that touches every line the suites exist for.

### One process per suite, still

`run.py` runs `pytest <one suite file>` per suite, exactly where it runs
`python <one suite file>` today, and keeps its 600-second timeout.

Not `pytest tests/stub` in one process: 52 modules that each rewrite global
module state at import, 45 that build Textual apps and 20 that run threads
would then share one interpreter. Process isolation per suite is a property
this project has for free today, and a migration is a bad moment to trade it
for a faster startup.

### Capture stays off, and the collector prints the summary line

`run.py` is given `-s` so the suites' own printed check lines reach it
unchanged, and a session hook prints `N/M checks passed` from the module's
`ok` list at the end, as the tail used to. With those two, `run.py`'s
reporting and `known_failures.signature()` need no change at all: the same
lines arrive, matched by the same regexes.

### Collection is confined to the self-contained tier

`pytest.ini` sets `testpaths = tests/stub` and `python_files = t_*.py`, and
the conftest refuses to collect a file outside that directory unless the
runner asks for it explicitly.

This is the one genuinely dangerous failure mode here. Collecting a file means
importing it, and the store suites build a client at module level — several
create tasks. A bare `pytest` typed at the repository root, with no arguments,
must not be a way to write to a real account. `tests/run.py` guards this today
by never importing a suite to classify it; the new entry point has to guard it
too.

### `pytest` goes in `requirements.txt`

`run.sh` already rebuilds `.venv` whenever that file changes, so one line there
keeps a fresh clone one step from a green run — which is what the spec asks of
the default run. A separate `tests/requirements.txt` would be tidier about what
the board itself needs and would make that path two steps, and the runner would
have to explain the second one.

The runner checks for pytest before starting and, if it is absent, names the
install command and runs nothing.

## Risks / Trade-offs

- **A part is dropped while converting 52 tails, and the suite still reports a
  pass.** This is the main risk of the whole change, and it is the hazard the
  change exists to close, so introducing it here would be the worst possible
  irony. → The per-suite check count is captured for all 52 suites before any
  edit and compared after every batch. A dropped part takes its checks with
  it; the count falls; the batch does not proceed until it matches.
- **The 9 suites that check at module level have to be wrapped into parts.**
  `t_gateway` (141 checks) and `t_mail` (65) are flat scripts. → Wrap each
  suite's module-level body in a single part first, with no other edit, and
  confirm the count is unchanged; split it into more parts only afterwards, if
  at all. Wrapping and splitting in one step is how a check gets lost.
- **A suite's parts share state the module set up, and pytest may run them in
  a different order than the tuple.** → Items are yielded in `PARTS` order,
  and the spec requires that order. Anything that reorders them (`-p
  randomly`, a `--lf` run) reorders what the suite meant; `--lf` re-running a
  single failing part is fine because a part that needs its predecessors was
  never re-runnable alone in the first place — which is worth finding out.
- **Importing a suite at collection time runs its module body**, which builds
  fixtures and patches globals. That is unchanged from today (the runner
  executes the same module), but under pytest it happens during collection,
  before any part runs. → The `__main__` guard means the body no longer
  *drives* anything; collection therefore does the same work the interpreter
  did at import before, and no more.
- **Two ways to run a suite can drift apart.** → The spec requires both to run
  the same parts and report the same count, and one task checks it on a
  sample of suites from each shape.

## Migration Plan

1. Capture the baseline: every self-contained suite's `N/M checks passed`,
   all 52, plus the tier total.
2. Add `run_parts` to the harness, the conftest collector, `pytest.ini`, and
   the dependency. Nothing is converted yet; the tier still runs as scripts
   and must still be green.
3. Convert in batches, comparing counts after each: the 43 suites that need
   only a tail rewrite first, in batches of about ten; then the 9 that check
   at module level, one at a time.
4. Switch `run.py`'s self-contained tier to `pytest <file>`, and confirm the
   tier summary, the per-suite counts and a deliberately failed check all read
   as they did.

Rollback is per batch: a suite's tail is the only thing that changed in it, and
a batch that will not reconcile can be reverted on its own without touching the
harness, the conftest or the runner.

## Open Questions

None that change the specs, the approach or the tasks. Two things are
deliberately left for later changes: the live tiers, and whether the 52 local
check helpers become one shared one.
