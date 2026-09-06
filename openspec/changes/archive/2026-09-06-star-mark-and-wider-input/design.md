## Context

See proposal.md — Why.

The mark lives in a one-cell column of its own, ahead of the checkbox, and is
produced in a single place. The prompt is a modal whose box is styled by a
rule shared with five other dialogues.

## Goals / Non-Goals

**Goals:**

- A mark that reads as "mine" at a glance rather than one that rewards
  looking twice.
- A prompt wide enough that a title is legible while it is being typed.

**Non-Goals:**

- Changing which tasks are marked, where they sort, or how they are counted.
- Widening the other five dialogues. A confirmation asking one short question
  reads worse stretched, and nothing about them prompted this.
- Turning the prompt into a wrapping, multi-line editor. That is a different
  feel and a larger change; a wider single line is what was asked for.

## Decisions

**The mark is `*`, the ASCII asterisk.**

Candidates were compared for how they read and for how many cells they
occupy, which is the constraint that actually bites: a mark two cells wide in
a one-cell column pushes every column beside it out of line.

| mark | width class | cells |
|---|---|---|
| `║` (today) | ambiguous | 1 here, 2 in an East Asian locale |
| `★` black star | ambiguous | 1 here, 2 in an East Asian locale |
| `⭑` black small star | neutral | always 1 |
| `✦` four-pointed | neutral | always 1 |
| `*` **asterisk** | narrow | **always 1** |

`*` was chosen on how it reads. That it is plain ASCII is a second benefit
rather than the reason: it is the only mark on the board guaranteed one cell
everywhere, so this change quietly retires the width risk the rail carried
and that `≡` still carries elsewhere.

**What giving up the joining costs.** The rail was picked so a run of marked
tasks would draw one continuous bar, and because marked tasks sort first they
are always adjacent, so the bar really does form. Losing it means five marked
tasks read as five marks. That is the deliberate trade: the bar was an
elegant idea that proved less useful than a mark that is instantly
recognisable. The spec withdraws the guarantee explicitly rather than letting
it rot.

**The prompt gets its own width of 90; the shared rule is untouched.**

Measured rather than guessed. The prompt's box is 62 cells today, and the
border and padding leave 50 for text — arithmetic said 56, and the measured
figure is what the table below uses. Against the 108 tasks currently on the
board, counting title lengths only:

```
  box    text cells   titles that fit        clipped
   62        50        72 of 108 ( 66%)         36     <- today
   80        68        86 of 108 ( 79%)         22
   90        78        98 of 108 ( 90%)         10
  100        88       101 of 108 ( 93%)          7
  110        98       104 of 108 ( 96%)          4
```

90 is the knee: it takes a person from two titles in three to nine in ten,
and the next twenty cells buy three points more while making the box dominate
the screen. Going wider trades a lot of width for very little coverage.

Six dialogues share one style rule today. Widening that rule would widen all
six, so the prompt gets a rule of its own instead. This is why the change
touches styling at all rather than only the constant.

**A narrow terminal is already handled.** The existing cap on how much of the
screen a dialogue may take does the clamping, measured:

```
  terminal  60 -> box 48, text 42
  terminal  70 -> box 57, text 51   (still better than today's 50)
  terminal  80 -> box 66, text 60
  terminal 140 -> box 84, text 78
```

So the wider preferred width costs nothing on a small screen, and no
extra rule is needed to make it safe.

## Risks / Trade-offs

**A run of marked tasks no longer reads as one block** → Accepted, and it is
the point. Recorded in the spec as a withdrawn guarantee so that a later
reader sees a decision rather than a regression.

**An asterisk is a weaker mark than a filled star** → Accepted on the user's
own judgement, made while looking at the alternatives rendered in place. It
is also the only candidate with no width caveat at all.

**Ten titles in a hundred are still too long for the prompt** → Accepted. The
whole title is still stored and returned; only the view of it scrolls. Making
that impossible needs a wrapping editor, which is out of scope here.

**A second style rule to keep in step with the shared one** → Accepted, and
cheaper than the alternative. The prompt now sets only its own width and
inherits everything else, so a later change to padding or border still
reaches it.
