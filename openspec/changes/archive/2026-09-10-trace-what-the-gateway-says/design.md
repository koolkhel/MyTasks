## Context

See proposal.md — Why, and its measurements. The code facts:

- `Server._talk(command, call)` is the single place every request passes
  through. Five call sites, one per verb the board issues, and each already
  holds what is worth recording: `_select` has the folder and whether it is
  readonly, `present` and `mark_seen` have the folder and a count, `move` has
  the folder, a count and the target, `_number_here` has the folder and the
  message identity.
- Two requests do not pass through it: `login`, in `Server.__enter__`, and
  `logout`, in `__exit__`. Both are already converted there, more broadly than
  `_talk` converts, which is why the previous change left them alone.
- `journal.py` writes the log and the crash file, is stdlib-only, and resolves
  its directory from a module-level `PATH` that `tests/harness.py` repoints —
  which is how crash files are withheld from every suite without the suites
  knowing they exist.
- `gateway.py` imports nothing from this repository today.
- Both mailbox workers hold `_mail_gate` for the length of an operation, so
  only one operation talks to the account at a time.

## Goals / Non-Goals

**Goals:**

- A person reading one file can say which request a session died on and how
  the account was behaving before it.
- Recording that cannot be forgotten, switched off, or made to hold something
  it should not.

**Non-Goals:**

- The protocol lines themselves. See the decision below: they answer nothing
  extra and carry the one secret worth keeping out.
- Timing the connection's setup. Measured at 0.58 s against a single request
  measured near ten seconds; not worth reaching for, and reaching for it is
  what would put a password in scope.
- Rotating or capping. A file a day, removed by hand. Deciding for somebody
  when their own diagnostic history stops being useful is not this change's
  business.
- Fixing the repeated folder selects the trace will make obvious. Its own
  change, and better argued once there are numbers.
- Reading the trace from the board, or showing it. Nothing reads it.

## Decisions

### `_talk`, not `imaplib`'s own tracing

`imaplib` routes its debug output through `_mesg`, an instance method, so a
subclass could capture every protocol line without touching a call site. It is
the more obvious seam and the wrong one:

- **It sees the password.** `_mesg` is called for the LOGIN line. `_talk` is
  not, login being outside it — so a trace built on `_talk` cannot contain a
  credential, rather than containing one that is then masked. A masking rule is
  a thing to get right; not being on the path is not.
- **It answers nothing extra.** Each of the four questions the crash left open
  — which message it died on, whether the gateway was degrading, whether the
  socket had been idle, what the repeated selects cost — is answered by a
  command name, a duration and an order. Response lines add volume.
- **It hands back strings to parse.** `_talk` already has the command as a
  name and the outcome as either a return or an exception.

### The line is written where the request is, and `gateway.py` imports `journal`

`_talk` times `call()` and writes one line. That makes `gateway.py` depend on
a module in this repository, which it does not today.

Considered instead: a `trace=` callable passed in beside `connect=` and
`stop=`, keeping the gateway free of local imports. Rejected because it makes
always-on a caller's obligation, and "always on" is the whole requirement — a
gateway used directly, as the live suites use it, would trace nothing, and the
next caller would have to remember. The requirement says the fault cannot be
reproduced on demand; a trace that depends on being wired up is off exactly
when it is wanted.

The module's own note about being copied rather than imported concerns a
*sibling repository* — a path dependency that would stop this repo working from
a fresh clone. `journal` is in this repo and imports only the standard library,
so that reasoning does not reach it.

### A file a day, its directory taken from the log's

The trace is written to `imap-<date>.log` in the directory `journal.PATH`
names. Two things follow for free: `logs/` is already excluded from commits,
and the suites' existing redirection of `journal.PATH` withholds the trace from
every suite without any suite being changed — the same property the crash file
was given for the same reason.

The date is the day at the moment of writing, in the same UTC the log stamps
use. An operation running across midnight writes into both days, which is
honest and is what a reader looking for "the night it broke" wants.

### One line per request, and what is on it

When, the command, the folder, how many messages or which one, how long, and
how it ended. Enough to answer the four questions and nothing whose meaning
has to be interpreted.

The identity goes on a search, because "which of the seven did it die on" was
one of the four questions and a search is per message. The log beside it
already records identities and is already specified to, so this is consistent
rather than new ground; what neither may hold is a subject or a sender, and
neither can, because no request asks for one.

`_talk` does not summarise the response. Whether a search found anything is
already in the operation's own line in the log, and teaching `_talk` each
command's response shape would put parsing in the one function that currently
has none.

### No lock

Reviews and undos both hold `_mail_gate` for the length of an operation, so
requests are serialised and their lines cannot interleave. Appending with the
log's existing best-effort write needs nothing added.

## Risks / Trade-offs

- **~470 KiB a day of use, unbounded across days** → a file a day makes the
  growth legible and removable, and the alternative — capping one file — can
  push the beginning of a long fault out of the only record of it. The user
  chose the per-day form for that reason.
- **A file append per request could slow a review** → twelve appends against a
  review measured at 13 to 120 seconds of network. Below noise, and the suites
  measure the request count so a regression in what is *asked of the account*
  would show up as a changed count rather than a changed duration.
- **`gateway.py` gains a local import** → it stays importable on its own —
  `journal` is stdlib-only — and the alternative traded a real requirement for
  a stylistic one.
- **A future verb that fetches a body would break the structural promise** →
  the promise is worth stating in the spec precisely so that adding such a verb
  has to reckon with it. The suites assert the absence, so it fails rather than
  drifts.
- **The trace will show the repeated archive selects and nothing will happen**
  → possible, and still better than not knowing. Named as a non-goal so the
  next change can be about that alone.
