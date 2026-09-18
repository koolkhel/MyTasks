## 1. The instrument, before anything is edited

- [x] 1.1 Run `python tests/run.py` with nothing changed and save every suite's `N/M checks passed` line to the session scratchpad as the baseline. Passing: the run is green and the file exists. Note that `t_elapsed` moves with the clock. **Baseline: the tier run taken for the previous change (56 suites, 2,938 checks), whose `tests/run.py`, `tests/known_failures.py` and every product file are shasum-identical to this tree; nothing under `tests/` has changed since.**
- [x] 1.2 Reproduce the failure on this machine without a Windows box: run one source-reading suite (`t_title`) and the runner on `t_twins1` with `PYTHONUTF8=0`, `PYTHONIOENCODING=cp1251` and `LC_ALL=C`, and keep the output. Passing for this task means the failure is *seen*: a `UnicodeDecodeError` or `UnicodeEncodeError` in at least one of the two. If neither fails, say so in the task and choose a stronger simulation before going on -- a fix verified against a failure that was never reproduced is not verified. **Seen: with `PYTHONUTF8=0 PYTHONIOENCODING=cp1251 LC_ALL=C PYTHONCOERCECLOCALE=0` the preferred encoding is US-ASCII; `t_title` exits 1 with `UnicodeDecodeError ... byte 0xe2` reading main.py, and the runner on `t_twins1` exits 1 with `UnicodeDecodeError ... byte 0xf4` decoding the suite's output.**

## 2. The reads and the decodes

- [x] 2.1 Add `encoding="utf-8"` to every text `open`, `read_text` and `write_text` in `tests/` (22 sites by the exploration's count: the 14 source reads, `run.py`'s `.env` read, `baseline.py`, `capture9.py`, `make_sample_mail.py`, `t_noleak`, and the empty-file opens in `t_workspace`, `t_window`, `t_version`). Verify with the guard part of 4.1 reporting zero, and with `t_title`, `t_work5`, `t_undo3`, `t_review`, `t_pane`, `t_busy`, `t_promote`, `t_workspace`, `t_window`, `t_mailflat` each passing with their baseline counts under the 1.2 simulation. **The scan found 33 sites in 20 files, not 22 -- it is the authority, not the hand count.**
- [x] 2.2 Add `encoding="utf-8"` to every `subprocess.run(..., text=True)` in `tests/` -- `run.py`, `t_noleak` (2), `t_title`, `t_gateway` (2), `t_busy` (2), `t_trace` (2). Verify: the guard part of 4.1 reports zero, and the runner started under the 1.2 simulation reads `t_twins1`'s output and prints its line rather than raising.

## 3. What is printed

- [x] 3.1 In `tests/testtoken.py`'s `child_env`, hand every child `PYTHONUTF8=1`, and say in its docstring why the runner cannot rely on the machine for this. Verify in a new part of `tests/stub/t_runner.py`: `child_env` of an environment without the variable carries it set to `1`, and one that already sets it is left as it was.
- [x] 3.2 In `tests/parts.py` -- which every suite imports first -- reconfigure `sys.stdout` and `sys.stderr` to UTF-8 at import where they are text streams that can be reconfigured, so that a suite run directly or under pytest prints its checks whatever the machine's locale. Verify: under the 1.2 simulation, `python tests/stub/t_twins1.py` prints its Cyrillic check names and exits 0, and `pytest tests/stub/t_twins1.py` does the same.

## 4. The guard

- [x] 4.1 Add a part to `tests/stub/t_runner.py` that scans every `.py` under `tests/` for a text `open(`, `read_text(`, `write_text(` or `text=True` with no `encoding=` in the same call, allowing binary modes, and fails naming each offender with its file and line. Verify: the part reports zero offenders after 2.1 and 2.2, and -- checked once by hand, then reverted -- reports exactly one when an `encoding=` is removed from one site. **Bitten: with the encoding removed from `t_work5.py:195` the part named that one site and nothing else; restored.**

## 5. Verification against the stub

- [x] 5.1 Run the whole self-contained tier normally and compare every suite's count with the 1.1 baseline; freeze `tests/` with `shasum` before and after. Passing: no count dropped, `t_runner` is the only suite whose count rose, no product `.py` changed.
- [x] 5.2 Run the whole self-contained tier under the 1.2 simulation, with no `PYTHONUTF8` set for the runner. Passing: it reports the same per-suite counts as 5.1 and exits 0. This is the check the change exists for; if it cannot be made to pass, the change is not done. **Passed: 56 suites, 2950 checks under `PYTHONUTF8=0 PYTHONIOENCODING=cp1251 LC_ALL=C PYTHONCOERCECLOCALE=0`, every per-suite count identical to the normal run.**

## 6. What is published

- [x] 6.1 In `README.md`, where the tests section says the tier passes on a fresh clone with nothing configured, add that it does so whatever the machine's default encoding. Passing: the sentence is there and says nothing about Windows support, which this change does not promise.
