## 1. Baseline and dependency

- [x] 1.1 Capture the baseline before touching anything: run the self-contained
      tier with `python tests/run.py` and save every suite's reported
      `N/M checks passed` line, all 52, plus the tier summary, to a file kept
      for the duration of the change. Passing is a saved list of 52 lines and a
      summary reading `52 passed, 0 failed`. This is the instrument every
      conversion task below is checked against, so it is captured before the
      first edit and never re-taken afterwards. **Result: captured — but of 54 suites, not the 52 this task names. `t_paint` and `t_drawn` arrived with model-refactoring after this change was planned, so the tier is two suites larger and the batches in groups 3 and 4 are two short; both are folded in below. The baseline is the tier run taken at the end of markup-copying-options: `54 passed, 0 failed`, with `main.py`, `board.py` and `t_copy.py` at the checksums they still have, so it describes exactly the code this change starts from and predates its first edit.**
- [x] 1.2 Add `pytest` to `requirements.txt` and install it into `.venv`.
      Verify with `.venv/bin/python -m pytest --version` printing a version,
      and with `python tests/run.py` still reporting `52 passed, 0 failed`
      against the unconverted suites — the dependency alone must change
      nothing. **Result: done. `pytest>=8.0` in `requirements.txt`, pytest 9.1.1 in `.venv`, and the tier re-run with it installed: 54 passed, 0 failed, every count identical to 1.1. `main.py`, `board.py` and `harness.py` were byte-identical before and after that run.**
## 2. The machinery

- [x] 2.1 Add `run_parts(parts, ok)` to `tests/harness.py`: call each part
      directly or through `asyncio.run` depending on whether it is a coroutine
      function, in the order given, then print `N/M checks passed` and return 0
      or 1. Verify by using it in one already-converted-by-hand suite
      (`t_window`, 7 sync parts then 9 async) run directly: same 103 checks,
      same exit code as the baseline line for it. **Result: done. `run_parts(parts, ok)` in the harness dispatches on `inspect.iscoroutinefunction`, runs in the order given, prints the count and returns the exit status. t_window converted and run directly: 16 parts, 103/103, its baseline count.**
- [x] 2.2 Add `tests/conftest.py`: collect a suite file by importing it and
      yielding one item per entry in its `PARTS`, run each item the way
      `run_parts` runs a part, and fail an item when any check it appended to
      the module's `ok` list is false, naming the part and how many of its
      checks failed. Verify with `.venv/bin/python -m pytest -s
      tests/stub/t_window.py`: 16 items reported by part name, all passing. **Result: done. `tests/conftest.py` collects a suite as its `PARTS`, runs each part as `run_parts` would, and fails an item when a check it appended to the module's `ok` list is false. `pytest -s tests/stub/t_window.py`: **16 passed**, each named for its part. The conftest imports no product module, so a suite that checks the board can be decided without an application still finds none imported.**
- [x] 2.3 Print the `N/M checks passed` line from a session hook in the
      conftest, from the module's `ok` list, so a pytest run of a suite prints
      what its tail used to. Verify by running `t_window` under pytest and
      under `python tests/stub/t_window.py` and diffing the two outputs' last
      line — identical. **Result: done. A session hook prints the line from the module's `ok` list. Diffed both ways for t_window: identical, `103/103 checks passed`.**
- [x] 2.4 Add `pytest.ini` with `testpaths = tests/stub` and
      `python_files = t_*.py`, and make the conftest refuse to collect a file
      outside `tests/stub` unless the runner asks for it. Verify with
      `.venv/bin/python -m pytest --collect-only -q` at the repository root:
      the collected files are exactly the 52 under `tests/stub`, and no file
      from `tests/store`, `tests/tracker`, `tests/config`, `tests/gateway` or
      `tests/probes` appears. This is the check that a bare `pytest` cannot
      reach a real account.
 **Result: done, and verified only once every suite was converted — before that a bare `pytest` could not get past collection, because importing an unconverted suite ran it and exited. `python_files` is set to a pattern that matches nothing, deliberately: the suites are collected by the conftest, and leaving pytest's own collector matching them too would import all 54 a second time looking for `test_` functions that do not exist. `pytest --collect-only` at the root now reaches exactly the 54 files under `tests/stub` and nothing from store, tracker, config, gateway or probes. `.pytest_cache/` is gitignored; the cache itself is left on, since it is what `--lf` remembers.**
## 3. Converting the 43 suites that need only a tail

Each batch: move the driving code behind a `__main__` guard, declare `PARTS` in
the order the old tail ran them, drive it through `run_parts`, change nothing
else. After each batch, run those suites through `python tests/run.py <names>`
and compare each one's `N/M checks passed` with its line in the 1.1 baseline.
A batch is done only when every line matches exactly.

