## 1. What the requirement now claims

- [x] 1.1 Verify against synthetic rows that an all-day event leads a day holding past-due tasks, and is above every one of them
- [x] 1.2 Verify an all-day event leads the day's own untimed tasks, and that the two kinds are not mixed together
- [x] 1.3 Verify an all-day event leads the tracker block
- [x] 1.4 Verify several all-day events all lead the day and keep a stable order among themselves across repaints
- [x] 1.5 Verify a timed event is unaffected by all of the above, so the placement settled earlier still holds

## 2. Verification

- [x] 2.1 Add the checks to the calendar suite and verify it passes, with no change to any source file
- [x] 2.2 Verify against the real board, reading kinds and times only, that today's all-day event leads every row
- [x] 2.3 Confirm no regression: run the existing suites and verify the failing set is unchanged, since this change alters no behaviour
