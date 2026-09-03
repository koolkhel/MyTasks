## Why

The board binds sixteen keys and advertises them in a single-row footer that does not fit. Measured against the real app rather than estimated: the entries need roughly 174 cells plus the command-palette hint, and the footer truncates at **every** width tried — at 160 columns `? Help` is cut, at 120 everything from `Cancel` onward, and at 80 it breaks mid-word at `r Relo`.

The four that disappear first are cancel, set-date, delete and help — including the one key that would have listed all the others. A person who cannot see `? Help` has no route to the keys the footer just hid.

## What Changes

- Replace the single-row footer with a key bar that wraps, so no label is ever clipped and none is dropped. At the widths this board is used at that is two rows; at 80 columns it needs three, because two rows of 80 cells cannot hold ~174 cells of entries.
- The bar SHALL list exactly the keys the board binds, the same guarantee the help overlay already carries, so a future binding cannot quietly go unadvertised.

### Not in this change

- **Refresh.** The request that prompted this also asked for a way to see changes made in the SingularityApp — but `r` already does that. Verified against the live API with the board open: an external add, an external rename, an external completion and an external deletion were each picked up on pressing `r`. Nothing to build; it was hidden rather than missing, which is the same problem this change fixes.

## Capabilities

### Modified Capabilities

- `task-board`: gains a requirement for the always-visible key bar. Nothing currently specified changes — the footer is not mentioned anywhere in the capability today, so this closes a gap rather than altering behaviour.

## Impact

- `main.py` — the layout swaps the built-in footer for a small widget, plus its styling. Nothing else in the file changes.
- `singularity.py` — no change. This touches no query, no write, and no task.
- No new dependency, and no change to `run.sh`, `requirements.txt`, or `.env`.
- What the built-in footer contributes and a replacement has to account for: the `^p palette` hint, and clicking an entry to invoke it. Both are conveniences rather than the board's own behaviour, and the design records which are kept.
- Measurements recorded as the state that motivated the change, not as fixtures: 16 shown bindings, ~174 cells of entries, truncation at 80, 100, 120 and 160 columns.
- The repo has no automated test suite; verification is by rendering the board at several widths and reading the result, which is how the truncation was found.
