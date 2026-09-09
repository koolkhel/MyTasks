## Context

See proposal.md — Why. What follows is only what shapes the approach.

There are 82 scripts in one session's scratchpad; 64 are current, 18 are
snapshots of a suite as it stood before a particular change. Of the 64, four
turn out to assert nothing at all, leaving 60 suites: 39 need nothing but the
repository, 18 talk to the real task store, and 3 talk to the issue tracker —
one of those, the tracker's ordering suite, needs both.

Those counts are measured rather than read off the imports, and the imports
mislead. Three suites that call into the tracker module make no network call
at all: two set the environment themselves to test how configuration is
parsed, and pass with the environment emptied, and one substitutes the fetch.
Classifying by what a suite imports would have put all three behind a VPN.

They are not a framework. Each is a script that prints its own check lines and
exits non-zero if any failed; roughly ten thousand lines of hand-written
comparisons, not asserts. Between them they encode a great deal that was
learned by getting it wrong, which is the reason this change moves them rather
than rewriting them.

Four of them compare the board against a recorded baseline of the real
account, which is per-person and per-day and expires at midnight.

```
   scratchpad (76M, one session)          repo
   ---------------------------            ----
   82 scripts                    -->      64, the current ones
   harness.py, baseline.py       -->      shared, beside them
   sample_mail/ (synthetic)      -->      a fixture, with its generator
   captures, baselines, .bak,    --x      not committed: they describe
     spec snapshots, worktrees              a real account, or are litter
```

## Goals / Non-Goals

**Goals:**

- What the suites assert survives, unchanged, under version control.
- A clone with no credentials can run something meaningful and get a green
  result.
- A failure that means nothing is labelled as such once, not rediscovered.

**Non-Goals:**

- Rewriting a suite as pytest, or reworking any assertion. The next change
  does that, with this one committed to diff against.
- Diagnosing the seven suites that fail. They are recorded, not fixed.
- Continuous integration. There is no remote to run it on.
- Making the live tiers runnable by anyone but the account's owner. They
  cannot be, and pretending otherwise would mean deleting them.

## Decisions

**A suite's directory is its declaration, because classifying it by import
would run it.**

The tiers are directories: one for suites needing nothing, one for the task
store, one for the tracker. The runner reads the directory and never imports a
suite to find out what it needs.

That is not a style preference. Several live suites construct a client at
module level — `api = SingularityClient()` on the third line — so importing
one to inspect a marker would open a connection and, for a few, create tasks.
A declaration you have to execute the file to read is not a declaration. A
directory is also visible in `ls` and cannot silently disagree with how the
runner groups things, which a marker inside the file can.

Where a suite needs two things, it goes in the more demanding tier. The
tracker's ordering suite needs the store as well, and lives with the tracker
suites; asking for that tier means having both.

A suite that reads configuration but calls nothing needed a fourth tier after
all, and the reasoning that said otherwise was wrong in a way worth recording.

Two suites do set the environment they want and restore it, and those are
self-contained. But four others read the real configuration and assert on what
they find — the calendar accounts, that a full tracker configuration loads.
The measurement that cleared them was unsound: `python-dotenv` finds `.env` by
walking up from the *calling module*, and the board's modules sit beside it,
so emptying the environment never hid the file. All four went on reading the
real thing while the check reported them hermetic.

Only a checkout with no `.env` exposed it, which is why that is now the test
and not an emptied environment. The `config` tier is not paced — it makes no
network call — but it refuses to start without the settings it reads.

**A suite that needs a snapshot of the old product is not imported.**

One suite loads a copy of `main.py` as it was before a change and compares
what the two draw. That is the same thing the `_ref` and `_old` copies are,
arrived at from the other direction, and it is excluded on the same ground:
keeping it would mean committing a superseded copy of the product as test
data, which is a worse thing to own than the comparison is worth. It was
already failing 12 of its 14 checks.

**A file that asserts nothing is a probe, and a probe is never run.**

