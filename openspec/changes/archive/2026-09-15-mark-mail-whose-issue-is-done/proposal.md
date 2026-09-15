## Why

The inbox shows notifications about issues, and some of those issues are
already finished. Nothing on the board says so, so a row about a resolved
issue looks exactly like a row about one still being argued over — and the
only way to tell them apart is to open the tracker, one issue at a time.

The notifications already carry the answer. The tracker draws a resolved
issue's key struck through, and that styling survives into the mail: every
notification names the issue it is about in a header of its own, and the link
to that issue in the message's HTML carries a line-through in its inline style
once the issue is resolved.

Measured on the account this was found on, across one folder:

| | |
|---|---|
| notifications in the folder | 571 |
| …naming their own issue in a header | **571 — all of them** |
| …linking that issue in their HTML | **571 — all of them** |
| distinct issues | 112 |
| issues whose newest notification shows the key struck | 59 |

The tracker also writes state changes into the plain-text part, and those name
the state exactly. They were the obvious candidate and they are the worse one:

- A state change is an **event**, on the one message where it happened. The
  struck key is a **condition**, on every message sent afterwards.
- That one message leaves the folder as soon as it is filed, and the archive
  is not mirrored locally, so the board can never learn it again. 35 of the 59
  resolved issues have no state change left in the folder at all.
- The two never disagree where both are visible: of the 20 issues whose last
  visible state change was to the done state, **all 20** are struck. None is
  struck without cause.

So the strike answers for every issue and keeps answering; the state line
answers for 46 of 112 and forgets.

## What Changes

- **A mail row is marked when its issue is done.** The row's newest message
  decides, which is the message the row already shows.
- **The fact is read from the notification, never from the tracker.** No
  request is made, nothing is configured, and a board with no tracker reachable
  behaves exactly as one with.
- **Done means what the tracker means by it** — the key drawn struck through,
  which covers both an issue that was fixed and one that will not be. Neither
  needs attention again, which is the whole of what the mark is for.
- **The mark is on the mail row only.** A task promoted from the row does not
  carry it: a task is the board's own, and keeping it in step would mean the
  board re-reading mail on behalf of tasks.
- **The row's title is drawn struck through**, which is how the board already
  draws a task that is done and how the notification itself draws the key.
- **No state names anywhere.** The states are localised text from a workflow
  somebody else configures; reading them would tie the board to that wording
  and to a language. The strike needs none of it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement added, one modified.
  - **Added** — *A mail row says when its issue is already done*: where the
    fact comes from, that it costs no request to the tracker, which message
    decides, and what happens to mail that carries no such marking at all.
    Its own requirement rather than a clause bolted onto an existing one:
    *Mail is shown in the inbox* is about where mail sits and how it is
    counted, and *What a mail row shows* is about drawing. Neither is about
    what a row knows, and stretching either would have hidden a new promise
    inside a requirement about something else.
  - **Modified** — *What a mail row shows*: a row whose issue is done is drawn
    saying so. All five existing scenarios are unaffected and return
    unchanged.

## Impact

**Code**

- `mail.py` — the HTML part gains a parse of its own. This was planned as
  riding on a parse already happening and that was wrong: `_body` prefers a
  message's plain-text part, and a tracker notification carries both, so the
  HTML of the messages this is about is never read today. The existing reader
  does the work — it already watches links and their attributes — but it has to
  be pointed at the part `_body` skips. A field on `Message` carries the
  answer, the same shape as the field added for the read flag.
- `main.py` — the row builder draws the title struck when the thread's newest
  message says the issue is done. The board already draws a finished task that
  way, so this is the existing expression applied to another row.

**Cost** — one extra parse of the HTML for every message that has one. The
reader is measured at 0.06 ms a message, so on the order of a thousand
notifications this is tens of milliseconds against a read path measured in
hundreds; the performance suite measures the read path rather than assuming it.

**Not affected** — no request to the tracker, no request to the mail account,
no configuration, and nothing about folding, reviewing, promoting or the
counts.

**Fragility** — this reads a styling choice in someone else's HTML template. A
tracker upgrade can change it, and the failure would be silent: nothing marked,
nothing said. The suite should hold a canary so that "no message in the whole
folder carries the marker" is visible as a fault rather than as a quiet day.

## Assumptions recorded

- **A row is done when its newest message says so.** A thread's messages are
  about one issue, and the newest carries the most recent word on it.
- **The mark is as old as the last notification.** An issue reopened with no
  further mail goes on reading as done. That is inherent to not asking the
  tracker, which is the point of the change rather than an oversight.
- **Fixtures are synthetic.** The markup shape is copied; the host, the project
  keys and the subjects are invented, because this repository is public.
