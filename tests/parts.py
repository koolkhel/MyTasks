"""Running a suite's parts, for a suite that runs itself.

Its own module rather than part of the harness, and that is the whole point
of it: importing the harness blanks the configuration loaders, which is right
for a suite driving a board and wrong for one checking what a loader does
with a real file.  Two suites here are of the second kind, and before this
they simply did not import the harness.  A helper they cannot import is a
helper that would have split the tails in two.

Nothing in here touches a module, a loader or the clock.
"""
import asyncio
import inspect
import sys


def print_utf8():
    """Make what a suite prints UTF-8, whatever the machine's locale says.

    Every suite imports this module before it prints a check, and eighteen
    of them print names that are not ASCII.  Under a cp1251 locale the first
    such print raised and the suite died -- when run on its own, that is:
    the runner already tells its children to print UTF-8, and a guarantee
    that holds only through the runner fails at exactly the moment somebody
    runs one suite by hand to narrow a failure down.

    Reconfigured rather than replaced, so a stream that has been captured or
    substituted -- pytest's, a suite's own StringIO -- is left alone: only a
    real text stream that offers `reconfigure` is touched, and one already
    writing UTF-8 is not touched at all.
    """
    for stream in (sys.stdout, sys.stderr):
        fix = getattr(stream, "reconfigure", None)
        encoding = (getattr(stream, "encoding", "") or "").replace("-", "").lower()
        if fix is not None and encoding != "utf8":
            try:
                fix(encoding="utf-8")
            except (ValueError, OSError):      # closed, or not a real stream
                pass


print_utf8()


def run_parts(parts, *checks):
    """Run a suite's parts in order and report what they checked.

    A part is called directly or given to `asyncio.run` depending on what it
    is, which is how every suite here has always run one: Textual's
    `run_test` is entered inside a part, so the event loop the board under
    test lives in begins and ends there.  Keeping that exactly as it was
    matters more than it looks -- the suites are the instrument, and a loop
    with a different lifetime is a different instrument.

    The order is the order given.  Several parts share state their module set
    up before any of them ran, so running them in another order would change
    what they are checking without saying so.

    More than one list of checks is allowed because one suite keeps two --
    it asks two different kinds of question and reports them separately --
    and its total has always been the sum.  Counting one of them would drop
    the other silently, which is exactly the kind of loss this arrangement
    exists to make impossible.

    Returns what the suite should exit with, so that a suite's whole tail is
    one line and there is nowhere for fifty-four of them to drift apart.
    """
    for part in parts:
        if inspect.iscoroutinefunction(part):
            asyncio.run(part())
        else:
            part()
    made = [good for one in checks for good in one]
    print(f"\n{sum(made)}/{len(made)} checks passed")
    return 0 if all(made) else 1
