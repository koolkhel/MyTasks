## 1. The widths

- [x] 1.1 Narrow the project column to 11 cells and verify the common project names still read in full
- [x] 1.2 Give the title column the width the others leave, floored at a readable minimum of 30, and verify the table fits the viewport at 65 columns and above and scrolls below it
- [x] 1.3 Verify the fixed cost is what the width is derived from rather than a guess: the other columns plus the table's own padding, measured rather than assumed

## 2. Shortening what does not fit

- [x] 2.1 Build the title cell as styled text shortened to the column's width with a visible mark, and verify a too-long title ends with that mark while one that fits is untouched
- [x] 2.2 Verify shortening keeps a title readable: a link still carries its address, a past-due title keeps its colour, a finished one keeps its strike, and no markup appears as text
- [x] 2.3 Shorten an over-long project name the same way, and verify the one project that no longer fits shows the mark rather than appearing to end where it was cut
- [x] 2.4 Verify a row still occupies exactly one line whatever the title's length

## 3. Following the terminal

- [x] 3.1 Recompute the widths from the terminal as it is now rather than as it was at startup, and verify a title shortened at one width is shown in full after the terminal is widened
- [x] 3.2 Verify narrowing the terminal shortens more, and that narrowing past the minimum leaves the minimum in place and lets the list scroll
- [x] 3.3 Verify the redraw on resize costs no fetch and no write

## 4. What this must not disturb

- [x] 4.1 Verify which tasks are shown, their order, the marks, the when-column and the counts are all unchanged
- [x] 4.2 Verify the focus view still shows the whole title, which is what makes a shortened row acceptable
- [x] 4.3 Verify opening a link from a row whose title was shortened still opens the right address

## 5. Verification

- [x] 5.1 Write a suite covering the width arithmetic, the shortening and its mark, the styling that must survive it, the resize path and the narrow-terminal floor, and verify it passes
- [x] 5.2 Verify against a rendered board rather than by reading values: capture the drawn rows at several terminal widths and check what a person would actually see
- [x] 5.3 Confirm no regression: run the existing suites, updating only those that assert the old column widths, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand
