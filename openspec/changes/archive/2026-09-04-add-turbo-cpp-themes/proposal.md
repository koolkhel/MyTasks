## Why

The board runs on Textual's stock theme and looks like every other Textual application. The wanted look is the Turbo C++ editor theme — the DOS-era yellow-on-dark with the cyan selection bar — in both the variants that theme ships.

The extension is installed locally, so the palettes are read from its own files rather than reconstructed from memory of what Borland looked like.

## What Changes

- Add two themes built from the extension's colour values: **Turbo C++ Dark** on a black ground, and **Turbo C++ Blue** on the classic `#0000AA`.
- The board starts in the dark one. Both are selectable while it runs, so switching needs no restart and no new key.
- Where the source gives a value that cannot work in this board, choose deliberately rather than copy: the blue variant's chrome is light grey and needs dark text on it, exactly as the original IDE had; and its "muted" colour is the same value as its foreground, so muted text needs a dimmed value instead of no distinction at all.
- Make the task list show the ground it is given. Three separate defaults were painting over it: alternating row shading, a list background of the raised surface colour rather than the ground, and a five-percent blend of the foreground over that. Together they turned a black ground into `#25251C`, so choosing a ground had almost no visible effect. The editor this theme comes from had none of the three. This is the one part of the change that is not purely a colour value, and it applies under every theme rather than only the Turbo ones.
- Nothing about the board's structure, behaviour or key bindings changes.

### Established rather than assumed

- The extension ships two themes. They share their foreground (`#FFFF55`), selection (`#00AAAA`), error (`#FF5555`) and link (`#55FFFF`) colours, and differ in **94 of their 183** interface colours — the difference is the whole chrome, not just the background.
- The palette is the DOS 16-colour set: `#FFFF55` yellow, `#00AAAA` cyan, `#FF5555` red, `#55FFFF` bright cyan, `#AAAAAA` grey, `#00AA00` green, `#FF55FF` magenta.
- The board references only seven theme tokens in its styling — `$text-muted`, `$panel`, `$accent`, `$text`, `$surface`, `$error`, `$name` — plus one it resolves at runtime for past-due titles.
- Textual's own theme object takes very nearly the same slots the editor theme provides, so the mapping is close to one-for-one.
- A stylesheet can ask for an automatically contrasting foreground, which resolves to black on the blue variant's light-grey chrome and white on the dark variant's near-black. That is what lets one stylesheet serve both themes without branching on which is active.

## Capabilities

### Modified Capabilities

- `task-board`: gains a requirement that these two themes are offered and which one starts, and a second requirement that whatever theme is active must preserve the distinctions the board's other requirements depend on. Nothing currently specified changes: the existing rule about a past-due title being "rendered in a colour that sets it apart" already names no colour, and the new requirement is what keeps it true under a different palette.

## Impact

- `main.py` — two theme definitions, their registration, the starting theme, and any styling rule that quietly assumes a dark panel.
- `singularity.py` — no change. This touches no query, no task and no request.
- No new dependency; Textual defines themes natively.
- The past-due colour is resolved at runtime from the active theme rather than hard-coded, so it follows the theme automatically — but its new value has to stay distinguishable from an ordinary title, which is why that is specified rather than assumed.
- The `^p` palette already lists every registered theme, so both become switchable with no new binding and no change to the key bar.
- The repo has no automated test suite; verification compares resolved colour values under each theme, which is checkable without a terminal.
