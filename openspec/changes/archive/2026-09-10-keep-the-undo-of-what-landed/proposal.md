## Why

An action can take several writes — moving a task respaces its run, one write
per task. Where one of those writes is refused, the board decides then and
there whether the action left anything worth undoing. It cannot know: the
action's other writes are still in flight.

    refusal settles first  ->  0 undo entries left  (LOST)
    refusal settles last   ->  1 undo entry left    (kept)

Nothing but timing separates those two, and the probe left behind for it
reproduces both on demand.

The consequence is worse than losing the entry. When the refusal settles
first, the entry is dropped; the action's other writes then land and run
`applied += 1` against a list that no longer holds it, so the increments go
nowhere. Three writes succeed, the board shows their effect, and the undo key
cannot reach them. Silently — nothing says so.

`forget()`'s own docstring states the intended rule: *the entry goes only when
nothing of it was applied*, because *a single refusal among five would
otherwise throw away the ability to undo the four that landed*. The rule is
right. It is asked at the wrong moment.

And it is nowhere in the spec. Two requirements come close and neither
forbids this: one says a refused write SHALL NOT be reachable, which is true
before and after — the bug is about the *successful* writes becoming
unreachable; the other says only the refused write's effect is undone and the
others stand, which they do, on screen. What is lost is the ability to undo
them, and no requirement covers it. That is why a race could break the rule
with no check to hang on.

## What Changes

- The decision moves to when it can be answered: an action's entry is dropped
  only once every write in it has settled, and only if none of them was
  applied. Where a refusal arrives with the action's other writes still in
  flight, nothing is decided yet.
- No new state is kept. Whether an action still has writes outstanding is
  counted from the queues that hold them, the way the board already counts its
  writes in flight for the status line.
- Only the refusal path changes. A confirmed write cannot cause a drop, having
  just applied something, so it is left alone.
- The rule goes into the spec: an action of which anything landed stays
  reachable by the undo key, and the outcome SHALL NOT depend on the order in
  which the action's writes settle.
- The probe becomes a suite. It was written asserting nothing, because at the
  time the two orderings disagreed and there was no right answer to state.
  After this they agree, so the forced-ordering cases move in beside the check
  they explain and the probe goes.

## Capabilities

### Modified Capabilities

- `task-board`: *Undoing reaches back, and never turns round* already says what
  the undo key cannot reach — a write the API refused. It gains what it can:
  an action of which any write landed, however many of its other writes were
  refused, and regardless of the order the answers came back in.

### New Capabilities

None.

## Impact

- `main.py` — the refusal path and the function it calls to drop an entry.
  Nothing else: not the queues, not the drain, not what a refusal reports.
- `tests/stub/t_undo1.py` — gains the two forced orderings, beside the check
  that has been failing about one run in five under a loaded tier.
- `tests/probes/t_race.py` — removed, its question now having an answer.
- `tests/known_failures.py` — the `t_undo1` entry goes. It records a product
  race, and the race is what this removes.
- No change to what a person sees when a write is refused, except that the
  undo key now reaches what the action managed to write.

## What was measured

- The probe, run just now: the refusal forced to settle first leaves no undo
  entry; forced to settle last, one. The scenario is one action writing four
  rows with one of them refused.
- `t_undo1`'s entry in the known-failure list records it failing about one run
  in five under a loaded tier and none in five alone, with exactly one failing
  check — which is what a race that depends on scheduling looks like.
- Both settle paths reach the board through `call_from_thread`, so they run on
  the same thread that queues the writes. An action therefore always has all
  of its writes queued before any of them can settle, which is what makes
  counting them a sound test for "the last one".
