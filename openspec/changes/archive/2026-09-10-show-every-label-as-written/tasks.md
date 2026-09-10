## 1. What is drawn

- [x] 1.1 In `main.py`, have `KeyBar.rebuild` assemble its rows as styled
      text rather than writing them as markup, so the key is never parsed.
      Escaping cannot serve here: the toolkit's `escape` leaves a lone `[`
      alone, by design, and the bar's `[` is a fragment next to markup rather
      than a whole string — see design.md. Verified by 3.1 and 3.2.
- [x] 1.2 In `main.py`, escape the message in `set_status`, once, rather than
      at any of its callers. Verified by 3.3; and by 3.5, which is the check
      that nothing the board writes itself reads differently afterwards.
- [x] 1.3 In `main.py`, escape the task's title where it is interpolated into
      each of the six prompts built from one — the date, project and link
      pickers, the note editor, and the confirmation before deleting.
      Verified by 3.4.
- [x] 1.4 In `main.py`, escape the foreign text in the two prompts that list
      things to choose between: the project picker's project names and the
      link picker's labels, both drawn as markup by the option list. Verified
      by 3.7.

## 2. A suite for the rule

- [x] 2.1 Add `tests/stub/t_markup.py`, a self-contained suite (no
      credentials, picked up by `python tests/run.py` because the runner
      lists the tier's directory). It drives the app against the stub client
      on synthetic tasks whose titles contain square brackets and text shaped
      like a tag, and reads what is *drawn* rather than what was assembled.
      Passing: the file runs alone and reports its own total with no failures.

## 3. Stub checks — no credentials, run with `python tests/run.py`

- [x] 3.1 In `tests/stub/t_markup.py`, check the drawn key bar. Passing: the
      row the bar draws, parsed back to its text, contains `[ Note up` and
      `] Note down`, and no part of the bar's own styling — no `[/b]`, no
      `[/dim]` — appears in that text.
- [x] 3.2 Beside the existing entries check in `tests/stub/t_still.py`'s
      `the_key_bar`, add the same assertion about the drawn row. Passing: the
      suite reports its new total with no failures, and the section that
      promises the bar names the character now looks at the screen as well as
      at the entry.
- [x] 3.3 In `tests/stub/t_markup.py`, check the status line on a task whose
      title contains square brackets. Passing: the drawn status text contains
      the title's every character, brackets included, for a message the board
      produces itself — the refusal to move a task past the edge of a day.
- [x] 3.4 In `tests/stub/t_markup.py`, check each of the six prompts on such a
      task: the date, project and link pickers, the note editor, and the
      delete confirmation. Passing: each prompt's drawn text contains the
      title as written, with no character of it lost.
- [x] 3.5 In `tests/stub/t_markup.py`, check that an ordinary message is
      unchanged. Passing: a status message with no markup characters in it
      draws exactly the text it was given, and the error class still applies
      to an error — the styling that is CSS rather than markup is untouched.
- [x] 3.7 In `tests/stub/t_markup.py`, check the two prompts that list things
      to choose between, with a project named and a link labelled using square
      brackets. Passing: each drawn option shows its text as written, with no
      character lost.
- [x] 3.6 Prove the new checks are not vacuous: take each of the three
      escapes back out in turn, confirm the checks named against it fail
      (3.1/3.2 for the bar, 3.3 for the status, 3.4 for the prompts), then
      put it back and confirm they pass. Passing: each failure is observed
      before its fix and absent after it.

## 4. What must not have moved

- [x] 4.1 Re-run the suites that already read the bar or the status line —
      `tests/stub/t_still.py`, `tests/stub/t_move.py`, `tests/stub/t_work3.py`,
      `tests/stub/t_undo3.py`, `tests/stub/t_note.py`, `tests/stub/t_fit.py`.
      Passing: each reports its own total with no failures, so escaping the
      status did not change any message a suite reads.
- [x] 4.2 Run `python tests/run.py` — the self-contained tier, no credentials.
      Passing: the tier's summary line reports every suite passed, none
      failed, and no suite newly counted as known to fail. The store,
      tracker and gateway tiers are not required: nothing here touches the
      task store, the issue tracker or the mailbox.
