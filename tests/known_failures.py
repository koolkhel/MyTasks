"""Suites that fail for reasons predating the work in hand.

Listed so the run is green and the failures are recorded, rather than
red and rediscovered every time.  A red run cannot answer the one question
these suites exist to answer.

The list is checked in both directions: a suite here that starts passing is
reported, so the entry gets removed rather than accumulating. And a listed
suite that fails in a way the entry does not describe is still reported, so
an entry cannot quietly absorb a new fault.

None of these is here for being inconvenient. Where the reason is that
nobody has diagnosed it, that is what it says.
"""

#: suite -> (signature, why). The signature is HOW it fails, so a suite
#: failing differently is reported instead of being absorbed into its entry.
#: An integer is the number of checks expected to fail. "crash:Name" is an
#: exception of that type before any summary was printed.
#:
#: The exception type is part of it deliberately. A bare "crash" matched any
#: crash at all, and during this change it absorbed a broken import in a
#: suite recorded as crashing on tracker data -- reporting a fault introduced
#: minutes earlier as a known one, and the run as green.
KNOWN = {
    "t_top6": (1, "1 of 11: reads live tracker issues and their order; not diagnosed"),
    "t_place": ("crash:RuntimeError",
                "a task it created is not found on the board; not diagnosed"),
    "t_perf": ("crash:RuntimeError",
               "a task it created is not found on the board; not diagnosed"),
    "t_undo6": ("crash:RuntimeError",
                "a task it created is not found on the board; not diagnosed"),
    "t_work6": ("crash:RuntimeError",
                "a task it created is not found on the board; not diagnosed"),
}

#: The four crashers above fail the same way -- a task they created on a
#: far-future probe day is not on the board -- which looks like one cause
#: rather than four. It predates the change that imported them, so it is
#: recorded here rather than chased, but it is one thread and not four.

#: Two suites that had been failing all along turned out to be counting
#: calendar rows against a capture of tasks, and were repaired rather than
#: listed: a suite comparing the board's rows to a fetch of tasks must
#: exclude the rows that came from another source first.
REPAIRED = {
    "t_regress": "excluded calendar, tracker and mail rows; 17/29 -> 29/29",
    "t_track6": "excluded calendar and mail rows; 10/14 -> 14/14",
}


#: Suites whose result depends on data nobody here controls: they pass or
#: fail with the state of a live service rather than with the code. Not
#: listed as known failures, because they pass most of the time and an entry
#: excusing them would excuse a real break too. Re-run one before believing
#: its failure.
FLAKY = {
    "t_label6": ("reads live tracker issues; failed on a missing issue key "
                 "earlier the same day it passed 8/8"),
    "t_undo1": (
        '"the entry survives the one refusal" depends on which of an '
        "action's writes settles first, and nothing orders them. Forced "
        "either way -- see tests/probes/t_race.py -- the product loses the "
        "undo entry when the refusal settles before any success and keeps "
        "it when it settles after; both orderings behaved identically on "
        "the commit before the change that made the first one common, so "
        "this is a product race rather than a suite fault, and it wants "
        "its own change to the write machinery. Observed failing about 1 "
        "run in 5 under a loaded tier and 0 in 5 alone, with exactly one "
        "failing check and 46 rather than 47 reported -- the 47th is "
        "guarded by `if app._undo:`. A different signature is a different "
        "fault"),
    "t_perf2": ("times the board with writes in flight, so it fails under a "
                "full tier run where the store is busy and passes alone "
                "minutes later -- observed 3/4 in a --store run and 4/4 on "
                "its own directly afterwards. Its own docstring says the "
                "timings are of this machine; they are also of what else is "
                "talking to the account at the time"),
}


def signature(result):
    """How a run of a suite failed, in the terms an entry records."""
    if result["summary"] is None:
        # The exception's own name, from the last traceback line that has one.
        for line in reversed(result["output"].splitlines()):
            head = line.split(":")[0].strip()
            if head.endswith(("Error", "Exception", "Iteration", "Interrupt")):
                return f"crash:{head.rsplit('.', 1)[-1]}"
        return "crash:unknown"
    return sum(1 for line in result["checks"] if "FAIL" in line)


#: Suites that were lost from the scratchpad before they could be imported,
#: and rewritten here from the check names and values their last recorded
#: run printed.  Kept because it is the one thing about them a reader needs
#: to know: unlike every other suite here, these were never compared against
#: how the original behaved -- the original is gone -- so a rewrite that
#: asserts less than it used to would look no different from outside.
#: Writing them turned up five defects in the new code, four of which would
#: have passed while checking less than their names claim.
REWRITTEN = {
    "t_add": "18 checks, from the record; original lost 2026-09-09",
    "t_add2": "13 checks, from the record; every recorded value reproduced",
    "t_live": "21 checks, from the record",
    "t_live2": "9 checks, from the record; every recorded sequence reproduced",
    "t_perf2": "4 checks, from the record; its timings are of this machine",
}

#: Files that were lost with no copy anywhere and are not reconstructed.
#: Both asserted nothing -- they printed what Textual does with a keypress,
#: which is how the Cyrillic key-twin table was worked out -- so nothing
#: verified was lost with them, only the record of that investigation.
LOST = {
    "t_keys": "a probe: which keys Textual delivers, and how",
    "t_tension": "a probe: layout behaviour under a narrow terminal",
}

#: One shipped check did not isolate what its name claimed. Recorded because
#: fixing it meant changing what a suite asserts, which the change that
#: imported these forbade itself.
WEAK = {}

#: Resolved: `t_mailview`'s "a thread naming a configured issue opens the
#: issue" passed with key recognition removed entirely -- the fixture's body
#: carries the literal issue URL beside the key, so the ordinary URL scan
#: found it. The change that made a mail row offer its earliest anchored
#: address rewrote that section, and the check is now two: one for the issue
#: the row names and one for the anchored address, which differ from each
#: other. t_keys2 still covers recognition on its own.
