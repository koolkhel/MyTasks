## 1. Client support for the dateless buckets

- [x] 1.1 Add a named position type to `singularity.py` covering a calendar day plus the inbox and never sentinels, so callers pass one value rather than flags; verify `./.venv/bin/python -c "import singularity"` succeeds and the sentinels compare distinctly from any `date`.
- [x] 1.2 Add client queries for the two buckets — undated and not deferred, undated and deferred — each excluding finished tasks; verify their lengths equal the API's own `pagination.total` for `start.isSet=false` split by `deferred.eq` (37 and 2 at time of writing), and that no returned task carries a `start`.
- [x] 1.3 Add one client method that sets a task's schedule — a given day, never, or cleared — issuing a single `PATCH` carrying both `start` and `deferred`; verify against a synthetic task that day→never→cleared→day each land the intended state and that `deferred=true` with a non-null `start` is never produced.

## 2. The view model in the TUI

- [x] 2.1 Replace `TaskApp.day` with a single view value and dispatch `load` to the day query or the matching bucket query; verify in the pilot that all three views populate and that switching between them leaves no stale rows.
- [x] 2.2 Make the header name the view — the inbox and never by name, a calendar day as it does today — and keep the task count in the status line; verify the pilot reads "Inbox", "Never", and an unchanged `Thursday 03 September 2026  ·  today`.
- [x] 2.3 Bind `i` to the inbox and `n` to never, make previous/next-day inert while a dateless view is shown, and keep `t` returning to today's day view; verify each key in the pilot, including that `h`/`l` in the inbox leave the inbox displayed.
- [x] 2.4 Make the add action follow the shown view — undated in the inbox, deferred in never, dated on a calendar day; verify by adding a synthetic task in each of the three views, checking the stored `start` and `deferred`, then deleting each.

## 3. Date assignment

- [x] 3.1 Add the picker modal offering today, tomorrow, a given day, never, and clear, following the existing `TaskInput`/`Confirm` modal pattern; verify each choice returns its own result and that abandoning the picker returns nothing.
- [x] 3.2 Chain the "a given day" choice into a `YYYY-MM-DD` prompt that reports a malformed value without touching the task; verify a good date is accepted and `not-a-date` is refused with the task's `start` and `deferred` unchanged.
- [x] 3.3 Wire the picker to the client's schedule method and bind it to `d`; verify against a synthetic task that dating it from the inbox removes it from the inbox and places it on the chosen day, that never removes its date, and that clear returns it to the inbox.
- [x] 3.4 Add the new keys to `Help.TEXT` and confirm the footer; verify the help overlay lists the inbox, never, and date-assignment keys, still opens on `?` and closes on `esc`, and mentions no priority action.

## 4. Ordering and end-to-end verification

- [x] 4.1 Confirm dateless views order by pinned then title without a second sort function, relying on the existing sort key degrading when start and completion are constant; verify with synthetic undated tasks that a pinned one leads and the rest are alphabetical.
- [x] 4.2 Drive one pilot run over a synthetic task through the whole lifecycle — created undated, seen in the inbox, dated to a far-future day, seen on that day and absent from the inbox, sent to never, seen in the never view with no date, cleared back to the inbox, deleted — asserting on the captured request bodies that no write ever pairs a `start` with `deferred=true` and none carries a `priority`; do not exercise this against a real dated day.
- [x] 4.3 Confirm the day view is unchanged: today's listing still shows finished tasks in their existing order, and `./run.sh --cli` and `./run.sh --cli --date <a far-future day>` both still run.
