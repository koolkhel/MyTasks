## Context

See proposal.md for why. What shapes the approach is what was measured rather
than assumed, so the measurements come first.

Three probes were captured in cool-retro-term with the IBM 3278 profile, each a
synthetic test pattern printed and photographed through the same window capture
the published pictures use.

The first probe printed one `☐` (U+2610) on several lines that differed only in
what else they carried. It came out large on a line reading `all-day` beside a
Cyrillic title and small on a line reading `08:00` beside one. That is the fault
exactly as reported: in the board, all-day rows show a large box and timed rows a
small one, and `all-day` is simply the label with no digits in it.

The second probe put `☐ ☑ ☒` on one line. The empty box drew large and the other
two small, on the same line, in the same style. So the three members of one
family already come from two substitutes, and ticking a task changes the size of
its box whatever else is on the row.

The third probe printed U+25A0 through U+25AB as a run. Four of the twelve drew
small and crisp, in the font's own weight; the other eight drew oversized, in the
manner of a substitute. So the font provides the white square, the black square
and the two small squares, and nothing else in that block.

| candidate triple | in the font | same size on every row |
|---|---|---|
| `☐ ☑ ☒` ballot box, in use now | no | no |
| `□ ■ ▣` white, black, inner-filled | partly | no |
| `□ ▣ ▨` white, inner-filled, hatched | partly | no |
| `□ ■ ▨` white, black, hatched | partly | no |
| `□ ✓ ✗` white square, check, cross | yes | yes |
| `○ ● ⊗` circles | yes | yes |

Two triples survive. The board is used in cool-retro-term and in kitty, and the
surviving two draw natively in both.

## Goals / Non-Goals

**Goals:**

- One mark per task state, each drawn by the terminal's own font, identical on
  every row that carries it.
- The rule stated in one place, so the next mark added to the board is chosen
  rather than guessed.
- The published pictures show what the board now draws.

**Non-Goals:**

- Choosing marks for the event row, the tracker row or the mail row. All three
  draw natively from the font today and are left alone.
- Changing which marks the mailbox indicator draws. It keeps the check, the
  cross and the arcs. Only the comment explaining them is corrected, because
  this change makes the reason it gives false.
- Making the board correct in a Chinese, Japanese or Korean locale. That is given
  up on purpose for these marks, and the decision below says why.
- A setting to choose the marks. One vocabulary that works is worth more than a
  choice nobody would revisit.

## Decisions

### The triple is `□ ✓ ✗`, not the circles

Both survive the font test. The square wins on meaning. An empty square in a
column of empty squares reads as something waiting to be ticked, which is what
the column is for; a circle reads as a status light. And the two filled states
are far apart at this size as a check and a cross, where the circle family offers
a filled circle against a crossed circle, which differ by a few pixels on a row
that is eleven pixels tall.

The check and the cross are not new to the board. The mailbox indicator uses
them already, which is a cost rather than a saving; the decision below faces it.

Rejected: keeping a box shape for all three states. The font has a white square
and a black square and nothing between them, so "done" would have to be a solid
block. A solid block says "filled", not "finished", and against the row's
selection bar it reads as a gap rather than a mark.

### `✓` and `✗` mean two things, and this reverses a written decision

The day bar's marks were chosen to avoid the row's. Its comment says so: `☑` and
`☒` were rejected there because they "are already this board's ticked and
cancelled task marks and would say the wrong thing in the corner of the eye". The
rule behind that is one glyph, one meaning, board-wide. Giving the rows a check
and a cross breaks it from the other end.

It is reversed knowingly. What the old decision protects is a glance at the day
bar not being read as a row; the two sit in opposite corners, in different
columns, and a check means the untroubled state in both places. What it costs is
a board where one glyph has to be read in context. That was judged the smaller
cost against a done mark that is legible at row height.

Two alternatives were weighed and put aside, both live options rather than straw
men:

- **A circle family for the rows** (`○ ● ⊗`). Survives the font test, collides
  with nothing, and needs no second edit. Put aside because the done and
  cancelled marks are both dark blobs at row height, where the check and the
  cross are told apart at a glance. Legibility on every row beat tidiness in the
  vocabulary.
- **Moving the day bar's marks instead**, so each glyph keeps one meaning.
  Correct by the old rule, and rejected for widening a change about the row's
  tick box into the mailbox indicator, whose three states are a spec'd behaviour
  of their own.

One consequence must not be left behind: the day bar's comment states its reason
as a fact about the row's marks, and that fact stops being true. It is corrected
in this change, to say what is now so and that the collision is deliberate.

### The width-in-every-locale rule is narrowed, not abandoned

`□` is East-Asian-Ambiguous: a terminal configured for Chinese, Japanese or
Korean draws it two cells wide, which would push the column beside it out of
place. Nothing in the font satisfies both that rule and the coverage rule. The
characters that are one cell in every locale are the ballot boxes, which the font
lacks, and the small squares, which are too faint to carry the column.

So the rule is split. It stays as written for the green star, which is ASCII and
costs nothing to keep. It is not extended to the state marks. The coverage rule
wins because it fails every day on the machine the board runs on, where the width
rule fails only in a locale nobody here uses.

This also settles a latent case: the event diamond is Ambiguous too and has been
since it was chosen. Under the narrowed rule it stops being a thing to fix.

### The rule goes beside the marks, once

Three comments in the code each solve one instance of this and none of them
states the rule. The copy mark's comment argues about width, the mailbox
indicator's about the ballot boxes, the green star's about width again. The mark
table gets the rule in full, and the three comments point at it instead of
re-deriving it.

## Risks / Trade-offs

- **The open box is quieter than what it replaces.** The substitute box the board
  draws today is large; the font's own white square is smaller. → Accepted, and
  named in the proposal. It is the price of a box that stays one size, and no
  option offers both.
- **A font without the white square would fall back again.** → The rule is now
  written down with the reason, so the next person meets the argument rather than
  the symptom. The change also leaves the probe method described here, which
  answers the question for any new font in one capture.
- **A person reading `✓` in the day bar and `✓` on a row may take them for one
  thing.** → Accepted, against an explicit earlier decision of this board's, and
  argued above rather than left to be noticed. The mitigation is distance: the
  two marks never share a column, a row or a corner of the screen.
- **A terminal in a CJK locale will draw the column one cell wide of true.** →
  Given up on purpose. Written into the spec so it is a decision on the record
  rather than a defect waiting to be filed.
- **The pictures and the README go stale the moment the marks change.** → Remade
  in the same change, by the one command that makes them.

## Migration Plan

Nothing to migrate. The marks are drawn from the task's stored state on every
repaint, no mark is persisted anywhere, and no stored data mentions one. A person
who upgrades sees different characters in the same column on the next repaint.

Rolling back is restoring the mark table.
