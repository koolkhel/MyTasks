## 1. The instrument, before anything is edited

- [x] 1.1 Take the stub tier's baseline -- every suite's `N/M checks passed` line -- or adopt the last run if `tests/`, `run.sh` and every product file are shasum-identical to it. Passing: the counts are on file and describe this tree. **Adopted the previous change's run (57 suites, 3,036 checks): every file under tests/, run.sh and every product file shasum-identical to this tree.**

## 2. The tracker's own order

- [x] 2.1 In `tracker.py`, ask for `ordinal` beside `name,localizedName,login` in `ISSUE_FIELDS`, and give `Issue` a `priority_rank: int | None = None` read from the Priority value's ordinal (None where there is no priority or no ordinal). Verify in `tests/stub/t_version.py`: a raw issue whose Priority carries `ordinal: 2` has rank 2, one with ordinal -1 has rank -1, one with no Priority field has None, one whose value has no ordinal has None; and `t_costs_nothing` still pins the request to one string, updated for the new token.
- [x] 2.2 In `parse()`, sort by `(rank is None, rank, config.rank(state), key)`. Verify in `tests/stub/t_version.py` with raw issues built by hand: three issues at ordinals 4, 0, 2 in one state come back 0, 2, 4; two at the same ordinal in two states come back in the configured state order; two at the same ordinal and state come back by key; an issue with no priority comes after one at ordinal 4; two at ordinal 0 in two different states come back in state order (the case B chose: priority before state).

## 3. Nothing else moves

- [x] 3.1 Verify in `tests/stub/t_track2.py` that the block's *placement* -- after the unfinished tasks, before the finished -- and every row's cells are as they were, with issues of differing priority handed in: the `t_block`, `t_readonly` and `t_priority` parts keep their counts, and a new check in `t_priority` asserts that a Minor issue with a smaller key is drawn below a Major one with a larger key. Passing: the suite's count rises by exactly the new checks and no existing check changes.

## 4. Verification against the stub

- [x] 4.1 Run `t_version` and `t_track2` alone under pytest and confirm every declared part is collected. Passing: the parts listed equal each suite's `PARTS`.
- [x] 4.2 Run the whole self-contained tier, frozen (`shasum` of `tests/`, `run.sh` and every product file before and after), and compare every count with the 1.1 baseline. Passing: no count dropped; only `t_version` and `t_track2` rose. **57 suites, 3,049 checks; only t_version and t_track2 rose; frozen across the run.**

## 5. Verification against the live tracker

- [x] 5.1 Run the tracker tier once, `python tests/run.py --tracker`, and compare it suite for suite with a run against a git worktree at HEAD taken the same session. Passing: identical results; `t_top6` is expected to report as a stale known failure in both. Counts only -- no key, summary, priority word or version of any real issue is printed or recorded. **Identical, suite for suite: t_version6 9/9 in both; t_label6, t_top6 (stale known entry, crash:IndexError) and t_track6 fail the same way at HEAD. Counts only.**
- [x] 5.2 By hand: open the board with the tracker configured and confirm the block lists the most urgent issue first, by the letters in the leftmost column. Report only that it does. **Confirmed by hand by the user: the real block is ordered most urgent first.**

## 6. What is published

- [x] 6.1 In `docs/screenshots.py`, give the two invented issues different priorities with ordinals that put the more urgent one first even though its key is larger, and regenerate. Passing: `docs/today.png` shows the block most urgent first, on invented data. **docs/today.png: the Critical DM-214 (`C`) leads the Minor DM-198 (`m`) despite the larger key; invented data.**
- [x] 6.2 In `README.md`, where the tracker is described, say the block is ordered most urgent first in the tracker's own order. Passing: the sentence is there and names no priority by name.
