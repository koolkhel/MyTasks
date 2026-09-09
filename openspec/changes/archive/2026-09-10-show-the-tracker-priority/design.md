## Context

See proposal.md — Why. What was measured against the real tracker, since most
of the decisions rest on it:

- `ISSUE_FIELDS` asks for `customFields(name,value(name,login))` — every custom
  field, not a named few — and `_custom_fields` keeps each dict-valued one
  under its own name. So `fields["Priority"]` is already populated on every
  fetch and simply never read.
- The API's own value names are English: `Show-stopper`, `Critical`, `Major`,
  `Normal`, `Minor`. Asking for `localizedName` on the value returns the names
  a person reads in the tracker's interface, and their first letters are
  Н, К, С, О and Н.
- The same priority is worded differently in different definitions —
  Обычный / Обычная, Серьезная / Серьезный, Неотложная / Неотложный,
  Критический / Критическая. First letter unchanged in every pair.
- **Н is Неотложн— (most urgent) and Незначительн— (least).** Confirmed from
  the whole vocabulary, not inferred.
- Colour is supplied per value and is not usable: Critical is `#e30000` in one
  definition and `#ffc8ea` in another, and in the first it is the *same* red as
  Show-stopper.
- Ordinals are not comparable: one definition runs -2, -1, 1, 3, 5 and another
  0, 2, 3, 4, 5, and in the first Critical sorts above Show-stopper.
- The leftmost column is declared one cell wide and carries the configured
  tag's mark. `is_green` returns False for a tracker row "which the board made
  up rather than fetched and which carries no tags at all", so that cell is
  empty on exactly the rows a letter would fill.
- Column 1 already means different things by row kind — a checkbox for a task,
  `▸`, `@` or `◇` for the three sources — so a column whose meaning depends on
  the kind of row is the established pattern rather than a new one.

## Goals / Non-Goals

**Goals:**

- The board holds no list of the tracker's priorities.
- One letter, one cell, legible without colour.

**Non-Goals:**

- Colour, and ordering by priority. Ruled out on the measurements above, not
  on taste — both would encode a comparison the tracker does not actually
  make. Recorded in the proposal so a later reader does not re-propose them.
- Colour is out for a second reason, which would have been enough on its own:
  the board has two themes, and the tracker's palette is fixed hex — `#e30000`,
  `#ffee9c`, `#e6f6cf` — with no relation to either theme's ground. This
  repository has already paid for that once. The header was drawn in the
  framework's declared colours and measured 2.18:1 in the blue theme, which is
  not readable, where the same declaration measured 17.27:1 on the dark one;
  the fix was to stop using the declared colour and is recorded beside the
  rule it departs from. A priority colour taken from the tracker would be the
  same mistake with a palette nobody here controls. A letter reads on both
  themes because it is not a colour at all.
- Priority in the detail pane, in the status line, or as a filter. The ask is
  a letter on the row.
- Any way to change a priority. A tracker row refuses writes and gains no key.
- Reopening SingularityApp's own priority, which an archived change removed
  from the board deliberately. Different system, writable, and not this.

## Decisions

### The letter comes from the tracker's word, not from a table

`Issue` gains the localised name of its priority, and the row's letter is that
name's first character. `ISSUE_FIELDS` becomes
`customFields(name,value(name,localizedName,login))` — one token, the same
request, the same page size, no extra call.

The alternative was a mapping in the board's source from the English value to
a Cyrillic letter. It reads simply and is wrong twice over: it would need
editing when the tracker adds or renames a priority, and it would put a
decision about a person's tracker into a repository that gets shared. The
board already refuses that shape for states, keeping the tracker's last word
rather than a list of states, and for the work project, which is configured
rather than named in source.

What the board does keep is the rule *first letter, upper case unless it is the
least urgent*. That is a presentation rule about letters, not a list of
priorities.

### The least urgent is identified by the tracker's own order, read per definition

Lower case needs to be applied to exactly one priority, so the board has to
know which is least urgent — and the ordinals are not comparable between
definitions. They are, however, ordered *within* one: the largest ordinal in
the definition an issue's priority came from is its least urgent value.

That is more than one issue's own value can answer, so the practical rule is
the one the vocabulary supports: match the API's value name, which is stable
English regardless of how the tracker is localised, and lower-case the letter
for `Minor`. The English name is not shown to anybody; it is used only to
decide a case. If a tracker had no `Minor`, nothing is lower-cased and nothing
is wrong.

Alternatives considered:

- *Lower-case by ordinal.* Needs the definition's full range, which an issue's
  value does not carry; fetching bundles is a second endpoint and admin
  permission the board should not need.
- *Lower-case whenever the letter collides with another shown row's.* Makes a
  row's appearance depend on what else is on screen, so the same issue reads
  differently on different days.

### The letter goes in the leftmost column, which is free for these rows

No cell moves and no column is added. The column keeps the tag mark for tasks
and takes the priority for tracker rows, which is what column 1 already does
with the source marks.

Rejected: a column of its own. It would cost a cell of width on every view for
a value only today's tracker rows have, and the title column is already fitted
to what is left.

### Cyrillic in a one-cell column is a departure, taken deliberately

A Cyrillic capital is East Asian Width *Ambiguous*, which the mailbox marks
avoid on purpose — an Ambiguous character may render two cells wide in a
terminal configured for CJK, and this column is one wide. In this board's
locale it is one cell, and the board already draws Cyrillic titles.

Taken anyway, because the alternative is a letter from an alphabet the person
does not read the tracker in — the English first letters collide worse
(`Major` and `Minor` both M) and would mean nothing at a glance. Recorded here
and asserted in the suites so the departure is visible rather than discovered:
the letters are checked to be one character each, and the row is checked to
draw with the same cells at the widths the board is used at.

## Risks / Trade-offs

- **A CJK-configured terminal could widen the letter to two cells** → accepted
  and documented above; the suites assert the letters are single characters and
  that a row's other cells are unchanged, so a widening shows up as a layout
  failure rather than as a wrong letter.
- **`Minor` matched by its English name is a string in the source** → true, and
  it is the API's stable value name rather than anything about this account or
  its projects. Nothing private, and nothing a person sees.
- **A priority the tracker adds gets a letter nobody chose** → deliberate: an
  unknown priority shows its own first letter, upper case, which is more useful
  than showing nothing and cannot be wrong about what the tracker calls it. If
  it collides with another letter, the two read alike — the same situation the
  spec already accepts for two states ending in the same word.
- **A tracker with no localisation** → `localizedName` may be absent, in which
  case the English value name's first letter is used. It is the tracker's own
  word either way, which is what the rule says.
- **The leftmost column now means two things** → already true of column 1, and
  the two cannot occur on one row: a task has no priority to show and a tracker
  row has no tags.