- [x] 3.1 Batch A (t_add, t_bands, t_block, t_bulk, t_busy, t_cal, t_copy,
      t_crash, t_elapsed, t_group2) — counts match the baseline for all ten. **Result: batch A done — t_add 19/19, t_bands 23/23, t_block 30/30, t_bulk 102/102, t_busy 112/112, t_cal 49/49, t_copy 71/71, t_crash 44/44, t_elapsed 36/36, t_group2 15/15. All ten match the baseline.**
- [x] 3.2 Batch B (t_green2, t_green3, t_keys2, t_label2, t_mailperf,
      t_mailview, t_mark, t_markup, t_move, t_neigh) — counts match for all ten. **Result: batch B done, with one swap — `t_mailperf` turned out to check at module level, so it moved to group 4 and `t_star2`, which reads cleanly, took its place. t_green2 21/21, t_green3 31/31, t_keys2 27/27, t_label2 18/18, t_mailview 107/107, t_mark 103/103, t_markup 27/27, t_move 36/36, t_neigh 19/19, t_star2 15/15. All ten match.**
- [x] 3.3 Batch C (t_note, t_pane, t_paste, t_pastein, t_promote, t_review,
      t_search, t_still, t_top, t_trace) — counts match for all ten. **Result: batch C done — t_note 39/39, t_pane 85/85, t_paste 40/40, t_pastein 50/50, t_promote 78/78, t_review 132/132, t_search 107/107, t_still 40/40, t_top 30/30, t_trace 72/72. All ten match. `t_paste` imported nothing from the harness at all and gained one import line.**
- [x] 3.4 Batch D (t_track2, t_track3, t_twins2, t_twins4, t_undo1, t_undo3,
      t_version, t_window, t_work3) — counts match for all nine. **Result: batch D done, with `t_paint` folded in — t_track2 69/69, t_track3 16/16, t_twins2 79/79, t_twins4 12/12, t_undo1 55/55, t_undo3 41/41, t_version 26/26, t_window 103/103, t_work3 36/36, t_paint 45/45. All ten match.**
- [x] 3.5 Batch E (t_work5, t_workspace, t_writes, t_fit) — counts match for all
      four.
 **Result: batch E done, with `t_drawn` folded in — t_work5 31/31, t_workspace 91/91, t_writes 55/55, t_fit 37/37, t_drawn 5/5. All five match. That is 45 suites converted with every count identical.**
## 4. Converting the 9 suites that check at module level

These have checks outside any function — `t_gateway` has 141 and `t_mail` 65,
as flat scripts. Wrap each suite's module-level body in one part, with no other
edit; do not split it into several parts in the same step. One suite at a time,
each verified against its baseline line before the next is started.

- [x] 4.1 t_fit2, t_star, t_star2 (4 module-level checks each) — each suite's
      count matches its baseline line. **Result: done — t_fit2 17/17, t_star 36/36, t_star2 15/15 (that last one converted in batch B, reading cleanly). Each wrapped into one named part with no other edit.**
- [x] 4.2 t_green (14), t_twins1 (15), t_title (22) — each count matches. **Result: done — t_green 14/14, t_twins1 46/46, t_title 25/25. Two things came out of these. `t_twins1` reached only the repository on its path, never the suites, so it could not import a shared helper at all; it gained the one line its neighbours all have. `t_title` keeps **two** lists of checks and its total has always been their sum, so wrapping it against one list silently reported 22 of 25 — the runner and the collector now take as many lists as a suite keeps, and `t_title` names both in `CHECKS`.**
- [x] 4.3 t_mailflat (25), t_mail (65) — each count matches. **Result: done — t_mailflat 25/25 and t_mail 62/62, both their baseline counts. `t_mail` is not a body and a tail: its checks sit between its definitions all the way down the file, so the whole body from the first heading became the part, as a pure indent. Nothing moved, so every helper still closes over what it was written beside. Two things had to be handled: importing the harness blanks `mail.load_config`, which this suite exists to check, so the runner helper was moved into `tests/parts.py` where importing it changes nothing; and `cfg` was lifted to module level, being read by more than one stretch.**
- [x] 4.4 t_gateway (141) — count matches. Note this is the stubbed suite of
      that name in `tests/stub/`, not the live `tests/gateway/` tier, which
      this change does not touch.
 **Result: done — t_gateway 239/239, its baseline count, wrapped the same way, with `KINDS` lifted to module level. Both suites now run **nothing** at import: 0 checks on load, where t_gateway ran 219 of its 239 before. That was not cosmetic — collected in a process that had already read another suite, it failed outright on a loader that suite had blanked.**
