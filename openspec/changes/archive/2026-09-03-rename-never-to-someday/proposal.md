## Why

The board calls its dateless deferred bucket "Never". SingularityApp calls the same thing "Someday", and the underlying API field is literally `deferred`. Checking a task that was set to Someday in the app confirms it: it comes back as `start=None, deferred=true` and nothing else — byte-for-byte what the board has been presenting as Never.

So the option being asked for already exists, under a name that misrepresents it and disagrees with the app the board is a front-end for. "Never" reads as abandoned; `deferred` means postponed, which is a different intent and the one actually wanted.

## What Changes

- Rename the concept throughout: the bucket, the view it is reached by, the date-picker option, the header label, and the help text all say **Someday** instead of Never.
- The view and the picker option both move from the `n` key to `s`, leaving `n` unbound.
- **No stored data changes.** A someday task is `start=None, deferred=true`, exactly as a never task was, so nothing in the store is rewritten and the two tasks currently in the bucket simply appear under the correct name.

### Not in this change, and why

- **A separate "never" state.** The API cannot express one. `showInBasket` is the trash mechanism and the server rejects it outright (`showInBasket=true requires deleteDate to be set`); tags, task groups and kanban statuses are all `403 Forbidden [scope]` for this token; `group` cannot be created or enumerated for the same reason; `externalId` is writable but is not a filter field (`Unknown filter field: externalId.eq`) and is invisible in the app, so a distinction stored there would exist only inside this board. With `deferred` being the single dateless flag available, Someday is the one state there is.
- **Any notion of "this week".** The someday list is what a week's workload gets pulled *from*; the list itself carries no week, and the API has no field that would hold one.

## Capabilities

### Modified Capabilities

- `task-board`: the deferred bucket is renamed from never to someday. One requirement is replaced because its name changes, and ten more are reworded because their text names the bucket. No behaviour changes — every rule about what the bucket contains, how it orders, what it excludes and how it is reached stays exactly as specified.

## Impact

- `singularity.py` — the bucket enum member and its label.
- `main.py` — the two key bindings, the view action, the picker choice, the day-navigation status message, and the help overlay.
- No migration, no new dependency, and no request the client did not already send.
- One mechanical limitation worth recording: four scenario *titles* keep the word "never" — `Sending a task to never`, `Dating a task that was set to never`, `Never-ing a task that had a date`, and `Adding to never`. A `MODIFIED` block cannot rename a scenario, because the validator correctly treats a renamed scenario as a dropped one, and replacing those requirements under their own names is rejected (`Requirement present in both ADDED and REMOVED`). Their normative text is updated; only the titles lag. Cleaning them would mean renaming the parent requirements, which would misrepresent requirements that are not changing.
- The repo has no automated test suite; verification is through the Textual pilot harness and read-only checks against the live store.
