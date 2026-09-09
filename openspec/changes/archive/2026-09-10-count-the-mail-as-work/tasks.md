## 1. Let the board recognise mail as work

- [x] 1.1 Widen `is_work` to answer true for a mail row as well as for a task
      in the work project, with a comment saying why it is a rule here rather
      than a stamped project in `mail_rows` — the focus card reads
      `project_id` for any row, mail rows included, and a stamp would make it
      announce the work project. Verify in `tests/stub/t_mailview.py` (stub)
      on a board holding mail and a work project: passing means `is_work` is
      true of every mail row and unchanged for everything else, and that no
      mail row's `project_id` was set.
- [x] 1.2 Confirm the focus card is unaffected: opening it on a mail row still
      shows no project name. Verify in `tests/stub/t_mailview.py` (stub) by
      selecting a mail row and reading what the card is given; passing means
      the project it names is empty, as it is today.
- [x] 1.3 Confirm nothing else that reads `project_id` changed its mind about
      a mail row — in particular that `belongs()` still keeps mail rows in the
      inbox, since it excludes project-bearing tasks from it. Verify in
      `tests/stub/t_mailview.py` (stub) that the inbox's mail rows are all
      still present with the mode off; passing means the row count is what it
      was before this change.

## 2. Filter it where the other sources are filtered

- [x] 2.1 Move the mail rows inside the work-filter block in `repaint`:
      counted into `hidden_work` with the tasks, the issues and the events,
      and filtered before the concatenation that appends them. Verify in
      `tests/stub/t_mailview.py` (stub) that pressing the key with mail in the
      inbox leaves no mail row in the view, and pressing it again restores
      every one.
- [x] 2.2 Keep the ordering exactly as it is: mail filtered in place and still
      concatenated last, so the inbox's tasks hold the order they had alone.
      Verify by the existing ordering cases in `tests/stub/t_review.py` and
      `tests/stub/t_mailview.py` (stub, fixture copied per run as those suites
      already do) passing unchanged, plus one case that hides and shows the
      mail and compares the full row order to what it was.
- [x] 2.3 Assert the invariant rather than only the case: with the mode on,
      **no row on screen counts as work**. The sum first planned here — rows
      shown plus `hidden_work` equalling the rows the mode-off view shows —
      is vacuous for this bug and was checked to be: a source that escapes
      the filter adds to neither side, so the sum balances while the rows are
      still on screen. Verified by reverting the fix: the sum passed, the
      no-work-row check failed. Asserted for each source where that source's
      own board already exists rather than by duplicating source setup into
      one suite — `tests/stub/t_mailview.py` for mail, `tests/stub/t_block.py`
      for tracker issues, `tests/stub/t_cal.py` for work events and
      `tests/stub/t_work3.py` for plain tasks (all stub). Passing means every
      one reports no work row on screen with the mode on, and the sum beside
      it as a second, weaker check.

## 3. Report what is shown

- [x] 3.1 Take `shown_mail` and `shown_messages` from the filtered list, the
      way `shown_issues` already is. Verify in `tests/stub/t_mailview.py`
      (stub): passing means the status line reports the thread and message
      counts with the mode off, reports neither with it on, and reports them
      again when the key is pressed a second time.
- [x] 3.2 Confirm the inbox's daybar now says how much it hid instead of
      saying only that it is hiding. Verify in `tests/stub/t_mailview.py`
      (stub) that with the mode on the daybar carries a hidden count equal to
      the number of mail rows; passing means the count is present and correct,
      where today the inbox shows the bare phrase with no number.
- [x] 3.3 Check the two readings are legible together on one bar — the task
      count and the hidden count in the same line, with the mailbox mark still
      pushed to the right edge. Verify in `tests/stub/t_mailview.py` (stub) at
      a narrow width as well as a wide one: passing means neither number is
      truncated at 120 columns and the bar does not lose the mark at 80.

## 4. Verification against a stub

- [x] 4.1 Run the mail and work-filter suites together:
      `.venv/bin/python tests/run.py t_mailview t_work3 t_review t_track2
      t_cal t_top t_block`. Passing means each reports all of its checks
      passed at its new count, and in particular that the tracker's and the
      calendar's own hiding cases are untouched by the widened rule.
- [x] 4.2 Run the full stub tier with `.venv/bin/python tests/run.py`. Passing
      means the only failures are ones shown pre-existing by running that
      suite against a git worktree at HEAD. Result: 40 passed, 1 failed —
      `t_busy`'s narrow-terminal case, identical at HEAD, and calendar-
      dependent rather than related to this change: the daybar it measures is
      a date, the check needs that line to reach 37 characters, and in
      September only a Wednesday's day name is long enough. `t_elapsed`, the
      other calendar-dependent one, passed this run because the hour moved.
      Neither is recorded in `tests/known_failures.py`; both are surfaced to
      the user rather than fixed here.
- [x] 4.3 No live tier is needed and none is run. This change writes nothing,
      touches no account, and asks the mailbox for nothing it was not already
      asked; the filter only decides which of the rows a view already chose
      are painted. Verify by confirming the diff touches neither `gateway.py`
      nor `mail.py`, and that `tests/stub/t_mailview.py` shows no request was
      made to any server when the key is pressed.
