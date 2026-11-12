# TODO

What is left from the whole-repo review of 2026-11-12. Its first five findings
(a paste crashing the recurring view, reviewed mail coming back on a view
change, 8-bit mail headers dropping a message, per-message refusals on the
mail server being ignored, and paced writes leaking their place) are fixed,
along with undo in the recurring view.

Sizes are estimates. Function names are given rather than line numbers, which
move.

## Bugs

- [ ] **Undo right after a paste lets the unsent lines through.**
  `main.py`, `paste_tasks` and its `reverse`: `reverse` sees only the lines
  already sent, so the ones still waiting in `_paced` are created afterwards
  and the board has already said "Undid". Fix: `reverse` sets a flag that makes
  each unsent `send` return None, and drops their placeholder rows. Found by
  reading the code, not reproduced.
- [ ] **Days next to a clock change are an hour off.** `singularity.local_tz`
  freezes today's UTC offset and uses it for every date. Fix:
  `with open("/etc/localtime", "rb") as f: return ZoneInfo.from_file(f)`. Only
  matters in a zone that changes its clocks.
- [ ] **An unreadable mail folder looks empty.** `mail._messages` returns `[]`
  on an `OSError` from `box.keys()`. Fix: delete that `try` so `read()`
  reports `MailboxUnreadable`. -3 lines.
- [ ] **An event that started yesterday shows yesterday's time.** `ical.Event.label`
  and `sort_key`, and the event minutes in `board.py`, read `start`; an event
  from 23:00 to 01:00 shows today as "23:00" and sorts last. Fix: use
  `max(start, the day's midnight)`.
- [ ] **A mail folder is found by its name alone.** `gateway.Mailbox.folders`
  keeps the first folder of a name anywhere in the tree, so `Inbox/Jenkins` and
  `Archive/Jenkins` collide. Fix: refuse a name that appears twice. Not
  reproduced.
- [ ] **`t_green8`'s failures are not counted.** It prints "LEFT MARKED", which
  `tests/run.py`'s `CHECKS` pattern does not match. Goes away with the store
  tier cleanup below.

## Code to delete (about 200 lines)

No caller anywhere, tests included:

- [ ] Board forwarders on `TaskApp`: `event_rows`, `mail_rows`, `matches`,
  `ordering_key`, `place_issues`, `shows_mail`, `tracker_rows`; and
  `marked_cell`, `has_ended`, `_mail_when`, `_title_text`.
- [ ] `main.minutes_into_day`, the empty `NoteArea` subclass, the unused
  imports (`asyncio`, `Horizontal`, `Coordinate`, `email.utils`) and the nine
  names `main` re-exports from `board` for nobody. Also `gone = ""` in
  `action_undo` and the `Screen { layers: ... }` rule nothing uses.
- [ ] `ical.Event.ended_by`, the macOS-before-14 fallback in `ical._request`,
  the unused `EKEntityTypeEvent` import.
- [ ] `mail.Thread.text`, `mail.ISSUE_HEADERS` (repeats `ISSUE_HEADER`).
- [ ] `singularity`: `_past_due_tasks`, `Listing.due_now`, `iter_tasks`,
  `PRIORITY_NAMES`/`HIGH`/`NORMAL`/`LOW` with `Task.priority`, `Position`,
  `UNPINNED`, and `set_schedule`'s `use_time` parameter.
- [ ] `singularity.parse_ending` and `Task.ending_read`: they can only ever say
  "never ends", so `series_facts`' "end read" text never shows. Two test lines
  in `t_series` change.

## Kept only for tests (about 80 lines)

- [ ] The six paint counters copied onto `TaskApp` (`shown_issues`,
  `shown_events`, `shown_mail`, `shown_messages`, `hidden_by_search`,
  `past_due`): keep `self.painting` and point the tests at it.
- [ ] The six board forwarders only tests call (`belongs`, `event_key`,
  `is_work`, `patched`, `place_events`, `search_text`), and `is_green` and
  `shortened`: point the tests at `app.board()` or `board.Board`.
- [ ] `mail.Message.key`, `mail.Thread.about`, `gateway.Server.number`,
  `holds`, `Outcome.done`, `Pending.previous` and `Pending.task_id`.

## Repeats to merge

- [ ] **Dialogs** (about 50): eight escape-to-dismiss copies become one
  `Dialog(ModalScreen)`; the four `.focus()` calls go (Textual focuses the
  only focusable widget). `LinkPicker` and `ProjectPicker` are one list dialog.
