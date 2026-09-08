## 1. Whether an event has ended

- [x] 1.1 Ask an event whether it has ended, against an instant given to it, and verify an event whose end has passed says yes while one under way and one still to come say no
- [x] 1.2 Verify the boundary is the end and not the start, by an event that began before the instant and ends after it
- [x] 1.3 Verify an all-day event answers sensibly for a day already past, the day itself, and a day still ahead

## 2. Drawing it

- [x] 2.1 Draw a row receded when its event has ended, using the attribute measured to survive the row cursor rather than a colour, and verify a drawn row carries it
- [x] 2.2 Verify the row keeps its mark, its start time, its name and its calendar, and is neither hidden nor struck out
- [x] 2.3 Verify an event that has ended is still distinguishable from one still to come while it is the selected row
- [x] 2.4 Verify a task's row is drawn exactly as before, and that a past-due task's own colour is untouched

## 3. Which day, and which instant

- [x] 3.1 Judge against the current time rather than the fetched instant, and verify it works on a day that carries no reference at all
- [x] 3.2 Verify every event on a day earlier than today reads as past, and none on a day later than today does
- [x] 3.3 Verify a day holding events on both sides of the current time shows exactly the ended ones receded

## 4. Keeping up

- [x] 4.1 Redraw when the number of shown events that have ended changes, and verify a row becomes receded once its end passes, without the day being fetched again
- [x] 4.2 Verify nothing is redrawn while that number is unchanged, and that the selected row and the cursor stay where they were
- [x] 4.3 Verify the check fetches nothing, on any view — including the inbox and someday, which hold no events

## 5. The clock

- [x] 5.1 Show the current time at the right of the header, to the minute, using the framework's own clock, and verify it is present and reads as hours and minutes
- [x] 5.2 Verify the clock advancing redraws no row and moves neither the selected row nor the cursor
- [x] 5.3 Verify the header still shows what it showed before, and that both bundled themes draw the clock legibly

## 6. Saying so

- [x] 6.1 Add a line to the help overlay explaining that an event which has ended is shown receded and that the clock is the current time, and verify the overlay reads correctly and names no Cyrillic key

## 7. Verification

- [x] 7.1 Write a suite covering the boundary, the three positions in time, the selected row, the days on either side, the redraw when the set changes and the stillness when it does not, and the clock — against synthetic events — and verify it passes
- [x] 7.2 Verify against the real board, reading kinds and times only, that today's events which have ended are receded and the rest are not
- [x] 7.3 Confirm no regression: take a fresh baseline first, then run the existing suites and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite passing today still passes
