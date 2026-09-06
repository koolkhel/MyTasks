## 1. Reading the rest of the event

- [x] 1.1 Carry the event's location and its description on the event record, verbatim and unparsed, and verify against the machine — counts only, never a description — that both arrive for the events that have them and are empty for the events that do not
- [x] 1.2 Verify the calendar module still imports nothing of the board's, so the rule about what may be opened has not been copied into it
- [x] 1.3 Verify reading two more fields per event leaves a day's read within the few milliseconds the day change relies on

## 2. The address the row carries

- [x] 2.1 Resolve the address once when the row is built — the location first, the description second, using the board's existing rule for what may be opened — and verify with synthetic events that each source is found on its own and that the location wins when both hold one
- [x] 2.2 Verify an address whose scheme is neither `http` nor `https` is refused from either field, and that the event is then treated as carrying none unless it holds another that may be
- [x] 2.3 Verify an event with neither field, or with text holding no address at all, carries none and nothing about the row changes

## 3. Opening it

- [x] 3.1 Open the event's address by the key that already opens a task's link and a tracker issue's page, and verify the address handed over is the event's own
- [x] 3.2 Say the event has no link, naming it an event rather than a task, when the key is pressed on one carrying no address, and verify nothing is opened
- [x] 3.3 Verify opening writes nothing: no request to the task store, and nothing changed on the event or in the calendar
- [x] 3.4 Verify every key that writes still refuses on an event exactly as before, so opening is the one key that acts

## 4. The description on screen

- [x] 4.1 Carry the description in the field the detail area already draws, and verify a selected event shows it where a selected task shows its note
- [x] 4.2 Escape the description before it is drawn, and verify a description containing square brackets and markup-like text is shown as its own characters, changes no style, and leaves the rest of the board as it was
- [x] 4.3 Verify an event with no description shows an empty detail area, that a description is shown whether or not the event carries an address, and that selecting a task afterwards shows that task's own note with nothing of the event's left

## 5. Saying so

- [x] 5.1 Add a line to the help overlay saying an event's link opens with the same key, and verify the overlay lists it

## 6. Verification

- [x] 6.1 Write a suite covering the two sources and their precedence, the refused schemes, the absent cases, the opening and its refusal message, the write refusals, and the escaping — against synthetic events only — and verify it passes
- [x] 6.2 Verify against the real calendar, reading counts only and never a description or a title, that the events holding an address resolve one and the events holding none resolve none
- [x] 6.3 Confirm no regression: run the existing suites, and verify today, the inbox and the someday view show the same tasks, order and counts as captures taken beforehand, and that no capture or fixture records a description
