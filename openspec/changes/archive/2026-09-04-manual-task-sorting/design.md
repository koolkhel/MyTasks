## Context

See proposal.md — Why for the motivation and what was established against the
live API.

The facts that shape the approach, each confirmed rather than assumed:

- `scheduleOrder` is an integer on every task, writable on create and on
  PATCH. Verified: created with 5000 it stored 5000; patched from 0 to 12345
  it stored 12345.
- **It is integers only.** Sending 12345.5 stored 12345. Fractional
  midpoint insertion is therefore not available, which rules out the usual
  "order between two neighbours" trick as a general mechanism.
- The list endpoint does not sort by it. Five tasks created with orders
  9000/3000/6000 came back in none of those sequences, so ordering stays the
  client's job — as it already is.
- It does not track time. Two of today's timed tasks sort 18:00 before 08:00
  by `scheduleOrder`, which is why it can only ever be the last key.
- Every task the board creates today is stored with `scheduleOrder` 0. Three
  created in a row all read 0.
- `sort_for_display` already takes `now` as the switch that enables the
  past-due dimension (`singularity.py:794`), so it has a precedent for a
  parameter that turns one ordering key on for day views only.
- `Pending` records one `task_id` and one `patch` (`main.py:393`), which is
  all a one-write move needs.
- The API can fail transiently: a DELETE returned `HTTP 500 Sync error ...
  number in queue 2` during this investigation and succeeded on retry. Any
  multi-write scheme therefore has to survive one of its writes failing.
- `/v2/batch` executes its operations independently rather than as one
  transaction, confirmed with both a 404 and a 400 on the second operation
  while the first applied. It is one request, not one unit of work.

## Goals / Non-Goals

**Goals:**

- One ordering function serving both day and dateless views, so the two
  cannot drift.
- A move that is one write, so that it cannot be half applied.
- An invariant held by construction rather than by trusting the server.

**Non-Goals:**

- No global renumbering, no gap maintenance, and no migration of existing
  `scheduleOrder` values. Swapping never consumes numbering space, so the
  scheme needs none of that. The one exception is narrow and local: existing
  data contains tasks that share an order value, and two tied tasks cannot
  swap to any effect, so that case is repaired for the tied run alone. It is
  a repair for data that predates this change, not a maintenance pass the
  design depends on.
- No reordering across ordering groups. Lifting an all-day task above a timed
  one would mean lying about the time, and time is not a preference.
- No reordering in the dateless views, and no change to their ordering.

## Decisions

### Moving writes one task, not two

A move changes only the moved task's stored order, setting it to a value
between its destination neighbours. One write cannot half-apply, so "no two
tasks share a stored order" holds by construction rather than by relying on
anything the server promises.

This replaces an earlier decision to exchange the two tasks' values in a
single batch. That was written believing `/v2/batch` applied its operations
atomically. It does not — see below — and a swap needs two writes, so the
invariant would have depended on a guarantee that is not there.

The integer-only field is what made swapping attractive: exchanging values
consumes no numbering space. Insertion does consume it, but the space is
ample. Measured on today's real ordering groups, the gaps inside a group are
8684, 26052, 108 and 296 — every one with room to insert between rows, and
the two large groups with room for many.

Rejected: renumbering the whole day on each move. One request rather than
one write, but it rewrites every row to move one and destroys the sparse gaps
SingularityApp's own reordering left.

### `/v2/batch` is not atomic, and is not used

Verified against the live API twice, with different failure kinds:

    second op targets a deleted id    statuses [200, 404]   first op applied
    second op has an invalid body     statuses [200, 400]   first op applied

Operations execute independently, so a batch is one request, not one
transaction. It is also no faster for a pair — 1198 ms median against 1850 ms
for two sequential writes, both dominated by the server's sync queue and
varying between 184 ms and 4229 ms.

