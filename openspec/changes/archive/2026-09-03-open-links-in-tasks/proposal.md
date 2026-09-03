## Why

Six task titles carry a link, and every one of them is currently unusable. Five are stored as HTML — `<a href="https://…">https://…</a>` — which the board renders literally, so a row reads `<a href="https://habr.com/ru/articles/1055…` and the actual address is both mangled and unreachable without opening the app on another device.

## What Changes

- Recognise a link in a task title: an HTML anchor's `href`, or a plain `http`/`https` address written in the title. The row and the focus card show the readable address instead of the raw HTML.
- Add an **open link** action on the `o` key, which hands the address to the operating system the way `open` does. This is the guaranteed path: it needs no mouse and does not depend on the terminal.
- Also render the address as a link span, so a terminal that supports hyperlinks makes it clickable directly. This is a bonus on top of the key, not the mechanism relied on.
- Only `http` and `https` addresses are opened. A title is ordinary text that happens to be handed to the operating system's opener, and nothing else should be launchable through it.
- An address with no scheme is treated as `https`. One of them is stored as `academia.edu`, which would otherwise fail to open.

### Established rather than assumed

- The stored links: five HTML anchors plus one address written plainly into a title, all resolving to `https` once the bare domain gains a scheme. In every anchor the visible text equals its `href`, and each title carries 13–75 further characters of ordinary text around the link.
- **No note contains a link**, and no title or note uses a markdown link. A plainly written address did turn up in a title while this change was being implemented, so recognising that form is load-bearing rather than the future-proofing it looked like at planning time.
- Textual's markup requires the address to be quoted: `[link='https://…']` is accepted while `[link=https://…]` raises a markup error.
- **Whether clicking works cannot be verified here.** A hyperlink is rendered by the terminal, not the application, and neither a link span nor a click action fired under the headless test harness. The key exists precisely so the feature does not rest on that.

### Not in this change

- **Notes.** Scanning note bodies was a separate option and was not taken, and no note holds a link. Titles only. Worth saying because the note is shown in the detail strip and the focus card rather than the row, so "the selected task's link" would need a tie-break rule that nothing currently needs.

## Capabilities

### Modified Capabilities

- `task-board`: gains link recognition, an action to open one, and the display rule that stops raw HTML reaching the row. Two existing requirements change — the row presentation, and the list of actions on the selected task.

## Impact

- `singularity.py` — a way to extract a task's link and its display title, which is a property of a task rather than of the board.
- `main.py` — the row and focus-card rendering, one binding and its action, the help overlay, and the key bar picks the new entry up on its own.
- No new dependency; the standard library opens the address and Textual already exposes the call.
- **Escaping becomes load-bearing.** Titles are already passed through markup, so a title containing `[` is silently mangled today — `Plan [urgent] thing` renders as `Plan  thing`. No title contains one right now, but this change constructs markup around titles deliberately, so the escaping has to be explicit rather than accidental.
- The repo has no automated test suite; verification uses synthetic tasks for the extraction rules and a stubbed opener, so nothing launches a browser and no real task is touched.
