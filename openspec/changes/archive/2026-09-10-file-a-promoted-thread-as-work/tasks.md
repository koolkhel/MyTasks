## 1. The field

- [x] 1.1 In `main.py`, add `projectId` to the dictionary `action_promote`
      already builds, and add it only when `self.work_project` is not `None` —
      never as a key holding `None` or `""`, which the store refuses. Verified
      by 2.1 and 2.2 below; no other file changes.

## 2. Stub checks — `tests/stub/t_promote.py`, no credentials, run with `python tests/run.py`

Each of these drives the app against the stub client over a copy of the
committed sample maildir, made fresh for the run, as the suite already does.

- [x] 2.1 Check what the creation carries when a work project is configured.
      Passing: the task the stub client was asked to create belongs to the
      board's configured work project.
- [x] 2.2 Check the field is absent, not empty, when no work project is
      configured. Passing: the created task's fields contain no `projectId` at
      all, and the promotion still happens — a task is made and the row still
      leaves the queue.
- [x] 2.3 Check the placeholder is filed before the store has answered.
      Passing: the row on screen under a placeholder id belongs to the work
      project, so the view filters it as it will filter the real task.
- [x] 2.4 Check the promoted task is hidden by the key for work. Passing: on
      the day the task landed, hiding work removes it and showing work brings
      it back — with the app's work project set as the suite's neighbours set
      it.
- [x] 2.5 Check the promotion's other promises are untouched. Passing: the
      suite's existing checks — title from the thread, the day, the note and
      the message identity, the stored order, the refusals, and undo removing
      the task — all still pass, and the suite reports its new total with no
      failures.
- [x] 2.6 Prove the new checks are not vacuous: take the one field back out,
      confirm 2.1, 2.3 and 2.4 fail, then put it back and confirm they pass.
      Passing: the failure is observed before the fix and absent after it.
- [x] 2.7 Re-run `tests/stub/t_work5.py`, whose source check fails if the
      board's own source sets `projectId` to `None` or to `""`. Passing:
      t_work5 passes unchanged, which is what makes 1.1's conditional form
      load bearing rather than incidental.

## 3. Live check — `tests/store/t_prolive.py`, the suites' token, against the real account

- [x] 3.1 Add a check that the task the live promotion made comes back filed.
      Passing: the task the store hands back on today belongs to the project
      `load_work_project()` names. The suite already uses the suites' token
      (`SINGULARITY_TEST_TOKEN`, never the board's), names its task `zz-`,
      promotes from a per-run copy of the committed sample maildir rather than
      the real mailbox, and deletes the task in a `finally` — none of that
      changes, and its "deleted afterwards, leaving nothing behind" check must
      still pass.
- [x] 3.2 Run the store tier once with `python tests/run.py --store`, paced
      about 25 seconds from any other live suite so the store does not answer
      HTTP 429. Passing: t_prolive passes at its new total, and no other store
      suite fails that was not already failing at HEAD.

## 4. Whole-tier verification

- [x] 4.1 Run `python tests/run.py` — the self-contained tier, no credentials.
      Passing: the tier's own summary line reports every suite passed, none
      failed, and no suite newly counted as known to fail.
