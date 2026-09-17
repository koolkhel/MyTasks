"""What is on screen is the answer, not a second opinion.

`t_paint` shows that what the board would draw can be decided with nothing
started.  This shows the other half: that the table holds exactly that
decision, cell for cell, rather than a second computation of the same thing
made on the way to the screen.

It is small on purpose.  The rules about what a row says are checked in the
suites that own them; the only thing asked here is whether the drawing agrees
with the deciding.

Everything is stubbed -- no account, no network, no mailbox.  Every task,
event and issue is invented.
"""
import asyncio, datetime as dt, sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import *
import ical, main, tracker
from main import TaskApp
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
CFG = ical.Config(work="WorkAcc", personal=("Me",))
TRACK = tracker.Config(base_url="https://tracker.invalid", token="zz",
                       assignee="me", projects=("ZZA",), states=("open",))

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


def timed(tid, title, hh, checked=0):
    t = mk(tid, title, TODAY, checked=checked, timed=True)
    t.raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(hh, 0), tzinfo=TZ))
    return t


def ev(title, hh, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False)


def issue(key, summary):
    return tracker.Issue(key=key, summary=summary, project="ZZA",
                         state="In progress", assignee="me",
                         base_url="https://tracker.invalid",
                         priority="Major", priority_value="Major")


def plain(cell):
    """A cell as the characters it puts on the line."""
    return cell.plain if hasattr(cell, "plain") else str(cell)


async def the_table_holds_what_was_decided():
    print("\n1.1 a view with all four sources on it")
    tasks = [timed("T-1", "write it up", 9),
             timed("T-2", "ship it", 15, checked=CHECKED),
             timed("T-3", "a title long enough to be cut " + "x" * 90, 11)]
    app = TaskApp(TODAY)
    app.client = StubClient(tasks)
    app.calendar_config = CFG
    app.tracker_config = TRACK
    # Both sources are reached through a replaced fetch rather than the real
    # one: the board fetches them itself on the way up, and this shell has
    # neither a calendar grant nor a tracker to ask.
    saved_cal, saved_track = ical.fetch, tracker.fetch
    ical.fetch = lambda cfg, day: [ev("standup", 10)]
    tracker.fetch = lambda cfg, **kw: [issue("ZZA-1", "an issue")]
    try:
        async with app.run_test(size=(100, 30)) as pilot:
            for _ in range(14):
                await pilot.pause()
            table = app.query_one(DataTable)
            # What the board would say now, asked afresh.  The rows on
            # screen were drawn from an answer built the same way a moment
            # earlier, so the two must agree character for character.
            answer = app.board().paint()
            check("as many rows drawn as decided",
                  table.row_count, len(answer.rows))
            drawn = [[plain(c) for c in table.get_row_at(i)]
                     for i in range(table.row_count)]
            decided = [[plain(c) for c in cells] for cells in answer.cells]
            check("every cell on screen is the cell that was decided",
                  drawn, decided)
            check("and every source is among them",
                  (len(drawn), len({len(r) for r in drawn})), (5, 1))
            # The cut title is the case that would differ if the drawing did
            # its own shortening: the width comes from the screen, and a
            # second computation would have to fetch it again.
            cut = [r for r in drawn if r[3].endswith("…")]
            check("a title the column had to cut agrees too", len(cut), 1)
    finally:
        ical.fetch, tracker.fetch = saved_cal, saved_track


async def the_line_under_them_agrees():
    print("\n1.2 and the line under the rows")
    app = TaskApp(TODAY)
    app.client = StubClient([timed("T-4", "one", 9), timed("T-5", "two", 10)])
    async with app.run_test(size=(100, 30)) as pilot:
        for _ in range(10):
            await pilot.pause()
        answer = app.board().paint()
        shown = str(app.query_one("#status").content)
        check("the status line is what was decided", shown, answer.status)


for part in (the_table_holds_what_was_decided, the_line_under_them_agrees):
    asyncio.run(part())

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
