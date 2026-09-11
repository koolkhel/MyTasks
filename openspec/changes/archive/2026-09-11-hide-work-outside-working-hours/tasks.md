## 1. The window rule and its configuration

- [x] 1.1 Add `parse_working_window(hours, days)` to `singularity.py`: a pure
      function of two strings returning a window, or saying why it cannot be
      read. Verify with a new self-contained suite `tests/stub/t_window.py`
      run as `python tests/stub/t_window.py`: an hour inside the range is
      inside; an hour after the end is outside; a day not in the configured
      days is outside for its whole length; absent days means Monday to
      Friday; an end no later than the start is unreadable; an unparseable
      range or day name is unreadable. Passing is every check `ok` and exit 0.
- [x] 1.2 Add `load_working_window(env_path=None)` beside `load_work_project`,
      a thin wrapper over 1.1 returning `None` when `WORK_HOURS` is absent or
      blank. Verify in `tests/stub/t_window.py` that the parser is what the
      suite exercises and the reader is only checked for the absent case --
      python-dotenv finds the real `.env` by walking up from `singularity.py`,
      so a suite that empties the environment does not hide it, and a suite
      asserting on a configured window would pass or fail by whose machine it
      ran on.

## 2. The board's state

- [x] 2.1 Before naming anything, check each new name against the classes it
      would live on: `hasattr(main.TaskApp, n)` and `hasattr(textual.app.App,
      n)` for `working_window`, `apply_window`, `_work_override` and
      `_window_hides`, plus `grep -n "def <n>(" main.py`. Passing is every
      name unused. Two collisions have landed here before, one of which
      stopped a running app accepting messages.
- [x] 2.2 Add `_work_override` and `_window_hides` to `TaskApp.__init__` and
      load the window beside `work_project`. `hiding_work` keeps its type, so
      nothing that reads it changes. Verify by running the existing
      `tests/stub/t_work3.py` and `tests/stub/t_work5.py` unchanged: with no
      window configured they must pass exactly as they do now.
- [x] 2.3 Add `apply_window(moment=None)`: take the window's answer for that
      moment, compare with `_window_hides`, and on a change record it, clear
      `_work_override`, set `hiding_work` and repaint. On no change, return
      having touched nothing. The moment is an argument so a suite can hand it
      any hour of any day. Verify in `tests/stub/t_window.py` by calling it
      directly with a Friday 17:59, a Friday 18:01 and a Saturday noon, and
      asserting `hiding_work` and that the no-change call repaints nothing.
- [x] 2.4 Call `apply_window()` once at startup so the board opens in the
      state the clock says. Verify in `tests/stub/t_window.py` that an app
      built with a window and a moment outside it has `hiding_work` true with
      no key pressed, and an app built with no window has it false.
- [x] 2.5 Make `action_toggle_work` set `_work_override` to the flipped value
      as well as `hiding_work`, leaving its two existing refusals (no work
      project configured, work project not found) untouched. Verify in
      `tests/stub/t_window.py` that the key flips what the clock set, and in
      `tests/stub/t_work3.py`/`t_work5.py` that the unconfigured board's key
      behaves exactly as before.

## 3. The crossing

- [x] 3.1 Call `apply_window()` from the existing sixty-second tick beside
      `recheck_elapsed`, one timer rather than two. Verify in
      `tests/stub/t_window.py` by driving the tick's two calls with a moment
      either side of the boundary: crossing repaints, not crossing repaints
      nothing.
- [x] 3.2 Verify the lapse rule in `tests/stub/t_window.py`: a press outside
      the window followed by the window opening leaves the screen unchanged;
      a press inside the window followed by it closing leaves the screen
      unchanged; two presses leaving the mode where the clock had it make the
      next crossing act as though no key had been pressed; and a press with
      no crossing lasts however long it is left.
- [x] 3.3 Verify in `tests/stub/t_window.py` that a crossing with a work row
      selected keeps the scroll position and puts the selection on the
      nearest surviving row, and that a crossing sends no write -- the stub
      client records the requests made, so passing is zero of them.

## 4. What the board says

- [x] 4.1 Add the reason to the status line: where `_work_override is None`
      and the window is hiding the rows, name whether the hour or the day put
      it outside, alongside the count already reported. Where a press hid
      them, report exactly what is reported today. Verify in
      `tests/stub/t_window.py` by reading the status widget's drawn text --
      `widget.visual.plain`, as `tests/stub/t_markup.py` does -- for four
      cases: hidden by the hour, hidden by the day, hidden by a press, and
      not hidden at all.
- [x] 4.2 Report an unreadable window once at startup through the existing
      status-notice path, and never from the tick. Verify in
      `tests/stub/t_window.py` that an app built with an unreadable window
      opens, says so once, hides nothing, and says nothing further after two
      ticks.
- [x] 4.3 Verify in `tests/stub/t_window.py` that a window configured with no
      work project hides nothing and says nothing of its own accord, the
      key's existing refusal being the only thing that mentions it.

## 5. Verification against a stub

- [x] 5.1 Run the whole self-contained tier with `python tests/run.py` and
      compare against `tests/known_failures.py`. Passing is no suite worse
      than its known result and `t_window.py` at full marks. Freeze the
      product code for the run and confirm with `shasum main.py
      singularity.py` afterwards, so the run is known to be about one
      version.
- [x] 5.2 Add `t_window.py`'s expected result to the runner's inventory if
      the runner needs it named, and verify `python tests/run.py --list`
      shows it in the `stub` tier.

## 6. Verification against the live board

- [x] 6.1 Separate from the stub runs above: put a window whose edge is
      seconds away into the environment the way `.env` spells it, run the
      real board with the real reader restored, and let its own timer carry
      it over. Passing is the work rows leaving on the timer, the status line
      naming the hour, the view landing where the key would leave it, and the
      key bringing the rows back. This touches no account and spends no
      quota; it is here because no stub can show a timer firing on a real
      clock.
      The original wording asked for the scroll offset to be unchanged, which
      was wrong: halving a list moves the view up to the end of the shorter
      one, as `The list stays where it is when it is redrawn` requires. What a
      crossing must match is what the key does, which 3.3 compares directly.
- [x] 6.2 Confirm the unconfigured board is unchanged: with no `WORK_HOURS`
      in the environment or in the board's own `.env`, run the real board and
      check that nothing is hidden, the status line and daybar say nothing
      about a window, two ticks change nothing, and the key still works.
