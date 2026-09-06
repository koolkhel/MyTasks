## Context

See proposal.md — Why.

Nothing here was taken on trust: every claim below was measured in a
throwaway kitty instance driven by its own remote control, reading the tab
title back rather than looking at a screenshot.

The board's entry point is one line — the app is constructed and run — which
is the whole seam this needs.

## Goals / Non-Goals

**Goals:**

- The tab says what is in it while the board is running.
- The terminal is left as it was found.

**Non-Goals:**

- A name that reports the day, the counts or the view. Decided against: a tab
  bar is scanned, not read, and a name that moves is worse than one that does
  not.
- Anything terminal-specific. A terminal's own remote control could set a tab
  title directly, but it would work in that terminal alone and would need
  remote control switched on.
- Naming the command-line listing, which runs from another entry point and
  writes to a pipe as often as to a terminal.

## Decisions

**Ask with the escape sequence every terminal understands.**

Setting the title is an escape sequence written to the terminal, not an API.
The form used is the one that sets both window and icon name, which is what a
tab picks up:

```
   set     ESC ] 0 ; <name> BEL
   push    ESC [ 2 2 ; 2 t        remember the current title
   pop     ESC [ 2 3 ; 2 t        put it back
```

Measured, reading the title back from the terminal at each step:

```
   t=1s    tab = 'alt-probe.sh'   what the terminal chose by itself
   t=5s    tab = 'MyTasks'        after the set
   t=10s   tab = 'MyTasks'        still set
   t=14s   tab = 'alt-probe.sh'   after the pop -- the ORIGINAL, not blank
```

The push and pop are what make this polite rather than merely present. The
alternative — setting the title to nothing on the way out — leaves a blank
tab, which is not what was there before.

**Restoring is not universal, and that is acceptable.** The set is understood
almost everywhere; the remembering is understood by fewer terminals. Where it
is not, the pop is ignored and the name outlives the board until the shell's
next prompt replaces it. That is why the requirement asks for the name first
and the restoration second, rather than making one conditional on the other.

**The alternate screen does not come into it.** The board draws on the
terminal's alternate screen, so the question arises whether entering or
leaving it disturbs the title. Measured above: the title survived both, at
t=5s inside the alternate screen and t=10s after leaving it. Titles live
outside the screen buffer. No ordering constraint follows, so the set can
happen before the board starts and the restore after it stops.

**Write only to a terminal.** Whether output is a terminal is already
knowable at the entry point. Guarding on it is what keeps a redirected run
clean, and it costs one condition.

**Restore in a `finally`.** The board can exit by failing, and the terminal
should not keep the wrong name because of it.

## Risks / Trade-offs

**A terminal that does not remember titles keeps the name after the board
exits** → Accepted, and stated in the requirement rather than hidden. In
practice a shell prompt commonly rewrites the title at once; that was observed
here, where the tab was renamed to the running command or the working
directory on every prompt.

**A terminal that understands neither sequence** → It ignores them. They are
well-formed sequences that an unsupporting terminal consumes rather than
prints, so the failure is silence rather than rubbish on the screen.

**Another program renaming the tab while the board runs** → Out of the board's
hands, and not worth defending against. The board sets the name once when it
starts rather than reasserting it, which is the quieter behaviour.
