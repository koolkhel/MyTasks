## 1. The instrument, before anything is edited

- [x] 1.1 Run `python tests/run.py` with nothing changed and save every suite's `N/M checks passed` line to the session scratchpad as the baseline, or adopt the last run if `tests/` and every product file are shasum-identical to it. Passing: the counts are on file and the tree they describe is this one. **Adopted the previous change's final run (56 suites, 2,950 checks): every file under tests/ and every product file shasum-identical, the untracked calendar_access.py the only difference and no suite reads it.**

## 2. One answer to who is asking

- [x] 2.1 Create `terminal.py` with `host_app(ppid=None, run=subprocess.run)`, `declares_calendar_reason(app)`, `usage_keys_missing(app)`, `signature(app, run=subprocess.run)` and the `USAGE_KEYS` table, moved out of `calendar_access.py`. Verify in the new stub suite `tests/stub/t_access.py` against a fake `.app` in a temp dir and a `run` stub: a plist with neither key declares no reason, one with either key does, `signature` answers `unsigned`/`adhoc`/the authority from the three `codesign` outputs, and the parent walk finds the app past a shell and a login process, skips a `Python.framework` bundle, and answers None when the chain reaches pid 1.
- [x] 2.2 Make `calendar_access.py` import from `terminal` and take `run`/`input` as parameters so its decisions can be driven. Verify in `t_access`: the diagnosis dict for the fake app, the "for X, not for Y" wording when the asked-about app is not the host, and that `--fix` against a fake unsigned app copies the plist, adds both keys, calls the re-sign and the reset through the stub and never touches anything real; against a fake developer-signed app it changes nothing and says why; declined at the prompt it changes nothing; against an app already granted it says so and changes nothing.

## 3. The board names the fourth case

- [x] 3.1 In `ical.py`, where the status is still "not determined" after the request, ask `terminal` whether the owning application declares a reason; where it does not, raise `CalendarUnreadable` naming the application and `calendar_access.py --fix`; otherwise the message as today. Verify in `tests/stub/t_cal.py`: with `terminal.host_app` and `declares_calendar_reason` replaced to answer a keyless fake app, the board shows the day's tasks and its message names the app and the helper; with a declaring app the message is unchanged; the existing refusal checks keep their counts.

## 4. The launcher

- [x] 4.1 Add the pre-flight to `run.sh`: when `CALENDAR_WORK` or `CALENDAR_PERSONAL` is set in `.env` or the environment, and not `--cli`, run `calendar_access.py --quiet` and ignore its exit code, then start the board as before. Add `--quiet` to the helper: print only when there is something to say. Verify: `t_access` checks `--quiet` prints nothing for a granted host and prints the diagnosis for a keyless one; a source check in `t_access` asserts `run.sh` runs the helper before `exec`, guarded by the calendar variables, with its exit ignored, and not on the `--cli` path.
- [x] 4.2 By hand, in kitty (already granted): `./run.sh` prints nothing about the calendar and starts. Passing: no calendar line before the board appears. Report only that; no event or account name. **Confirmed by hand by the user.**
- [x] 4.3 By hand, in cool-retro-term before the fix: `./run.sh` prints the diagnosis naming cool-retro-term and the fix command, then starts the board, which shows the day and names the app and the helper in its calendar message. Then `calendar_access.py --fix`, quit and restart cool-retro-term, `calendar_access.py` -- the prompt appears; Allow -- and `./run.sh` shows the events. Passing: the sequence above; report counts of events only, never a title. **Confirmed by hand by the user: after `--fix` and a restart of cool-retro-term the prompt appeared and the board shows the calendar.**

## 5. Verification against the stub

- [x] 5.1 Run `t_access` and `t_cal` alone under pytest and confirm every declared part is collected. Passing: the parts listed equal each suite's `PARTS`.
- [x] 5.2 Run the whole self-contained tier and compare every count with the 1.1 baseline, freezing the product files and `tests/` with `shasum` before and after. Passing: no suite's count dropped; `t_access` is new and `t_cal` may have risen; nothing else rose. **57 suites, 3014 checks; t_access new (56), t_cal 49 -> 57, nothing else moved; frozen across the run.**

## 6. What is published

- [x] 6.1 Add `calendar_access.py` and `terminal.py` to the README's file map and a sentence under configuration: the calendar needs the terminal, not the board, to be allowed, and `calendar_access.py` is how. Passing: both files named; the sentence says nothing about granting, which nothing here does.
