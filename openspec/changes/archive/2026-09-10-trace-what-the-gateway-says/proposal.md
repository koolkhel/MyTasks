## Why

The board died mid-review on the real account, and the log said one thing: a
review of seven messages started. Nothing about which of the seven it was on
when the line dropped, whether the gateway had been slowing for minutes or
went from healthy to gone, or whether the socket had been idle when it went.
Four questions, none answerable, and the change that made the failure
survivable could not make it legible.

Each of the four is answered by knowing which command ran, when, and for how
long. Nothing more is needed: not the request lines, not the responses.

The board writes two lines a review — what was attempted, and how it ended.
Between them is a conversation of ten to thirty requests, and every one of the
measurements this board was designed around came from timing those requests by
hand, once, and writing the numbers into comments. A gateway that answers a
folder select in ten seconds is a fact about a mailbox on a particular day;
the comments record what it did in July.

The seam already exists. The change that stopped a dropped line from ending
the session routed every request through one function, so that `imaplib`'s
exceptions could be converted in one place. That function sees every command,
by name, with both outcomes — which is exactly what a trace needs, and it was
built for something else entirely.

## What Changes

- Every request the board makes to the mail account is written down: when,
  which command, which folder, how many messages or which message, how long it
  took, and how it ended.
- Always on. The fault it exists for cannot be reproduced on demand, so a
  trace that has to be switched on is a trace that is off when it is needed.
- A file a day, beside the log the board already writes, so the day a fault
  happened is found by its date and old days are removed with `rm`. Measured:
  about six thousand lines and 470 KiB for a full pass of the mailbox, against
  a log that holds 298 lines in total — one file would bury the other.
- The trace holds no subject, no sender and no part of a body. This is
  structural rather than a rule to remember: the board issues six IMAP verbs
  and not one of them fetches a header or a body.
- It holds no credential either, and for the same kind of reason. The one
  command that carries a password is the one command that does not go through
  the traced path — login is converted by the connection's own setup, which
  the trace does not touch.
- Written best-effort, like the log: a trace that cannot be written changes
  nothing the board does and says nothing to the person about itself.
- Never read back. No row depends on it and deleting it changes nothing on
  screen, which is what makes it safe to keep at all.

## Capabilities

### Modified Capabilities

- `task-board`: one new requirement for the trace — that every request is
  recorded with its duration and outcome, always, in a file a day, and what it
  may and may not contain. It sits beside the requirement for the log of what
  the board did to the mailbox, which stays as it is: that one is the
  narrative, read routinely, and this one is the conversation underneath it,
  read when something is wrong.

### New Capabilities

None.

## Impact

- `gateway.py` — the one function every request already passes through gains
  timing and a line. Nothing else in the file changes: the connection's setup
  and teardown are left alone deliberately, on the measurement below.
- `journal.py` — where the trace is written, beside the log and the crash
  file, so all three share one directory, one best-effort discipline and one
  redirection in the suites.
- No product behaviour changes. No extra request is made to the account, and
  the board asks the mailbox for nothing it was not already asking.
- `logs/` is already excluded from commits, and a trace of a real account's
  folders and message identities is exactly why.

## What was measured, and what it settles

- Requests a review makes, against the recording server the suites use: 12 for
  a row of one message, 18 for three, 30 for seven. At about 500 rows in the
  mailbox, a full pass is ~6,000 lines.
- Connect, the password command, login and logout together take 0.58 s against
  the real gateway — 0.34, 0.02, 0.21 and 0.00. A single folder select on the
  archive was measured at about ten seconds. So the parts outside the traced
  path are not worth reaching for, and leaving them alone is what keeps
  credentials out of the trace.
- A row of seven messages makes **eleven** folder selects, seven of them
  re-selecting the archive once per message where a helper already exists to
  avoid re-selecting a folder that is open. At ten seconds each that is about a
  minute of repetition per folded row, and most of the nine minutes the crash
  spent before it died. The trace makes that visible in a person's own numbers;
  fixing it is a separate change, and this is what would price it.
