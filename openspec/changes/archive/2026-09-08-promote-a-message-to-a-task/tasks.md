## 1. Finding a message's file again

- [x] 1.1 Record, on each message read from the mailbox, the folder it came from and its key within that folder, so the file it was read from can be found again — and verify a message read from a named folder reports that folder rather than the mailbox's own inbox
- [x] 1.2 Verify a message whose Message-ID is missing is still addressable by its key, since its identity falls back to that key

## 2. Turning a thread into a task

- [x] 2.1 Add the key `f`, which promotes the selected mail thread: a task on today titled from what the thread is about, created through the path that already adds a task — and verify the created task's title, date and all-day flag match what adding a task produces
- [x] 2.2 Verify the stored order is past everything the day holds, so a promoted task joins the end of the day's sequence rather than disturbing it
- [x] 2.3 Verify the task is on screen before the store has answered, by holding the write open
- [x] 2.4 Verify undo removes it and says what it reversed
- [x] 2.5 Verify a refusal from the store is reported and leaves no task on screen that does not exist
- [x] 2.6 Verify the key creates nothing on a task, a calendar event or a tracker issue, and says what it is for

## 3. What the task carries

- [x] 3.1 Write the newest message's body and that message's identity into the created task's note, in the form the board already writes notes, and verify the note reads back as written
- [x] 3.2 Verify the key that opens a task's link opens what the message pointed at, found in the note — with no address extracted or stored separately
- [x] 3.3 Verify a thread whose newest message has an empty body still creates a task, with a note carrying the identity alone
- [x] 3.4 Verify the note can be edited afterwards by the key that edits a note, holding what was written
- [x] 3.5 Verify a body holding square brackets or other markup-like characters is shown as its own characters, styles nothing, and leaves the rest of the board as it was

## 4. Taking the thread out of the queue

- [x] 4.1 Read only the messages not yet marked read, in every folder the board reads, and verify a message flagged read does not appear whether it was flagged here or by another program
- [x] 4.2 Mark every message in the promoted thread read, in the folder each was read from, and verify the row is gone from the inbox when the mailbox is next read
- [x] 4.3 Create the task before marking, and verify a mailbox that cannot be written leaves the task standing and reports that the message could not be marked
- [x] 4.4 Mark the thread's messages unread again when the promotion is undone, and delete the created task, so one press of undo reverses both halves — and verify the row is back in the inbox and the task gone
- [x] 4.5 Verify a message marked unread again stays in the folder's current area rather than returning to its new area, since it has been looked at
- [x] 4.6 Verify marking read is the only change: compare the mailbox file by file before and after a promotion and confirm no message moved folder, none was removed, no name changed beyond its own flags, and no content differs
- [x] 4.7 Verify the board wrote no record of the promotion anywhere on disk but the mailbox itself

## 5. Saying so

- [x] 5.1 Add `f` to the help overlay and the key bar, explaining that it turns a mail thread into a task on today, and verify both list it and that the overlay names no Cyrillic key
- [x] 5.2 Verify the shipped wording no longer claims the board alters nothing in the mailbox, in the help text and in `mail.py`'s own description, since it now marks messages read

## 6. Verification

- [x] 6.1 Write a suite covering the creation and its fields, the note's contents, opening through it, the empty body, both refusals, the row leaving the queue, and the mailbox being otherwise untouched — against a synthetic maildir copied per run and a stubbed store — and verify it passes
- [x] 6.2 Verify against the live store with a thread from a copy of the sample maildir that a promoted task reads back with its note intact and is then deleted, leaving nothing behind
- [x] 6.3 Confirm no regression: take a fresh baseline first, then run the existing suites and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite passing today still passes
