## 1. The instrument, before anything is edited

- [x] 1.1 Take the stub tier's baseline -- every suite's `N/M checks passed` line -- or adopt the last run if `tests/` and every product file are shasum-identical to it. Passing: the counts are on file and describe this tree. **Adopted the previous change's run (57 suites, 3,014 checks): every file under tests/, every product file and run.sh shasum-identical to this tree.**

## 2. The tracker says more

- [x] 2.1 In `tracker.py`, add `description` to `ISSUE_FIELDS` and a `description: str = ""` to `Issue`, read from the raw issue with an absent or null value becoming the empty string. Verify in `tests/stub/t_version.py` (which already builds raw issues by hand): an issue with a description carries it, one without carries `""`, one with `null` carries `""`; and a source check that `ISSUE_FIELDS` names `description` and the fetch function's request count is unchanged (the existing `t_costs_nothing` part).

## 3. The row carries it, the area shows it

- [x] 3.1 In `board.py`, give the tracker row `"note": issue.description`, and add a function beside the other row vocabulary that answers a tracker row's facts line -- state, project, and `fix: <versions joined>` where any -- as text, from the row alone. Verify in `tests/stub/t_paint.py` style (no terminal) in a new part of `t_track2`: the facts for a row with one version, with two in the tracker's order, with none; a row with no description has an empty note; the drawn cells are unchanged against the existing `t_block` checks.
- [x] 3.2 In `main.py`, make the detail area and the focus card use that facts line for a tracker row where they use a task's flags, with the description escaped as a note is. Verify in `tests/stub/t_pane.py`, part `rows_from_elsewhere`, extended: selecting a tracker row shows its facts on the first line and its description beneath; a description holding `[brackets]` is shown as those characters; moving to a task shows that task's own note and none of the issue's text; the focus card shows the same facts and description. Passing: the part's new checks pass and its old ones keep their count.

## 4. Verification against the stub

- [x] 4.1 Run `t_track2`, `t_pane`, `t_version` alone under pytest and confirm every declared part is collected. Passing: the parts listed equal each suite's `PARTS`.
- [x] 4.2 Run the whole self-contained tier, frozen (`shasum` of `tests/` and every product file before and after), and compare every count with the 1.1 baseline. Passing: no count dropped; only `t_track2`, `t_pane` and `t_version` rose. **57 suites, 3,036 checks; only t_track2, t_pane and t_version rose; frozen across the run.**

## 5. Verification against the live tracker

- [x] 5.1 Run the tracker tier once, `python tests/run.py --tracker`. Passing: its per-suite results match a run of the same tier against a git worktree at HEAD taken the same session, suite for suite -- the known live flakiness (`t_label6`, `t_top6`) counted by that comparison, not by the eye. Report counts only; no issue key, summary, description or version is printed or recorded. **Both runs, minutes apart: 1 passed, 3 failed, suite for suite -- t_version6 9/9 in both; t_label6, t_top6 and t_track6 fail identically at HEAD, so they predate this change. Noted for a follow-up: t_top6's known-failure entry records `1` and it now crashes with IndexError at HEAD too, so the runner reports it as a new failure rather than a known one.**
- [x] 5.2 By hand: open the board in a terminal with the tracker configured, select an issue, confirm the first line of the area reads state, project and `fix: …`, and the description beneath; press `enter` and confirm the card agrees. Report only that it does; nothing about any issue. **Confirmed by hand by the user against the real tracker.**

## 6. What is published

- [x] 6.1 In `docs/screenshots.py`, give the two invented issues a description and a version, and move the today picture's cursor onto one of them so the area shows what this adds; regenerate. Passing: `docs/today.png` shows an issue's facts line and description, on invented data only. **docs/today.png shows the selected issue's line `In progress · DM · fix: 3.2, 3.3` and its description, all invented.**
- [x] 6.2 In `README.md`, the "Notes" paragraph says an issue's description and its fix version arrive in the same place as a task's note. Passing: the sentence is there and names no real issue.
