## 1. The baseline this change is measured against

- [x] 1.1 **58 suites, 3,088 checks, 0 failed; frozen across the run.** Record the self-contained tier's per-suite counts before any edit: `python tests/run.py` with the product code, `tests/` and `docs/screenshots.py` hashed by `shasum` before and after the run, saved to the session scratchpad. Passing: the run finishes, the hashes match either side, and the saved file holds one `N/M checks passed` line per suite to compare against in 5.1.

## 2. The marks

- [x] 2.1 Replace the three state marks in `board.py`'s `MARKS` table with `□` (U+25A1), `✓` (U+2713) and `✗` (U+2717) for the open, done and cancelled states. Passing: `python -c` printing the table shows the three new code points and nothing from U+2610 to U+2612.
- [x] 2.2 Write the choosing rule beside `MARKS` in full: a mark drawn in a fixed column is one the terminal's own font provides, and looks the same on every row; and the width-in-every-locale rule holds for the green star and not for these. Passing: the comment states both halves and gives the reason each exists, and a reader meeting a new mark can decide without re-deriving it.
- [x] 2.3 Point the three comments that each solved one instance of this at the rule in 2.2 rather than re-arguing it: the copy mark's, the mailbox indicator's and the green star's. Passing: each still says what its own mark is and why, and none repeats the general argument.
- [x] 2.4 **The collision was raised mid-apply and the user chose to accept it; proposal and design were corrected before any code was written.** Correct the comment beside the mailbox indicator in `main.py`. It says `☑` and `☒` were passed over there because they are already the row's ticked and cancelled marks, which this change makes false. Passing: the comment names the marks the rows now draw, says the day bar shares two of them on purpose, and gives the reason the sharing was judged acceptable.
- [x] 2.5 Note beside the event diamond that it is East-Asian-Ambiguous and that the narrowed rule permits it. Passing: the comment says so, so the next reader does not file it as a defect.

## 3. Checks

- [x] 3.1 Update the two suites that name the old glyphs literally, `tests/stub/t_arch.py` (the archive keeps a completed and a cancelled row's mark) and `tests/stub/t_fit.py` (the marks survive a column refit). Passing: both suites run against the stub and report every check passing, with their counts unchanged from 1.1.
- [x] 3.2 Add a part to a self-contained suite for the spec's first four scenarios: the three states are told apart; the mark follows the state alone, checked by building rows that differ in title, script, timed against all-day, and project, and asserting one mark for one state; no state mark lies in U+2610 to U+2612; each mark is one cell by the standard width table. Passing: the new part runs against the stub, each check names what it asserts, and the suite's count rises by exactly the number of checks added.
- [x] 3.3 Add a part covering the two remaining scenarios: ticking an open task leaves the done mark in the same single cell with the columns beside it in place, and a row marked for copying shows the copy mark beside the state mark its state always draws. Passing: the part runs against the stub and both checks pass.

## 4. What the board shows about itself

- [x] 4.1 Update the mark table in `README.md`, which prints the old three, and any sentence naming them. Passing: the table shows the three new marks and the file holds no character from U+2610 to U+2612.
- [x] 4.2 Remake the three drawn pictures and the cool-retro-term one with `python docs/screenshots.py` and `python docs/screenshots.py --crt today`, hands off the keyboard while the second runs. Passing: all four files are written, and the open, done and cancelled marks in them are the new ones at one size.
- [x] 4.3 Look at the remade cool-retro-term picture and confirm the fault is gone: every open row's mark is the same size whether its row carries a time or reads all-day. Passing: the marks match across those rows in the captured picture.

## 5. Verification

- [x] 5.1 **58 suites, 3,102 checks, 0 failed; no suite's count dropped; t_paint the only one that rose, 45 to 59; frozen across the run.** Run the whole self-contained tier frozen, `python tests/run.py` with the product code, `tests/` and `docs/screenshots.py` hashed before and after, and compare every suite's count with 1.1. Passing: nothing failed, no suite's count dropped, the only counts that rose are the suites given parts in 3.2 and 3.3, and the hashes match either side of the run.
- [x] 5.2 Update the suite and check totals quoted in `README.md` if 5.1 moved them. Passing: the sentence names the totals 5.1 reported.
