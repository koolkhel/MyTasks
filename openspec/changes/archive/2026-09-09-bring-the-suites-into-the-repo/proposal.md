## Why

The suites that verify this board do not exist anywhere durable. They are 82
standalone scripts in one session's scratchpad — 64 current ones, the rest
pre-change copies — and when that session ends they are gone. Twenty-six
changes have been verified with them; nothing of that survives except the
claim in each archived `tasks.md` that it passed.

That is already costing something. A fresh session cannot answer "did I break
anything" without rebuilding the instrument first, and it cannot know that
seven suites fail for reasons that predate whatever it is working on. The
knowledge of *which* failures mean nothing lives only in this conversation.

## What Changes

- The surviving 55 suites move into `tests/` in the repo, unchanged in what
  they assert, and five more are written afresh: they were lost from the
  scratchpad during this change, which is the argument for it made concrete. The 18 `_ref` and `_old` copies do not come: they are snapshots of
  a suite as it stood before one particular change, and they have served that
  purpose.
- One further suite is left out for the same reason as those copies: it
  compares the board against a snapshot of the *product* as it stood before a
  change, so importing it would mean committing three thousand lines of
  superseded `main.py` as a fixture. It was already a known failure.
- Four more files come in as probes rather than suites, and are never run.
  They assert nothing — they print what Textual does with a keypress, which is
  how the Cyrillic key-twin table was worked out — so counting them as passing
  suites would make a green run mean less than it appears to.
- A runner, `tests/run.py`, discovers the suites and runs them: the stubbed
  ones as a batch by default, the live ones only when asked, paced apart and
  counting throttle errors, and refusing to start when the credentials they
  need are absent.
- Suites are separated by what they need to run: nothing beyond the repository
  (34), the board's own configuration (4), the real task store (18), or the
  issue tracker behind a VPN (3). A clone with no `.env` runs the first group
  and comes back green.
- The seven suites that currently fail are imported and listed as known
  failures, each with a one-line reason, so the default run is green and the
  failures are recorded rather than rediscovered.
- **A tracker key scrubbed from this history with `filter-repo` appears in
  seven of these suites, and another project's code in one.** They are
  replaced with invented keys before anything is committed. This is the one
  part of the change that cannot be got wrong.
- The synthetic sample maildir becomes a fixture, with the generator that
  produced it, so its provenance is checkable and it can be rebuilt.
- Absolute paths go. Every suite currently hardcodes both the scratchpad and
  the repo, which is what makes them unrunnable anywhere else.
- **Not in scope:** rewriting the suites as pytest. That is the next change,
  deliberately separated so the rewrite happens with a committed version to
  diff against rather than against the only copy. Nothing here changes what a
  suite asserts.
- **Also not in scope:** fixing the seven failing suites, adding CI, and
  bringing in the scratchpad's captures, baselines and backups — the last of
  those describe a real account and belong nowhere near the repo.

## Capabilities

### New Capabilities

- `test-suite`: what the repo's suites are, what each one is allowed to need,
  how the runner decides which to run, and what it does about a suite that is
  known to fail. Its own capability rather than part of `task-board` because
  it describes the instrument, not the board.

### Modified Capabilities

None. The board's behaviour does not change: no file it reads, writes or
draws is touched.

## Impact

- `tests/` — new: the suites, the runner, the shared harness, the fixture.
- `.gitignore` — the baselines and captures a live run generates describe a
  real account and must stay out.
- `requirements.txt` — whatever the suites need that the board does not.
- `.env` — a second token for the account, used only by the suites, so a test
  run that exhausts the quota does not take the board down with it. It is
  gitignored, as every other credential here is.
- The task store and the tracker — unchanged, but a live run still creates and
  deletes real tasks, and the runner is what keeps that opt-in.
- **The commit convention needs one amendment**: staging with
  `git add -- '*.py' openspec` silently omits the maildir fixture, which is
  not a `.py` file. Left alone, the tests would land without the data three of
  them read.
