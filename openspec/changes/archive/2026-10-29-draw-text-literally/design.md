## Context

See proposal.md for why. Two parsers are involved, and they disagree:

```
                           who parses it        escape() enough?
detail area, focus card    Textual markup       no  -- raises or drops text
status line, subtitle bar  Textual markup       no
prompts, picker options    Textual markup       no
table cells (rows)         Rich Text.from_markup  nearly -- a trailing "\" doubles
```

`escape()` is written for Rich's tag grammar (`[a-z#/@]…`). Textual 8 reads
more as a tag, so anything parsed by Textual leaks. Rows survive only
because `board.shortened` builds them with Rich's parser.

The leak is not limited to the `escape()` calls. Some foreign text reaches a
Textual-parsed widget with no escaping at all -- `board.tracker_facts` joins
an issue's state, project and fix versions into the detail line as they
come. Every place foreign text meets a parser has to be found, not only the
ones already guarded.

The board has already solved this once: the key bar (`main.py`, `rebuild`)
is built with `Content.assemble`, so nothing in it is parsed, and its comment
predicts this failure.

## Goals / Non-Goals

**Goals:**
- No foreign text is ever parsed for markup, in any widget.
- The board's own styling keeps working, attached as style.
- A single idiom per kind of site, so a new site picks the safe one by
  default.

**Non-Goals:**
- Changing the crash policy. `_handle_exception` still ends the session on an
  unanticipated failure.
- Catching `MarkupError` around drawing. It would hide the defect and leave
  text silently dropped -- the larger half of the bug never raises.
- Changing what any row, card or prompt says, or how it is laid out.

## Decisions

### 1. Hand the toolkit text, not markup -- three idioms by site

| site | idiom |
|---|---|
| a dialogue's question or title, and the options it lists | the dialogue draws what it is given as `Content(text)`, so callers quote a title in a plain f-string and none of them can get it wrong; no question carries styling of its own |
| text with no styling of its own (a note, the focus card's title and facts, the status line, the subtitle bar) | `Content(text)` |
| foreign text with board styling around it, should a widget ever need both | `Content.from_markup(template, title=…)`: the template is the board's own and is parsed; the `$` values are inserted as text and never parsed |
| table cells | `rich.text.Text` built with `Text.assemble` / `append(text, style)`, link as `Style(link=url)` |

During apply every dialogue question turned out to be a plain sentence, so
the dialogues take text rather than each call building a template; that also
covers questions a call-site list would miss. No site needed `from_markup`.

Measured on Textual 8.2.8 with `[--x=A-B] y`, `[A]`, `[$var]`, `a\[b]`,
`end\`, `$title` and `[b]x[/b]` as the value: `Content.from_markup` with a `$`
variable showed each one as written, and the template's own `[dim]` still
applied.

Alternatives considered:
- *Escape every `[`* (`s.replace("\\","\\\\").replace("[","\\[")`). Fixes the
  brackets but shows `a\[b]` as `a\\[b]` and `end\` as `end\\`: it is
  another guess at the parser's grammar, and the guess is what failed.
- *A stronger `escape` of our own.* Same problem: correct only for as long as
  it tracks a parser we do not own, across a Rich/Textual split that has
  already moved once.
- *`markup=False` on the widgets.* Works where a widget has no styling at
  all, but the status line, subtitle and rows all carry styling of their
  own; one idiom per kind of content is easier to keep right than a flag per
  widget. `Content(text)` gives the same effect where it applies.

### 2. Rows build Rich `Text`, not Textual `Content`

`DataTable` cells are Rich renderables, and `shortened` already truncates a
Rich `Text` with an ellipsis. `_markup_title` becomes a function returning
`Text`: the title as text, the link's span styled by `Style(link=url)` found
by position in the plain title rather than by matching escaped markup.
Prefixes (`↻ `, `≡ `), dim, strike and the count `(n)` are appended as styled
parts. `shortened` takes a `Text` and stops parsing.

Alternative: pass `Content` to the table. Not taken -- the table's own
currency is Rich, and truncation already works on it.

### 3. The subtitle bar becomes `Content` once, at the end

`search_note`, `work_note` and the subtitle builder pass strings that are
joined and then parsed. None of the parts carries styling of its own -- the
date, the work note, the search term and the mailbox mark are all plain --
so the parts stay strings and `with_mark` returns the finished line as
`Content(...)`. It measures `cell_length` rather than `len(markup)`, which
counted the escape backslashes as width.

Alternative, first planned: make every part `Content` and join with
`Content("  ·  ").join(...)`. Not needed while no part is styled, and it
would have changed four helpers' return types for no difference on screen.

`tracker_facts` and `series_facts` keep returning `str`; the detail area and
focus card turn them into `Content(...)` as foreign text.

### 4. A guard so the idiom stays

`t_markup` asserts that neither `main.py` nor `board.py`
imports `escape` from `textual.markup` or `rich.markup`. Once nothing
escapes, the next site to need it is a site about to be written wrongly.

## Risks / Trade-offs

- [A site is missed, especially one with no `escape()` today] → The inventory
  in tasks.md is built from every `update(`, `Static(`, `Label(`, `Option(`,
  prompt constructor and row cell, not from the `escape(` list alone; the
  guard in decision 4 catches regressions only for sites that would import
  `escape`.
- [A link span moves when the title is shortened] → Build the span on the
  plain title before truncation; Rich's `truncate` keeps spans that survive
  the cut. Covered by the existing link-in-a-row suites.
- [`Content.from_markup` templates written with an f-string by habit, which
  parses the value again] → No site needed one in the end. A future one
  keeps its template a plain string literal and passes values only as
  keyword arguments; the hostile-shape suites would show a value consumed.
- [The board's own styling changes slightly where escaped markup and
  assembled styles differ] → The existing suites that read what is drawn
  (`visual.plain`, the composited screen) keep passing unchanged; anything
  they catch is a regression.

## Migration Plan

None. No stored data or configuration changes. Rollback is a revert.
