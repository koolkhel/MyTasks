## Why

The board died on the real account today at 17:30:02Z, part way through
reviewing a row of seven messages, and the journal it had just been given
says so precisely: one `starting` line with no counterpart, and nothing else
until the restart forty minutes later. The gateway had already moved all
seven and confirmed them gone from the folder; it was on the archive-side
half, one search a message, when the gateway closed the socket in the middle
of an `EXAMINE`. `imaplib` turned the empty read into `IMAP4.abort`.

Nothing catches that. `GatewayUnreachable` is raised in exactly one place —
around connect and login — so it covers a review that cannot *start*.
`MoveFailed` covers a move that cannot be *confirmed*. Neither covers the
connection dying part way through, which against this gateway is the likeliest
of the three: measured review times on the account run from 13 s to 120 s for
a single message, and the longer an operation is open the better its chance of
being cut. So the exception went past the worker's `except`, Textual wrapped
it in `WorkerFailed`, and the session ended.

Two costs. The row's seven messages sit in the archive unread — `mark_seen`
comes last of all, deliberately — and nothing anywhere records which seven.
And the traceback went to the terminal, where it survives only as long as the
scrollback and only because it was hand-saved into a file; the journal, which
is durable, says nothing about why the operation never finished.

The requirement this violates is already written down. *The mailbox never
delays or breaks the board* is the title; its scenarios are all about reading
a mailbox, and acting on one broke the board.

## What Changes

- A connection lost part way through a mailbox operation becomes an ordinary
  failure of that operation: the row returns to the queue, the indicator shows
  a failure, the journal records it with the folder, the count and the
  duration, and the session continues. This is the failure that happened, and
  after this change it is not a crash at all.
- The gateway keeps its own error vocabulary. Every failure it reports is one
  of its own two exceptions; a protocol or socket error from underneath does
  not escape it. The board goes on knowing nothing about `imaplib`.
- Any unhandled failure that still ends the session writes itself to a file
  first, in `logs/` beside the journal, named by the time it happened so that
  one crash never overwrites another.
- The crash file carries the full traceback **with frame values**, which is
  what the operations log deliberately does not carry. Diagnosing today's
  crash needed the frames and the exception; keeping the values is a choice to
  pay ~200 KB and hold real message text in exchange for never wishing the
  file had more in it. `logs/` is already excluded from commits, which is what
  makes that affordable, and the exclusion becomes part of what the crash file
  requires rather than a convenience it borrows.
- **The board still exits** when a failure is genuinely unhandled. A crash file
  is evidence of a bug, not a state to keep working in. Recorded as a
  requirement so it is not quietly improved into surviving.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *The mailbox never delays or breaks the board* extends from
  reading the mailbox to acting on it — a connection lost mid-operation is
  that operation failing, not the session ending. One new requirement says
  what an unhandled failure leaves behind, and that the board still goes.

## Impact

- `gateway.py` — where a protocol or socket failure becomes one of the
  gateway's own two exceptions. `Server.__enter__` already does this for
  connect and login; nothing does it for the six verbs afterwards.
- `main.py` — the app gains a hook on the path Textual already takes to end a
  session after an unhandled exception, and writes the file there. The two
  mailbox workers' `except` clauses are unchanged in shape: once the gateway
  keeps its vocabulary, the failure they already handle is the failure that
  arrives.
- `journal.py` — the crash file sits beside the operations log and shares its
  directory and its best-effort discipline; the operations log's content rule
  is untouched.
- No new dependency: the traceback rendering is what Textual already builds
  for the terminal.
- `logs/` is already gitignored. Nothing new needs excluding, and the crash
  file's content makes that exclusion load-bearing rather than tidy.
