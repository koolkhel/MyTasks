## 1. Naming the tab

- [x] 1.1 Add a constant holding the name and the three escape sequences, documented with what each does, and verify by reading the source that no terminal is named in it
- [x] 1.2 At the entry point, remember the current title and set the board's own before the board starts, and verify against a real terminal that the tab takes the name
- [x] 1.3 Restore the previous title after the board stops, in a `finally` so that failing restores it too, and verify the tab returns to exactly what it showed before rather than to a blank

## 2. Leaving other runs alone

- [x] 2.1 Write nothing when the board's output is not a terminal, and verify a redirected run's output contains no escape byte
- [x] 2.2 Verify the command-line listing is untouched, since it runs from another entry point
- [x] 2.3 Verify a terminal that ignores the sequences neither breaks the board nor prints them, by running with the sequences going somewhere that cannot interpret them

## 3. What this must not disturb

- [x] 3.1 Verify the board still starts, draws and quits as before, and that its exit status is unchanged for both a clean quit and a failure
- [x] 3.2 Verify the name does not change as tasks are ticked, added, reordered or the view is switched
- [x] 3.3 Verify the title survives the board entering and leaving the alternate screen, which is where it draws

## 4. Verification

- [x] 4.1 Write a suite covering the sequences emitted, the tty guard, and restoration on both a clean exit and a raised error, and verify it passes
- [x] 4.2 Verify against a real terminal, reading the tab title back at each stage rather than by eye: before, while running, and after quitting
- [x] 4.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand
