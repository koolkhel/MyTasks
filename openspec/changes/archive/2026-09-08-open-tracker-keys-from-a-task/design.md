## Context

See proposal.md — Why.

Three things already exist and this change joins them up.

The tracker module builds an issue's address from its configured location and
a key, for the rows in the block. It also reads a list of projects, used today
only to narrow the block's query.

The task code has one scanner, `url_in`, which returns the *first* openable
address in a piece of text; it is what a title is read with. The rule for what
may be handed to the opener — the scheme allowlist — lives beside it.

The action that opens a link already branches three ways: a tracker row's own
page, an event's resolved address, and otherwise a task's title.

```
   what the row is          where its address comes from
   ------------------       ----------------------------
   a tracker issue          built from configuration + key   (exists)
   a calendar event         found in location, then notes    (exists)
   a task                   the FIRST address in the title   (exists)
                            ^ this is what changes
```

Measured on this account, to size the risk rather than guess it:

```
   tasks examined                                  515 / 203*
     carrying a configured project key               1
     carrying an openable address                   13
     an address in the NOTE but not the title        0
     more than one address by a raw pattern          3
       ... of which more than one DISTINCT address   0
     false positives from an unconstrained pattern   0
   * the narrower figures come from a 29-day window; the wider
     scan was cut short by the store's rate limit
```

## Goals / Non-Goals

**Goals:**

- An issue mentioned in a task reachable by the key that opens everything else.
- Nothing a task can open left unreachable.

**Non-Goals:**

- Reading the tracker to check an issue exists. The address is built, not
  verified; a key naming nothing opens a page that says so, which is the
  tracker's job to say and not worth a request to pre-empt.
- Marking an issue key in the row the way an address in a title is marked. The
  row already carries a star, a mark and two labels; deliberately left plain,
  and easy to add later.
- Anything about the tracker block's own rows. They have their address already.

## Decisions

**Recognise only the configured projects.**

An unconstrained pattern for "letters, a dash, digits" also matches `GPT-4`,
`COVID-19`, `ISO-8601` and every version number written that way. Constraining
it to the projects already configured removes that whole class, needs no new
setting, and means the recognised set changes when the configuration does
rather than when a regular expression is edited.

Measured, an unconstrained pattern would have found no false positives in 515
tasks — so this is protection against text not yet written, chosen because it
is free rather than because the data demanded it.

Where no tracker is configured, no key is recognised. The board without a
tracker is an ordinary board, as it already is for the block.

**One scanner that finds every candidate, not a second that finds the first.**

`url_in` returns the first address; the chooser needs them all. Rather than a
parallel scanner, the existing one is expressed in terms of a new one that
yields every openable address in order, so the scheme allowlist and the
anchor-before-plain preference are applied in exactly one place. Two scanners
that must agree about what may be launched is the arrangement to avoid — that
reasoning is why `url_in` was extracted in the first place, when an event's
text needed reading.

**The address of an issue named by key belongs to the tracker module.**

It is the tracker's own scheme — its configured location and `/issue/<key>` —
and the module already builds it for a reported issue. The board asks for it
rather than assembling one, so there is one place that knows the shape of a
tracker address.

**A task's candidates are collected once, in reading order.**

Title then note, each scanned for keys and for addresses. Reading order needs
no rule to be predictable and no tie to be broken. It also means the answer
does not depend on which kind of candidate is looked for first, which an
ordering by kind would.

**The chooser is the picker the board already has.**

A modal screen holding a list, escape to cancel, dismissing with the chosen
item — the shape the project picker uses. Not a new interaction to learn, and
the two should look alike because they are the same act.

## Risks / Trade-offs

**A key that names no issue** → Opens a tracker page that says so. Accepted
rather than pre-empted: checking would mean a request before every open, on a
tracker that needs a VPN and is already the slowest thing the board talks to,
to prevent a mistake whose cost is one page load.

**Reading notes changes what `o` does** → It does, in principle. Measured, no
task on this account has an address in its note but not its title, so nothing
that works today behaves differently. The change is additive now and correct
later, which is the best case; it is recorded because the measurement is what
makes it true, not the design.

**Asking where it used to open** → No task does, in the end. Three looked as
though they held several addresses under a raw pattern for "http-something",
and all three hold one address written twice — twice over as an anchor's
target and its visible text, once as a plain repetition. So the chooser is a
rule with no present case: correct, asked for, and unexercised by today's
data. Recorded because a measurement that changed twice under examination is
worth leaving visible; the first count was wrong because the pattern counted
the same address more than once.

**Text that looks like a key inside an address** → An address can contain a
project name and digits — a link to an issue, for instance. The key found in
such text and the address itself would be two candidates for one thing.
Collapsing candidates that resolve to the same address handles it, and that
collapsing turns out to matter on real data for a different reason: the three
tasks that appeared to hold several addresses each hold one twice, and without
it every one of them would ask a pointless question.

**The pattern and the configuration drifting apart** → The projects come from
the tracker's own configuration, so there is nothing to keep in step. A test
that a key is recognised for a configured project and refused for an
unconfigured one is what holds that.
