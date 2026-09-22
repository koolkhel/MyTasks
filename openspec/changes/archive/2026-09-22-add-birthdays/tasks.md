## 1. Settle whether the calendar can be read at all

- [x] 1.1 Before writing code, confirm the calendar this change is for yields events. Instrument: a throwaway probe run by hand from the terminal that holds the calendar grant, printing per calendar only its source title, source type, calendar title, calendar type and a **count** of events in a 365-day window — never an event title, and nothing committed. Passing: the calendar appears in the listing with a non-zero count. A zero count means the address-book grant is missing and no amount of selection work will show its events; stop and report that instead of continuing.

## 2. The selection rule

- [x] 2.1 Add to `ical.py` a pure selection function taking the `Config` and a sequence of `(source title, calendar title, identifier)`, returning the identifiers to read and the configured names that matched nothing. No framework import, no I/O. Verify by importing it in a Python shell with no pyobjc installed and calling it.
- [x] 2.2 Match on NFC-normalised, case-folded titles on both sides, against the source title and the calendar title alike. Verify with the suite in 2.4.
- [x] 2.3 Deduplicate the chosen identifiers, so a calendar named both directly and through its account is read once and keeps its first position.
- [x] 2.4 Add `tests/stub/t_calsel.py` — a self-contained suite for the selection rule, declaring its parts in `PARTS` and doing nothing at import. Cases: an account name selects all its calendars; a calendar name selects that one; a calendar name does not bring in its account's other calendars; a name that is both an account title and another calendar's title selects both; an account and one of its own calendars named together select it once; a decomposed (NFD) title in the configuration matches a composed one from the machine and the reverse; a name matching nothing is returned as unmatched while the rest are still selected; nothing configured selects nothing and reports nothing unmatched. Fixtures are synthetic triples invented in the suite — no real account or calendar name. Passing: `.venv/bin/python -m pytest tests/stub/t_calsel.py` is green and every part reports its checks.

## 3. Reading a day

- [x] 3.1 Change `ical.fetch` to gather the triples from the framework, call the selection function, and return a frozen result carrying the events and the unmatched names. Keep `CalendarUnreadable` for the framework being absent, permission refused, permission to write only, and no accounts at all on the machine — a configured name that matched nothing no longer raises.
- [x] 3.2 Update `tests/config/t_ical.py`: its two live checks currently assert that a missing account **raises**, which this change reverses. Replace them with checks that a missing name is returned as unmatched while the real account's events still come back. Keep the existing `_status()` guard and its skip, so a machine without the grant skips rather than reporting the system's answer as the board's. Instrument: the config tier, against this machine's real calendar. Passing: `.venv/bin/python tests/config/t_ical.py` is green, or skips those checks explicitly when the grant is absent.

## 4. Work, and the row

- [x] 4.1 Change `Config.is_work` to take the account and the calendar and match either, normalised and case-folded as in 2.2. Update its call site in `board.py:event_rows`, which has both to hand. Verify with the `work_filter` and `configuration` parts of `tests/stub/t_cal.py`.
- [x] 4.2 Extend `tests/stub/t_cal.py` with a case where what is configured as work names a **calendar** rather than an account: the key that hides work removes that calendar's event rows and the hidden count includes them. Passing: `.venv/bin/python -m pytest tests/stub/t_cal.py -k work_filter` is green and the suite's total check count has risen.

## 5. The board keeps the events it did read

- [x] 5.1 Change the calendar worker in `main.py` to take the events and the unmatched names together, so a reading with unmatched names both draws its events and records the standing message. The handler that records the message no longer empties `self.events`. Keep `CalendarUnreadable` on its existing path, which does still empty them.
- [x] 5.2 Make the unmatched-name message stand and come down like the calendar's other trouble: it survives a refresh for another reason, and clears when every name matches. Verify by adding a part to `tests/stub/t_cal.py` that drives the board with a reading carrying one unmatched name, asserts the other calendar's rows are drawn and the message is present, then refreshes the view for an unrelated reason and asserts the message is still there. Passing: that part is green under `.venv/bin/python -m pytest tests/stub/t_cal.py`.

## 6. Documentation

- [x] 6.1 Update the configuration table in `README.md` so the two calendar entries read as naming accounts **or** calendars, and say that a name matching nothing costs that name rather than the calendar. No account or calendar name from any real machine appears in the text. Verify by reading the rendered table.

## 7. Verification

- [x] 7.1 Stub tier, on its own: `.venv/bin/python tests/run.py`. Passing: green, with no suite's check count lower than at HEAD — compare against a worktree at HEAD, since a part dropped from a `PARTS` tuple takes its checks with it and nothing else would say so.
- [x] 7.2 Config tier, on its own and separately from 7.1: `.venv/bin/python tests/run.py --config` from the terminal holding the calendar grant. Passing: green, or skipping the calendar checks with the stated reason. Re-run once before believing a failure.
- [x] 7.3 Live check of the outcome, by hand and last: name the birthday calendar in `CALENDAR_PERSONAL` and start the board. Passing: its rows appear on a day the calendar holds one, the other configured sources still show their events, and removing a letter from the name leaves those other events on the board beside a standing message naming the broken entry. Nothing from this check is committed — no calendar name, no event title. **Run as:** the real `ical.fetch` against this machine's calendar, driving a real board through Textual's `run_test` with the task store stubbed, on a day the calendar really holds one. `.env` was not edited and the TUI was not driven by hand; adding the entry to `.env` is the user's own call. 8/8 checks, including that naming the source instead pulls in a second calendar.
- [x] 7.4 Confirm the code was not edited during 7.1–7.3: `shasum ical.py board.py main.py` before and after, matching. Un-check any verification task whose run predates a later edit to what it verified.
