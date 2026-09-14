Every check below runs in the stub tier -- `python tests/run.py`, which needs
no credentials, no network and no mailbox. Nothing in this change talks to the
task store, the mail account or the tracker, so no suite here spends the
account's quota and the question of which token is used does not arise. The
one task that needs the real board is group 7, kept separate because it fails
for different reasons and is re-run differently.

The new suite is `tests/stub/t_search.py`. Where a task says "the new suite
passes", passing means the runner prints `t_search N/N checks passed` with no
`[FAIL]` line **and exits 0** -- the exit status is read, not just the output,
because a suite that crashes before constructing anything prints no `[FAIL]`
line at all and has been misread as success on this board before.

## 1. What a row reads as

- [x] 1.1 Add one function answering what a row's title reads as for a search: the title the row carries, before a mail subject gains its thread count and before the column shortens it. Verify in the new suite, on two mail rows — a short thread of three and a long single one, because a subject long enough to be cut is long enough for the cut to take the count away with it — that the searched text equals the stored subject in both, that the count is in the drawn cell and not in what is searched, and that the long subject is cut in the cell but not in what is searched. Verify by behaviour that a word past the cut is still found, that a bracket in a subject is searched for as itself, and that the thread count is not searchable. *(Amended during apply: the original wording claimed the drawn cell also differs by carrying an escaped `[`. It does not — `shortened` parses the markup back, so the bracket reaches the cell as itself. The escaping is a trap for an implementation that matches the half-built markup string, which is what the function's docstring now records.)*
- [x] 1.2 Verify in the new suite that the function answers for all four kinds of row -- a store task, a mail thread, a calendar event and a tracker issue -- returning each one's own title and never an empty string.

## 2. The filter

- [x] 2.1 Add the attribute holding the live search term, defaulting to no search. Verify in the new suite that a freshly built board has no search in force and draws every row.
- [x] 2.2 Narrow every source in `repaint`, at the line where the work filter narrows, and record how many rows were removed. Verify in the new suite that with a term in force, only matching rows are drawn, and that the recorded count equals the number removed.
- [x] 2.3 Verify in the new suite, with one check per source, that a non-matching row of each kind is removed: a store task, a mail thread, a calendar event and a tracker issue. Four separate checks, so that a fifth source added later without a check is visible as an absence rather than passing quietly.
- [x] 2.4 Verify in the new suite that the match ignores letter case, and that a term matching part of a word matches.
- [x] 2.5 Verify in the new suite that the search reads the title alone: a term appearing only in a message's sender, only in its body, or only in a task's project name leaves that row undrawn.
- [x] 2.6 Verify in the new suite that narrowing preserves order: the rows that survive appear in the same relative order as with no search in force.
- [x] 2.7 Verify in the new suite that the two filters compose -- with work hidden and a term matching some work rows, those rows stay undrawn; clearing the search leaves work still hidden, and clearing the work filter leaves the search still in force.
- [x] 2.8 Verify in the new suite that no request is sent to change a task when a search is started, changed or cleared: the stub client records no write.

## 3. The keys and the prompt

- [x] 3.1 Add the prompt screen asking for a term. Verify in the new suite that pressing the search key pushes it and that confirming a term puts that term in force.
- [x] 3.2 Bind `/` and `;`, both with their layout twins where they have free ones. Verify in the new suite that each of the bound keys opens the prompt, including the Russian character for `;`.
- [x] 3.3 Bind escape on the board to clear the search. Verify in the new suite that escape with a term in force draws every row again, and that escape with no search in force does nothing and raises nothing.
- [x] 3.4 Verify in the new suite that cancelling the prompt with a search already in force leaves that search exactly as it was, and that confirming an empty term clears the search.
- [x] 3.5 Verify in the new suite that no two actions answer the same key: expand every binding the board declares, including its layout twins, and assert no key appears twice. This is the check that would have caught binding `/` alone.
- [x] 3.6 Move the existing twin-coverage guard in `tests/stub/t_twins2.py` to the amended requirement, the old one having failed on the new binding as written. It now allows a key to lack its twin only where that twin already belongs to another action, and asserts separately that every action is reachable in either layout. Add `SearchInput` to the classes it walks. Verify by running `python tests/run.py t_twins2` — passing is every check passing and exit 0 — and by binding `/` alone and confirming it fails, naming the unreachable action.

