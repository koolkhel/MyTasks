## Why

Copying the marked rows writes markdown, and markdown is right for one of the
two editors these rows go to and wrong for the other.

TaskPaper puts its own `-` in front of every line and has no use for a box, so
a row copied from here arrives as `- - [ ] write it up` and has to be cleaned
up by hand. Joplin renders the same line as a checklist item, which is exactly
what is wanted there.

One key cannot serve both, and which one is needed depends on where the rows
are going rather than on anything the board knows.

## What Changes

- `y` copies the marked rows as **plain lines**: the row's title, one per
  line, and nothing else.
- `Y` copies them as **markdown**, which is precisely what `y` does today —
  `- [ ]`, `- [x]`, and a ticked box with a struck-through title for a
  cancelled task.
- Everything else about copying is the same for both keys: every marked row
  including one a filter is hiding, in the order the rows were marked, the
  title as the row carries it rather than as the column drew it, the marks
  left in place, and a refusal that leaves the clipboard alone when nothing
  is marked.
- The board says which form it copied, so a mis-hit is visible rather than
  discovered on paste.
- The help screen and the key bar name both keys.

**This changes what `y` already does.** Anyone with the habit gets plain lines
where they used to get markdown. That is the point of the request — the plain
form is the common case — but it is a change to a key that works today, not a
new key beside it.

### Recorded assumption

Plain means the title and nothing else, so **a finished task and an unfinished
one come out as the same line**, and a cancelled one loses its strike. There
is no way to say "done" in a plain line without inventing a marker, and this
board's rule for copy and paste has been that it is as simple as a notepad.

The consequence is worth stating rather than discovering: **a plain copy does
not round-trip.** Copy five rows with `y`, paste them back, and five
*unfinished* tasks arrive. `Y` round-trips; `y` does not. If a plain copy
should instead carry something like TaskPaper's `@done`, this assumption is
the thing to overturn, and it changes the spec rather than the plan.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *Copying the marked rows as text* becomes two keys with two
  forms. What each writes differs; everything else the requirement says about
  copying — which rows, in what order, which title, what happens with nothing
  marked — holds for both and is stated once.

## Impact

- **Code**: `main.py` only — one binding added, the copy action split in two,
  a plain form beside `as_markdown`, the notice, and the help text.
- **Dependencies**: none.
- **Keys**: `Y` is free. The board binds three uppercase keys today (`J`, `K`,
  `W`), and the layout-twin table already gives every uppercase letter its
  Russian twin, so `Y` gets `Н` without anything being added. The lowercase
  `y` bound on the confirmation dialog for "yes" is a different screen and is
  untouched.
- **Tests**: `tests/stub/t_copy.py` (40 checks) is the suite that reads what
  was copied; it grows a second form to check. Six other suites press `y`, all
  of them answering a confirmation rather than copying.
- **The key bar**: wraps rather than truncating, so an extra entry costs at
  most one row of height on a narrow terminal and hides nothing.