Four of these print what the framework does — how Textual delivers a
keypress, which is where the Cyrillic key-twin table came from — and check
nothing. They have no pass or fail and always exit zero.

They are kept, because rediscovering that behaviour costs an afternoon, and
they are kept *outside the tiers*, because a runner that counted them would
report four passes that assert nothing. A green number that includes them is
worse than not having them: it is a green number that cannot be trusted.

Told apart by inspection rather than by output: a file with no check idiom
anywhere in it asserts nothing, whereas judging by whether it printed check
lines would also have caught the suites that crash before their first check
and the one whose output shape the recorder did not yet recognise.

**Five suites are written afresh, because they were lost mid-change.**

Seven files disappeared from the scratchpad while this change was being
applied: five suites and two probes. Nothing on the machine holds them, and
one further suite survived only because a copy had been made for the
before-and-after comparison. The premise of this change arrived early and
uninvited.

They are rewritten here rather than mourned, from the check lines the
before-picture recorded — which give every check's name and the value it
saw, so what each asserted is known even though its code is not.

The honest cost, stated because it cannot be measured away: **these five are
new suites under old names.** Every other suite in this change is guarded by
a check-by-check comparison against how it behaved before the move, and that
guard cannot exist for these. A rewrite that quietly asserts less than the
original did would look identical from outside. Their recorded check names are
reproduced exactly, which is the strongest available substitute and is not the
same thing.

**The other scripts are moved, not rewritten. Exactly three mechanical edits
are allowed.**

Paths become relative; the scrubbed identifiers are replaced; a suite that can
write to a fixture takes a copy. Nothing else — not a reworded check, not a
tidied helper, not a renamed variable.

The reason is that this change has no way to tell whether a rewrite weakened
something. The suites are the instrument; edit the instrument and the
measurement in the same change and neither can vouch for the other. So every
suite is run before the move and after it, and its check lines compared, which
only means something if the edits are small enough to be enumerated.

**The known-failure list carries reasons and is checked in both directions.**

A list of names would rot into a list nobody dares delete from. So each entry
records what is known — including "not diagnosed", which is the honest entry
for most of these — and the runner reports a listed suite that *passes*, so
the list shrinks when someone fixes something without noticing.

An entry is per suite, not per check. Finer would be better: two of these fail
2 checks of 14 and the other 12 are real coverage that a suite-level entry
throws away. It is not done here because per-check quarantine means parsing
each suite's output format, and the output format is the thing the pytest
change is about to replace. Recorded as a known cost, to be fixed there.

**The baseline stays out of the repository and the suites go on refusing a
stale one.**

A baseline describes one person's account on one day. Committing it would make
four suites fail for everyone else, every day. It is written to a directory
the repository excludes, produced by the capture script that lives with the
suites, and the loader already exits with instructions when it is absent or
from another day — which is behaviour worth keeping rather than replacing,
since it was written after four suites spent a day comparing today against
yesterday.

**Pacing and throttle-counting belong to the runner, not to each suite.**

The store's quota is a property of the account, shared by every suite. Putting
a sleep in each one would mean eighteen places to get it wrong and no way to count
across them. The runner spaces the store tier, runs it one at a time, and
recognises the store's throttle error in a suite's output so it can report the
count and call a throttled run inconclusive.

Recognising it by its message is admittedly brittle. The alternative — having
each suite report throttling structurally — means touching all eighteen, which the
"moved, not rewritten" decision forbids. Matching the message is the cost of
that decision and belongs in the same place it will be fixed: the pytest
change, where a suite can raise something the runner catches.

**The suites get the account's second token, handed to them rather than read
by them.**

The account has two tokens. A full store-tier run can exhaust the quota — it
did exactly that during the previous change, and stayed throttled for over
half an hour — and when it does, it should be the suites' quota that is gone,
not the one the board the person is working in depends on.

The runner reads `SINGULARITY_TEST_TOKEN` from the gitignored `.env` and
launches each store-tier suite with it as `SINGULARITY_TOKEN`. Handed over
rather than read directly, for two reasons: no suite needs changing, which the
"moved, not rewritten" rule requires, and no product code learns that a test
token exists — the suites go on exercising exactly the path a real run takes.