## 4. What the board says

- [x] 4.1 Put the term in the day bar beside the work filter's note. Verify in the new suite that the day bar names the term in the inbox, on a calendar day and in the someday view.
- [x] 4.2 Put the removed count on the status line beside the work filter's. Verify in the new suite that the status line reports the count and that the count of rows it already reports is still the number of rows drawn.
- [x] 4.3 Verify in the new suite that the board says a search is in force even when the search removes nothing, and even when it removes every row.
- [x] 4.4 Verify in the new suite that with no search in force the day bar and the status line say nothing about one.
- [x] 4.5 Verify in the new suite that with work hidden and a search in force the board reports both, and neither replaces the other.

## 5. Selection and redraws

- [x] 5.1 Verify in the new suite that after a search is applied, the selection is on a row that is drawn; and that when no row matches, nothing is selected and the board reports the view as empty.
- [x] 5.2 Verify in the new suite that a search applied in the inbox is still in force after moving to a calendar day and to the someday view, without the key being pressed again.
- [x] 5.3 Verify in the new suite that rows arriving after the search is in force are narrowed by it: add rows through the stub client, the calendar and the mailbox, repaint, and assert the non-matching ones are not drawn.
- [x] 5.4 Verify in the new suite that a redraw the person did not ask for -- a write confirming while a search is in force -- leaves the search in force and the surviving rows unchanged.

## 6. Help and the key bar

- [x] 6.1 Add the search key to `Help.TEXT`, which is written by hand rather than derived from the bindings. Verify in the new suite that the help text names the key and that no key in it is spelled in any alphabet but English.
- [x] 6.2 Verify in the new suite that the key bar names the action once and shows `/` for it, the bar naming a binding by its first key.

## 7. Verification of the whole

- [x] 7.1 Run the new suite alone: `python tests/run.py t_search`. Passing is every check passing and exit status 0. **Result: `t_search 102/102 checks passed`, exit 0.** The suite first reported its summary in a format the runner does not parse and was listed with a dash where its count belongs; it now prints the line the runner reads.
- [x] 7.2 Run the whole stub tier: `python tests/run.py`. Passing is every suite passing with no new failure against the 46 suites that pass today, and exit status 0. **Result: 47 passed, 0 failed, 0 known to fail, exit 0, in 616s — the 46 that passed before plus `t_search` at 102/102, with `t_twins2` at 79/79 after its guard was moved to the amended requirement. Code frozen for the run at `shasum main.py` = `943196218ed7`, confirmed unchanged afterwards.**
- [x] 7.3 Vacuity check: make the filter a no-op -- have it return every row -- re-run the new suite, and confirm it fails, reading the exit status rather than grepping the output. Then restore the filter and confirm it passes again. A suite that passes with the feature removed has checked nothing. **Result: 34 of 102 checks failed, exit 1. Restored; `shasum main.py` back to `943196218ed7`.**
- [x] 7.4 Second vacuity check, for the reporting: remove the day-bar note, re-run, and confirm the group 4 checks fail. Restore and re-run. **Result: 7 checks failed, all in group 4 (4.1, 4.3, 4.5). Restored; checksum back to `943196218ed7`.**
- [x] 7.5 Run the board by hand against the real inbox -- not a suite, and not part of the stub tier: search for a word that appears in several subjects, confirm the view narrows, move to another day and confirm the term is still named on the day bar, then press escape and confirm the rows return. Passing is all four observed. **Result: run by the board's owner against the real inbox; reported working.**
- [x] 7.6 While the board is open, measure whether a bare escape clears the search without a noticeable delay, escape also being the first byte of every arrow-key sequence. Record the result in the change. If it is noticeable, say so rather than adjusting the design here -- a second key for clearing would be its own decision. **Result: confirmed working by the board's owner, pressing escape on the running board, with no delay reported. An observation rather than an instrumented timing -- nobody timed the keypress -- and the right instrument all the same: the stub suite drives Textual's headless pilot, which injects the key directly and never exercises the terminal's escape-sequence decoding, which is the thing this risk was about. The risk the design raised was whether a delay would be noticeable; it was not. If one appears later, the design names the remedy.**
