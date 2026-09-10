## Context

See proposal.md — Why, and its measurements. The code as it stands:

- `Server.numbers(folder, idents)` opens the folder once, readonly, then calls
  `_number_here` per identity. Exactly the shape the confirmation and the undo
  both want, and used today only for the source folder.
- `archive()`'s confirmation loops over `here` calling
  `srv.number(config.archive, ident)`, which opens the archive *and* searches
  it; then loops over `elsewhere` doing the same. So `n + 1` archive openings,
  the extra one being `mark_seen`'s.
- `restore()` loops one identity at a time: `srv.number(archive, ident)`,
  `srv.mark_seen(archive, [number], seen=False)`, `srv.move(archive,
  [number], folder)`. Three openings a message.
- `mark_seen` and `move` both take a list already, and `archive()` already
  calls each with one — `mark_seen(config.archive, arrived)` in one request
  for the whole row, and `move(folder, moved, config.archive)` likewise. So
  the batched forms are exercised against the real gateway on every review.
- `archive()` takes `stop` and asks it between messages; `restore()` does not
  take one at all.

## Goals / Non-Goals

**Goals:**

- The archive is opened a fixed number of times per operation.
- The give-up the board relies on survives, and gets finer.

**Non-Goals:**

- Fewer searches. One search a message is what this gateway supports; see the
  decision below.
- Making a single-message row faster. It is already at the minimum, and 387 of
  545 rows in this mailbox are single-message ones. This change is about the
  penalty that grows with a row, not about the common case.
- Touching `main.py`, the board's error handling, or what a review reports.
- Any change to what is confirmed. Both halves stay: absent from the folder it
  was in, present in the archive.

## Decisions

### Explicit reuse of `numbers()`, not an idempotent `_select`

The confirmation becomes one `numbers(config.archive, here + elsewhere)` call
whose result is partitioned, and `restore()` becomes one `numbers()` then one
`mark_seen()` then one `move()` per folder.

The tidier alternative was to have `_select` remember what is open and skip a
redundant opening. One small change, and it would fix paths nobody audited.
Declined:

- Its correctness rests on the server treating a selected mailbox as live
  rather than as a snapshot — that a search after a move sees the move without
  re-selecting. This is the server whose deviations the gateway's own source
  records, including answering an OR of eight identities with two matches. A
  cache underneath the confirmation, against that server, trades the one thing
  the confirmation exists to protect for a smaller diff.
- It would change behaviour on every path that selects, including ones this
  change has no reason to touch. The explicit version changes two call sites
  and each is a pattern with live runs behind it.

### One search a message stays

A single search naming the whole row would reduce the searches from `n` to
one. This gateway answers an OR of eight identities with two of the eight,
which is why the confirmation searches one at a time and is recorded in
`numbers()`'s own docstring. Re-stated here because the arithmetic makes it
tempting: after this change the searches are what remains of the cost, and
they are the part that cannot be reduced.

### `numbers()` gains a way to give up, and the granularity improves

The board is required to let an operation part way through give up cleanly
when it is forced to end, and that is the `stop` asked between messages in the
loop being replaced. So `numbers()` takes an optional `stop`, asked between
searches, and the confirmation passes the one it already has.

This is better than what it replaces, not merely equal: the check used to come
after an archive opening and a search, about fifteen seconds apart; it now
comes after a search, about one.

`restore()` does not take a `stop` today and does not gain one. Its cost after
this change is three openings and `n` searches, so the whole operation is
shorter than one of the openings it used to make per message.

### The undo's order: find, mark, move

Marking must come before moving. After a move the message is in another folder
with another number, so marking it afterwards would mean finding it again —
another search, and against a folder whose numbering has just changed.

That ordering is what makes all-or-nothing achievable: the failure window is
between one `STORE` and one `MOVE`, and the `MOVE` carries the whole row, so
either the row comes back or none of it does. Where the `STORE` fails, nothing
has moved. Where the `MOVE` fails, everything is unread in the archive, which
is the state the board reports and the person can retry from.

Rejected: moving first and marking in the target folder. It costs a second
search per message and puts the marking on the folder the board is otherwise
careful never to write to.

### The check that has to move

`tests/stub/t_trace.py` asserts eleven folder openings and eight archive
openings for a row of seven, with six of them called repetition. That is the
shape being removed, and the assertion moves to the new one — two archive
openings for any row. It was written as a check rather than a comment for this
exact moment.

## Risks / Trade-offs

- **A search after one opening might behave differently on this gateway than a
  search after its own opening** → this is the only genuinely new behaviour and
  the reason the live tier is not optional here. `numbers()` already does it
  against a source folder on every run; against the archive, and against
  messages moved in moments earlier, it is unproven. A live task asserts a
  folded row confirms correctly and that the trace shows two openings.
- **All-or-nothing means a failed undo restores nothing where it used to
  restore some** → chosen deliberately. A row split between a folder and the
  archive is the state hardest to reason about, and the board cannot describe
  it in one notice. Written into the spec so it reads as a decision.
- **The spec's measured figures will go stale again** → they are corrected
  here rather than left, and the board now writes a trace, so the next
  correction is a matter of reading the file rather than timing by hand.
- **Single-message rows gain nothing, so a person may not notice any
  difference** → true, and stated in the proposal rather than left for them to
  discover. The gain is on the 158 folded rows holding two thirds of the
  messages.
