## Why

The board ended the session twice in a row on 2026-10-29: the cursor landed on
a mail row whose body quoted a command's usage line, the detail area drew it,
and Textual raised `MarkupError: Expected markup value` on a shape like
`[--option=A-B]`. The note had been escaped first. `textual.markup.escape` is
Rich's escape carried over -- it guards only a `[` followed by a lowercase
letter, `#`, `/` or `@` -- while Textual 8's own parser also reads `[A…`,
`[-…`, `[$…` and `[_…` as tags. What the escape misses either raises, ending
the session through the crash handler, or is silently consumed: `[A]`,
`[$var]`, `[_x]` and `[--k=SECS]` vanish from the screen while staying whole
in the store. The row cannot be selected at all while that note holds the
shape, so a person cannot finish the task on the board.

The spec already says text the board did not write is shown as its
characters. The means it names -- escaping before drawing -- is what fails,
and the suite that checks it uses only lowercase shapes, which the escape does
cover.

## What Changes

- Text the board did not write -- titles, notes, mail subjects and senders,
  calendar and project names, labels, the search term, and anything quoted in
  the status line or a prompt -- is handed to the toolkit as text, never as
  markup to be parsed. Styling the board adds around it (dim, strike, a link)
  is attached as style, not written as tags around escaped text.
- Every `escape()` call in `main.py` and `board.py` goes; nothing in the
  board relies on escaping any more.
- Table rows, which Rich parses and which therefore did not crash, move to
  the same footing, which also stops a title ending in a backslash being
  shown with two.
- The crash policy is unchanged: an unanticipated failure still ends the
  session. The fix removes this failure rather than surviving it.
- The detail requirement stops naming escaping as the mechanism and states
  the outcome; scenarios are added for the shapes that crashed or vanished.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: the detail area's note rule is restated as an outcome rather
  than a mechanism, and a requirement is added that text the board did not
  write is shown as its characters whatever its shape, in every place it is
  drawn, and that drawing it can never end the session.

## Impact

- `main.py`: the detail area, focus card, status line, subtitle bar (search
  term), and every prompt and picker that quotes a title, project name or
  label (date, project, link, note, delete, version).
- `board.py`: `_markup_title`, `row_for` for tasks, mail, tracker and event
  rows, and `shortened`, which today parses markup to build a cell.
- `tests/stub/t_markup.py`, `tests/stub/t_note.py` and the row suites gain the
  shapes Textual and Rich parse differently.
- No dependency changes; Textual 8.2.8's `Content` already provides what is
  needed.
