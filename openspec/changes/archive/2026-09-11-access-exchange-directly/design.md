## Context

See proposal.md — Why, for the measurements this rests on.

What matters for the shape of the work:

- `gateway.py` already has the seam this needs. `Server(config, connect=None)`
  exists so that a suite can drive every path without a server, and
  `tests/fakeimap.py` uses it. The protocol lives behind that seam; the module's
  public names — `Server`, `numbers`, `present`, `move`, `mark_seen`, `number`,
  `holds`, `archive`, `restore`, `GatewayUnreachable`, `MoveFailed` — are what
  `main.py` knows, and none of them names a protocol.
- Every request already passes through one funnel, `Server._talk(command, call,
  about)`, which converts exceptions, times the call and writes the trace line.
  A protocol swap is a change of what `call` does, not of how failure or
  tracing works.
- The board's reads do not go through `gateway.py` at all. `mail.py` reads the
  mirrored maildir from disk. The two halves already have nothing in common but
  the folder names.
- The credential is fetched by a configured command at the moment it is needed,
  and deliberately stays outside the traced path so a password cannot be
  written to the trace.

## Goals / Non-Goals

**Goals**

- A review costs about a second rather than about ninety.
- The module's public surface, its two exceptions, its trace and its busy
  accounting are unchanged, so `main.py` and the board's behaviour are
  untouched apart from speed.
- The stub tier keeps its structure: a fake behind the existing seam.

**Non-Goals**

- Reading mail over the network. Measured and rejected: 0.87s from the mirror
  against 20–30s for the same set over the service. The mirror stays.
- Removing the sync tool or the local gateway. They fill the mirror and go on
  doing so. This change stops the board from *needing* the gateway; it does not
  uninstall anything.
- Calendar or contacts over the same service. The calendar comes from the
  system's own event store and is not part of this.
- Autodiscovery. The address is configured, as the gateway's was.

## Decisions

### The protocol changes behind `_talk`, and nothing above it

`_talk` is the only place a protocol error becomes one of this module's two
exceptions, and the only place a trace line is written. The swap replaces the
bodies of the methods that call it — a search becomes one restricted query
instead of a select and a search, a move becomes a request naming item
identities instead of a select and a copy — and leaves the funnel alone.

The trace's own vocabulary changes with it: the lines will name the requests
actually made. The requirement about the trace asks for "which command it was"
and is protocol-neutral, so the log keeps its promise with different words in
it.

Rejected: a second module beside `gateway.py`, choosing at run time. That is
the dual-path option, declined: it doubles the surface that the most expensive
test tier has to cover, and the board has no use for two answers to the same
question.

### The archive is found once and remembered by identity

The service names folders by an opaque identity, and finding the archive by
name costs a walk of the folder tree — measured at 1.36s to resolve all three
source folders and the archive together, and 4.18s when walking for one folder
alone. That is a per-session cost, not a per-review one: the identity is stable,
so it is resolved once when a `Server` is entered and used for every request
after.

This is the one place the new protocol has a cost the old one did not, and it
is why the resolution belongs in `__enter__` beside the login rather than in
each method.

### What a row costs, counted in requests

The old economy was counted in folder openings because opening was the
expensive thing. The new one is counted in requests, and a confirmation is one
query naming every identity in the row — so the property the spec cares about,
that a folded row costs no more than a single one, is kept by construction
rather than by careful ordering.

The measured search cost does not depend on the size of the folder: 0.42s
against a folder of 33 items, 0.96s against one of 20,821. So the archive stops
being the expensive half of a review.

### Configuration gains an address and keeps the credential command

The board needs the service's address where it needed a host and a port. The
credential keys keep their meaning but not their names: a key called
`MAIL_IMAP_USER` describing an account reached without IMAP is a lie of the
kind this repository does not leave lying around.

So: a new key for the address, new names for the identity and the credential
command, and the old names read as a fallback — an unedited configuration goes
on working, and nothing silently stops reviewing because a key was renamed. The
fallback is documented in the spec's own terms: the address is what decides
whether reviewing is configured at all.

### The fake moves to the same seam

`tests/fakeimap.py` answers a protocol; its replacement answers the new one at
the same seam, `Server(config, connect=...)`. `t_gateway.py` drives the board's
own vocabulary — review this row, undo that one, fail this request — so its 209
checks keep their shape and their names. Only the fake behind them is new.

The live tier is different: `t_gwlive.py` drives a real account and asserts on
what a real server did, so it is rewritten rather than adapted. Its discipline
does not change — a copy of the sample mailbox per run, tasks and messages named
`zz-`, everything deleted in a `finally`, counts printed and never content.

### One dependency, taken deliberately

The library brings 14 transitive dependencies, all available as wheels for the
Python this board runs, including a native XML parser and a cryptography stack.
The board has four dependencies today and `imaplib` is in the standard library,
so this is the change's real cost. It buys a protocol the account speaks
natively, and it removes the board's need for a translator it does not control.

## Risks / Trade-offs

- **A spike is not a review** → the numbers come from one session against one
  account: authentication, searches in two folders, a move, a mark-read, and a
  write on a message the spike created. A real review moves real messages in
  folders the spike only searched. The live tier is what turns the projection
  into a measurement, and it runs before this is believed.
- **The identity resolution could go stale** → a folder identity is stable, but
  a folder moved or recreated between runs would invalidate one held across a
  session. It is resolved per `Server`, which lasts one review, so the window
  is a single operation and a failure reports as the folder not being found.
- **Throughput is worse for bulk reads than the mirror** → measured, and the
  reason the read path is out of scope. If a cache is ever wanted, it is its own
  change with its own argument.
- **The trace's lines change shape** → anything reading old trace files by eye
  will see a different vocabulary. The trace is a diagnostic written for a
  person, not an interface, and the requirement asks only that each line name
  its command.
- **Two credential key names for a while** → the fallback is a kindness that
  costs a branch. It should be removed once the configuration is edited, and
  that removal is a task in this change rather than a promise.

## Migration Plan

The configuration gains the service address; the sync tool and the local
gateway are left installed and untouched, so falling back is reverting the
commit and changing nothing else. Nothing on disk or in the account is
rewritten by this change, and no message is touched that a review would not
have touched anyway.
