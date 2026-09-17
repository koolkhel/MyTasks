## 1. The two forms

- [x] 1.1 Add a plain form beside `as_markdown` — the row's title and nothing
      else — and split `copy_line` so it can write either. Keep `as_markdown`
      exactly as it is, including its signature: `t_copy` calls it directly
      five times and those checks are the record of what markdown means here.
      Verify with `t_copy` against stubs: the checks that call `as_markdown`
      directly pass unchanged. Its key-driven checks cannot — every one of them
      presses `y` and expects markdown, which is the behaviour this change
      moves to `Y` — so they move with it under 3.1. Saying they would pass
      unchanged was wrong when this task was written. **Result: done. `copy_line(task, *, markdown: bool)` writes either form and `as_markdown` is untouched, signature included. The keyword is required rather than defaulted, so no call site can pick a form by accident. t_copy's direct calls pass with the form named.**
- [x] 1.2 Bind `Y` to copying as markdown and leave `y` copying plainly, both
      through `keys()` so each gets its Russian twin. Verify against stubs by
      reading the bindings back: `y` and `н` reach the plain action, `Y` and
      `Н` the markdown one, and the confirmation dialog's own `y` is
      untouched. Check the names against the framework first — `hasattr(App,
      name)` and a grep for `def <name>(` — before adding either action.
 **Result: done. Read back from the bindings: `copy_marked` is on `y,н` and `copy_marked_markdown` on `Y,Н`, both through `keys()`. The confirmation dialog's own `yes` is still on `y,н` — a different screen, untouched. Checked the new names against the framework first: `action_copy_marked_markdown` and the shared `copy_marked` are both absent from Textual's `App`.**
## 2. What the board says about it

- [x] 2.1 Make the notice name the form: `Copied N row(s) as plain text` and
      `Copied N row(s) as markdown`. Both are said explicitly rather than one
      by omission, because the point is to see a mis-hit before pasting.
      Verify with `t_copy` against stubs: pressing each key leaves its own
      wording on the status line. **Result: done. `Copied 3 row(s) as plain text` and `Copied 3 row(s) as markdown`, both said outright. t_copy checks each key leaves its own wording on the status line.**
- [x] 2.2 Name both keys where keys are named: the key bar entries (`Copy` for
      `y`, `Copy md` for `Y`) and the help screen's copying paragraph, which is
      hand-written text and has to say which key gives which form. Verify with
      `t_copy`'s existing group 4.4, which already checks that the help and the
      key bar name the copying keys: it must name both and still be English
      only.
 **Result: done. Key bar entries `Copy` and `Copy md`; the help's copying paragraph became two, saying which form each key gives and that a plain line says nothing about whether a task was done. t_copy's group 4.4 now checks both keys are named, that the help says which form each gives, and that both entries are on the bar at 120, 100 and 80 columns — it is still English only.**
## 3. Verification against the stub

Everything here runs against stubs and substituted sources: no credentials, no
network, no account.

- [x] 3.1 Extend `t_copy` with the plain form: the three states of a task all
      come out as bare titles, a cancelled row loses its striking, a mail row's
      subject arrives without the message count, the order is the order of
      marking, and a hidden marked row is copied. Passing is the suite green
      with the new checks, and its markdown checks unchanged. **Result: done. t_copy went 43 checks to 71. The plain form has its own direct-call group (the three states all come out as bare titles, a cancelled row loses its striking, a mail subject arrives without the message count, a long title without the shortening, foreign rows as their titles) and its own key group (order of marking, both clipboard routes, the notice, marks left in place, the Russian twin, and a row another view is holding). The markdown key's checks are the ones that were `y`'s, now pressing `Y` and `Н`.**
- [x] 3.2 Check the round-trip both ways in `t_copy`: a finished task copied as
      markdown and pasted back arrives finished; the same task copied plainly
      and pasted back arrives unfinished. Passing is both, which is what makes
      the plain form's loss deliberate rather than undiscovered. **Result: done, both ways. A finished task copied with `Y` gives `- [x] ship it`, and pasting that back adds a task that is finished. The same task copied with `y` gives `ship it`, and pasting that back adds a task that is not. That is the plain form's loss made deliberate rather than undiscovered.**
- [x] 3.3 Full tier: `python tests/run.py` reports every suite passing, and
      every suite other than `t_copy` reports the same check count it reported
      before this change. Take that baseline before the first edit. Note that
      `t_elapsed` reports 36 checks by day and 31 in the last hour, so a
      difference there is the clock rather than this change — settle it against
      a worktree at HEAD rather than assuming either way. **Result: `54 passed, 0 failed`. Every suite but `t_copy` reports exactly the count it reported in the baseline taken before the first edit — `t_copy` went 43 to 71, which is 3.1 and 3.2. `t_elapsed` came out at its daytime 36/36 this time, so the clock caveat did not arise. `main.py`, `board.py` and `t_copy.py` were byte-identical before and after the run. The six other suites that press `y` were all answering a confirmation, as the proposal said: none of them moved.**

## 4. At the board, by hand

- [x] 4.1 Mark a few rows, press `y`, and paste into TaskPaper. Passing is one
      bullet per line rather than two, and no `[ ]` left over. **Result: confirmed at the board.**
- [x] 4.2 Mark the same rows, press `Y`, and paste into Joplin. Passing is a
      checklist: the finished ones ticked, the cancelled one ticked and struck. **Result: confirmed at the board.**
- [x] 4.3 With the Russian layout active, press `н` and `Н` and confirm they do
      what `y` and `Y` do. Say which terminal it was done in — the clipboard is
      written by two routes and one of them is configured per terminal.
 **Result: confirmed at the board. The terminal was not named, so this records that the twins work where it was tried rather than on which terminal — the clipboard's escape-sequence route is configured per terminal, so another one is a separate question.**