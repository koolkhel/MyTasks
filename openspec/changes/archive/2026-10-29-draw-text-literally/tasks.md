## 1. Failing suites first

- [x] 1.1 Add the hostile shapes to `tests/stub/t_markup.py` as one shared tuple -- `[--opt=A-B]`, `[A]`, `[Ab] text`, `[ABC=1]`, `[$var]`, `[_x]`, `[--k=SECS] [--v=path]`, `a\[b]`, `end\`, `[b]one[/b]` -- all synthetic, and drive them through the detail area, the focus card, the status line, every prompt the suite already opens, and the picker options. Verify with `python tests/run.py t_markup` (stub, no account) that the new parts fail on the current code -- some with `MarkupError`, some with characters missing -- and the existing parts still pass.
- [x] 1.2 Add to `tests/stub/t_note.py` a row whose note holds `[--opt=A-B]`; select it, move off and back. Verify with `python tests/run.py t_note` (stub) that it fails now: the app exits on the first selection.
- [x] 1.3 Add row-cell checks for a task title, a mail subject and sender, a finished (struck) mail row, an over event and its calendar, and a tracker title and project, each holding the shapes from 1.1, reading the drawn cell's `plain` text and styles. Put them in `t_markup` beside the others. Verify with `python tests/run.py t_markup` (stub) that only `end\` fails among the row checks (Rich parses rows), which pins down the one row defect. (Found when run: the task row's project column was never escaped at all, so `[b]one[/b]`, `a\[b]` and `end\` also fail there -- the row work in 2.3 covers it.)

## 2. Rows build Rich text

- [x] 2.1 Change `board.shortened` to take a `rich.text.Text` and stop calling `Text.from_markup`. Verify with `python tests/run.py t_fit t_fit2` (stub) that truncation and its ellipsis are unchanged.
- [x] 2.2 Replace `_markup_title` with a function returning `Text`: the plain display title, the link span styled `Style(link=url)` at the position of `link_text` in it, and `↻ ` / `≡ ` prefixes added as text. Verify with `python tests/run.py t_title t_star t_star2` (stub) that link rows still open and show their readable text.
- [x] 2.3 Rebuild the mail, tracker and event branches of `row_for` and the task branch's styled parts (dim, strike, `(n)` count, late colour) by appending styled parts to `Text`; remove every `escape(` from `board.py`. Verify with `python tests/run.py t_markup t_mailview t_paint t_track2 t_track3 t_cal` (stub): the row checks from 1.3 pass, including `end\`, and the styling suites pass unchanged.

## 3. Widgets draw Content

- [x] 3.1 Detail area and focus card: draw the note and the focus title as `Content(text)`, and the facts line (`tracker_facts`, `series_facts_for`, flags, deadline) as `Content`, so an issue's state, project and versions are no longer parsed. Verify with `python tests/run.py t_note t_pane t_markup` (stub): 1.2 passes and the detail and focus parts of 1.1 pass.
- [x] 3.2 Status line: `status.update` takes `Content(message)`; the error colour stays a CSS class. Verify with `python tests/run.py t_markup` (stub) that the status-line parts of 1.1 pass and "nothing the board writes itself is altered" still passes.
- [x] 3.3 Subtitle bar: `search_note`, `work_note` and the parts joined into the bar stay plain strings and `with_mark` returns the finished line as `Content`, measured by `cell_length` (design decision 3, revised during apply). Verify with `python tests/run.py t_search t_bands t_markup` (stub) that searching for `[--opt=A-B]` and `[A]` shows the term as typed and the mailbox mark still sits at the right edge.
- [x] 3.4 Prompts and pickers (date, project, link, note editor, delete confirmation, file-under confirmation, version prompt, list options): each dialogue draws its question or title as `Content(text)`, callers quote titles unescaped, and each `Option` is built with `Content(text)` (design decision 1, revised during apply: no question carries styling, so no template is needed). Remove every `escape(` from `main.py` and its import. Verify with `python tests/run.py t_markup t_version t_label2` (stub) that the prompt and choice parts of 1.1 pass.

## 4. Keep it that way

- [x] 4.1 Add a part to `tests/stub/t_markup.py` (not `t_arch`, which turned out to be the archive's suite) asserting that neither `main.py` nor `board.py` imports `escape` from `textual.markup` or `rich.markup`. Verify with `python tests/run.py t_markup` (stub) that it passes now, and fails when the import is put back by hand.
- [x] 4.2 Update the comments that described escaping as the safeguard (the detail area, the focus card, the status line, `_markup_title`'s docstring, `search_note`) so they describe what the code now does. Verify by `grep -n -i 'escap' main.py board.py` showing only the key and terminal escapes, plus four comments that say why escaping is *not* used (`_title_text`, the key bar, the focus card note, the detail area).

## 5. Whole-suite verification

- [x] 5.1 Freeze the code (`shasum main.py board.py` before and after) and run the self-contained tier: `python tests/run.py` (stub, no credentials). Passing means every suite passes, or any failure also fails identically against a git worktree at HEAD (pre-existing, matched by `tests/known_failures.py`). No store, tracker or gateway suite is needed: nothing written to the account changes, and no task store quota is spent.
- [x] 5.2 On the real board (live account, by the user): select the mail row that ended the session on 2026-10-29, move off it and back, open its focus card, and complete it. Passing means the board stays open throughout and no new `logs/crash-*.txt` appears.
