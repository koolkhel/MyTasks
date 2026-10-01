## Context

See proposal.md for why. What shapes the approach is what the real folders
actually carry, measured during exploration. Header names and counts only; no
subject, sender, project or key was read out of the probes.

The mailbox holds 977 messages in the folders the board reads, and 918 of them
carry `Auto-Submitted` or `List-Unsubscribe`. None is from a person. Three
senders account for nearly all of it, and each declares what its message is
about:

| header | messages | what it identifies |
|---|---|---|
| `X-YouTrack-Issue` | 558 | the issue |
| `X-GitLab-Project-Id` + `X-GitLab-MergeRequest-IID` | 293 | the merge request |
| `X-Jenkins-Job` | 62 | the job |
| `X-Jenkins-Result` | 62 | `SUCCESS` 36, `FAILURE` 18, `ABORTED` 8 |

The present fold scrapes an issue key out of the message text and pairs it with
the first address found there. Against the header it is almost right and
dangerous where it is not:

| | messages |
|---|---|
| header and scraped key agree | 550 |
| they disagree | 1 |
| header present, the scrape missed it | 11 |
| key in the text, no header at all | 234 |

Those 234 are the hazard the compound rule exists to survive, and they are
review and build mail quoting an issue. A header only the tracker sets cannot
see them.

What the rows come to, every figure through `mail.threads` so the folds are
compared on the same pipeline rather than by grouping headers in a probe:

```
  no fold at all, chain grouping alone           611
  what the board draws today                     367
  folded by each sender's own declaration        294
     one per tracker issue                  150
     one per merge request                   81
     one per build job                        4
     declaring nothing, chain-grouped        59
```

Two earlier figures were wrong and are corrected here. 611 was quoted as
"today" when it is what the board would draw with no fold at all, and a probe
that keyed merge requests on their project alone reported 302. The win is 73
rows, a fifth, not a half. It is worth recording because it changes what this
change is for: the argument is the 234 wrongly folded messages, and the shorter
view is a benefit rather than the point.

## Goals / Non-Goals

**Goals:**

- Fold on what a sender states, so the board stops inferring a fact it was
  given.
- Halve the inbox without hiding anything, except where the thing hidden is
  provably not news.
- One rule per sender, each independently checkable, rather than one clever
  rule covering all of them.

**Non-Goals:**

- Making the inbox emptiable. 294 rows is a fifth off 367 and nowhere near a
  queue anybody clears in a sitting. This change makes the grouping correct and
  takes some duplication with it; it does not decide what deserves attention,
  beyond the one case where the sender says.
- Filtering review mail. Measured and deliberately declined, below.
- Any new source, any configuration, any change to what reviewing or promoting
  a row does.

## Decisions

### Fold by declaration, and drop the text rule rather than keep both

The replaced rule and the new one answer the same question, so keeping both
means deciding which wins on the 235 messages where they differ. There is no
good answer to that, and the measurement says the text rule is wrong on all of
them: 234 it folds and should not, 1 it folds differently from what the sender
says. So the text scrape goes.

This also frees the fold from the tracker configuration. The present rule has
to know which projects count, in order not to mistake a version number for an
issue. A declaration needs no such list, and a board whose tracker is not
configured at all folds tracker mail correctly from now on, which it could not
do before.

Rejected: keeping the text rule as a fallback where no header is present. It
would fire on exactly the 234 messages that make it dangerous, since those are
the ones with a key and no header.

### A merge request needs both of its identifiers

`X-GitLab-MergeRequest-IID` is the number shown in the interface and it
restarts in every project, so two unrelated merge requests share a number
routinely. The pair with `X-GitLab-Project-Id` is what identifies one. The
internal `X-GitLab-MergeRequest-ID` is unique on its own but is not the number
anybody sees, and a row keyed on something invisible is harder to check against
the interface when a fold looks wrong.

### Review mail is folded and not filtered

GitLab sets `X-GitLab-NotificationReason` only when the message concerns the
reader personally: `assigned` on 99, `review_requested` on 4, absent on 247. So
there is a ready-made filter, and 31 of the 81 merge requests would disappear
under it.

Declined, by the person whose inbox it is. Folding loses nothing, so it is safe
by construction; filtering hides a merge request somebody is following, and the
cost of missing one is higher than the cost of 31 rows. The header is therefore
not read at all by this change, rather than read and ignored.

This is the asymmetry the whole change rests on: fold freely, filter only where
the sender declares something the board can judge.

### Build mail is the one place a filter is justified

A build server declares its outcome. A success asks nothing of anybody, and an
aborted build is somebody stopping a job they started, usually because they
started it wrongly, which leaves nothing to fix. Neither is news, and the
server says which is which, so no judgement is being made by the board.

Taken from the declaration and not from wording, for the reason the issue-done
mark already follows: words are in whatever language and vocabulary a server
happens to use, and matching them ties the board to one deployment.

It saves no rows today: all four jobs have at least one failure, so all four
keep a row. What it changes is what a row holds and what reviewing it files
away, which is 36 successes and 8 aborted builds out of 62. The spec says a
job with nothing but those gets no row, which is the behaviour wanted and is
simply not exercised by today's mailbox.

### The message reader keeps the headers, the fold reads them

Deciding what a message is about already belongs outside the maildir reader,
because it used to need the tracker configuration and an address finder. That
reason has gone, but the split stays: the reader's job is turning a maildir
into messages, and three sender-specific rules are not that.

So the reader widens what it keeps from one header to the few that matter, and
the fold becomes a function of a message's declarations alone. That makes the
fold a pure function over data a suite can build by hand, which the present one
is not.

## Risks / Trade-offs

- **A sender renames or drops a header.** → Folding falls back to chain
  grouping for that sender, which is what the board did before any of this. The
  view gets noisier; nothing is hidden and nothing breaks. A mailbox-tier check
  reports the headers' presence so the day it happens is visible.
- **The one message where the header and the scrape disagree.** → The header
  wins, by the rule above. One message in 977, and the sender's own statement is
  the better authority.
- **Build filtering hides something that mattered.** → Only `SUCCESS` and
  `ABORTED` are hidden, both declared by the server. A failure is never hidden.
  If an aborted build turns out to matter, one value moves and the spec changes
  with it.
- **294 rows is still too many, and the saving is smaller than first sold.** →
  Named in the proposal rather than pretended away, with the two mismeasurements
  that produced the larger claim. The remaining bulk is one row per issue, which
  is the shape that was asked for; whether 150 issues is itself the problem is a
  different question, and this change does not touch it.
- **Review mail stays as noisy as it is.** → The filter exists and was declined
  on purpose, with the number it would have saved recorded here so the decision
  can be revisited knowing its price.

## Migration Plan

Nothing to migrate. Folding is computed on every read, nothing about it is
stored, and no configuration changes. A person who upgrades sees fewer rows for
the same mailbox on the next reload.

Rolling back is restoring the previous fold.

## Open Questions

- Whether the 67 messages that declare nothing are worth a fourth rule. They
  are chain-grouped today and that is adequate; what they are has not been
  looked into, because it does not change anything else here.
