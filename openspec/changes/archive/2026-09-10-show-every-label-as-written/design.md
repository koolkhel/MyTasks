## Context

See proposal.md — Why.

Three facts decide the shape of this.

- `textual.markup.escape` is already imported in `main.py` and already applied
  to every title, note, sender, calendar name and subject the board draws. The
  rule exists; three places do not follow it.
- The three differ in whether they need markup of their own. The key bar draws
  `[b]key[/b] [dim]label[/dim]` and cannot stop parsing markup. The status line
  and the prompts pass a plain sentence to a widget that parses markup because
  that is the widget's default, not because anything wants it.
- Measured, not assumed: of the 42 calls to `notice` and `set_status`, none
  passes markup.

## Goals / Non-Goals

**Goals**

- The bracket keys read as brackets on screen.
- A task's title survives into every prompt and every message that quotes it.
- Checks that look at what is drawn, since what is assembled was already right.

**Non-Goals**

- Changing any label's wording. `Note up` and `Note down` stay as they are;
  what was wrong was the drawing, not the words.
- Auditing every widget in the board. The three places are the ones where text
  the board did not write, or a character the toolkit treats as styling, reach
  a markup-parsing widget.
- Upgrading or pinning Textual. The board should draw correctly on a parser
  that does not accept `[[`, which is the current one.

## Decisions

### Escaping fixes the text, and cannot fix the bar

Escaping is what every other drawing site here already does, and it is the
right answer for the status line and the prompts: each of those draws one
string, and escaping it before it is drawn is a one-line rule a reader can
check.

It cannot fix the key bar, and the reason is worth writing down because the
first attempt at this change assumed it could. `textual.markup.escape`
escapes a bracket that *begins something tag-shaped* — its own pattern is
`\[[a-z#/@][^[]*?]` — which is exactly right for text: a lone `[` in a
sentence begins nothing and cannot be taken for styling, so it is returned
unchanged. The bar is not that case. There the escaped fragment is
concatenated with markup that follows it, so the untouched `[` merges with
the `[/b]` written after it and the pair is mangled. `escape` applied to the
key is a no-op, and the bar still read `[[/b] Note up` with the fix in place.

So the bar is assembled as styled text instead: `Content.assemble`, with
bold and dim carried by the text rather than written around it. Nothing is
parsed, so no key can break the bar again whatever character it is — which is
a stronger guarantee than escaping could give, since the bar's entries come
from the bindings and the next one is not ours to predict.

Rejected: `markup=False` on the widgets. It would fix the status line and the
prompts and express the intent exactly, but it cannot fix the bar either — the
bar needs its own bold and dim — so it would leave the same two mechanisms
with the harder one still to write.

Rejected: escaping the bracket with a rule of our own, `"[" -> "\\["`. It
works, and it is one line, but it reimplements a piece of the toolkit's markup
grammar in the board and would have to be revisited every time that grammar
moves. The bar has no need of markup at all.

### Escaped where it is drawn, not where it is built

The status line escapes inside `set_status`, once, rather than at each of the
42 calls that reach it. A rule applied at the boundary cannot be forgotten by
the next caller, and every one of those calls passes a sentence rather than
markup, so there is nothing to lose.

The prompts are the other way round: each is built by its own call site from a
title, and the dialogue classes are shared with prompts that carry no title at
all. Escaping the title where it is interpolated keeps the escaping next to the
thing that needs it, and leaves a dialogue free to be given markup later if
some prompt ever wants it.

The key bar escapes both the key and the label. The label needs it only in
principle — every description today is plain words — but the bar builds its
entries from the bindings, and a binding described with a bracket some day
should not be able to break the bar again.

### Why this was not caught

The suites check `KeyBar.entries()` and `KeyBar.pack()`. Both were and are
correct: the entry for the bracket key is `("[", "Note up")`, and the packing
puts it where it belongs. The step that breaks is the one between the entry and
the screen, and nothing looked there. So the checks this change adds read the
drawn row and the drawn prompt, and a check that reads only the entries would
pass on the broken board — which is the definition of the wrong instrument.

## Risks / Trade-offs

- **A message that wanted markup would now show it as text** → none does, and
  the status line's error colour is a CSS class rather than markup, so it is
  unaffected. A caller that ever wants markup in the status has to say so
  rather than getting it by default, which is the safer direction.
- **Double escaping** — a caller that escapes a title and then reaches the
  status line, which escapes again, would show a backslash → the fix is applied
  in one place per string: the status line escapes the whole message and no
  caller escapes anything for it. The prompts escape the title and nothing
  escapes them afterwards, because a prompt is not passed through the status.
- **A suite reading the status as raw markup sees the escape** → the checks
  compare the drawn text rather than the assembled string, which is what they
  should have done from the start.
- **Two mechanisms for one rule** — the bar carries its styles, everything else
  escapes → the line between them is not taste but a fact about the toolkit: a
  whole string that is drawn as-is can be escaped, a fragment placed next to
  markup cannot. Said here so the next person does not "make it consistent" by
  putting the bracket back into a markup string.
- **The toolkit changes its parser again** → the checks assert the drawn text,
  so a parser that stops accepting the escape fails them rather than shipping.

## Migration Plan

None. No stored data, no configuration and no key changes; the same keys draw
differently.
