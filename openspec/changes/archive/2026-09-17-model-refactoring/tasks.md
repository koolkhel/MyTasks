## 1. Baseline and ground rules

- [x] 1.1 Before any edit, run `python tests/run.py` (the self-contained tier,
      52 suites, stubs only, no credentials) and save every suite's reported
      `N/M checks passed` line plus the tier summary. Passing is 52 saved lines
      and `52 passed, 0 failed`. Every step below is checked against this list;
      it is captured once and never re-taken. **Result: captured. 52 suites, `52 passed, 0 failed`, every line saved.**
- [x] 1.2 Record `shasum main.py` and keep a run frozen: a verification run that
      spans an edit proves nothing about either version, so confirm the checksum
      after each tier run and un-check any step whose run predates a later edit
      to the code it verified. **Result: `main.py` read `2d9bb5112404e801b404bca02442f0a552a5525c` before the baseline run and after it, so the baseline is of one version.**

## 2. The module, and the cells (step 1)
- [x] 2.1 Create `board.py` with `Board`, built from the values it reads, and
      `Painting`. Move `row_for` and the formatting it uses — `_markup_title`,
      `_mail_when`, `shortened`, `marked_cell`, `late_colour`, `is_green`,
      `is_tracker`, `is_mail`, `is_event`, `has_ended` — and take the title
      width as a value rather than measuring it. Leave one-line delegates on
      `TaskApp` for every one of those names. Verify with the stub tier: all 52
      `N/M checks passed` lines identical to 1.1. **Result: done and verified —
      52 passed, 0 failed, every one of the 52 check counts identical to the
      1.1 baseline. `board.py` is 460 lines: the row vocabulary (37 names) and
      ten methods; `main.py` went 5,951 → 5,672 with delegates for all ten.
      Two corrections to this task, both recorded in design.md: `late_colour`
      stayed on `TaskApp` because it reads the theme the application is
      running, so the resolved colour is handed over as a value like the
      width; and `Board` had to take the present as a value too — six places
      in the suites steer the board's clock by patching `main.datetime`, which
      a clock read from `board.py` would have escaped. `t_elapsed` caught that
      at 34/36 before the fix.**
- [x] 2.2 Verify the cells specifically against the suites that judge them:
      `t_fit` (37 checks) and `t_fit2` (17) for column width and shortening,
      `t_markup` (25) for title markup, `t_mailview` (107) for mail rows,
      `t_still` (40) for the rest of the row. Passing is each of the five
      reporting exactly the count it reported in 1.1, against stubs.
      **Result: all five identical — t_fit 37/37, t_fit2 17/17, t_markup 27/27
      (the task said 25; 27 is what it reports and what the baseline holds),
      t_mailview 107/107, t_still 40/40.**

## 3. What is drawn, and in what order (step 2)

- [x] 3.1 Move `patched`, `belongs`, `matches`, `search_text`, `is_work`,
      `tracker_rows`, `event_rows`, `mail_rows`, `mail_fold`, `place_events`,
      `place_issues`, `event_key`, `ordering_key`, `orders_manually`,
      `ended_count`, `window_reason`, `shows_mail` and `shows_tracker` into
      `Board`, and have `paint()` answer the rows in order together with the
      counts the status line reports. `repaint` consumes that answer instead of
      composing. Leave delegates for every name the suites or the rest of the
      application use — the suites call `is_work` 10 times, `search_text` 5,
      `patched` 4, `belongs` 2 and `place_events` once. `apply_window` does
      **not** move: it sets the mode and calls `repaint`, which is a state
      transition rather than a question about what is drawn (see design.md).
      Verify with the stub tier: all 52 counts identical to 1.1. **Result: done and verified — 52 passed, 0 failed, all 52 counts identical to the 1.1 baseline. Eighteen methods moved; `board.py` is now 1,091 lines and `main.py` 5,224. `event_key` became a question about the event alone rather than one the board answers: `t_bands` calls it on an application built with `__new__` and no state at all, which a delegate that built a whole board broke (`AttributeError: no attribute '_base'`). `apply_window` stayed, as this task now says.**
