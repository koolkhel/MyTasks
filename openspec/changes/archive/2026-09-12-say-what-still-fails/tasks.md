Two files change and no product code does, so the board cannot regress: the
day-guarded baseline and the before-and-after capture are not the instrument
for this change and are not used. Everything below is verified by running the
suites themselves.

## 1. Establish that the four really pass

- [x] 1.1 Run the four through the runner so they are paced and given the
      suites' token, not the board's:
      `.venv/bin/python tests/run.py t_place t_perf t_undo6 t_work6`.
      This is the live tier against the real task store. Passing is all four
      reported `ok`, each summary equal to its own total (20/20, 5/5, 11/11,
      16/16), each marked `(fixed)` because it is still listed, zero
      throttles, and no leftover tasks reported at the end. Re-run any single
      failure once before believing it -- these suites contend over one
      account.
- [x] 1.2 Record the run: the four summaries and the date, into the
      resolution note written in 2.2, so that the removal rests on a run
      somebody can point at rather than on a claim.

## 2. Take the four off the list

- [x] 2.1 Remove the `t_place`, `t_perf`, `t_undo6` and `t_work6` entries from
      `KNOWN` in `tests/known_failures.py`. Anchor each edit on its own suite
      name and assert the anchor is present before writing. Passing is
      `.venv/bin/python -c "import sys; sys.path.insert(0,'tests'); import
      known_failures as k; print(sorted(k.KNOWN))"` printing `['t_top6']`
      and nothing else.
- [x] 2.2 Write the resolution record beside `REPAIRED`, `REWRITTEN` and
      `LOST`: what the four entries said, that all four passed twice on
      2026-09-12 plus the run from 1.1, and that they were removed for
      passing rather than for being inconvenient. Remove the trailing
      paragraph that calls them "one thread and not four", since the thread
      is closed. Passing is all four names still present in the file, none of
      them inside `KNOWN`, and the module importing clean.
- [x] 2.3 Confirm the runner stops treating them as known:
      `.venv/bin/python tests/run.py t_place t_perf t_undo6 t_work6` again,
      live against the task store with the suites' token. Passing is all four
      `ok` with no `(known)` and no `(fixed)` note on any of them, since
      there is no entry left to match.

## 3. Let the calendar suite say what it cannot run

- [x] 3.1 In `tests/config/t_ical.py`, guard the final block -- the one
      headed "an account that is not on the machine is reported, not passed
      over" -- on `ical._status() == ical._FULL_ACCESS`, read after the suite
      has restored the real `_status`. Anchor the edit on that block's own
      `print(...)` line and assert the anchor is present before writing.
      Passing is `.venv/bin/python -c "import ast;
      ast.parse(open('tests/config/t_ical.py').read())"` exiting 0 and the
      guard appearing after the `ical._status = real` restore, not before it.
- [x] 3.2 On the refusal path, print which permission is missing and how many
      checks were not run, and count only the checks that ran. Passing is
      covered by 3.3.
- [x] 3.3 Run it on this machine, which does not grant the permission. This
      is the config tier: it reads the board's own `.env` and touches neither
      the task store nor its token. `time .venv/bin/python
      tests/config/t_ical.py`. Passing is exit 0, a summary reading
      `13/13 checks passed`, a line naming the calendar permission as the
      reason two checks did not run, and a wall time under five seconds --
      which is what shows the 30-second access-request path was not taken.
- [x] 3.4 Show that the guard, and nothing else, is what skipped them. With
      `ical._status` substituted to report full access, run the same suite
      and confirm the two checks are attempted again. This is a substituted
      status, not a real calendar, so they are expected to fail here; the
      point is that they run. Passing is the two check names appearing in the
      output where 3.3 showed a skip.

## 4. On a machine that grants the permission

- [x] 4.1 Ask the user to run `.venv/bin/python tests/config/t_ical.py` from
      a terminal that holds the calendar grant, with `!` so the output lands
      here. This shell cannot do it and must not try. Passing is
      `15/15 checks passed` and no skip line -- both guarded checks ran and
      the guard let them.

## 5. Leave the rest of the suites as they were

- [x] 5.1 Run the self-contained tier, which needs no credentials and no
      token: `.venv/bin/python tests/run.py`. Passing is the same result as
      at HEAD before these edits, with no suite newly failing and no mention
      of the four.
- [x] 5.2 Freeze the two edited files and confirm the verification covered
      what shipped: `shasum tests/known_failures.py tests/config/t_ical.py`
      after 1.1, 2.3, 3.3, 3.4 and 5.1 have all run, compared against the
      same command taken before 5.1 started. Passing is the two pairs
      identical. Un-check any task above whose run predates a later edit to
      either file.
