## Context

See proposal.md for motivation and for the measurements.

One thing about those measurements to carry into reading them: the folder is
worked down continuously. It held 571 notifications when this was explored and
100 a few hours later, because the queue was being filed the whole time. Every
count here is a snapshot, and the proportions are what carry, not the totals.

What shapes the approach is where the board already stands:

```
   reading mail           no network, no credentials, a local mirror
   the tracker block      a network call, today's view only
                          |
                          +-- these are separate on purpose
```

The board reads mail without reaching anything, and that is a property worth
keeping: it is why the inbox draws while the tracker is down. Asking the
tracker whether each of a few hundred rows is finished would undo it, which is
what makes the notification the right place to look.

## Goals / Non-Goals

**Goals:**

- Tell a finished issue from an unfinished one at a glance, in the queue.
- Cost nothing: no request, no credential, no configuration.
- Survive the tracker's workflow being renamed or relabelled.

**Non-Goals:**

- **No tracker request.** Not per row, not per session, not lazily.
- **No state names.** Not read, not matched, not configured.
- **No mark on a promoted task.** A task is the board's own; keeping it in step
  would mean the board re-reading mail on behalf of tasks.
- **No claim about the present.** The board reports what it was last told.

## Decisions

### The signal is the struck key in the notification's own HTML

A notification names the issue it is about in a header of its own, and links
that issue in its HTML. When the tracker considers the issue done it draws the
key struck through, and the inline style survives into the mail.

*Alternative considered: the state change in the plain-text part*, which names
the state exactly. Rejected on measurement. A state change is an event on one
message; the strike is a condition on every message after it. The message
carrying the event leaves the folder when it is filed and the archive is not
mirrored, so the board forgets. At the time of measuring, 35 of 59 resolved
issues had no state change left in the folder, and the two never disagreed
where both were visible: all 20 issues whose last visible change was to the
done state were struck.

It also needs no vocabulary. The states are localised strings from a workflow
somebody else edits, and one of them is a prefix of another -- a "ready for
testing" state begins with the same word as the done state, which a substring
match would read as done 29 times.

### The issue is taken from the header, not from the links

A notification often links other issues: a comment mentioning one, a related
issue. Keying on "an issue link in the message" attributes another issue's
state to this row -- while exploring, that inflated the issue count from 112 to
196 and produced a contradiction that took a second pass to explain.

The header says which issue the message is *about*. Every message measured
carried it.

### Any self-link that is struck means done

A notification carries **two** links to its own issue, not one: the key,
titled with the project, and the summary, titled with who created the issue.
Only the key is struck. So the rule is *any* link to this message's own issue
carrying the strike, never "the" link -- there is no single one -- and never
"every" link, which the summary would always defeat.

This is measurable rather than a guess: of 100 messages, 100 carried more than
one self-link, and the ones whose links disagreed were exactly the ones whose
issue was done.

### Detected while the HTML is already being parsed

`mail.py` turns a notification's HTML into readable text, and its reader sees
every start tag with its attributes on the way through. The anchor and its
style pass under it already; nothing new has to be parsed and no second pass
over the body is needed.

The answer rides on `Message` as one field, which is the shape the read flag
took: something the account said, carried off the parse, for the board to use
later. The thread's newest message decides the row.

### Drawn the way a finished task is drawn

The board already strikes the title of a task that is done, and the
notification itself strikes the key. Using the same expression means one
vocabulary for "finished" rather than two.

*Alternative considered: a character in the leftmost cell*, which is empty on
mail rows. Rejected as a second thing to learn for the same fact, but it
remains the fallback if the strike turns out not to survive the cursor.

That last point is a measurement, not an assumption: the board's notes record
that on the selected row a *colour* is replaced while *dim* survives. Strike
should behave like dim, and apply will check it rather than assume it.

## Risks / Trade-offs

**It reads a styling choice in someone else's template.** A tracker upgrade can
change or drop it, and the failure is silent -- nothing marked, nothing said. →
The suite holds a canary: a check that the shape the detector looks for is
still the shape the fixture has, so a template drift shows up as a failing
check rather than as a quiet inbox. The board cannot check the real account
without reaching it, so this catches the shape changing, not the day it
changes on the server.

**The mark is as old as the last notification.** An issue reopened without a
new notification goes on reading as done. → Inherent, stated in the spec, and
the price of not asking the tracker. The board says what it was told rather
than claiming to know.

**A row folding messages about one issue could in principle hold messages that
disagree.** → The newest decides, which is already how the row picks the
subject, the sender and the date it shows.

**Mail from sources that are not the tracker.** Two of the three watched
folders are not tracker mail at all. → They carry no self-link, so the field is
simply false and nothing is marked. Not an error and not reported as one.

## Open Questions

None that change the specs, the approach, or the task breakdown.
