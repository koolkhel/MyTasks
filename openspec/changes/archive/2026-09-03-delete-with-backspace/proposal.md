## Why

Deleting a task is bound to `delete`, meaning the forward-delete key. Mac laptop keyboards do not have one: the key labelled Delete sends backspace, and forward-delete only exists as `fn`+that key. So on the machine this board runs on, the delete action cannot be reached at all — the spec says a task can be deleted behind a confirmation, and on this hardware it cannot.

## What Changes

- Bind the delete action to `backspace` as well as `delete`, so the key labelled Delete on a Mac keyboard reaches it.
- Update the help overlay, which the spec already requires to list only keys the board actually binds.
- Keep `delete` bound rather than replacing it. It costs nothing, still works, and an external keyboard with a real forward-delete key keeps working. This was a decision rather than a request; say so if you would rather have backspace alone.

## Capabilities

No capability changes, so this change sets `skip_specs: true`.

The spec describes the board's actions without naming any key — it says a task can be deleted behind a confirmation, and separately that the help overlay lists only keys the board actually binds. Both statements are already correct and stay correct: the set of offered actions does not change, the confirmation does not change, and the help requirement is satisfied by updating the overlay. What changes is only which keypress reaches an action the spec already guarantees, which is implementation. Adding a requirement here would mean inventing one to justify a delta.

## Impact

- `main.py` — one binding entry, and the corresponding line in the help overlay.
- `singularity.py` — no change. Nothing about the API or the task model is involved.
- No new dependencies, and no change to `run.sh`, `requirements.txt`, or `.env`.
- Verified during planning against a scratchpad copy rather than assumed: `backspace` on the board reaches the delete action and raises the existing confirmation, and inside the rename, add, and date prompts `backspace` still erases a character without triggering a delete, because the binding is not a priority one and the text input's own binding takes the key first. Binding this as a priority binding would break text editing the way the focus-card change briefly broke confirming a rename.
- The confirmation gate is unchanged, which matters more than usual here: the API's delete is permanent, and a task deleted through it returns 404 rather than landing in a basket.
