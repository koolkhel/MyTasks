## 1. What the board remembers

- [x] 1.1 In `main.py`, add one field to the app holding what is being worked
      on and when that began, and confirm the name exists on neither `App` nor
      `ModalScreen` before using it (`hasattr` on both, and a grep for a method
      of that name in this file). Passing: the check is run and recorded in the
      commit message or the code comment; 3.1 then proves the field behaves.
- [x] 1.2 Set it at the end of `action_start_workspace`, after the program has
      been started and not before — an abandoned prompt or a program that
      cannot be started leaves it as it was. Passing: 3.2 and 3.3.
- [x] 1.3 Starting work on another row replaces it; starting on the same row
      begins the count again. Passing: 3.4 and 3.5.

## 2. What the card shows

- [x] 2.1 Give `TaskFocus` one optional argument for the moment work began,
      and draw a line saying when that was and how long ago, under the facts it
      already shows. Nothing is drawn when the argument is absent. Passing:
      3.6 and 3.7.
- [x] 2.2 Have the card own an interval while it is open — started on mount,
      stopped on unmount — that redraws the line. Passing: 3.8, which advances
      a clock the suite controls rather than waiting a real minute.
- [x] 2.3 Open the card at the end of `action_start_workspace`, handing it the
      moment just recorded. Passing: 3.2.
- [x] 2.4 Have `action_focus_task` hand the card the same moment when the
      selected row is the one being worked on, and nothing otherwise. Passing:
      3.6 and 3.7.

## 3. Stub checks — `tests/stub/t_workspace.py`, no credentials, run with `python tests/run.py`

Every check drives the app against the stub client with an invented tracker
configuration, as the suite already does, and reads what the card draws rather
than what was assembled.

- [x] 3.1 The field starts empty and holds one pair once work is started.
      Passing: nothing is being worked on before the key is pressed, and after
      it the row it names is the issue the workspace was started for.
- [x] 3.2 Starting a workspace opens that issue's card. Passing: the screen on
      top is the card, it shows that issue's title, and dismissing it returns
      to the view and the row the person was on.
- [x] 3.3 An abandoned prompt and a program that cannot be started open no card
      and record nothing. Passing: no card is on top, the field is unchanged,
      and the board says what it said before this change — the existing checks
      for both cases still pass unedited.
- [x] 3.4 Starting work on a second issue replaces the first. Passing: the
      first issue's card then shows no line about time worked.
- [x] 3.5 Starting work again on the same issue restarts the count. Passing:
      with a clock the suite controls, the count after the second start is
      measured from the second start.
- [x] 3.6 The card shows the line for the issue being worked on, whichever key
      opened it. Passing: the line is present and identical whether the card
      came from starting a workspace or from the key that opens a card on any
      row.
- [x] 3.7 A card on any other row shows no such line. Passing: the drawn card
      holds no "since" line at all — not an empty one, and not a zero.
- [x] 3.8 The line keeps up with the clock. Passing: with the suite's own clock
      advanced past a minute boundary, the drawn line shows the larger figure
      without any key being pressed.
- [x] 3.9 Prove the new checks are not vacuous: take the line out of the card,
      confirm 3.6 and 3.8 fail; stop setting the field, confirm 3.1, 3.2, 3.4
      and 3.5 fail; then restore both and confirm they pass. Passing: each
      failure is observed before its fix and absent after it.

## 4. What must not have moved

- [x] 4.1 Re-run `tests/stub/t_star2.py`, which builds a `TaskFocus` directly,
      and `tests/stub/t_fit2.py`, `tests/stub/t_pane.py`, `tests/stub/t_star.py`,
      `tests/stub/t_twins2.py` and `tests/stub/t_mailview.py`, which read the
      card. Passing: each reports its own total with no failures and none of
      them is edited.
- [x] 4.2 Run `python tests/run.py` — the self-contained tier, no credentials.
      Passing: the tier's summary reports every suite passed, none failed, and
      no suite newly counted as known to fail. No live tier is required:
      nothing here reaches the task store, the tracker, the calendar or the
      mailbox.
