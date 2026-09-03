## 1. Bind backspace to delete

- [x] 1.1 Add `backspace` alongside `delete` on the delete binding, as a normal binding and explicitly not a priority one; verify the binding lists both keys and that `./.venv/bin/python -c "import main"` still succeeds.
- [x] 1.2 Confirm backspace reaches the delete action from the board: verify that pressing it on a selected task raises the existing confirmation, and that declining leaves the task present. Decline rather than confirm here, so this check cannot destroy anything.
- [x] 1.3 Confirm the text prompts still own the key: verify that inside the rename, add, and pick-a-date prompts, backspace erases one character and opens no confirmation. This is the failure mode a priority binding would cause, so check all three prompts and not just one.
- [x] 1.4 Update the help overlay line for delete to name backspace; verify the overlay opens, names backspace, still mentions no priority action, and that the footer's entries are otherwise unchanged.

## 2. Verify end to end

- [x] 2.1 Delete for real with backspace: on a far-future day holding no other tasks, create one synthetic task, press backspace, confirm, and verify the task is gone and refetching it returns 404. Destructive keypresses MUST run only on a day holding no real tasks, selecting by task id before each press.
- [x] 2.2 Confirm `delete` still works as well, by raising the confirmation with it and declining.
- [x] 2.3 Regression pass: `./.venv/bin/python -c "import main, singularity"` succeeds, `./run.sh --cli` runs, enter still opens the focus card without ticking, space still ticks and unticks, and the board still writes no `priority` and never pairs a `start` with `deferred=true`.
