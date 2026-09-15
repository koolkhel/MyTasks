## Context

See proposal.md — Why. What follows is the measurement and the two places the
colours are decided.

The selected row is styled by one stylesheet rule: the table's cursor
component gets the theme's accent as its background and the theme's
contrasting text colour as its foreground. That text colour is asked for as
"whatever contrasts with the ground", and against the accent — a mid-tone — it
resolves to a light value. Light text on a mid-tone bar is the worst of the
three choices available.

A marked row's bar is not set in the stylesheet. It is read at draw time off
the selected row's own component style, which is why the two are identical
today and why changing one currently changes both.

Measured, on the colours each theme declares:

| what | against | ratio |
| --- | --- | --- |
| selected row's text today | its own bar | 2.48 to 1 |
| marked row's text | the same bar | 2.68 to 1 |
| dark text | the same bar | 7.33 to 1 |
| dark text | the brighter bar | 17.13 to 1 |
| the brighter bar | the marked bar | 2.34 to 1 |
| the marked bar | the dark theme's ground | 7.33 to 1 |
| the brighter bar | the dark theme's ground | 17.13 to 1 |
| the marked bar | the blue theme's ground | 4.64 to 1 |
| the brighter bar | the blue theme's ground | 10.84 to 1 |

Both colours are declared by both themes. The brighter one is named as the
themes' primary and is referred to nowhere in the board's stylesheet, so
taking it for this collides with nothing.

## Goals / Non-Goals

**Goals:**

- The selected row is the most legible row on the board rather than the least.
- It is found by colour, not by reading the weight of its text.
- It is found whether or not anything is marked, and whether or not the rows
  around it are the marked ones.

**Non-Goals:**

- Changing anything about marking: which rows take a mark, how long marks
  last, where the cursor goes, what is copied. Only the two colours.
- Introducing a colour. Every value here is one the themes already declare,
  which is what keeps "looks like Turbo C++" a checkable claim.
- Contrast beyond what tells the rows apart. This is a legibility fix for one
  row, not a pass over the palette.

## Decisions

### The selected row takes the brighter bar, the marked row keeps the present one

Rather than the other way round. The selected row is the one that has to be
found in a hurry; brightness is what finds it. A marked row is a state a
person set deliberately and can afford to be the quieter of the two, and
leaving it where it is means this change cannot disturb how a run of marks
reads.

Alternative considered: leave both bars as they are and only darken the
selected row's text. That reaches 7.33 to 1 and fixes legibility, but leaves
the two rows the same colour — so finding the cursor in a run of marks still
means reading text rather than glancing. It fixes the smaller half of the
complaint.

### The text colour is left to the theme after all

Written first as a second half of the change -- name the text colour rather
than let the theme resolve it, on the reasoning that asking for "whatever
contrasts" is what produced 2.48 to 1. Measured, that reasoning turned out to
be about the old bar rather than about resolving: against a mid-tone the
question is answered badly, and against the brighter bar it is answered well.

The figures decided it. Naming the ground as the text colour gives 17.13 to 1
under the dark theme and 10.84 to 1 under the blue one. Letting the theme
resolve it gives 13.67 to 1 under both. Better on one theme, worse on the
other, against a question that is comfortably answered either way -- so the
line is not worth its own existence, and the change is one colour rather than
two.

What makes deriving safe is the check on it, not the derivation. A suite
asserts the bar is the lighter of bar and text and that the two are at least
4.5 to 1 apart, in both themes. A framework that moved its threshold would
fail a run rather than a person.

### The marked row's bar stops being read off the selected row's

Today the row-style hook takes the selected row's background and uses it. Once
the two differ that is exactly wrong — it would keep them identical, which is
the defect. The marked bar becomes a value of its own, read from the theme
like any other.

This is the one place a change here can go unnoticed: nothing fails if the
hook goes on reading the wrong style, the two bars simply stay the same. A
check that the two differ is therefore the check that matters most.

## Risks / Trade-offs

**The brighter bar is loud** → It is the themes' link colour, and a full row of
it is more assertive than this board has been anywhere else. Accepted: it is
one row, it is the row a person is looking for, and the complaint that opened
this was that it could not be found. If it proves too much in use, the
alternative above — darker text on the present bar — is a smaller step that
can be taken instead without touching anything else.

**Terminals vary** → The ratios are computed from the colours the themes
declare, not from what a particular terminal paints. A terminal with its own
palette for the sixteen colours could render either bar differently. This is
why the change is confirmed at the board by eye as well as by the computed
values, in the terminal actually used.

**Two themes, one check** → A check naming a colour would pass on the theme it
was written against and say nothing about the other. Every check here compares
colours to each other rather than asserting a value, so both themes are tested
by the same words.