## 5. The runner

- [x] 5.1 Make `tests/run.py` launch each self-contained suite as
      `pytest -s <file>` in its own process, keeping the 600-second timeout,
      and leave every other tier launching exactly as it does now. Verify that
      `python tests/run.py --list` is unchanged and that a single named suite
      (`python tests/run.py t_pane`) reports the same count as its baseline
      line. **Result: done. `command_for(tier, name)` is the only place that decides, and it decides on the directory alone: the self-contained tier goes through `pytest -s`, every other tier is started exactly as before. One process per suite either way, 600-second timeout kept. `tests/run.py --list` is unchanged (54 stub, 3 probes) and `tests/run.py t_pane` reports 85/85, its baseline count.**
- [x] 5.2 Make the runner check for pytest before starting a self-contained
      run and, when it is absent, name the install command and run nothing.
      Verify by running `python3 tests/run.py` with the system interpreter,
      which has no pytest: it prints what to install, runs no suite, and exits
      non-zero. **Result: done. The guard refuses before anything is started, naming the install command, and returns 2 — the same shape as the refusal for a missing credential. The task's instrument was to run with the system interpreter, which does not isolate it: that interpreter also lacks `python-dotenv` and fails earlier, on an import the runner has always needed. The branch was exercised directly instead, with `has_pytest` answering False: it printed what to install, ran no suite and exited 2.**
- [x] 5.3 Update the project context in `openspec/config.yaml` to say that the
      self-contained tier runs under pytest, that a suite declares its parts,
      and that collection is confined to that tier. Verify by reading it back:
      it describes the runner a person would now meet, and still names
      `python tests/run.py` as the command.
 **Result: done. The project context now says that a suite names its parts and does nothing at import, that the runner starts the self-contained tier with pytest one process per suite, that collection is confined to that tier and why, and that the other tiers are still run as scripts. It still names `python tests/run.py` as the command, which has not changed.**
## 6. Verification against the stub

Everything in this group runs against stubs and substituted sources. No
credentials, no network, no account.

- [x] 6.1 Full tier: `python tests/run.py` reports `52 passed, 0 failed`, and
      every one of the 52 `N/M checks passed` lines is identical to the 1.1
      baseline. Passing is an empty diff between the two lists of 52 lines. **Result: `54 passed, 0 failed`, and every one of the 54 check counts identical to the 1.1 baseline — an empty diff. Run twice: once when the conversion was first complete, and again after the five suites that still checked at import were re-wrapped, since a verification run that predates a later edit proves nothing about what is there now.**
- [x] 6.2 A part can be named from outside: `.venv/bin/python -m pytest -s
      tests/stub/t_pane.py -k rewinding` runs that part and no other. Passing
      is one item reported, named for the part, and the suite's other parts
      absent from the output. **Result: done. `pytest -s tests/stub/t_pane.py -k rewinding` reports `1 passed, 8 deselected` and only that part's 9 checks ran.**
- [x] 6.3 A failing part is re-runnable alone: break one check in one part of
      `t_still` by hand, run the suite under pytest, then re-run with `--lf`
      and confirm only that part runs. Restore the file and confirm with
      `shasum` that it is byte-identical to what it was before the edit. **Result: done. One check broken in `ticking_holds`: the suite reported `1 failed, 5 passed` in 24.3s, and `--lf` then reported `1 failed, 5 deselected` in 6.3s — only the part that failed. Restored, and `shasum` reads `f56ce873e29cc1030fca5cd6f2a8b60fe7f45a62` as before.**
- [x] 6.4 Both ways of running a suite agree: for one suite from each shape
      (`t_window` tail-only, `t_mail` wrapped body, `t_bulk` already had a
      `main_`), run `python tests/stub/<suite>.py` and
      `.venv/bin/python -m pytest -s tests/stub/<suite>.py` and compare the
      `N/M checks passed` line. Passing is the same count from both, for all
      three. **Result: done — all three agree. t_window 103/103, t_mail 62/62, t_bulk 102/102, the same count run as a script and run under pytest.**
- [x] 6.5 Loading a suite runs nothing: import each of the 52 modules in a
      subprocess without running them, and confirm none prints a check line and
      none exits the process. Passing is 52 imports completing and no `ok`,
      `FAIL` or `[PASS]` line printed by any of them. **Result: done, and it took a second pass. All 54 modules load, none exits the process, none prints a check line and none makes a check. The first pass found five suites still checking at import — t_fit2, t_mailflat, t_star, t_star2 and t_title — because the wrapper had taken only their trailing block; they were re-wrapped whole. `t_star` needed one more thing: it drove an async part before its first heading, so that part is now declared beside the other. `t_title`'s second check list moved up beside its first, and `t_title` gained the path line its neighbours have, as `t_twins1` did.**
