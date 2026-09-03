## 1. The wrapping key bar

- [x] 1.1 Add a widget that reads the board's shown bindings, renders each as its key and description, and packs them into as many rows as the available width needs; verify the entries it produces match the board's bindings exactly — same count, same order, no entry invented or dropped.
- [x] 1.2 Pack by measured width rather than in equal cells; verify that at a width where two rows suffice the packing uses two, that no row exceeds the available width, and that no entry is split across rows.
- [x] 1.3 Include the command-palette hint as an entry so the existing route into the palette survives; verify it appears once and is not what gets pushed off.
- [x] 1.4 Re-pack when the terminal is resized; verify that a board rendered wide and then narrowed re-flows to more rows instead of clipping, and that widening again reduces the rows.

## 2. Put it on the board

- [x] 2.1 Swap the single-row footer for the new widget in the layout, and confirm the widget cannot take focus or consume key events; verify that every advertised key still reaches its action — check movement, a view switch, and an action that opens a modal — since a display that stole focus would silently disable the keys it advertises.
- [x] 2.2 Give the task list the remaining height; verify the day header, the task rows and the status line are all still visible with the bar taking two rows, and that nothing overlaps.

## 3. Verify it actually fits

- [x] 3.1 Render the board at 80, 100, 120, 160 and 200 columns and verify at each that every one of the board's shown descriptions appears in full, that none appears as a partial word, and that none appears twice. These are the widths where the current footer was measured to truncate, so each is a case that must now pass.
- [x] 3.2 Confirm the bar and the help overlay agree: verify every key the bar names is described in the overlay and that neither names a key the board does not bind, comparing both against the bindings rather than against each other alone.
- [x] 3.3 Confirm nothing else regressed: the inbox still reports its shown and filed counts, today still gathers past-due tasks with their ages, `r` still reloads, and the focus card, date picker and delete confirmation all still open — with any destructive keypress confined to a day holding no real tasks.
- [x] 3.4 Confirm this change reads and writes nothing: with a request spy, render the board at several widths and switch views, and verify no POST, PATCH or DELETE was sent and that a before-and-after snapshot of today and both buckets is identical.