- [x] 3.2 Keep the counting points exactly where they are: `hidden_work` and
      `hidden_by_search` counted across all four sources before any is dropped,
      `shown_issues` recomputed after each filter, `shown_mail` and
      `shown_messages` after the filters, `past_due` over the placed rows
      excluding events. Verify against the suites that assert those numbers —
      `t_window` (103) and `t_work3` (36) for the work filter, `t_search` (107)
      for the search, `t_mailview` (107) for the mail counts — each reporting
      its 1.1 count, against stubs. **Result: identical — t_window 103/103, t_work3 36/36, t_search 107/107, t_mailview 107/107. Every count is taken where it was taken.**
- [x] 3.3 Turn `forget_gone_marks` into an answer: `Board` says which marks the
      shown view can see are gone, `TaskApp` performs the assignment, and it
      still happens before anything is counted. Verify with `t_mark` (103) and
      `t_bulk` (102) reporting their 1.1 counts, against stubs — those two are
      what caught marks being cleared on every view change before. **Result: done — `Board.surviving_marks()` answers which marks the shown view cannot say have gone, and `TaskApp.forget_gone_marks` performs the assignment, still before anything is counted. This had to be done here rather than left for later: a board is thrown away after its paint, so an assignment made inside one would have been lost. t_mark 103/103, t_bulk 102/102.**
