## Context

See proposal.md — Why.

Two facts shape the approach. The column that carries a tracker row's state is
not the tracker's own: it is shared with every task the board shows, where it
carries a start time, `all-day`, or how overdue the task is. Its width is
therefore a shared budget, and the widest thing a task puts there is eight
cells. And the width is currently written down twice — once as the constant
the label is trimmed to, once as the literal the column is declared with —
with nothing that keeps the two equal.

```
   mark   state / when   task title                       project
  +----+--------------+--------------------------------+-----------+
  | >  | progress     |  a tracker row                  | PROJ     |
  | [ ]| 999d ago     |  a task, the widest label there | Личное    |
  +----+--------------+--------------------------------+-----------+
         ^ one column, two kinds of label
```

## Goals / Non-Goals

**Goals:**

- One rule that produces a readable label for any state the tracker might
  report, not only the ones configured today.
- A width that is decided in one place.

**Non-Goals:**

- Per-state labels configured by hand. The block is grouped by state, so the
  label is confirmation rather than the only way to tell rows apart; that does
  not justify a second configuration format to keep in step with the first.
- Making the column fit a state's whole phrase. `Requires improvement` is
  twenty cells, which is most of a task title.

## Decisions

**The label is the state's last word, lowercased, and the column is eleven
cells.**

Four rules were compared against the three configured states and against
states the tracker might plausibly report later:

| state | today (8) | shed leading words (8) | shed (11) | last word (11) |
|---|---|---|---|---|
| `In progress` | progress | progress | In progress | **progress** |
| `In review` | review | review | In review | **review** |
| `Requires improvement` | **Requires** | improvem | improvement | **improvement** |
| `Waiting for reply` | Waiting | reply | for reply | **reply** |
| `Won't fix` | Won't fi | fix | Won't fix | **fix** |
| `Submitted` | Submitte | Submitte | Submitted | **submitted** |

Today's rule — drop a leading `In `, cut to eight — is the first column, and
`Requires` is the entry that prompted this change. Shedding leading words
until the phrase fits keeps more of a state intact and is the most faithful of
the four, but it needs the reader to accept `for reply`, and it only reaches
`improvement` at eleven cells anyway, so it costs the same width without
being simpler. Widening far enough to print whole phrases was rejected under
Non-Goals.

Eleven cells is what `improvement` needs and nothing more. It costs three
cells of task title. No state is truncated among those configured, and a
longer one is still cut rather than allowed to overflow.

Lowercasing is not only cosmetic: it is what makes the column uniform by rule
rather than by luck. `progress` and `review` are lowercase today because
`In ` happens to be what precedes them; `Requires` is the first state whose
own capitalisation reaches the screen, and `Submitted` would be the next.

**The width is named once.** The column takes its width from the same constant
the label is trimmed to, so the two cannot drift. This is why the change
touches the column declaration at all.

**A comment in the day's own code stops being true.** The bound on how
overdue a task reads is explained by reference to an eight-cell column. The
bound itself is unchanged — the label still has to be short — but the reason
given for the number is no longer accurate, so it is corrected rather than
left to mislead the next reader.

## Risks / Trade-offs

**Two configured states can end in the same word** — for example `In review`
and a later `Needs review` — and would then read identically → Accepted. The
block is grouped by state in the configured order, so the rows still appear
in separate runs and the position tells them apart; the spec records this
rather than claiming the label alone is always distinguishing. Nothing here
prevents revisiting it if such a pair is ever configured.

**A state whose last word is uninformative** — `Won't fix` reads `fix` →
Accepted, and it is not a state this board is configured to watch. Shedding
leading words would have kept `Won't fix` whole, which is the one place that
rule reads better; it loses elsewhere, and this trade was made deliberately.

**Three cells leave the task title** → Accepted. The title column is the
flexible one and absorbs the change; the project column, already the widest
fixed one at twenty-two, is untouched.