- [ ] **Write paths** (about 80): add and paste each work out where a new
  task lands (`new_task_fields()`); the date-to-fields mapping is written four
  times (`singularity.set_schedule`, `done_for_today`'s landing, the dated add,
  the fake client) and becomes `singularity.schedule_fields()`; seven set
  writes end with the same report, which `submit_many` can make; rename and
  note repeat the single-row guard.
- [ ] **Action wrappers** (about 25): `prev_day`/`next_day`,
  `move_up`/`move_down`, `copy_marked`/`copy_marked_markdown`,
  `note_up`/`note_down` become bindings with arguments. `t_twins2` asserts the
  action names.
- [ ] **Smaller repeats** (about 150): the two themes share eight settings; the
  archive and series loaders are near-copies; five `load_*` env readers and
  `SingularityClient` constructor options nobody passes; the payload-decode
  lines six times in `mail.py`; `Board.paint` filters each source by hand;
  `Archive` and `Series` are one class.
- [ ] **IMAP leftovers** (about 25): `gateway.load_config` still falls back to
  `MAIL_IMAP_USER` / `MAIL_IMAP_PASSWORD_COMMAND`; `journal` writes
  `imap-*.log`; `t_noleak` lists IMAP names. Run `grep -c '^MAIL_IMAP' .env`
  first: if `.env` still uses the old names, removing the fallback turns mail
  review off without a word. Document the new names in the README.

## Speed

- [ ] `mail_fold` builds a whole `Board` per message, on the worker thread,
  while `Board.mail_fold` never reads `self`. Make it a `@staticmethod` and
  pass `board.Board.mail_fold`. Not measured.

## Decide

- [ ] Keep `./run.sh --cli` (`singularity._main`, about 50 lines)?
- [ ] Keep `docs/screenshots.py --crt` (about 170 lines, `t_pictures`' 260
  lines and the Quartz dependency) for one README picture?

## Tests (about 2,700 lines)

- [ ] **Scaffolding in every stub suite** (about 1,200): add
  `pythonpath = . tests` to `pytest.ini` and drop the 9-line path preamble;
  drop the `__main__` tails and `parts.run_parts` (nothing runs a suite
  directly); one pair of `check` helpers in `parts.py` (14 suites call the
  truthy one `check`); one `settle` in the harness; `set_schedule_order` in
  `StubClient`. Run the stub tier once afterwards.
- [ ] **One four-source board fixture** for `t_bulk`, `t_copy`, `t_mark`,
  `t_search` (about 270), and the mail suites' `select` (about 150).
- [ ] **Checks repeated across suites** (about 530): the foreign-row refusal
  (7 suites, one `refuse_foreign`) as one table in `t_block`; the work-filter
  rules (5 suites) once on a four-source board; twin keys already covered by
  `t_twins2`'s property check; "escape clears marks" three times; request
  counts in both `t_gateway` and `t_trace`; `t_busy` repeating `t_review`'s
  outcomes; `t_search`'s rule cases through six boards (use `painting()`);
  `t_mark`'s three theme loops; `t_bulk`'s two parts that call internals.
- [ ] **Store tier** (about 650, and live runs saved): delete `tests/probes/`,
  `t_twins6`, `t_work6`, and `t_green8` with its `CHECKS` pattern (give
  `t_green7` ten trials); keep one baseline check (`t_regress`); move
  `t_label`'s table into `t_top`; keep only `t_undo6`'s cramped case.
- [ ] **Checks that read the source** (about 70): `t_workspace` counting
  `Popen(`, `t_undo3`'s `undo_reason=` count, `t_window`'s source text,
  `t_pane`'s CSS strings, docstring wording in `t_promote`, `t_review` and
  `t_busy`, `t_fit`'s `inspect.getsource`, `t_title`'s greps. Replace with
  behaviour (patch `Popen`, check its arguments). Keep `t_markup`'s `escape`
  guard.
- [ ] **Small cuts** (about 90): the unread tables in `known_failures.py`
  (keep `FLAKY`); `run.py`'s `has_pytest` and its hand-written `.env` parser;
  the harness's import fallbacks for modules that all exist now.

Not worth doing: rewriting the suites as plain pytest functions. About 700
more lines, for 2,916 rewritten checks and parts that share state.
