## 1. Rename the bucket in the client

- [x] 1.1 Rename the bucket enum member and its label from never to someday, leaving its `deferred` mapping untouched; verify the someday member reports `deferred` true and the inbox member false, that the two compare distinctly and neither equals a `date`, and that `import singularity` succeeds.
- [x] 1.2 Confirm the rename changes no query: verify the someday bucket returns exactly the same task ids as the never bucket did — the count and membership must be identical, every row undated and deferred — since only the name is changing.

## 2. Rename it on the board

- [x] 2.1 Move the view from the `n` key to `s` and rename its action; verify `s` shows the someday view, that `n` is now unbound and does nothing at all, and that `i`, `t`, and day movement are unaffected.
- [x] 2.2 Change the date-picker option from `n`/Never to `s`/Someday; verify the picker lists Someday and no longer offers Never, that choosing it leaves a synthetic task at `start=None, deferred=true`, and that the other four choices still return their own values. Run this on a far-future day holding no real tasks, selecting by task id before each press.
- [x] 2.3 Update the header label and the day-navigation message; verify the header reads as Someday with no date, that asking for the previous or next day there reports that someday has no days, and that the inbox and calendar-day headers are unchanged.
- [x] 2.4 Update the help overlay and confirm the footer; verify the overlay names someday, contains no mention of never, still opens and closes, and that the footer entry reads Someday while its other entries are unchanged.

## 3. Verify end to end

- [x] 3.1 Confirm no stored data changed: snapshot the two tasks in the bucket before and after and verify every field is identical, and that loading and switching between all views issues no POST, PATCH, or DELETE.
- [x] 3.2 Confirm nothing else regressed: the inbox still reports its shown and filed counts, today still gathers past-due tasks with their ages, enter still opens the focus card without ticking, space still ticks, and backspace still asks before deleting — the last three on a far-future day holding no real tasks.
- [x] 3.3 Search both source files for residual never/NEVER and confirm each remaining occurrence is deliberate — the dated-or-deferred invariant wording and the write-invariant comments use the word as an adverb; no bucket, binding, label, action, or help text may still say never.
