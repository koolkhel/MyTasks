## 1. Where the block joins the day

- [x] 1.1 Place the block after every unfinished row and before the first finished or cancelled one, in place of putting it in front, and verify with synthetic tasks that it lands there on a day holding past-due, timed, untimed and finished tasks
- [x] 1.2 Verify the block ends the list on a day with nothing finished, and leads it on a day where every task is finished
- [x] 1.3 Verify no unfinished task of the day falls between the block and the tasks naming no time, so the block is adjacent to them

## 2. What must not change with it

- [x] 2.1 Verify the block keeps its own sequence — grouped by configured state, by key within a state — wherever it now sits
- [x] 2.2 Verify ticking a task moves that task below the block while the block keeps its place between the unfinished tasks and the finished ones, and its sequence
- [x] 2.3 Verify the tracked count, the hidden-work count and the work filter are unchanged, since all three are settled before placement
- [x] 2.4 Verify the day's own tasks are in exactly the order they would be with no block present
- [x] 2.5 Verify a tracker row still refuses every key that writes, still cannot be reordered, and still opens with the key that opens a link

## 3. Saying so

- [x] 3.1 Update the help overlay where it says the issues appear above the day's tasks, and verify the overlay reads correctly and still names no Cyrillic key

## 4. Verification

- [x] 4.1 Write a suite covering the placement, the two edge days, the block's own sequence, ticking across the block, and the day's own order — against synthetic tracker issues and tasks — and verify it passes
- [x] 4.2 Verify against the real board that today's block sits below the day's unfinished tasks, reading kinds and times only and never an issue's key or summary
- [x] 4.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks and counts as captures taken beforehand, with the tasks' own order identical and only the block's position differing