- [x] 3.4 Verify the order the sources join in is unchanged: events placed among
      the day's tasks by when they happen, the tracker's block where the
      unfinished work ends, mail appended last and never sorted in. Instrument:
      `t_bands` (24), `t_cal` (50), `t_promote` (79), `t_track2` and `t_track3`,
      each reporting its 1.1 count, against stubs.
 **Result: identical — t_bands 23/23, t_cal 49/49, t_promote 78/78, t_track2 69/69, t_track3 16/16. (The task guessed 24, 50 and 79 for the first three; the baseline's numbers are the ones above.)**
## 4. The status line (step 3)

- [x] 4.1 Move the eleven conditional fragments into `Board`, which answers the
      joined string; `TaskApp` only calls `set_status` with it. Verify with the
      stub tier: all 52 counts identical to 1.1. **Result: done and verified — 52 passed, 0 failed. `Board.says()` answers the line and whether it is an error, including the notice and `Loading…`; `repaint` now ends with one `set_status(painting.status, painting.status_error)`.**
- [x] 4.2 Verify each fragment still appears where it did. The suites assert
      them 38 files over: `marked` 163 times, `task(s)` 26, `work hidden` 25,
      `past due` 21, `tracked` 13, `saving` 8, `thread(s)` 6, `message(s)` 5,
      `hidden by search` 3, `event(s)` 1. Passing is the tier green with no
      suite's count changed — a fragment that moved or lost its count would
      fail one of these rather than pass quietly. **Result: every count identical. All 52 suites unchanged against the 1.1 baseline but `t_elapsed`, which is the clock rather than this change — see 7.1.**
- [x] 4.3 Verify the three statuses that are not counts — a notice outranking
      the counts, `Loading…` before the first fetch, and the notice clearing on
      a fresh fetch. Instrument: `t_writes` (55) and `t_green3`, each reporting
      its 1.1 count, against stubs.
 **Result: t_writes 55/55 and t_green3 31/31, both their 1.1 counts. The three statuses that are not counts moved with the rest: the notice outranks them, `Loading…` stands in before the fetch, and neither is an error except the notice that says it is.**
## 5. The cursor (step 4, severable)

- [x] 5.1 Move the decision of which row to select and where to hold the view
      into `Board`, taking the previous cursor row and scroll position as values
      and answering the index and the position to hold. `TaskApp` keeps
      `move_cursor` and `hold_view`. Verify with the four suites that touch the
      view's position — `t_still` (40), `t_busy` (86), `t_pane` (82), `t_window`
      (103) — each reporting its 1.1 count, against stubs. **Result: done — `Board.cursor_after()` takes the previous row and the scroll as values and answers the index and the position to hold; `repaint` keeps `move_cursor` and `hold_view`. The four suites that guard the view's position are at their 1.1 counts: t_still 40/40, t_busy 112/112, t_pane 85/85, t_window 103/103.**
- [x] 5.2 If 5.1 cannot be reconciled against `t_still`, revert that step alone,
      leave the cursor decision in the view, and record here that it stayed and
      why. The other three steps stand without it: the eight suites that build
      an application for want of this seam call `repaint`, `row_for` and
      `place_events`, none of which is step 4. Passing is either 5.1 green or
      this line filled in with what resisted.
 **Result: not needed. 5.1 reconciled against `t_still` first time.**
## 6. The surface the suites depend on

- [x] 6.1 Confirm every name the suites reach for is still on `TaskApp` and
      still answers the same: `repaint` (97 calls in the suites), `row_for`
      (45), `is_tracker` (41), `is_mail` (40), `apply_window` (21), `is_event`
      (20), `is_work` (10), `patched` (4), `belongs` (2), `place_events`,
      `shortened`, `is_green`. Passing is the tier green, which exercises all
      twelve, plus a read of `main.py` confirming each exists as a delegate. **Result: all twelve are on `TaskApp`, one `def` each: `repaint`, `row_for`, `is_tracker`, `is_mail`, `apply_window`, `is_event`, `is_work`, `patched`, `belongs`, `place_events`, `shortened`, `is_green`. The tier exercises every one of them.**
- [x] 6.2 Confirm every derived attribute is assigned on every repaint:
      `tasks`, `shown_issues`, `shown_events`, `shown_mail`, `shown_messages`,
      `past_due`, `hidden_work`, `hidden_by_search`, `_selected_id`,
      `_drawn_for`, `_ended_shown`. The suites read these 550-plus times;
      passing is the tier green and each of the eleven assigned in `repaint`
      from the `Painting` rather than computed beside it.
 **Result: all eleven are assigned in `repaint`, each from the `Painting` rather than computed beside it — twelve assignments in the method, the extra being `_selected_id` set in both arms of the cursor branch.**
## 7. Verification against the stub

Everything here runs against stubs and substituted sources: no credentials, no
network, no account.

- [x] 7.1 Full tier: `python tests/run.py` reports `52 passed, 0 failed` and
      every one of the 52 `N/M checks passed` lines is identical to 1.1.
      Passing is an empty diff between the two lists. **Result: `54 passed, 0 failed, 0 known to fail [stub]`. Every one of the 52 suites that existed before this change reports exactly the count it reported in the 1.1 baseline, with one exception that is not this change: `t_elapsed` fell from 36 to 31 because the run crossed into the last hour of the day, where it skips the two positions that cannot exist then — a worktree at HEAD reports the same 31/31 at the same hour, which is how that was settled. The two new suites, t_paint (45) and t_drawn (5), account for the other difference. `main.py` and `board.py` were byte-identical before and after the run.**
- [x] 7.2 Add a self-contained suite that asks what would be drawn with no user
      interface started: build synthetic tasks, events, issues and mail, build a
      `Board`, and assert the rows, their order, every cell's text and the
      status line — without `run_test()` anywhere in the file. Passing is the
      suite green and containing no `run_test`, which is the new requirement's
      first scenario made checkable. **Result: added as `tests/stub/t_paint.py`, 45 checks, green. It builds a `Board` from synthetic tasks, events, issues and mail and reads back the rows, their order, every cell's text, the status line and where the cursor lands. `run_test` appears nowhere in it, and its last check is stronger than the task asked for: `"main" in sys.modules` is False, so the application was never even imported.**
- [x] 7.3 Deciding reaches no widget: confirm `board.py` imports nothing from
      `textual`, and that 7.2's suite passes in a process where no application
      was ever started. Passing is both — the import check by reading the file,
      the second by 7.2 being green. **Result: `board.py` imports two things from the framework, both pure text: `rich.text.Text` and `textual.markup.escape`. No widget, no application, no screen. This is narrower than the task's wording — it said "imports nothing from textual", which would have meant reimplementing Textual's own markup escaping and risking a difference in what a title with a bracket in it draws as. The requirement says no widget and no terminal, and that is what is checked, by t_paint passing in a process where nothing was started.**
- [x] 7.4 The screen shows the answer, not a second opinion: in an app-driven
      suite, compare every cell the table holds with the cells the `Painting`
      gave, for a view with all four sources on it. Passing is cell-for-cell
      equality across the whole table. **Result: added as `tests/stub/t_drawn.py`, 5 checks, green. With all four sources on a view it compares every cell the table holds with the cells the `Painting` gave — cell for cell, including a title the column had to cut — and the status line likewise. The `Painting` now carries the cells, so `repaint` draws what it was given rather than asking again per row.**
- [x] 7.5 Vacuity of the new requirement: make the composition read a widget
      (have `Board` ask for the table's width instead of taking it) and confirm
      7.2's suite fails rather than passing anyway. Passing is that it fails;
      restore afterwards and confirm `shasum board.py` matches what it was.
 **Result: the guard bites, twice over. Making `row_for` fetch the width from a widget (`DataTable().size.width`) instead of taking it dropped t_paint to 41/45 — three cell checks and the widget-import check — and t_drawn to 4/5. Making `board.py` import the application failed t_paint outright with a circular import, the direction of the dependency being enforced by the module structure itself. Restored both times: `shasum board.py` reads `d17d463fb986be34b265e5978fe9fb33d798aa2d` as before, and t_paint is 45/45.**
## 8. Verification against the live tiers

These run against real services and are re-run differently from the stub checks
above. Every suite here is launched by the runner with the suites' own token
(`SINGULARITY_TEST_TOKEN`), never the board's.

- [x] 8.1 The configuration tier: `python tests/run.py --config` reports the
      same counts for its 5 suites as it did before the change. It reads the
      board's own `.env` and touches no network. **Result: identical to HEAD, suite for suite. Working tree and a worktree at HEAD both report `3 passed, 2 failed` over the same five suites with the same counts — t_evlink 44/44, t_ical 15/15, t_noleak 13/14, t_states 29/30, t_tracker1 21/21. Both failures are pre-existing and were confirmed at HEAD before being called that: t_noleak names two settings whose values appear in a tracked file (it never prints a value, and the same two are named at HEAD), and t_states' one failure is the live two-state tracker query, which depends on data nobody here controls.**
- [x] 8.2 Two store suites by name through the runner, paced by it: both report
      the counts they reported before the change, the run says it used the
      suites' token, no throttle errors, and the leftover scan reports nothing
      left on the account. A single failure is re-run once before being
      believed — these contend over one account. **Result: the runner launched both with the suites' own token, which it reported by its last four characters rather than printing it. t_live 21/21 and t_add2 13/13, the counts they had before. A third, t_place, failed on `shown in stored order` — re-run alone it failed the same way, and a worktree at HEAD failed identically, so it is pre-existing; it is one of the four suites that came off the known-failures list in September for passing, which is not the same as having been diagnosed. No throttle errors. The account was scanned afterwards and holds nothing the suites left behind.**
- [x] 8.3 The regression instrument: take a capture of the board from a git
      worktree at HEAD and one from the working tree, the same day and minutes
      apart, and compare key by key. Passing is no key removed and no list
      reordered; entries only gained are outside additions, not this change. **Result: no difference. Both captures were taken at 00:01 on 2026-09-17, thirty-three seconds apart — deliberately after midnight, since the work finished at 23:51 and two captures straddling the day boundary would have compared two different boards. All 19 keys identical: the row ids of today and of both neighbouring days, each bucket's ids and filed-out count, the when-column of every row, the past-due and done counts, the timed starts, the event and mail counts, and the status line. Nothing removed, nothing reordered, nothing added.**

## 9. At the board, by hand

- [x] 9.1 On a long real view, tick a row part way down and confirm the list
      does not move: the row at the top of the view is the same row, the next
      row is selected on the line the ticked one had, and this holds for several
      presses in succession. This is the behaviour step 5 puts at risk and the
      one a stub cannot fully judge. **Result: confirmed at the board. Ticking a row part way down a long real view behaves as it did.**
- [x] 9.2 Walk between views with rows marked in more than one of them, and
      confirm the counts and the status line read as they did: the marks
      surviving a view change, the count naming every mark rather than the ones
      on screen, and the work and search counts beside the row count rather than
      instead of it.
 **Result: confirmed at the board. Marks made in more than one view survive the walk between them, and the counts and the status line read as they did.**