- [x] 6.6 A dropped part is visible: remove one part from `t_promote`'s `PARTS`
      by hand, run the suite, and confirm its check count falls below its
      baseline line. Restore the tuple and confirm the count returns to the
      baseline and the file's `shasum` matches what it was. **Result: done. Dropping `saying_so` from `t_promote`'s PARTS took it from 78 checks to 70 — and it still reported `7 passed`. That is the hazard this change exists to close, and the count is what shows it. Restored; `shasum` matches.**
- [x] 6.7 Soft checks survive: make the first check of one part of `t_writes`
      fail by hand, and confirm the later checks in that same part still ran —
      the suite's total count is unchanged from its baseline and exactly one
      check is reported failed. Restore and confirm the `shasum`. This is the
      property the vacuity technique depends on; if it is lost, the technique
      stops measuring anything. **Result: done. With the first check of `t_tick` made to fail, the failure reads `1 of 10 checks failed in t_tick` — so all ten ran. The suite's total stayed 55, and exactly one check failed.**
- [x] 6.8 The known-failure machinery still reads a run: with that same
      deliberate failure in place, confirm `known_failures.signature()` on the
      result returns the integer count of failed checks and not
      `crash:unknown`. Passing is an integer. **Result: done. On that same failing run the runner parsed `54/55 checks passed`, saw 55 check lines, and `known_failures.signature()` answered the integer `1` rather than `crash:unknown`.**
- [x] 6.9 No product code changed: `git diff --name-only` names nothing outside
      `tests/`, `pytest.ini`, `requirements.txt` and `openspec/`. Passing is
      that list containing no module the board imports.
 **Result: no product module changed — `git status` lists no `.py` outside `tests/`. The files this change touches are `tests/` (the 54 suites, the harness, the runner, the new `conftest.py` and `parts.py`), `pytest.ini`, `requirements.txt`, `openspec/`, and `.gitignore`, which this task did not name: the cache pytest writes needed a line there.**
## 7. Verification against the live tiers

These run against real services and are re-run differently from the stub
checks above. Every suite here uses the suites' own token
(`SINGULARITY_TEST_TOKEN`), never the board's, and the runner is what puts it
in place.

- [x] 7.1 The configuration tier is untouched: `python tests/run.py --config`
      runs its 5 suites as scripts, exactly as before, and reports the same
      counts as a run of that tier taken before this change. No network is
      involved; this reads the board's own `.env`. **Result: untouched, as intended. `command_for` starts every tier but the self-contained one exactly as before — read back: `config`, `store`, `tracker` and `gateway` all get `python <file>`, only `stub` gets `python -m pytest -s <file>`. The config tier reports the same five suites and the same counts as it did before this change: t_evlink 44/44, t_ical 15/15, t_noleak 13/14, t_states 29/30, t_tracker1 21/21. Those two failures are the pre-existing ones confirmed against a worktree at HEAD earlier today, not this change.**
- [x] 7.2 The store tier is untouched: run two store suites by name through the
      runner, paced by it as usual, and confirm they launch as scripts, that
      the run says it used the suites' token, and that the leftover scan
      reports nothing left on the account. Passing is both suites reporting the
      counts they reported before the change, no throttle errors, and an empty
      leftover report.
 **Result: unchanged. The runner launched both with the suites' own token, reported by its last four characters rather than printed: t_live 21/21 and t_add2 13/13, the counts they had before. No throttle errors, and the account holds nothing the suites left behind.**
## 8. At the board, by hand

- [x] 8.1 On a machine where the repository has been cloned fresh, run
      `./run.sh` once to build `.venv` from `requirements.txt`, then
      `python tests/run.py`. Passing is the tier running green with no step
      between the two beyond what `run.sh` does by itself — the default run
      still being the run a person can actually perform. **Result: done as far as this machine allows. A copy of the tracked tree with no `.venv`, built from `requirements.txt` alone, ran the tier: 51 suites matched the baseline exactly. Three differed and all three for the same reason — the copy was not a git repository, and `t_crash`, `t_busy` and `t_gateway` check that the crash file, the log and the account's own data cannot be committed. With `git init` they report 44/44, 112/112 and 239/239, their baseline counts. So the dependency claim holds: one `pip install -r requirements.txt` and the tier runs green, with no step between. What this does **not** show is another machine — same interpreter, same platform, same pip cache here.**

