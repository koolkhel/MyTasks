## 1. Reading and writing the format

- [x] 1.1 Add an encoder beside the existing decoder, turning text into a note document of one insert with its trailing newline assured, and verify text survives a round trip through both — several lines, non-ASCII, and text that is empty
- [x] 1.2 Verify the encoder's output is a string holding a JSON array, the shape the store declares, and that clearing produces the newline-only document the existing decoder already reads as empty
- [x] 1.3 Recognise a note the board cannot represent — an op carrying attributes, or an insert that is not a string — and verify both are detected while a note of text alone is not

## 2. The editor

- [x] 2.1 Add the editor component as a subclass of the framework's text area, with nothing added to it yet, so that keys acting on the text have a home later, and verify it edits text and that its inherited undo still works
- [x] 2.2 Put it in a screen holding the note's current text, with a key to save and a key to leave, and verify the harness can type into it, save, and read back what was stored
- [x] 2.3 Choose the saving key after measuring in the terminal whether a modifier combination reaches the board under both keyboard layouts; where it does not, either twin it or choose a key that is not a letter, and verify the chosen key works in both layouts

## 3. Saving it

- [x] 3.1 Write the note through the funnel every other write uses, and verify the board shows it at once, that the request is sent, and that undo reverses it
- [x] 3.2 Settle the note field to an empty document before the write is recorded, and verify undoing a note written onto a task that had none restores it without sending a null
- [x] 3.3 Write nothing when the text is unchanged, and verify no request is sent and no undo entry is added
- [x] 3.4 Clear the note when the editor is emptied, and verify the task carries none afterwards and that undo brings the old one back
- [x] 3.5 Verify leaving without saving writes nothing and leaves the note as it was

## 4. What may not be edited

- [x] 4.1 Refuse the key on an event and on a tracker issue before the editor opens, through the guard the other input-gathering actions use, and verify no editor appears and the board names the source
- [x] 4.2 Refuse a note carrying formatting the board cannot represent, and verify the editor does not open, nothing is written, and the board says why

## 5. Showing it

- [x] 5.1 Escape a task's note before the detail area draws it, and verify a note holding square brackets and markup-like text shows every character, applies no styling, and leaves the rest of the board as it was
- [x] 5.2 Verify the note shown updates as soon as a save is made, without waiting for the store to answer
- [x] 5.3 Add the key to the help overlay and the key bar, and verify both list it

## 6. Verification

- [x] 6.1 Write a suite covering the round trip, the empty and multi-line and non-ASCII cases, saving, cancelling, clearing, the unchanged case, undo, both refusals and the escaping — and verify it passes
- [x] 6.2 Verify against the live store with a task made for the purpose and deleted afterwards that a note written from the board reads back exactly, that clearing it takes effect, and that undo restores it
- [x] 6.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand
