## Context

See proposal.md — Why, for what happened and what it cost. The design-level
facts that shape the approach:

- `GatewayUnreachable` is raised only inside `Server.__enter__`, around
  `_connect()` and `login()`. Everything after that — six IMAP verbs across
  seven call sites — can raise `imaplib.IMAP4.abort`, `imaplib.IMAP4.error` or
  a bare `OSError`, and nothing converts them.
- Both mailbox workers catch exactly `(gateway.MoveFailed,
  gateway.GatewayUnreachable)`, and both decrement the busy count from a
  `finally` while calling `mail_broke()` only from the `except`. So an
  exception that escapes leaves the indicator at rest — the failure mark
  cannot appear for the one failure that got past everything. Fixing the
  boundary closes that hole without new machinery: the failure then arrives
  as one the `except` already handles.
- Textual 8.2.8 routes every unhandled exception — worker failures included,
  via `Worker._run` → `app._handle_exception(WorkerFailed(...))` — through
  `App._handle_exception(error)`. That runs on the app's own event loop, is
  called once, has the exception in hand, and is followed by
  `_fatal_error()`, which builds a `rich.traceback.Traceback` and appends it
  to `_exit_renderables` for printing to stderr **after** the terminal is
  restored. Nothing in that path touches disk.
- `journal.PATH` is a module-level string, and `tests/harness.py` already
  repoints it at a temp directory so no suite writes into the real log.

## Goals / Non-Goals

**Goals:**

- One place in the codebase knows `imaplib` exists, and it is not `main.py`.
- A crash file that needs no redirection of its own to be safe in tests.
- A crash writer that cannot itself become the reason a session ends badly.

**Non-Goals:**

- Surviving an unhandled failure. Decided: the session still ends.
- Retrying, resuming or reconnecting a dropped operation. The row comes back
  and a person ticks it again — that already works and is already specified.
- The redundant archive `EXAMINE`. `Server.number()` re-selects the folder on
  every call, so confirming a seven-message row issues seven archive
  `EXAMINE`s where one would do, at a measured ~10 s each against 20,749
  messages; `_number_here` exists for exactly this and the archive loop does
  not use it. That is why today's operation was open for nine minutes, and
  shortening it would genuinely reduce exposure — but it is a cost fix, not a
  correctness one, and it changes no requirement. Left out on purpose.
- Protocol-level logging of the IMAP conversation. Its own change.
- Rotating or pruning crash files. See Risks.

## Decisions

### The conversion happens inside `Server`, per command, not at the boundary of `archive()`

Every imaplib call in `Server` routes through one helper that converts
`imaplib.IMAP4.abort` and `OSError` to `GatewayUnreachable`, and
`imaplib.IMAP4.error` to `MoveFailed`. The split follows what the two names
already mean: `abort` and a socket error say the line is gone, which is
"could not be reached"; `error` says the server answered and refused, which
is "the move failed". The board handles both identically, so the distinction
shows up only in the sentence a person reads — which is the point of having
two names.

Alternatives:

- *Widen the workers' `except` in `main.py`.* Two lines, and it works. But it
  puts `imaplib` in the board's imports and makes every future mailbox caller
  responsible for remembering the protocol's exception hierarchy. The gateway
  exists to be the only thing that reaches outside.
- *Wrap the body of `archive()` and `restore()`.* Fewer edits, and covers the
  board's two entry points. But `Server` is public within the project and the
  live suites call `srv.holds(...)` directly, so a converted-at-the-top-level
  design leaves the class itself still leaking. Converting per command makes
  the property belong to the class rather than to two functions.
- *A decorator on each method.* Same effect, more indirection, and the
  helper has to wrap the single imaplib call rather than the whole method
  body — see the risk below about swallowing an unrelated `OSError`.

### The crash file is written from an override of `App._handle_exception`

`TaskApp` overrides it, writes the file, and calls `super()`. That seam is
the only one that sees a worker's exception: `sys.excepthook` never fires
because Textual handles the exception itself, and wrapping `TaskApp(day).run()`
in `main()` never sees it either — Textual only re-raises `_exception` under
`run_test`. Overriding `_fatal_error()` instead would miss any exception
carrying a `__rich__` method, which `_handle_exception` routes to `panic()`.

It is private API. That is the cost, and the mitigation is a check rather
than a comment: a stub suite asserts the method exists on `App` and that the
override is reached, so a Textual upgrade that renames it fails a test
instead of silently never writing another crash file. This is the same
discipline the project already records for names that collide with Textual's
own — here the name is meant to collide, and the check is that it still does.

### The traceback is found, not assumed — and this was wrong first time

The plan said: build from the exception argument rather than from
`sys.exc_info()`, because the failure was raised on a worker thread and
handed over as an object. Implementing it produced a **69-byte file** naming
`WorkerFailed` and nothing else, while Textual's own stderr dump had the
whole chain. Both halves of the reasoning were wrong:

