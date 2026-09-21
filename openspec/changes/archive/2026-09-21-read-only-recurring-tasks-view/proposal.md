## Why

A repeating task is the one thing on this board that only the official app can
explain. The board knows a task repeats and draws a glyph for it, and that is
all it knows: `recurring` is a boolean read off the presence of a `recurrence`
object. What the repeat actually says, when it next comes round, whether it
waits for the current one to be finished or stacks the next ones up regardless,
and how many are already stacked — none of that is anywhere but in the app this
board exists to need less.

It is also the answer to a question that is hard to ask any other way: what am I
signed up for? A repeat made once and forgotten goes on producing rows for
years. Probing the store during exploration found eighteen series quietly
responsible for four hundred and fifty-eight of the five hundred and thirty-two
live tasks on the account, some materialised out to 2028.

The store will not let the board author a repeat — neither the create nor the
update body has a recurrence field — so reading is the whole of what is
reachable. That is enough to be worth having, and it is worth having first.

## What Changes

- A new view, reached by `R`, listing every recurring series the account holds
  and nothing else. The board's fifth view, beside today, the inbox, the someday
  view and the archive.
- A series row SHALL say, in the notes pane, what its repeat means in words,
  whether it waits for completion or stacks up regardless, how many occurrences
  are already queued and how far ahead they run, and when the series ends. The
  row's own columns carry the next occurrence, the title and the project.
- Every write SHALL be refused in this view, and the board SHALL say so. This is
  deliberate and not merely unimplemented: a series row is a real, writable task,
  and nobody yet knows whether renaming or rescheduling one reaches the
  occurrences it has already generated. Finding that out is its own change.
- A repeat the board cannot read SHALL be said to be unreadable rather than
  guessed at. The store's own API documents the recurrence object as having no
  fields at all, so its shape is known only by observation and an unfamiliar one
  is a matter of when, not if.
- The view SHALL be fetched when it is first asked for and held until a reload,
  as the archive is, and SHALL be drawn as its pages arrive rather than after the
  last of them.
- **BREAKING** nothing. No existing view, key, count or write changes behaviour.

Not in scope: authoring or editing a repeat, which the store's API does not
offer; the occurrences themselves, which appear on their own days as they
already do; and the recurring glyph landing on series rather than on
occurrences, which is a real defect found during exploration and needs its own
decision about what an occurrence should show.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `task-board`: adds requirements for a recurring-series view — what it holds,
  what each row says about its repeat, that every write is refused, and that an
  unreadable repeat is reported rather than guessed. Modifies the requirement
  naming the view being shown, which counts the views and must now count five.

## Impact

- `singularity.py`: the `Task` facts a series exposes. `recurring` stays what it
  is; the repeat's rule, its next occurrence, its ending and its
  wait-or-stack flag become readable, and an occurrence's link back to its
  series becomes readable with them.
- `board.py`: a sentinel position for the view, the rows it holds, the row
  mapping and the pane's facts line, beside the ones the tracker already has.
- `main.py`: the key, the action, the fetch held until reload, the view's name
  and count in the day bar, and the refusal that covers every write.
- `tests/`: a self-contained suite for the view and the rule-to-words
  translation, and a store-tier suite reading real series shape as counts.
- `README.md`: the key bar and the view list.
- No new dependency, no configuration, and nothing a person must do after
  upgrading.
