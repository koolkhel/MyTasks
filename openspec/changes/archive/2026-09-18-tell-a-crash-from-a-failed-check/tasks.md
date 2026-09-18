## 1. The instrument, before anything is edited

- [x] 1.1 Run `python tests/run.py` with nothing changed and save every suite's `N/M checks passed` line to the session scratchpad as the baseline. Passing: the run is green and the file exists. Note beside it that `t_elapsed` moves with the clock (36 by day, 31 in the last hour).

## 2. What the runner says

- [x] 2.1 In `tests/run.py`, tell the two failures apart: a non-zero exit with a summary printed and no `FAIL` check-line is a crash. Mark it `CRASH`; keep `FAIL` for a run with failing checks and for a run that printed no summary at all. Verify in the new stub suite `tests/stub/t_runner.py`, which feeds `report()` synthetic outputs of three shapes -- checks failed, crashed after every check passed, crashed before a summary -- and reads the printed line: `FAIL`, `CRASH`, `FAIL` respectively.
- [x] 2.2 Read the cause out of what pytest printed: the `FAILED <path>::<part> - <Exception>: <message>` lines of its short summary. Put `<part> raised <Exception>: <message>` after the count on a `CRASH` line, and echo those lines in the "failed; run it alone" block, where today only `FAIL` check-lines are echoed. Verify in `t_runner`: the crashed shape's line names the part and the exception, and the block for it is not empty; the failed-checks shape's block still shows its `FAIL` lines and nothing else.
- [x] 2.3 Keep a known-failure's `known` and `FIXED` marks working for a crash: a suite listed with a crash signature that crashes the same way reads `known`, one that passes reads `FIXED`. Verify in `t_runner` with a synthetic `KNOWN` entry.

## 3. What the list records

- [x] 3.1 In `tests/known_failures.py`, make `signature()` answer `crash:<Exception>` for a run that exited non-zero with every check passed, taking the exception name from pytest's `FAILED ... - <Exception>:` line first and from the last traceback line otherwise; keep the integer for runs with failing checks and `crash:<Exception>` for runs with no summary. Verify in `t_runner`: the three shapes sign as `2`, `crash:RuntimeError`, `crash:ImportError`, and a crash-after-checks run against an entry recording `0` is reported as failing differently.

## 4. Verification against the stub

- [x] 4.1 Run `tests/stub/t_runner.py` under pytest on its own and confirm every part it declares is collected. Passing: the parts listed equal its `PARTS` and its `N/M checks passed` accounts for every check.
- [x] 4.2 Run the whole self-contained tier and compare every suite's count with the 1.1 baseline; freeze `tests/run.py` and `tests/known_failures.py` with `shasum` before and after. Passing: no suite's count dropped, `t_runner` is the only addition, the product files are untouched (`git status` shows no `*.py` outside `tests/` changed).
- [x] 4.3 Run `python tests/run.py t_bands` ten times in a row and keep every non-zero run's full output in the scratchpad. Passing: each run reads `ok` -- or, if one crashes, its line now names the part and the exception, and that output is kept for a follow-up change. This is verification of the reporting, not a diagnosis of the crash: the report that prompted this change was not reproducible in six runs. **Ten of ten read `ok`, 23/23; the crash did not recur and remains undiagnosed. Outputs kept in the session scratchpad.**

## 5. What is published

- [x] 5.1 Update the module docstring of `tests/known_failures.py` where it explains signatures, so that `crash:Name` is documented as covering a crash after the checks as well as one before any summary. Passing: the comment above `KNOWN` describes all three shapes.
