## 1. Knowing which tasks are green

- [x] 1.1 Add a loader for the configured tag identifier beside the one for the work project, and verify absent and blank both read as "not configured" rather than as an error
- [x] 1.2 Give a task a way to say whether it carries a given tag, tolerating a task whose payload has no tags at all, and verify with a tagged task, an untagged one, and a tracker row
- [x] 1.3 Read the configured tag back at startup and confirm what it resolves to, and verify against the real tag that the title it reports is the configured one

## 2. Where green sits in the order

- [x] 2.1 Insert the tag as the second key in `sort_key`, above the past-due one, and verify a marked task due today is ordered above an unmarked task long past due
- [x] 2.2 Verify a finished marked task still sinks below the unfinished unmarked ones
- [x] 2.3 Verify past-due tasks now form two runs, each ordered by how overdue its tasks are, and that untagged days are ordered exactly as before
- [x] 2.4 Verify the dateless views order marked tasks above pinned ones, and are otherwise unchanged
- [x] 2.5 Verify `group_key` picked the new key up with no edit of its own, by checking a move cannot carry an unmarked task above a marked one

## 3. The rail

- [x] 3.1 Add the margin column carrying `║` for a marked task and nothing for any other row, and verify a mixed view marks exactly the marked tasks
- [x] 3.2 Verify adjacent marked tasks produce a continuous bar, and that the rail appears on calendar days, in the inbox and in the someday view
- [x] 3.3 Verify no row prints the tag's name and that nothing about the mark depends on colour
- [x] 3.4 Verify the columns still fit and no other column lost room it needed, by rendering a day with the longest labels the board produces

## 4. The key

- [x] 4.1 Bind `g` to toggle the tag on the selected task, through the same write funnel every other action uses, and verify one press marks and a second unmarks
- [x] 4.2 Preserve any other tags the task carries, since the array is replaced whole, and verify with a task carrying a second unrelated tag
- [x] 4.3 Verify the write is optimistic: the rail appears before the API answers, and the view is not refetched
- [x] 4.4 Verify marking is undoable and is not confirmed, and that this leaves the existing rule intact that exactly the irreversible actions are the confirmed ones
- [x] 4.5 Refuse the key on a tracker row with the reason the board already gives, and verify nothing is written
- [x] 4.6 Say so when no tag is configured rather than doing nothing, and verify with the tag unset
- [x] 4.7 Verify `g` answers in a Russian layout as every other key does

## 5. The count

- [x] 5.1 Report how many marked tasks a view holds, beside the counts already reported, and verify none of the existing counts is replaced or altered
- [x] 5.2 Verify a view with no marked task reports no count for them

## 6. The clearing hazard

- [x] 6.2 Hold a removal back until it can be relied on when it follows a recent tag write to the same task, and verify a task marked and then unmarked ends unmarked where the tasks are kept, over several trials
- [x] 6.4 Read a removal back and send it again when the tag is still there, since waiting proved very good but not certain, and verify over ten live trials that every mark-then-unmark pair ends unmarked
- [x] 6.3 Verify a removal that follows no recent tag write is sent at once, and that the board never waits with a held-back write: the rail goes immediately, keys still answer, and the write is reported in flight
- [x] 6.1 Verify against the live API that pressing the key twice in quick succession leaves the task unmarked, since clearing was seen not to land when one task was patched repeatedly; if the per-task write queue does not already prevent this, pause and report rather than working around it silently

## 7. Verification

- [x] 7.1 Write a suite covering the ordering, the rail, the toggle, the count and the unconfigured case against synthetic tasks, and verify it passes
- [x] 7.2 Verify against the live board using a synthetic task of your own, marking and unmarking it and confirming the tag really changed upstream, deleting it afterwards
- [x] 7.3 Confirm no regression: run the existing suites, updating only those that assert an ordering the tag now changes, and verify today, the inbox and the someday view show the same tasks and counts as captures taken beforehand
