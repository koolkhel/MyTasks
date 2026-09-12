## 1. Make the card count its own sitting

- [x] 1.1 In `TaskFocus.__init__`, drop the `since` parameter and record the
      card's own start instead: `self.shown_since = datetime.now(tz)`, set
      before anything can read it. Verify by constructing a card in a Python
      session and reading `shown_since` -- it is a `datetime` in the given
      zone, with no argument passed.
- [x] 1.2 Make `compose` yield the count line unconditionally, and `on_mount`
      start the tick unconditionally -- both lose the `is not None` guard the
      optional parameter needed. Verify with `python tests/run.py t_workspace`
      once 2.x lands; until then, that the guards are gone is checked by
      reading the diff.
- [x] 1.3 Leave `worked_for`, `keep_up`, `on_unmount` and
      `WORKED_TICK_SECONDS` untouched, and change nothing in `worked_line`
      but the two docstring lines this change makes wrong -- it said "when
      work began", and what it reports is now when the card opened. Verify by
      extracting each definition from a copy of the file taken before the
      change and comparing bytes, with the extractor first shown able to tell
      two definitions apart. Passing means four identical and `worked_line`
      differing in those two lines alone.

## 2. Drop the board's memory of what is being worked on

- [x] 2.1 Delete the `working` field from the app's `__init__` and the
      `working_since` method. Verify with `grep -n 'working_since\|self\.working\b' main.py`
      -- no hits, and `self.working_window` (a different thing, the working
      hours) still there.
- [x] 2.2 Reduce `show_focus` to building the card with four arguments, and
      have `action_start_workspace` call it without first recording anything.
      Verify with `grep -n 'show_focus' main.py` -- two callers, both passing
      only the task, and `python -c "import main"` imports clean.
- [x] 2.3 Confirm nothing else read the removed field:
      `grep -rn 'working_since\|\.working\b' main.py tests/` returns only
      `working_window` hits.

## 3. Replace the checks that asserted the old behaviour

- [x] 3.1 In `tests/stub/t_workspace.py`, delete `t_working_remembered`,
      `t_working_one_at_a_time` and `t_working_shown`, and remove the three
      names from the runner tuple at the end of the file. Verify with
      `python tests/run.py t_workspace` -- it runs and passes at the reduced
      count, which is the before-count minus the 27 checks those three held.
- [x] 3.2 Keep the helpers `clock`, `card`, `since_line` and `close_card`;
      the new parts use all four. Verify they are still defined and that
      `since_line` reads `#focus-since` through `visual.plain`.
- [x] 3.3 Add `t_counts_on_any_row`: with the clock frozen, open the card with
      the key that opens a card on a board task, on a tracker row, on a mail
      row and on a calendar row, and check each shows `since HH:MM` for the
      frozen hour and `0m`. Passing means four rows, four counts, no row
      exempt.
- [x] 3.4 Add `t_coming_back_starts_again`: open a card at a frozen 14:00,
      move the clock to 14:20, check the open card shows `20m`, dismiss it,
      move the clock to 14:25, open the same row again and check it shows
      `since 14:25` and `0m`. Passing means the second opening reports the
      later hour, not the first.
- [x] 3.5 Add `t_workspace_counts_like_the_rest`: start a workspace with the
      recording launcher the suite already installs, and check the card it
      opens shows the frozen hour and `0m` -- the same line `t_counts_on_any_row`
      saw, reached by the other key. Passing means the two keys produce the
      same line.
- [x] 3.6 Add `t_nothing_is_added_up`: open and dismiss cards on the same row
      three times across a moving frozen clock, then check the app holds no
      attribute naming a total or a start (`working`, `worked`, `since` and
      `total` absent from `vars(app)`), and that the third card counts from the
      third opening alone. Passing means the board carries nothing between
      cards.
- [x] 3.7 Register the four new parts in the runner tuple and run
      `python tests/run.py t_workspace`. Passing means every part reports and
      the suite ends `0 failed`.

## 4. Prove the new checks are not vacuous

- [x] 4.1 With `main.py` copied aside first, make `compose` draw the count
      line only for tracker rows, run `python tests/run.py t_workspace`, and
      record which checks fail -- `t_counts_on_any_row` must fail on at least
      the task, mail and calendar rows. Restore from the copy and confirm with
      `shasum -c`.
- [x] 4.2 With `main.py` copied aside first, make `__init__` record the start
      once and keep it across openings (a module-level cache keyed by row), run
      the suite, and record which checks fail -- `t_coming_back_starts_again`
      and `t_nothing_is_added_up` must. Read the run's exit status, not only a
      grep for failures: the first attempt at this break raised at card
      construction, so the suite crashed having printed no failure at all, and
      a grep alone reported that as nothing wrong. Restore from the copy and
      confirm with `shasum -c`.
- [x] 4.3 Compute the text of each edited file before opening it for writing.
      The one-line form truncates the file when the argument raises, which has
      cost this repository `main.py` twice.

## 5. Verify nothing else moved

- [x] 5.1 Run the six stub suites that build a card directly, unedited:
      `python tests/run.py t_star2 t_fit2 t_pane t_star t_twins2 t_mailview`.
      Passing means all six at their current counts, with no edit to any of
      them -- which is the claim that dropping the fifth argument and drawing
      one line more disturbs nobody. If one fails on the card's new height,
      fix the card, not the suite.
- [x] 5.2 Run the whole stub tier, `python tests/run.py`. Passing means the
      tier's current pass count with `0 failed`, and the same set of
      known-to-fail suites as before this change. Stub only: no credentials,
      no store, no tracker, no mail account.
- [x] 5.3 Take `shasum` of `main.py` and `tests/stub/t_workspace.py` before
      the tier run and check them after, so that "the tier passed" refers to
      the bytes that ship.
- [x] 5.4 No live-account verification is part of this change. Nothing here
      sends a request, so no `store`, `tracker` or `gateway` tier run applies
      and none is claimed.
