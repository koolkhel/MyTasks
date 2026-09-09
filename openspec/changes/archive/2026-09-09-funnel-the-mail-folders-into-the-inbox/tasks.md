## 1. A fixture with the properties the real folders have

- [x] 1.1 Extend the mail fixture generator to write a flat layout — folders as directories beside one another, not dot-prefixed — and verify the generated mailbox is read by the flat resolver and refused by nothing
- [x] 1.2 Give the fixture the shapes measured on the real folders: several messages naming one configured issue and carrying the same first address; two naming the same issue with different first addresses; messages naming no issue at all; a group where some messages carry an anchored address and some do not; a group with no anchor anywhere — and verify each shape is present by counting them, with invented project keys and `.invalid` addresses only
- [x] 1.3 Verify the fixture is copied per run by every suite that reads it, and that a whole run leaves the committed fixture byte-identical
- [x] 1.4 Keep the empty `cur/` and `tmp/` markers in the new folders, and verify the fixture survives a clone by archiving the index and reading the mailbox from the extracted copy

## 2. Reading the real layout

- [x] 2.1 Resolve a named folder as a directory beside the others rather than a dot-prefixed subdirectory, and verify against the flat fixture that all named folders are read and an unnamed one is not
- [x] 2.2 Verify a named folder that does not exist is still reported rather than passed over, in the flat layout
- [x] 2.2a Verify naming no folder shows no mail and reports no failure, since the mailbox's own inbox is no longer read and naming none is how a person turns mail off
- [x] 2.2b Verify the configured directory is never read as a mailbox itself: point the board at a directory that holds maildirs but is not one, and confirm the named folders are read and the directory is not reported unreadable
- [x] 2.3 Verify unread-only reading is unchanged: a message flagged read does not appear, whether flagged by the board or another program
- [x] 2.4 Remove the flag-writing path entirely, so reading and reviewing write nothing to the local store; verify by digesting every file in the fixture before and after a run that reviews and promotes, and confirming no name, flag, folder or content differs

## 3. Folding messages about one issue

- [x] 3.1 Fold messages that name the same configured project's issue and carry the same first address into one row, and verify against the fixture that the same-issue-same-address group becomes one row reporting its message count
- [x] 3.2 Verify the same issue with different first addresses stays as separate rows — the condition that prevents filing away unreviewed mail
- [x] 3.3 Verify recognition uses a configured project's key and not a general letters-dash-digits pattern, by putting a version-like string in a subject and confirming it folds nothing
- [x] 3.4 Verify messages that name no configured issue are grouped exactly as before, by the headers saying which answers which
- [x] 3.5 Verify a folded row's message count is the number of messages it stands for, and that the inbox's message total still counts messages rather than rows

## 4. The gateway client

- [x] 4.1 Carry a trimmed copy of the neighbouring project's client — credential lookup, folder-name encoding, bulk identity-to-number fetch, batched move, search — with attribution and a note of where the original lives; verify it imports with no network call and that nothing of its send, attachment or index paths came across
- [x] 4.2 Verify the folder-name encoding round-trips a non-ASCII folder name, since the standard library has no codec for the form the protocol wants
- [x] 4.3 Map each of a row's messages to its server-side number, and verify against a substituted server that the folder is never fetched wholesale. Written as a bulk header fetch for the folder first, as design.md then said; measured against the real gateway at 45 s for a folder of 291 against 2.1 s for a single search, so it is a search a message instead — bounded by the row rather than the folder. The OR of a row's identities that would have made it one round trip returns 2 matches out of 8 on this gateway and is refused by the substituted server so the product cannot come to make one. design.md records the measurements
- [x] 4.4 Add a batched move taking a set of those numbers, and verify against a substituted server that a row of many messages issues one move rather than one per message
- [x] 4.5 Verify the credential is read at run time and never written to a file the repository tracks, by grepping the tracked tree for it after a run

## 5. Reviewing a message

- [x] 5.1 Make the key that ticks a task review the selected mail row instead: move every message it stands for to the archive, and verify against a substituted server that all of them are moved, not only the newest
- [x] 5.2 Verify the row is gone from the inbox at once, before the server has answered, by holding the move open
- [x] 5.3 Verify promoting archives as well as creating a task, and that the task is created first
- [x] 5.4 Verify nothing is deleted and nothing is moved anywhere but the archive, by recording every call made to the substituted server during a run of reviews and promotions

## 6. Confirming the archive

