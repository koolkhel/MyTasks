## Context

See proposal.md — Why for the motivation.

What was established against Textual 8.2.8 and the running app before this was
proposed, rather than assumed:

- A Cyrillic character arrives as its own key name: pressing `ф` gives
  `key='ф'`, `character='ф'`. Textual renames punctuation (`,` becomes
  `comma`, `.` becomes `full_stop`) but passes letters through untouched.
- `Binding("ф", ...)` fires its action. So does `Binding("Л", ...)`, so the
  shifted keys are reachable too.
- **A focused `Input` still receives those characters.** Typing `фуфайка`
  into a focused input left the value `фуфайка` and fired no action, and the
  same held for the Latin `aede` against bindings on `a` and `e`. Bindings
  only run when the board has focus. This was the one real risk: the app has
  been bitten before by a binding taking a key from a modal input.
- 27 bindings across five classes need a twin. `TaskInput` needs none.
- The key bar builds its entries from `binding.key.split(",")[0]`
  (`main.py:144`), so a binding that lists several keys already shows only
  the first.

## Goals / Non-Goals

**Goals:**

- One table of physical-key twins, stated once, used everywhere.
- No change to what is displayed.
- Nothing that could take a keystroke away from text being typed.

**Non-Goals:**

- No other layout. The mechanism would extend, but a table is only worth
  carrying for a language someone types in.
- No new keys, and no key moved.
- No attempt to detect the active layout. There is nothing to detect: both
  spellings are simply bound, and the one the keyboard sends is the one that
  arrives.

## Decisions

### The twin is added to the binding, not translated before dispatch

Each binding's key list gains the Cyrillic character, so `a` becomes `a,ф`.
Textual's own binding machinery then does the work.

Rejected: intercepting key events and rewriting Cyrillic to Latin before
dispatch. It would need only one hook rather than 27 edits, but it means
reimplementing which key reaches which context — the board, a modal, a
focused input — and getting that wrong is how a keystroke gets stolen from a
title being typed. The behaviour verified above comes free with bindings and
would have to be rebuilt by hand.

### The table is the whole layout, not only the keys in use

All 33 printable positions are recorded, not just the eighteen the board
currently binds. The table describes the keyboard, which is a fact
independent of this app, so a binding added later gets its twin without
anyone remembering that the table exists.

Expansion stays explicit: a helper turns `"a"` into `"a,ф"` and `"j,down"`
into `"j,down,о"`, and each binding calls it. Nothing is rewritten behind the
author's back, so reading the bindings still shows what they answer.

### Two keys go by Textual's names rather than their characters

`.` and `?` are `full_stop` and `question_mark` to Textual, and their twins
have to be written the same way:

    .  Did today  ->  ю          the physical . types ю
    ?  Help       ->  comma      Shift+/ types a comma in Russian, not ?

The `?` case is the one that is not a letter-for-letter swap: the Russian
layout puts the comma where the question mark is. Writing it as `comma`
rather than `,` also keeps it out of the way of the comma that separates keys
in a binding's key list.

### The display does not change

The bar and the help overlay name the English key alone. The bar's existing
`split(",")[0]` already yields that, so the twins cost no width — which is
what makes it safe to add eighteen of them to a bar that already wraps to two
rows.

Rejected: showing both spellings. It would roughly double the bar to tell a
person something their keycaps already say.

## Risks / Trade-offs

- **A binding could take a key from a title being typed** — the worst possible
  outcome, since it would corrupt text rather than merely fail → verified not
  to happen, and it is Textual's focus handling rather than anything in this
  change that prevents it; the check belongs in the tests so it stays true.
- **The table could be wrong for a layout variant** — this account's Russian
  layout is a third-party one, and its punctuation differs from the stock
  layout on the Option layer → the letters are the standard ЙЦУКЕН positions
  and the base layer's punctuation is standard, which is what this uses; the
  Option layer is not involved because none of these keys is pressed with it.
- **The help twin makes `,` open help in an English layout** — `?` and `,`
  sit on one physical key, so binding the character a Russian layout gives
  for `?` necessarily binds the character an English layout gives for `,`
  → accepted, and the only alternative is leaving help unreachable in
  Russian. It is confined to this one key: no letter twin can collide,
  because no English key produces a Cyrillic character, and the other
  punctuation twin (`/` to `.`) is bound to nothing. Opening help by
  accident costs one escape.

- **In a Russian layout the `/` key already types `.`** — so it fires "did
  today", and after this change both the physical `.` and `/` will → this
  predates the change and is a consequence of the layout, not of anything
  here; worth knowing rather than fixing, since no key is being taken away.
- **Twenty-seven call sites is twenty-seven chances to forget one** → the
  tests assert the property over every binding by walking the classes rather
  than by listing keys, so a binding added without its twin fails.
