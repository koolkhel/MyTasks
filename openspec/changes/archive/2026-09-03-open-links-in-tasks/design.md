## Context

See proposal.md — Why and its "Established rather than assumed" section for the measurements. What shapes the approach:

Titles already reach the display through markup, which is how the past-due colour and the strike-through on finished tasks are applied. That is fine while titles are plain words, and it is why a title containing `[` is quietly mangled today. This change starts building markup around titles on purpose, so the escaping stops being incidental.

The five stored links all take the same shape — an anchor whose visible text equals its `href` — but that is a coincidence of how they were captured, not a rule. In general an anchor's text and target differ, and the design does not assume otherwise.

## Goals / Non-Goals

**Goals:**

- Extraction that is a property of a task and testable against synthetic titles, with no board and no terminal involved.
- One reachable path that does not depend on terminal capabilities, so the feature works the day it ships.
- A title that reads as words, never as stored markup.

**Non-Goals:**

- Rendering the anchor's text and its target differently, or showing the target when the text differs. The title shows what a person wrote; the address is what gets opened.
- Notes. See the proposal.
- Following, resolving, previewing or validating an address. The board hands it over and stops.
- Making the hyperlink half work where the terminal cannot. That half is a bonus and is specified as one.

## Decisions

**Extraction belongs on the task, not the board.** A task can answer what its display title is and what its link is, given only its stored fields. That keeps the rules — anchor before plain address, first address wins, missing scheme becomes `https` — checkable against a handful of synthetic titles with no UI in the way, which is how the odd stored value (`academia.edu`) was found in the first place.

**Escape the title, then insert the link markup.** The order matters: escaping after insertion would neuter the markup just added, and escaping neither would let a title's own brackets be read as styling. The title's own characters are data; only the span the board adds is markup.

**Quote the address in the markup.** Textual rejects `[link=https://…]` outright with a markup error, so the value has to be quoted. This is a hard requirement of the library rather than a style choice, and it is worth a comment at the call site because the unquoted form looks perfectly reasonable.

**An allowlist of `http` and `https`, not a denylist.** A title is text a person typed or a browser extension wrote, and opening it calls out to the operating system's handler, which will launch whatever it is told. Enumerating what may be opened is the only version of this that stays safe as new schemes appear; a list of things to block would need updating forever.

**Open through Textual's own call rather than the standard library directly.** It is the same operation, but routing through the framework means a test can intercept it and assert the exact address without a browser ever launching. That is what makes the guaranteed half of this feature verifiable, and the unverifiable half is precisely the half that bypasses it.

**A missing scheme becomes `https`, but only for something that looks like a host.** `academia.edu` should open; a fragment that merely lacks a scheme and is not a host should not be handed over at all.

## Risks / Trade-offs

- **The clickable half cannot be verified before you try it.** A hyperlink is drawn by the terminal, and neither a link span nor a click action fired under the headless harness. Mitigated by shipping the key as the path that is tested; if the hyperlink does nothing in your terminal, nothing is lost that the key does not already provide.
- **Clicking a row also selects it.** Where the terminal does make the address clickable, one gesture means two things. Not resolvable from this side, and another reason the key is the primary route.
- **Task text is handed to the system opener.** The allowlist is the guard. Worth naming as a trust boundary rather than leaving implicit: nothing else in this board takes stored text and asks the operating system to act on it.
- **Only the first address is opened when a title holds several.** Every address still shows in the title, so nothing is hidden, but a title with two links has one of them behind no shortcut. No such title exists today.
- **Escaping changes how every title renders, not just the five with links.** The blast radius is wider than the feature, which is why the tasks check an ordinary title and a bracketed one alongside the link cases.
