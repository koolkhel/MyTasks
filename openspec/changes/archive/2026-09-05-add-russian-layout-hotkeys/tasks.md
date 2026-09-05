## 1. The twin table

- [x] 1.1 Add a table mapping each printable physical key to the character it types in a Russian layout, covering all 33 positions rather than only those bound today, and including the shifted letters; verify a check that `a` maps to `ф`, `k` to `л`, `K` to `Л`, and that the table is a bijection with no character appearing twice
- [x] 1.2 Add the two entries that go by Textual's key names rather than their characters — `full_stop` to `ю`, and `question_mark` to `comma` because the Russian layout puts a comma where the question mark is; verify a check that expanding each yields the expected key string
- [x] 1.3 Add the helper that expands a binding's key list, leaving a key with no twin untouched; verify a check that it turns `a` into `a,ф`, `j,down` into `j,down,о`, `K` into `K,Л`, and `escape` into `escape` unchanged

## 2. Applying it to every binding

- [x] 2.1 Expand the bindings on `TaskApp`; verify with `Pilot` that each of q, j, k, K, J, h, l, t, i, s, r, a, e, x, d, o, the did-today key and the help key runs the same action when its Russian character is pressed as when the English one is
- [x] 2.2 Expand the bindings on `DatePicker`; verify with `Pilot` that opening the picker and pressing the Russian character for each of its five choices takes that choice
- [x] 2.3 Expand the bindings on `Confirm`; verify with `Pilot` that a deletion confirmation is answered by the Russian characters for both yes and no
- [x] 2.4 Expand the bindings on `TaskFocus` and `Help`; verify with `Pilot` that each closes on the Russian character for its close key
- [x] 2.5 Confirm `TaskInput` needs nothing; verify a check that every key it binds is one whose character does not change with the layout

## 3. The property, asserted over every binding

- [x] 3.1 Add a check that walks every binding on every class and asserts that any key with a twin in the table has that twin in its key list, so a binding added later without one fails rather than being missed; verify it passes now and fails when a twin is removed from one binding
- [x] 3.2 Confirm no twin collides: verify a check that no Russian character added is already bound in the same context, and that no two actions in one context want the same character
- [x] 3.3 Confirm the keys that need nothing are left alone; verify a check that space, enter, escape, backspace, delete and the four arrows appear in no expansion

## 4. Typing is unaffected

- [x] 4.1 Verify with `Pilot` that typing a Russian title containing characters the board binds — including `ф`, `у`, `в` and `щ` — puts every character into the add prompt and runs no action
- [x] 4.2 Verify the same for renaming, and for the date picker's typed date field, so no prompt loses a keystroke to a binding
- [x] 4.3 Verify the whole reported flow with `Pilot`: add a task, type a Russian title, confirm, then press the Russian add character again and check the prompt reopens without a layout change

## 5. What is displayed

- [x] 5.1 Confirm the key bar still names only the English keys; verify a check that no entry it produces contains a Cyrillic character, and that its entries are unchanged from before this change
- [x] 5.2 Confirm the bar is no wider than before; verify a check that packing its entries at several widths yields the same rows as it did before the twins were added
- [x] 5.3 Add the line to the help overlay saying the keys work in either layout, naming no key; verify a check that the overlay contains the line and no Cyrillic character
- [x] 5.4 Confirm the bar and the overlay still agree; verify a check that every key the bar names is described in the overlay

## 6. Verify in the running app

- [x] 6.1 Exercise the reported flow end to end against the real API on a far-future day: add a task with a Russian title using the Russian add key, rename it with the Russian rename key, set its date through the picker using Russian keys, then delete it through the confirmation using the Russian yes key; select by task id before each keypress and confirm each effect by re-fetching
- [x] 6.2 Confirm no regression in the existing behaviour: verify the previously passing suites still pass, and that today's view, the inbox and the someday view show the same tasks and counts as captures taken beforehand
