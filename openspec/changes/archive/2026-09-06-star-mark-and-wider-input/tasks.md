## 1. The mark

- [x] 1.1 Replace the mark with an asterisk and rename the constant so it no longer says "rail", and verify a marked task's row carries it while an unmarked one carries nothing
- [x] 1.2 Verify the mark is one cell wide with no width caveat, by checking its Unicode width class rather than by eye
- [x] 1.3 Verify the mark still appears on a calendar day, in the inbox and in the someday view, and that a tracker row carries none
- [x] 1.4 Verify no row prints the tag's name and the mark cell carries the character alone, with no markup around it
- [x] 1.5 Verify the columns beside the mark still line up, by rendering a day holding the widest labels the board produces

## 2. The prompt

- [x] 2.1 Give the add-and-rename prompt a style rule of its own at a box width of 90, leaving the rule the other dialogues share untouched, and verify by measuring that the prompt is wider and each of the other five is exactly as wide as before
- [x] 2.2 Verify the text area inside the prompt grew from 50 cells to 78, measured rather than calculated
- [x] 2.3 Verify a title longer than the prompt is still accepted and returned whole, with only the view of it scrolling
- [x] 2.4 Verify a terminal narrower than the preferred width narrows the prompt to fit rather than overflowing, at several widths including one narrower than the prompt's old size

## 3. What this must not disturb

- [x] 3.1 Verify which tasks are marked, where they sort and how they are counted are all unchanged, with the tag configured and with it unset
- [x] 3.2 Verify adding and renaming still work end to end through the widened prompt, including a Russian title and the layout twins
- [x] 3.3 Verify the other five dialogues still open, answer and dismiss as they did

## 4. Verification

- [x] 4.1 Update the suites that assert the old mark and its joining — they assert a guarantee this change withdraws, so bring them to the new contract rather than changing the code back
- [x] 4.2 Write a suite covering the mark's identity and width, the prompt's width against the other dialogues, and the narrow-terminal case, and verify it passes
- [x] 4.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand
