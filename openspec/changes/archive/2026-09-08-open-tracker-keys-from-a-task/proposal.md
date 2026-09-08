## Why

A task naming one of the tracker's own issues — a project key and a number —
is about that issue, and the board knows where the tracker lives: it already
builds `{base_url}/issue/{key}` for the rows in the tracker block. But a *task* mentioning an issue is inert: the key is text, and
opening it means selecting it by eye, copying it, and finding the browser.

Two smaller things sit alongside it and are worth fixing in the same breath,
because all three are the same question — *what can this row open?*

A link in a task's **note** is unreachable. `o` reads the title and nothing
else. Notes became editable only recently, and a note is exactly where an
address gets pasted, so the blind spot is about to matter.

A task with **several** addresses silently opens the first, and there is no
way to reach the others. Measured over 204 tasks, no task carries more than
one *distinct* address today: the three that looked as though they did hold
the same address twice, once inside an anchor and once as its visible text,
or simply written out twice. So this part is a correctness rule with no
present case rather than a fix for something observed — worth saying plainly.

## What Changes

- A task mentioning an issue in one of the configured tracker projects offers
  that issue's page as something to open. The projects are the ones already
  configured for the tracker block; no new setting.
- Only those project keys are recognised, so text like `GPT-4`, `COVID-19` or
  `ISO-8601` can never be mistaken for an issue. Measured: an unconstrained
  pattern would have found no false positives in 515 tasks either, but the
  constraint costs nothing and removes the class of mistake.
- Both a task's title and its note are read for things to open, and the same
  rule applies to each kind of candidate. Anything else would mean an issue
  key in a note is openable while an address in a note is not.
- Where a task offers **more than one** thing to open, the board asks which,
  in the order they appear — title first, then note. One candidate opens
  directly, as now; none says the task has no link, as now.
- **Nothing that works today behaves differently.** No task on this account
  has an address in its note but not its title, so reading notes adds reach
  without changing an answer; and no task offers more than one distinct thing,
  so nothing that opens silently today starts asking. Measured, not assumed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement added — choosing among several things a task
  can open. Three modified — what is recognised as a task's link (widened from
  a title to a title and a note, and to tracker keys), opening a task's link
  (which now may present a choice), and the restriction on schemes (whose list
  of "ordinary text that reaches the opener" gains a task's note).

## Impact

- `tracker.py` — the address of an issue named by key, beside the address of
  an issue the tracker reported. It already knows how to build one.
- `singularity.py` — finding every openable address in a piece of text, beside
  the existing "find the first".
- `main.py` — collecting a task's candidates, the chooser screen, and the
  action that opens a link learning to ask.
- No new dependency and no new configuration. The tracker's project list is
  already read for the block's own query.