It is therefore not used at all. Its one remaining candidate was the
respacing below, but that is better as one write per task: the writes queue
per task and so drain concurrently, each shows on screen the moment it is
made, and each rolls back on its own if refused — none of which a single
batched request gives. Its `uuid` idempotency is real and was confirmed
(replaying an identical batch applied nothing a second time); the finding is
recorded here because it is the reason the move mechanism is what it is, not
because the endpoint is relied on.

### Renumbering, when it is needed, targets a range nothing occupies

Where the destination has no value available — the two tasks the moved one
must sit between hold adjacent integers — the run is first shifted into a
range above every stored order in the day, spaced by a fixed step, as one
write per task.

Choosing a disjoint range is what makes a partly-applied respacing safe: a
task that has moved to the new range cannot collide with one still holding
its old value, so even a respacing interrupted halfway leaves every order
distinct. That is what allows independent writes here rather than needing a
transaction nothing offers.

### The manual order is the last sort key, enabled per view

`sort_for_display` gains a parameter for whether the manual order applies,
mirroring how `now` already switches the past-due dimension on for today
alone. Day views pass it; the dateless views do not and keep the title as
their final key.

This keeps one function and one ordering rule set. The alternative, a second
sort function for days, would let the two orderings drift apart — which is
the failure the shared function exists to prevent.

Measured consequence of not scoping it: ordering the inbox by `scheduleOrder`
would move 24 of its 29 rows, and 27 of those rows carry 0, so they would end
up tied and fall back to the title regardless. The change would be visible
churn with no ordering gained.

### Which neighbour a task may trade with is derived, not enumerated

A move needs the adjacent task in the same ordering group. Rather than
re-deriving what "same group" means, the board compares the two tasks on
every sort key above the manual order. Equal on all of them means they may
trade; unequal anywhere means the boundary has been reached and the move
reports why.

Deriving it from the sort key rather than listing the conditions is what
keeps the rule true if the ordering above ever changes again — as it did last
change, when ticking began to reorder rows.

### A move needs no change to the pending-write model

A move is one write against one task, which is exactly what `Pending`
already records. The earlier design grew it to carry a pair, because a swap
touched two tasks and both halves had to be shown and taken back together.
Writing one task removes that need, and with it the risk that two pendings
on different task ids drain independently and leave a half-swapped view.

### A new task's order is chosen from the day already on screen

The board knows the day's tasks, so it sends one past the largest
`scheduleOrder` among them. No extra request, and the new task lands at the
end as specified.

Rejected: leaving the API's default of 0. Verified to put every added task at
the head of its group, tied with every other task the board ever added.

## Risks / Trade-offs

- **A swap between two tasks whose orders are equal does nothing** — this
  is not hypothetical: 43 of 100 sampled tasks share a value with another,
  and 27 of the 29 inbox tasks are all 0 → the board detects the tie and
  gives the moved task a value adjacent to its neighbour's instead, renumbering
  only the tied run when even that is taken. A move must never be a key that
  appears to do nothing.
- **The moved task's order is meaningless on another day** — `scheduleOrder`
  is global, so a task dated to a different day arrives with a position that
  means nothing there → accepted, and it is what the app itself does; the
  task simply lands somewhere in the new day's sequence and can be moved.
- **The app and the board can both reorder** — a position set on the phone
  and one set here race, last writer winning → accepted, unchanged from every
  other field the board writes; the optimistic layer already reconciles a
  write against what the server reports.
- **Insertion consumes numbering space where swapping did not** — repeated
  moves into the same gap eventually exhaust it → measured headroom is large
  (group gaps of 8684, 26052, 108, 296), and the renumbering path handles
  exhaustion when it comes; it is reached rarely rather than never.
- **Two more keys on an already full key bar** — the bar wraps to two rows
  and gained "clickable links" and "did today" recently → the existing
  requirement that no binding is hidden is what catches this, and it needs
  checking at a narrow width rather than assuming.
