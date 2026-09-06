## Why

One tag in the tracker's account, "Зеленая", separates the tasks that are a
person's own development from the job workload around them. The board cannot
see it: it never reads a task's tags, offers no way to set one, and orders
every task the same whether it carries the tag or not. So the distinction
exists in the data and nowhere on the screen, and the reason for making it —
putting personal work ahead of the job — has no effect at all.

The board already has the negative half of this axis: `w` hides the work
project. What is missing is the positive half, which says what to look at
rather than what to stop looking at.

## What Changes

- `g` toggles the tag on the selected task: pressed once it marks, pressed
  again it unmarks. The tag record upstream carries a hotkey of its own; the
  board ignores it and binds `g` like any other key.
- A tagged task carries a rail in the left margin. Where tagged tasks are
  adjacent the rail is continuous, so a run of them reads as one block rather
  than as several marks. No colour is used to distinguish them, and the
  colour the tag itself carries is deliberately ignored.
- Tagged tasks sort ahead of everything else the board manages, in every
  view, above the past-due band rather than within it. **BREAKING** for how a
  day reads: a task that is badly overdue now sits below a tagged task that
  is not yet due. That is the point of the tag, but it is a change to an
  ordering people rely on.
- The board reports how many tagged tasks a view holds, beside the counts it
  already reports.
- The tag is named in the environment by id, and the board confirms what that
  id resolves to rather than trusting it.
- Taking the mark off a task marked moments earlier waits a little before it
  is sent. The store accepts such a write and then does not apply it, so
  without the wait the board would show a task unmarked while it was still
  marked. The write is then read back and sent again if it did not take,
  because waiting makes the failure rare rather than impossible. The row
  loses its rail at once either way, and nothing else waits.

The tracker block is unaffected: it stays above everything, as a requirement
already fixed. Tagging is available wherever a task is selected.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: gains requirements for toggling the tag, for the rail that
  marks a tagged task, for tagged tasks sorting first, for the count, and for
  how the tag is configured and verified. One existing requirement changes:
  `Past-due tasks are ordered by how overdue they are` currently says they are
  ordered among themselves by how overdue they are, which stops being true
  when tagged tasks are lifted above the band — they still are, but in two
  runs rather than one.

## Impact

- `singularity.py`: `sort_key` gains a key above the past-due one; a task
  gains a way to say whether it carries a given tag; a loader for the
  configured tag id, beside the one for the work project.
- `main.py`: a binding whose key comes from the tag, a write that funnels
  through the existing one, a column for the rail, the count in the status
  line, and the startup lookup that confirms the tag.
- `.env`: one new entry naming the tag id. No token change: the tag is
  readable by id even though listing tags is not permitted.
- Undo, the work filter, the tracker block and manual ordering are all
  reached but not redesigned — the tag becomes another ordering key, and
  `group_key` follows it without a second edit.
