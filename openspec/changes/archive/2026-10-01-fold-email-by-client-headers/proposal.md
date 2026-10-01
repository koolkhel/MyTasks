## Why

The inbox draws 367 rows for 984 messages, and none of that mail is from a
person. It is three machines talking: a tracker, a code-review system and a
build server.

The board folds those messages by scraping an issue key out of the message text
and pairing it with the first address it finds there. That rule was written
carefully, against measured data, and it is still a rule about what the board
can *infer*. Every one of these senders states what its message is about, in a
header, and the board already reads one of those headers for an unrelated
purpose and throws the rest away.

**The case for this is correctness, not volume.** 234 messages carry an issue
key in their text and no tracker header, because they are review and build mail
quoting an issue in passing. Those are precisely the ones that merged 24 of 38
groups wrongly when the key alone was tried, and the present rule pairs the key
with an address purely to survive them. A header only the tracker sets cannot
pick them up at all, so the compound rule stops being needed and the board stops
guessing at a fact it was handed.

The view does get shorter, by less than first measured:

| | rows |
|---|---|
| no fold at all, chain grouping alone | 611 |
| what the board draws today | 367 |
| folded by each sender's own header | 294 |

73 rows, a fifth. An earlier draft of this proposal claimed it halved the view,
from 605 to 302. That was wrong twice over: 605 was chain grouping measured
without the board's own fold, and 302 came from a probe that keyed merge
requests on their project alone. Both are corrected here, and the smaller number
is the honest one.

## What Changes

- Messages SHALL be folded by what their sender declares, not by what the board
  reads out of their text. Three rules, one per sender, each keyed on a header:
  - the tracker's own issue header, giving one row per issue (150 rows for 561
    messages, which is the shape asked for);
  - the review system's project and merge-request identifiers together, giving
    one row per merge request (81 rows for 350 messages);
  - the build server's job name, giving one row per job (4 rows).

  Everything that declares nothing stays chain-grouped, which is 59 rows. The
  four together are the 294 above.
- Build mail SHALL be kept only where the build failed. A succeeded build is
  not news and an aborted one is somebody stopping a job they started by
  mistake, so neither earns a line in a queue. A job with nothing but those
  SHALL therefore have no row at all.
- The present text-scraping fold is **replaced**, not kept beside the new
  rules. Two rules answering the same question is how they come to disagree.
- Review mail SHALL be folded and SHALL NOT be filtered. The sender marks the
  messages that concern the reader personally, and 31 of the 81 merge requests
  carry no such mark, but hiding a merge request somebody is following is a way
  to miss one. Folding is safe because it loses nothing; filtering is not, and
  it is only worth the risk where the thing hidden is genuinely not news.
- Mail from anywhere else SHALL be grouped exactly as it is now, by the headers
  that say which message answers which. A sender that declares nothing is
  unchanged by this.

Not in scope: which folders are read, which is configuration; the reviewing and
promoting keys, which act on a row and do not care how it was made; and any
new source. This changes how existing mail becomes rows and nothing else.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `task-board`: replaces the requirement that folds messages by an issue named
  in their text with one that folds by the sender's own declaration, and adds
  the rule that a build message is kept only where the build failed.

## Impact

- `mail.py`: the message reader keeps the headers it already parses instead of
  one of them, and the thread grouping takes a fold that can answer for three
  senders. The chain-grouping fallback is untouched.
- `board.py`: the fold itself, which stops needing the tracker configuration
  and the address finder, and so stops being able to confuse a quoted key for
  a subject.
- `tests/`: the stub suites covering folding, and a mailbox-tier check that the
  headers this depends on are present on real mail.
- No configuration, no new dependency, and nothing a person must do after
  upgrading. A board whose mail declares nothing behaves exactly as before.
