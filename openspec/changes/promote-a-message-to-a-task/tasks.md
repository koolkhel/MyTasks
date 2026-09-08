## 1. Turning a thread into a task

- [ ] 1.1 Add the key that promotes the selected mail thread, creating a task on today titled from what the thread is about, through the path that already adds a task — and verify the created task's title, date and all-day flag match what adding a task produces
- [ ] 1.2 Verify the stored order is past everything the day holds, so a promoted task joins the end of the day's sequence rather than disturbing it
- [ ] 1.3 Verify the task is on screen before the store has answered, by holding the write open
- [ ] 1.4 Verify undo removes it and says what it reversed
- [ ] 1.5 Verify a refusal from the store is reported and leaves no task on screen that does not exist

## 2. What the task carries

- [ ] 2.1 Write the thread's address and the identity of the message it came from into the created task's note, in the form the board already writes notes, and verify the note reads back as written
- [ ] 2.2 Verify the key that opens a task's link opens what the thread pointed at, through the note
- [ ] 2.3 Verify a thread pointing at nothing still creates a task, with a note carrying the identity alone
- [ ] 2.4 Verify the note can be edited afterwards by the key that edits a note, and that a subject holding markup-like characters is drawn as its own characters in the created task
- [ ] 2.5 Verify the address chosen is the thread's newest message's, matching what the mail row itself offers

## 3. What promoting does not do

- [ ] 3.1 Verify the mailbox is untouched by a promotion: no flag set, no message moved, renamed, removed or marked read — compared file by file before and after
- [ ] 3.2 Verify the thread is still shown in the mail view afterwards, unchanged
- [ ] 3.3 Verify promoting the same thread twice creates two tasks, and that the board wrote no record of the first anywhere on disk
- [ ] 3.4 Verify the key creates nothing on a task, a calendar event or a tracker issue, and says what it is for

## 4. Saying so

- [ ] 4.1 Add the key to the help overlay and the key bar, explaining that it turns a mail thread into a task on today, and verify both list it and that the overlay names no Cyrillic key

## 5. Verification

- [ ] 5.1 Write a suite covering the creation and its fields, the note's contents, opening through it, the empty case, both refusals, and the mailbox being untouched — against a synthetic maildir and a stubbed store — and verify it passes
- [ ] 5.2 Verify against the live store with a thread from the sample maildir that a promoted task reads back with its note intact and is then deleted, leaving nothing behind
- [ ] 5.3 Confirm no regression: take a fresh baseline first, then run the existing suites and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite passing today still passes
