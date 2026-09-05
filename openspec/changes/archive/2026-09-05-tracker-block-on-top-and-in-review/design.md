## Context

See proposal.md — Why for the motivation.

Measured against the live tracker before proposing:

- For this person and these projects: one issue in progress, eleven in
  review, twelve together.
- The tracker takes several states in one query as a comma-separated list of
  braced names, and returns twelve for the pair.
- Today holds twenty-five of the board's own tasks, so the block becomes
  twelve rows above twenty-five. On a thirty-row terminal, with the header,
  day bar, detail pane, status line and two-row key bar taking about eight,
  most of the day's own tasks fall below the fold.

What the existing implementation already does, which decides how small this is:

- The block is concatenated after the day's rows have been selected, filtered
  and sorted. Moving it is changing which side of that concatenation it goes.
- The filter that hides work is applied to the block separately, because
  concatenation happens after filtering. That stays true whichever side it
  joins, and is the thing most easily broken by moving it.
- A row's second column is filled with the literal word "tracker", which the
  row's own mark already conveys.
- The selection is decided by which task it belongs on and, on arrival, by
  row number — so with the block on top the first row is a tracker row.

## Goals / Non-Goals

**Goals:**

- Both changes together, because either alone is worse than neither.
- Tell the two states apart without opening an issue.
- Keep the two structural guarantees the block already has.

**Non-Goals:**

- No colour. The mark distinguishes a tracker row from a task and the state
  label distinguishes tracker rows from each other; that is the distinction
  asked for, and the palette already carries five meanings.
- No skipping the block with the cursor. Starting on the first row is the
  rule the board already follows, and keeping it is worth more than avoiding
  one refused keypress.
- No limit on how many issues are shown. If twelve rows prove too many, the
  answer is to configure fewer states, which is why the states are configured.

## Decisions

### The states are a list, and their order is the block's order

One configured state becomes several, and the order they are configured in is
the order the block is grouped in. That gives the block a meaningful sequence
without inventing a ranking: whoever configures the states has already said
which matters most by writing it first.

Sorting is therefore by the state's position in that list, then by key — the
key part unchanged, so the order within a state stays stable between fetches
as it does today.

Rejected: ranking states by a built-in notion of importance. It would need a
table of state names in the source, which is exactly what configuring them
was meant to avoid.

### The state goes in the column that said "tracker"

That column is eight characters and currently holds a constant. `In progress`
does not fit, but the leading `In ` is noise once the column is only ever a
state, and `progress` is exactly eight. So the state is shown with a leading
`In ` dropped, and truncated if some future state is still too long.

This is the whole of the visual distinction, and it costs nothing: the column
exists, is the right width, and was carrying a word the row's mark already
said.

Rejected: colour. Five colours already mean something in a row — ordinary,
past due, finished, link, muted — and a sixth for "not yours" would be read
against those. A label says it outright.

### Moving the block is changing a concatenation, not the ordering

The block joins before the day's rows rather than after. Both guarantees hold
unchanged and for the same reason as before: it is not in the list being
sorted, so it cannot be interleaved or reordered.

The one thing that must move with it is the work filter, which is applied to
the block separately because concatenation happens after filtering. Nothing
about that changes — but it is the part that would silently half-work if it
were forgotten, so it is worth naming again rather than assuming last time's
reasoning carries.

### The count stops naming a state

What the board reports about the block cannot go on calling twelve issues "in
progress" when eleven of them are not. It reports how many it is tracking;
which state each is in is on the row.

## Risks / Trade-offs

- **Twelve rows above twenty-five push the day below the fold** — the reason
  both changes had to be weighed together → accepted knowingly, mitigated by
  ordering the block so the issue actually being worked on is its first row,
  and configurable by removing a state; the alternative, limiting the block,
  would hide work without saying so.
- **The first keypress after opening is refused** — the cursor starts on a
  read-only row → accepted; the refusal names the issue and says it lives in
  the tracker, which is a better first lesson than a silent no-op.
- **A configured state that matches nothing looks like an empty state** —
  a renamed state would quietly contribute no rows → it contributes nothing
  rather than failing, and the other states still appear, so the block is
  never empty because of one bad entry; the spec says so explicitly.
- **The block's order depends on configuration** — reordering the states in
  `.env` silently reorders the board → that is the intent, and it is the only
  way to say which state leads without a ranking in the source.
