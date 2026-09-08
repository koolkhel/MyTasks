## 1. Reading the mailbox

- [x] 1.1 Add the mailbox module in the shape `tracker.py` and `ical.py` established — its own configuration read from the environment, one failure type, plain records — and verify the source names no address, no host and no folder
- [x] 1.2 Read a maildir at the configured path and verify against the sample maildir that every message is found, with its sender, subject, date and identity
- [x] 1.2a Read the mailbox's own inbox plus any folders named in the environment, and verify only those are read while other folders in the same mailbox are not
- [x] 1.2b Report a named folder that does not exist rather than passing over it, and verify the failure names the missing folder
- [x] 1.3 Verify an encoded subject and a non-ASCII sender are decoded, and that a message with neither a subject nor a date is still read
- [x] 1.4 Turn every failure into the one type — a missing path, a path that is not a maildir, one unreadable — and verify a single unreadable message does not take the others down with it
- [x] 1.5 Verify no mailbox configured answers with nothing rather than raising, and that nothing is written to the maildir by reading it: no flag, no rename, no move

## 2. Threads

- [x] 2.1 Group messages into threads by the header that says which answers which, following a chain to its start, and verify the sample's three threads are found and its one-offs are not merged
- [x] 2.2 Verify two messages sharing a subject but answering nothing stay separate, so no subject fallback creeps in
- [x] 2.3 Verify a thread whose parent is absent from the mailbox is still a thread, and that a cycle in the headers cannot loop
- [x] 2.4 Order threads by their newest message and verify the newest thread leads

## 3. Where mail appears

- [x] 3.1 Show mail in the inbox view, above the tasks awaiting triage, and verify the inbox holds both with the mail leading
- [x] 3.2 Verify no mail row appears on any day or in the someday view
- [x] 3.3 Report how many threads and how many messages beside what the inbox already reports about tasks, and verify every count
- [x] 3.4 Verify the inbox's tasks are in exactly the order they would be with no mail present, and that an inbox with no mailbox configured is precisely the view it was before
- [x] 3.5 Verify moving to the inbox and back to a day leaves the day's tasks, order and counts exactly as they were

## 4. The row

- [x] 4.1 Draw a row carrying the newest arrival, the sender, the subject and — where there is more than one message — how many, and verify each against the sample
- [x] 4.2 Mark a mail row apart from a task's without relying on colour, distinct from the marks an event and a tracker issue already use, and verify all four are different
- [x] 4.3 Escape the subject and the sender before drawing, and verify a subject holding square brackets and markup-like text shows every character, applies no styling, and leaves the rest of the board as it was
- [x] 4.4 Shorten a subject or sender too long for its column and verify no other column is pushed off the screen at any terminal width the board supports

## 4a. What a message says

- [x] 4a.1 Carry the newest message's body where the detail area already looks, and verify a selected mail row shows it in the notes region
- [x] 4a.2 Verify the subject is not repeated at the head of the body, and that an empty body shows nothing
- [x] 4a.3 Verify a body holding square brackets and markup-like text shows every character, applies no styling, and leaves the rest of the board as it was
- [x] 4a.4 Verify selecting a task afterwards shows that task's own note with nothing of the message left

## 4b. Messages that are HTML

- [x] 4b.1 Show an HTML-only message as readable text, preferring a plain part where the message has one, and verify both cases against synthetic mail
- [x] 4b.2 Keep the addresses the markup carries so the row can still open them, and verify a link in HTML is found where the visible words do not contain it
- [x] 4b.3 Verify malformed HTML still yields a row rather than an error, and record why an external renderer was measured and not used

## 5. Opening

- [x] 5.1 Offer what the thread's newest message points at, through the machinery that already collects a task's candidates, and verify a thread of four near-identical addresses offers one
- [x] 5.2 Verify a thread naming an issue in a configured tracker project offers that issue, and that a key from an unconfigured project is ignored
- [x] 5.3 Verify one candidate opens directly, several ask which, and none says so — the same three ways a task behaves
- [x] 5.4 Verify opening writes nothing, to the mailbox or to the task store

## 6. What may not be done to a mail row

- [x] 6.1 Refuse every key that writes through the guard the other foreign rows use, and verify each refuses at once, asks for nothing first, and names the mailbox
- [x] 6.2 Verify a mail row is not counted among the tasks in what the board reports
- [x] 6.3 Verify reordering cannot reach a mail row and that its note cannot be edited

## 7. Not delaying the board

- [x] 7.1 Read off the drawing path, and verify a day's tasks are on screen while the mailbox is still being read
- [x] 7.2 Verify an unreadable mailbox is reported as the mailbox's failure and never as the day failing to load
- [x] 7.3 Verify the board stays responsive with a mailbox far larger than a person would read, by measuring against a generated one

## 8. Verification

- [x] 8.1 Write a suite covering the reading, the failures, the threading and its refusals, the view, the row and its escaping, the opening, and the write refusals — against a synthetic maildir only — and verify it passes
- [x] 8.2 Verify against a real maildir if one exists by then, reporting counts alone and never a subject, a sender or a body; where none exists, record that and rely on the synthetic one
- [x] 8.3 Confirm no regression: take a fresh baseline first, then run the existing suites and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite passing today still passes
