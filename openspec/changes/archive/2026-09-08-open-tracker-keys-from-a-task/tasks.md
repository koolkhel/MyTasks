## 1. Finding every candidate

- [x] 1.1 Express the existing first-address scanner in terms of a new one that yields every openable address in a piece of text in order, and verify the existing scanner's answers are unchanged for a title with one address, several, an anchor, a bare host, a refused scheme and no address at all
- [x] 1.2 Verify the new scanner returns them in the order they appear, keeps the anchor-before-plain preference, and refuses a scheme the allowlist does not carry — in the one place, so no second copy of that rule exists

## 2. An issue named by a task

- [x] 2.1 Add to the tracker module the address of an issue named by key, beside the address of an issue it reported, and verify both build the same shape from the same configured location
- [x] 2.2 Recognise a mention of a configured project followed by a number, and verify each configured project is recognised and a project that is not configured is refused
- [x] 2.3 Verify text shaped like a key but not a configured project — a version, a standard, a year — is not treated as an issue
- [x] 2.4 Verify no key is recognised when no tracker is configured, and that a task's addresses are unaffected in that case

## 3. What a task can open

- [x] 3.1 Collect a task's candidates from its title and then its note, each scanned for keys and for addresses, and verify the order is reading order with the title's first
- [x] 3.2 Verify a note holding an address makes it openable where the title holds none, and that a refused scheme in a note is not offered
- [x] 3.3 Collapse two candidates that resolve to the same address into one, so an issue mentioned both by key and by its own link is offered once, and verify it
- [x] 3.4 Verify a task's title is drawn exactly as before: recognising a key changes no row

## 4. Opening, and asking

- [x] 4.1 Open directly where there is exactly one candidate, of either kind, and verify no choice is presented — including the case where the only candidate is an issue key
- [x] 4.2 Say the task has no link where there are none, and verify the wording is unchanged
- [x] 4.3 Add the chooser as a screen of the shape the project picker uses, listing each candidate readably — an issue by its key, an address by the address — and verify the harness can open it, read the list and choose an item
- [x] 4.4 Verify choosing opens exactly the chosen one and nothing else, and that leaving without choosing opens nothing and writes nothing
- [x] 4.5 Verify opening still writes nothing at all: no request that changes anything, whichever route was taken
- [x] 4.6 Verify an event and a tracker row are unaffected — each still opens its own address with no choice presented

## 5. Saying so

- [x] 5.1 Update the help overlay to say that a task mentioning a tracker issue can be opened, and that the board asks when a task offers more than one thing, and verify the overlay reads correctly and names no Cyrillic key

## 6. Verification

- [x] 6.1 Write a suite covering the scanner, the key recognition and its refusals, the note as a source, the collapsing of duplicates, opening with one candidate, the chooser with several, choosing and leaving, and the untouched event and tracker rows — and verify it passes
- [x] 6.2 Verify against the real board, printing counts and the recognised keys only, that the task mentioning an issue resolves to an address built from the configured location, and that the tasks carrying several addresses now offer a choice
- [x] 6.3 Confirm no regression: take a fresh baseline first, then run the existing suites and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite that passes today still passes
