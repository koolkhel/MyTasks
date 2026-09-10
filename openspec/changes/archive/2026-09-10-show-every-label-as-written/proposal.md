## Why

The key bar shows `[[/b] Note up` where it should show `[ Note up`. The key it
draws is a `[`, and it is interpolated into a markup string — so the character
opens a tag and the closing `[/b]` is left on screen as text.

The toolkit changed under this. Rich's markup parser, which the board used to
draw through, reads `[[` as an escaped bracket and renders the entry correctly;
Textual 8 parses markup itself and does not, so the same string that was right
became wrong with no change to the board. The same mechanism is at work in two
more places, where it does not leave debris but silently swallows text: a task
titled `[draft] something` shows as ` something` in a prompt, and any status
message naming such a task loses part of the name.

## What Changes

- The key bar escapes what it draws, so a key that is a bracket appears as a
  bracket and the bar's own bold and dim still apply.
- The status line escapes the message it is given. Nothing that reaches it is
  markup: none of its callers pass any, and its content is the board's own
  sentences with a task's title quoted inside them.
- The dialogue prompts built from a task's title are escaped — the date,
  project and link pickers, the note editor, and the confirmation before
  deleting.
- The checks assert what is drawn, not only what was assembled. That is the
  hole this fell through: the suites check the bar's entries and its packing,
  both of which are correct, and nothing looked at the rendered row.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *The key bar names each action once, by its English key*
  already promises that a key whose toolkit name is a word is shown as the
  character a person presses, and names the bracket as an example. That
  promise is kept as far as the entry and lost when the entry is drawn, so it
  gains a scenario about the drawn bar. Beside it, one added requirement puts
  the status line and the prompts under the rule the rows, the notes and the
  focus card already follow: text the board did not write is shown as its
  characters.

## Impact

- `main.py`: `KeyBar.rebuild`, `set_status`, and the six prompts built from a
  task's title. No new dependency — `textual.markup.escape` is already
  imported and used for every row, note and card.
- `tests/stub/`: the key bar's drawn row, the status line, and the prompts.
- No API, storage or configuration surface changes.
