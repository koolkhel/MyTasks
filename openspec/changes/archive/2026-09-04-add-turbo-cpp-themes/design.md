## Context

See proposal.md — Why and its "Established rather than assumed" section for the measured palette. What shapes the approach:

The board already styles itself entirely through theme tokens rather than literal colours — seven of them in its stylesheet, and one resolved at runtime for past-due titles. That is why a theme swap is a small change: nothing in the board names a colour, so nothing has to be rewritten to follow a new palette.

The framework's theme object accepts almost exactly the slots the editor theme fills, with an escape hatch for values it would otherwise derive. Two of the editor theme's values cannot be used as given, and both belong to the blue variant: its chrome is light grey where the dark variant's is near-black, and its muted colour is the same value as its ordinary text.

## Goals / Non-Goals

**Goals:**

- Colours taken from the editor theme's own files, so "looks like Turbo C++" is checkable rather than a matter of taste.
- One stylesheet that serves both variants, with no rule that asks which theme is active.
- The distinctions the board depends on preserved under either theme, verified by comparing resolved values rather than by eye.

**Non-Goals:**

- Reproducing the editor theme's syntax highlighting. There is no code on this board; only its interface colours are relevant.
- A key to cycle themes. The command palette already lists every registered theme, and adding a binding would spend a key on something reachable in two keystrokes.
- Making the board's own colour decisions configurable. The themes are fixed definitions, not settings.
- Touching any behaviour. If a task moves, a count changes or a key does something new, this change has gone wrong.

## Decisions

**Both themes are defined as data, not as stylesheet overrides.** A theme object holds the palette; the stylesheet keeps referring to tokens. The alternative — writing literal colours into the board's styling — would work for one theme and make the second impossible without duplicating every rule.

**Ask the stylesheet for an automatically contrasting foreground on the bars.** This is what lets one rule serve a near-black panel and a light-grey one: it resolves to white on the first and black on the second. Verified rather than assumed, because the whole viability of a single stylesheet rests on it. Branching on the active theme was the alternative and is rejected: it would put the theme's name into the styling and need editing again for a third theme.

**Override only what cannot be derived.** The framework computes most of its variables from the handful of colours a theme declares, and those computed values are what the board's muted text and link colour come from. Only the blue variant's muted colour needs stating outright, because deriving it from a foreground identical to the ordinary text yields no distinction at all.

**The past-due colour stays resolved at runtime.** It already reads from the active theme rather than a literal, which is exactly what makes it follow a theme change for free. The risk this creates is that a new palette could resolve it to something too close to an ordinary title — so that becomes something to check per theme rather than a thing to hard-code around.

**Reproduce the shared colours exactly and let the variants differ only where the source differs.** The two editor themes share their text, selection, error and link colours; only the ground and the chrome change. Defining them independently would invite drift between two things that are meant to be the same theme in two moods.

## Risks / Trade-offs

- **All ordinary text becomes yellow.** Faithful — the editor drew all code that way — but it is a lot of yellow across a list of twenty rows, and it spends the most attention-grabbing colour on the most common element. Accepted deliberately; the fallback if it grates is to reserve yellow for the header, which is a small later change and not a redesign.
- **The blue variant's chrome inverts.** Light grey bars with dark text look right for Turbo C++ and unlike anything else in this board's history. The automatic contrast handles the mechanics, but it will look startling next to the dark variant.
- **A theme could quietly break a distinction the board relies on.** That is why it is specified rather than left to inspection: the check is a comparison of resolved values, so a future theme that flattens two of them fails rather than merely looking wrong.
- **The framework derives many variables from few inputs.** A future version could derive them differently and shift colours the board never states. Nothing to do about it beyond the per-theme checks, which would catch it.