Where only one token is configured the run uses it, so this is an improvement
where available rather than a new requirement to satisfy.

**No new dependencies.**

The suites import only the standard library, the board's own modules, and
`requests`, `rich` and `textual` — all already required. Nothing is added to
`requirements.txt`.

**The commit convention is amended in this change, not left to be discovered.**

Staging with `git add -- '*.py' openspec` matches no maildir fixture file, so
the mail suites would land without the data they read and fail for everyone
including the author. The pathspec gains `tests`, and the archive guidance
that records the convention is updated here rather than in a later change,
because the omission bites the moment this one is committed.

## Risks / Trade-offs

**A mechanical edit changes what a suite measures** → The likeliest is a path
edit that quietly points a suite at different data. Mitigated by running every
suite before and after and comparing its check lines, and by the edits being
few enough to list. The mail suites are the ones to watch: their fixture path
changes and their fixture handling changes together.

**Replacing a real tracker key changes a suite's meaning** → Measured rather
than assumed, and the assumption was wrong in an instructive way. The renamed
suites do not test key *recognition* at all: their keys are labels on
synthetic issues, and breaking `keys_in` leaves them passing. Recognition is
covered by one suite, which crashes when it is broken.

So the property to check for the renamed suites is that their keys are
load-bearing, which was established by simulating a botched scrub — renaming
the key in the fixtures but not in the expectations. All three tried then
failed checks (5, 2 and 3 of them), so an inconsistent scrub could not have
passed unnoticed. Replacements keep the original lengths, which also keeps
every truncation point identical.

**One shipped check does not isolate what its name claims** → Found by the
same experiment: a mail suite's "a thread naming a configured issue opens the
issue" passes with recognition removed, because the fixture's body carries the
literal issue URL beside the key, so the address is found by the ordinary URL
scan. The check is not wrong — the key does open the issue — but it would not
notice recognition disappearing. Recorded rather than fixed: fixing it means
changing what a suite asserts, which this change forbids itself.

**The scrubbed key returns through an unexamined file** → It is in seven
suites, and this change adds sixty-odd files at once. Mitigated by grepping
the staged diff before committing, which the archive guidance already
requires, and by grepping the whole tracked tree afterwards rather than only
the diff.

**Sixty-four scripts nobody reads again** → Importing ten thousand lines of
hand-written comparisons is a large addition of code that is not the product.
Accepted because the alternative is losing it, and because the pytest change
is what makes it legible. The risk is that the second change never happens and
this becomes the permanent state.

**A live tier that only one person can run will rot** → Nobody else can
execute 19 of these, so a break in them is found late, by that one person.
Unmitigated, and worth knowing: it is the price of keeping suites that verify
against the real API, which is where several real bugs were actually caught.

**The default run's green is narrower than it looks** → 45 suites passing says
nothing about the store, the tracker, the calendar or the mailbox as they
really behave. Mitigated only by the runner naming the group it ran, so a
green result is never reported as more than it is.

## Migration Plan

1. The scratchpad stays the source of truth until the imported copies have
   been run and compared, suite by suite, against their originals.
2. Scrub the identifiers first, before anything is added to the index. The
   scrubbing is verified against the whole tree, not just the diff.
3. Import in tiers: the self-contained 45 first, since they can be verified
   without touching an account; then the store tier; then the tracker tier.
4. The commit stages `tests` explicitly. If the fixture is missing from the
   commit, three mail suites fail on a fresh clone, which is the check that
   the pathspec amendment worked.
5. Rollback is deleting `tests/` and reverting the pathspec: nothing else
   depends on any of this, and the board is untouched.

## Open Questions

- Whether the two suites that fail 2 checks of 14 should keep their other 12
  checks running under a per-check quarantine, or stay suite-level until the
  pytest change. Deferrable: it changes neither the specs nor the tiers, only
  how much coverage the known-failure list costs in the meantime.