- [x] 6.1 Confirm both sides after a move — absent from the folder it was in, present in the archive — and verify the row stays gone only when both hold. Absence is proved by asking the folder for the numbers just moved, one flags fetch, which is the cheap half of the cost model
- [x] 6.2 Verify an unconfirmed archive brings the row back and says why, by making the substituted server accept the move and then deny the message is in the archive
- [x] 6.3 Verify a message already absent from its folder and found in the archive is reported as already reviewed rather than as a failure
- [x] 6.4 Verify a message in neither place is reported as such, rather than as success or as an error about the board
- [x] 6.5 Verify undoing a review moves the messages back to the folder they came from and says the row returns when the mirror next catches up
- [x] 6.6 Keep the identities the gateway confirmed are archived out of each read, for the session only, so the queue drains while the mirror lags; verify a reviewed row is still gone after leaving the inbox and returning, and that nothing else is hidden
- [x] 6.6a Mark a confirmed archive read, in one request for the row, on the numbers the confirmation already found; verify against a substituted server that the flag is set only in the archive, only after both halves confirm, and never when they do not — and that undoing a review clears it before moving the message back. Asked for after the first day's use: reviewed mail sat unread in the archive, where the account and every other reader still called it new
- [x] 6.7 Verify the held identities are pruned to what the mailbox still returns, dropped when a review is undone, and never held for a row whose archive could not be confirmed

## 7. Where mail sits, and what it opens

- [x] 7.1 Put the inbox's tasks before its mail rows, and verify against a stubbed store and the fixture that the tasks lead, the cursor starts on a task, and removing every mail row leaves the tasks in exactly the order they had alone
- [x] 7.2 Verify the inbox still reports how many mail rows and how many messages, beside what it reports about tasks
- [x] 7.3 Offer the earliest anchored address in a row, and verify against the fixture's partly-anchored group that the earliest anchored one is chosen — not the earliest message's, which may carry none
- [x] 7.4 Verify a row with no anchored address anywhere falls through to the newest message's addresses, so a run of build notifications keeps exactly the behaviour it has
- [x] 7.5 Verify an issue named in a row's text is still among what can be opened, and that a row with nothing to open still says so

## 8. Saying so

- [x] 8.1 Update the help overlay and the key bar: what ticking a mail row does, that mail follows the tasks, and that reviewing files the message where the board cannot show it again; verify both list it and that the overlay names no Cyrillic key
- [x] 8.2 Verify the shipped wording no longer claims the board alters nothing but a read flag, nor that mail leads the inbox's tasks

## 9. Configuration

- [x] 9.1 Read the mail directory, the folders to read, the archive folder's name and how to reach the gateway from the environment; verify a board with no gateway configured still reads mail and refuses to review it, saying why, and that the folders to read are named rather than discovered
- [x] 9.2 Verify a board with no mailbox configured is an ordinary board, and that an unreadable mailbox is still reported once without affecting the day, the tracker or the calendar
- [x] 9.3 Establish where the credential prompt appears when the board owns the terminal, and if it interrupts the view, fetch the credential once at startup instead; verify by running the board with the keychain item's authorisation cleared

## 10. Verification

- [x] 10.1 Write a suite covering folding, ordering, what is opened, reviewing, promoting and every confirmation outcome — against the flat fixture copied per run and a substituted server that records its calls — and verify it passes and needs no credentials, so it belongs to the self-contained tier
- [x] 10.2 Add a tier for suites that need the mail gateway, since none of the four existing tiers describes it: verify the runner lists it, refuses it when the gateway is not configured, and does not run it by default
- [x] 10.3 Verify against the real gateway that one message from a folder read daily is archived and confirmed on both sides, then moved back — naming counts only and no subject, sender or address
- [x] 10.4 Verify against the real gateway that a folded row of several messages is archived in one move and confirmed, and report how long the confirmation took. Measured: one message 32 s, a folded row of two 49 s — about 25 s a message, dominated by the 11.5 s search of the archive that confirms each one. Recorded in design.md
- [x] 10.8 Bound what the gateway can hold up: a deadline on every request, a running confirmation that gives up when the board closes, and reviews reaching the gateway one at a time. Found by using it — quitting mid-review hung for five minutes with nothing said, on four connections opened by four ticks
- [x] 10.5 Confirm no regression: take a fresh baseline first, then run the self-contained tier and the store tier with the suites' token, and verify today, the inbox and the someday view show the same tasks, order and counts, and that every suite passing before still passes
- [x] 10.6 Measure how long the inbox takes to draw with the real volume — some 460 mail rows beside the tasks — and record it; if drawing dominates, say so rather than leaving it for someone to discover
- [x] 10.7 Verify the tracked tree holds no subject, sender, address, project key or credential from the real account, by grepping it after every suite has run
