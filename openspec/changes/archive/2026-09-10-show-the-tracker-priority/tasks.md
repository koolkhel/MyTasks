## 1. Read the priority the tracker already sends

- [x] 1.1 Add `localizedName` to the value asked for in `ISSUE_FIELDS`, so the
      request becomes `customFields(name,value(name,localizedName,login))` —
      one token, the same call, the same page size. Verified in
      `tests/config/t_states.py` rather than `t_tracker1.py` (both config
      tier): `t_states` is a pure-parse suite that reaches no network, which is
      what a string assertion wants, and it keeps every priority check
      together. `t_tracker1` has a section that does reach the live tracker.
      Passing means the fields string asks for it and, with that one token
      removed, is character-for-character what it was.
- [x] 1.2 Give `Issue` the priority it arrives with: the tracker's own name for
      it, and the API's stable English value name beside it. Default both to
      empty so every suite that builds an `Issue` positionally or by keyword
      keeps working. Verify in `tests/config/t_states.py` (config tier,
      synthetic payload) that a payload carrying a priority parses into those
      two, and one carrying none parses into empties.
- [x] 1.3 Read them in `parse` out of the custom fields it already collects —
      the localised name where the tracker gives one, the English value name
      otherwise, since a tracker with no localisation still names its own
      priorities. Verify in `tests/config/t_states.py` (config tier) with three
      payloads: one with both names, one with the English name only, one with
      no priority field at all; passing means each yields the right pair and
      none raises.

## 2. Put the letter on the row

- [x] 2.1 Carry the priority on the row `tracker_rows` builds, under its own
      key beside the state and the project. Verify in `tests/stub/t_track2.py`
      (stub) that a row built from an issue with a priority carries it and one
      built from an issue without carries nothing.
- [x] 2.2 Draw the letter in the leftmost cell of a tracker row in `row_for`,
      where that row currently puts the empty string. Verify in
      `tests/stub/t_track2.py` (stub) that the cell holds the expected letter
      for each of the tracker's five priorities, and that the row's other four
      cells are character-for-character what they were.
- [x] 2.3 Apply the case rule: the first letter of the tracker's name, upper
      case, except where the API's value name is the least urgent, which reads
      lower case. Verify in `tests/stub/t_track2.py` (stub) with rows for the
      most urgent and the least, whose names begin with the same letter;
      passing means the two cells differ, and differ only in case.
- [x] 2.4 Confirm a task's leftmost cell is untouched — it still shows the
      configured tag's mark, and a tracker row still shows no tag mark. Verify
      by the existing green-tag cases in `tests/stub/t_green2.py` and
      `tests/stub/t_green3.py` (stub) passing unchanged, plus one case on a day
      holding both a tagged task and a tracker issue.
- [x] 2.5 Confirm nothing became writable: the row refuses what it refused, and
      no key touches a priority. Verify by the existing refusal cases in
      `tests/stub/t_track3.py` (stub) passing unchanged, and by grep that no
      binding or write path names the priority.

## 3. Hold the line on colour and on order

- [x] 3.1 Assert the letter is legible without colour: the cell's text carries
      the letter itself rather than only a style. Verify in
      `tests/stub/t_track2.py` (stub) by reading the cell's plain text with
      markup stripped; passing means every priority is distinguishable from the
      text alone.
- [x] 3.2 Assert the block's order is unchanged by priorities. Verify in
      `tests/stub/t_track2.py` (stub) by comparing the row order for issues of
      several priorities against the order the same issues take with no
      priority set; passing means the two are identical.
- [x] 3.3 Assert each letter is a single character, since the column is one
      cell wide and a Cyrillic capital is East Asian Width Ambiguous — the
      departure design.md records. Verify in `tests/stub/t_track2.py` (stub)
      that every letter the board can draw is one character, and that a
      tracker row draws with the same number of cells at 120 and at 80 columns.

## 4. Verification against a stub

- [x] 4.1 Run the tracker and green suites together: `.venv/bin/python
      tests/run.py t_track2 t_track3 t_green2 t_green3 t_block t_top t_label2`.
      Passing means each reports all of its checks passed at its new count, and
      the green-tag and refusal cases are unchanged.
- [x] 4.2 Run the full stub tier with `.venv/bin/python tests/run.py`. Result:
      40 passed, 1 failed — `t_elapsed`'s "it keeps its start time", shown
      pre-existing by running that suite against a git worktree at HEAD, where
      it fails identically. Not from this change: it is a regression from the
      change that took the suites off the clock, whose widened *over* fixture
      now starts at midnight while that one check still expects the old
      arithmetic. Left for its own change rather than absorbed here, on the
      user's decision. Passing means every other suite passes and the one
      failure is accounted for.
- [x] 4.3 Run the config tier for the parse changes with the tier's own
      invocation. These read the board's `.env`; `t_states` builds synthetic
      payloads against invented hosts and reaches no network, while
      `t_tracker1` has a section that does reach the live tracker — so its
      result is judged like a live one and re-run once before being believed.
      Passing means both report all checks passed.

## 5. Verification against the live tracker

- [x] 5.1 Run `tests/tracker/` against the real tracker. Result: `t_label6`
      13/13 (8/8 before the cases added in 5.2), `t_top6` reported as its
      recorded known failure at 10/11, `t_track6` 14/14. `t_track6` first
      refused to run at all: it is the day-guarded regression instrument and
      its baseline was yesterday's. A fresh baseline taken now would agree
      with the change, so the baseline was captured from a git worktree at
      HEAD instead — the same day, minutes apart, which is the instrument as
      the project describes it. The tier reads `tracker.load_config()`; the
      capture helper adopts the suites' token before building any client, so
      the board's own token stayed free.
- [x] 5.2 Confirm on the real account that the letters come out as expected,
      reporting counts and letters only — never an issue key, a summary, a
      project name or a person's name. Done as cases in
      `tests/tracker/t_label6.py` (live tracker) rather than a one-off run, so
      it stays checked; that suite already covers a label derived from the
      tracker's own words. Result: six tracker rows, six letters, the set
      `['О', 'С']`, each one character, each the first character of the
      tracker's own word, and nothing lower-cased that is not the least
      urgent. Passing means every issue the board
      would show reports a letter that is the first character of the tracker's
      own name for its priority, the least urgent reads lower case, and an
      issue with no priority reports nothing.
- [x] 5.3 Confirm the one extra token cost nothing: one request for the six
      issues the tracker reports, the same as before, and the diff touches no
      paging — pages are driven by `$top` and `$skip`, which a field list
      cannot reach. Measured by counting `requests.get` calls through a real
      fetch.
