## 1. The focus card

- [x] 1.1 Add a display-only modal screen following the existing `TaskInput`/`Confirm`/`DatePicker` pattern, rendering the selected task's full title, when it is due, its project, its deadline, and its note, and dismissing on escape; verify in the pilot that it opens, that its content carries each of those, and that escape returns to the board with the same view and the same row still selected.
- [x] 1.2 Omit the optional parts when the task has nothing for them; verify with synthetic tasks that a task with no project, deadline, or note renders only its title and when, and that one carrying all three renders all three, with no empty labels or stray separators left behind.
- [x] 1.3 Show the title in full; verify with a synthetic task whose title is longer than the width the task column can give it that the modal's rendered content contains the complete title string, and that this is the case the row itself cannot show.

## 2. Give enter to the focus card

- [x] 2.1 Split the combined tick binding so enter opens the focus card and space alone keeps tick; verify on an empty far-future day, with a single synthetic task, that enter opens the card and leaves `checked` unchanged, and that space still ticks and unticks. Keypress checks that can tick MUST run on a day holding no real tasks, selecting by task id before each press.
- [x] 2.2 Do nothing when there is no selection; verify that asking for the focus card on a view with no tasks opens no modal and leaves the board as it was.
- [x] 2.3 Add the key to the help overlay and confirm the footer; verify the overlay lists the focus key, still opens and closes, and mentions no priority action, and that the footer's other entries are unchanged.
- [x] 2.4 Reach the focus card through the task list's own row-selection message rather than a priority binding, so enter still confirms the rename, add, and pick-a-date prompts; verify all four enter paths — focus card opens, and each of the three prompts submits — plus that enter still never ticks and space still does.

## 3. Verify end to end

- [x] 3.1 Confirm the card opens on a selected task in the inbox and in the never view as well as on a day; verify by opening it in each of the three views on a task already present, without modifying any of them.
- [x] 3.2 Confirm the card writes nothing: with a request spy in place, open and dismiss it several times and verify no POST, PATCH, or DELETE was sent, and that a before-and-after snapshot of the task is identical.
- [x] 3.3 Regression pass: `./.venv/bin/python -c "import main, singularity"` succeeds, `./run.sh --cli` runs, the inbox still reports its shown and filed counts, and the board still writes no `priority` and never pairs a `start` with `deferred=true`.
