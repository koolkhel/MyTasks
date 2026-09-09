"""How long the inbox takes to draw with the volume the real folders hold.

The real directory holds some 1,200 unread messages folding to some 570 rows
-- 1,233 and ~460 when this change was planned, 1,137 and 574 measured the
day it was built, which is the same order and the same shape. Every check
about mail until now ran against a fixture of eighteen, where nothing about
drawing could show. This builds a mailbox of that size -- synthetic
throughout: generated subjects, invented project keys, `.invalid` addresses
-- reads it, and times the inbox drawing it beside a person's own tasks.

The real read, for comparison with what this measures: 1,137 messages in
0.50 s, folded in 0.02 s. Reading dominates drawing in both, and neither is
anywhere near a person noticing.

Its numbers are of the machine that runs it, so the bounds are generous and
the point is the ratio: whether drawing dominates reading, or the reverse.
A bound is asserted all the same, because "too slow to use" is a defect and
a suite that only printed a number would not catch it.
"""
import asyncio, datetime as dt, os, sys
from time import monotonic

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import mailfixture as F
import mail, main, tracker

#: What the real folders hold, as measured: rows, and messages behind them.
#: Kept at the planning figures rather than the day's, because a suite whose
#: expected numbers move with somebody's mailbox proves nothing.
ROWS = 460
MESSAGES = 1233
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
TRK = tracker.Config(base_url="https://track.corp.invalid", token="t",
                     assignee="me", projects=("ZZA",), states=("In progress",))
ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def big_mailbox():
    """A mailbox of the real shape: many single rows, some folded ones."""
    messages = []
    # The folded ones first: issues with several updates each. The plain
    # issue address comes before the anchored one in every body, which is
    # the order real notifications carry them in -- and the order the fold
    # depends on, since it folds on the first address a message holds.
    folded, deep, n = 130, 7, 0
    for issue in range(folded):
        for update in range(deep):
            n += 1
            issue_url = f"https://track.corp.invalid/issue/ZZA-{2000 + issue}"
            messages.append((
                f"ZZA-{2000 + issue}: update {update}",
                f"an update on {issue_url}"
                + (f" at {issue_url}#comment-{update}" if update else ""),
                {"Message-ID": f"<zz.f{issue}.{update}@example.invalid>"},
            ))
    # Then the rest as rows of their own, naming no issue at all.
    while len(messages) < MESSAGES:
        n += 1
        messages.append((
            f"build {n} finished", f"see https://ci.corp.invalid/job/{n}/console",
            {"Message-ID": f"<zz.b{n}@example.invalid>"},
        ))
    return F.build({"Bulk": messages}), folded, deep


async def main_():
    print(f"a mailbox of {MESSAGES} messages")
    started = monotonic()
    path, folded, deep = big_mailbox()
    built = monotonic() - started
    print(f"  built in {built:.2f}s")

    config = mail.Config(path, ("Bulk",))
    started = monotonic()
    found = mail.read(config)
    read = monotonic() - started
    check("every message was read", len(found), MESSAGES)

    def fold(message):
        keys = TRK.keys_in(message.text)
        import singularity
        urls = singularity.urls_in(message.text)
        return (keys[0], urls[0]) if keys and urls else None

    started = monotonic()
    rows = mail.threads(found, fold=fold)
    grouped = monotonic() - started
    expected = folded + (MESSAGES - folded * deep)
    check("and folded to the rows it should", len(rows), expected)
    print(f"  read in {read:.2f}s, folded in {grouped:.2f}s "
          f"-> {len(rows)} rows")
    check("the row count is of the order the real folders give",
          400 <= len(rows) <= 600, True)

    app = main.TaskApp()
    app.client = StubClient([mk(f"i{i}", f"a triage task {i}") for i in range(35)],
                            reference=NOW)
    app.calendar_config = None
    app.tracker_config = None
    app.mail_config = config
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        await pilot.press("i")
        for _ in range(30): await pilot.pause()
        app.mail_threads = rows
        started = monotonic()
        app.repaint()
        drew = monotonic() - started
        shown = sum(1 for t in app.tasks if app.is_mail(t))
        check("every row is on the board", shown, len(rows))
        check("beside the person's own tasks",
              sum(1 for t in app.tasks if not app.is_mail(t)), 35)
        check("the tasks are still first",
              app.is_mail(app.tasks[0]), False)
        print(f"  drawn in {drew:.2f}s for {shown} mail rows + 35 tasks")
        # Generous: this is a redraw of the whole table, and it happens on a
        # keypress, so a person notices anything above a moment.
        check("drawing stays under a second", drew < 1.0, True)
        started = monotonic()
        for _ in range(3):
            app.repaint()
        again = (monotonic() - started) / 3
        print(f"  and {again:.2f}s a redraw thereafter")
        # The ratio is the finding: reading a mailbox this size is dominated
        # by parsing message bodies, drawing by building table rows. Which
        # dominates decides where any later work would go.
        print(f"  reading {read:.2f}s vs drawing {drew:.2f}s: "
              f"{'reading' if read > drew else 'drawing'} dominates")

    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


sys.exit(asyncio.run(main_()))