- `WorkerFailed(self._error)` is *constructed*, never raised, so
  `error.__traceback__` is `None`. There are no frames on the object at all,
  and it does not chain to the original either — it holds it in `args`.
- `sys.exc_info()` is *not* empty at that point. `_handle_exception` is
  called from inside `Worker._run`'s `except Exception as error:` block, so
  the live exception is the original, with all its frames. That is exactly
  where Textual's render gets them, and why today's hand-saved file has both
  halves.

So the writer looks for frames in order: the argument if it has a traceback,
then whatever is currently being handled, then any exception the argument was
constructed around (`args`) — the last covering a call from outside an
`except` block, which is how a suite calls it. When the rendered exception is
not the one handed over, the file opens with a line naming the wrapper, so it
cannot silently be about a different failure from the one the log line names.

Textual's own parameters are kept: `show_locals=True`, `width=None`,
`locals_max_length=5`, `suppress=[rich]`. The file is then what the terminal
would have shown, which is the property that makes it useful to compare
against a hand-saved one like today's. Rendered through a `rich.Console`
pointed at the file with colour off, so the file is greppable rather than
full of escape sequences.

Textual's own parameters are kept: `show_locals=True`, `width=None`,
`locals_max_length=5`, `suppress=[rich]`. The file is then what the terminal
would have shown, which is the property that makes it useful to compare
against a hand-saved one like today's. Rendered through a `rich.Console`
pointed at the file with colour off, so the file is greppable rather than
full of escape sequences.

### The crash writer lives in `journal.py` and derives its directory from `journal.PATH`

Two reasons, both about not having to remember something later. The
best-effort discipline — never raise, never report itself — is already
written and tested there. And `tests/harness.py` already repoints
`journal.PATH`, so a crash file deriving its directory from it is withheld
from every suite for free; a second module with a second path constant would
be a second thing to redirect and a second way for a suite to write into the
real `logs/`.

### The operations log gets a line naming the crash file, carrying the exception's type and not its message

So that the durable, routinely-read log points at the crash rather than
falling silent — which is exactly what it did today. The type, not the
message: the log's content rule says no subject, no sender, no body, and
while `abort`'s message is safe (`command: EXAMINE => socket error: EOF`), an
arbitrary exception's message is not — a `KeyError` on a subject line would
put that subject straight into the file that promises not to hold one. The
crash file is where the message belongs.

### The file is named `crash-<UTC timestamp>.txt`, with a counter only on collision

UTC to second resolution, matching the journal's stamps, so the two read
together and the names sort by when they happened. Two crashes inside one
second is not a real scenario, but the requirement says one file never
overwrites another, so the writer takes the next free suffix rather than
trusting that.

## Risks / Trade-offs

- **A framework hook's argument is not necessarily the failure** — proven
  once already, above → the writer searches three places for frames and
  labels the file when the two differ, and a suite drives a wrapper
  constructed around a real exception, outside any `except` block, asserting
  the frames and a held value come through. Any future framework that wraps
  differently fails that case.
- **Overriding private Textual API** → a stub suite asserts
  `App._handle_exception` exists and that the override runs; a rename breaks a
  test, not a user's ability to diagnose a crash. The Textual version this was
  built against is recorded in the task notes.
- **The crash file holds real message text** → `logs/` is already excluded
  from commits, and the spec makes that exclusion the condition on the
  content rather than a habit. A suite asserts the crash file's directory is
  ignored by git. Accepted deliberately: today's crash was diagnosable from
  the frames alone, but a file that turns out to be missing the one value
  needed cannot be re-run.
- **Rendering locals can itself raise** — a `__repr__` that throws, a
  structure that recurses → the writer falls back to
  `traceback.format_exception` without locals, and if that fails too it writes
  nothing. It must never become the reason a session ends worse than it was
  already ending.
- **Crash files accumulate, ~200 KB each** → accepted, no rotation. They are
  rare, they are the evidence, and a board that deletes its own crash reports
  to save space would be deleting the thing this change exists to produce.
  Worth revisiting only if a crash loop makes them frequent.
- **Converting `OSError` could swallow an unrelated bug** — a file operation
  or a subprocess failure in the same method would become
  `GatewayUnreachable` and be reported as the mailbox's fault → the helper
  wraps the single imaplib call, never a method body, so only the protocol
  round trip is inside it.
- **A dropped line now leaves the row back on the board while some of its
  messages are archived** → already the specified behaviour, already
  self-healing once the mirror catches up, and better than the alternative:
  un-archiving confirmed messages to make the report tidy is the one thing
  that loses mail. Named in the spec so it reads as a decision.
- **The messages archived before a drop are never marked read** — `mark_seen`
  comes last of all, so a failed review leaves them in the archive unread and
  no record says which → unchanged by this design, and the crash file is now
  the record. Ticking the row again reports them already reviewed, which is
  the existing path.
