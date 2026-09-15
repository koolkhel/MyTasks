"""Marking rows: what the key does, how a mark is drawn, and how long it lasts.

Everything here is stubbed -- no account, no network, no mailbox. The calendar
is reached through a replaced `ical.fetch` rather than the real one, because
this shell has no macOS Calendar grant and a suite that asked for it would fail
for a reason that has nothing to do with marking.
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
import main, ical, mail, tracker
from main import TaskApp
from singularity import Bucket, CHECKED
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
TOMORROW = TODAY + dt.timedelta(days=1)
CFG = ical.Config(work="WorkAcc", personal=("Me",))

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

def ev(title, hh=9, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False)

def issue(key, summary):
    return tracker.Issue(key=key, summary=summary, project="ZZA",
                         state="In progress", assignee="me",
                         base_url="https://track.invalid")

def thread(ident, subject):
    when = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    return mail.Thread((
        mail.Message(sender="someone@example.invalid", subject=subject, when=when,
                     ident=f"<{ident}@example.invalid>", answers=None,
                     body="", text="", folder="Feed", key=ident),))


async def settle(pilot, n=8):
    for _ in range(n):
        await pilot.pause()

def make(position=None, tasks=(), mails=(), events=(), issues=()):
    app = TaskApp(position) if position is not None else TaskApp()
    app.client = StubClient(list(tasks), reference=dt.datetime.now(TZ))
    app.mail_config = None
    app.tracker_config = None
    app.calendar_config = CFG if events else None
    app._pending_mail = list(mails)
    app._pending_events = list(events)
    app._pending_issues = list(issues)
    return app

class run:
    def __init__(self, app, size=(120, 40)):
        self.app, self.size = app, size

    async def __aenter__(self):
        self.saved = ical.fetch
        ical.fetch = lambda cfg, day: list(self.app._pending_events)
        self.ctx = self.app.run_test(size=self.size)
        self.pilot = await self.ctx.__aenter__()
        await settle(self.pilot, 12)
        self.app.mail_threads = list(self.app._pending_mail)
        self.app.tracker_issues = list(self.app._pending_issues)
        if self.app._pending_events:
            self.app.events = list(self.app._pending_events)
            self.app.events_day = self.app.position
        self.app.repaint()
        await settle(self.pilot)
        return self.pilot

    async def __aexit__(self, *exc):
        ical.fetch = self.saved
        return await self.ctx.__aexit__(*exc)


def row(app, title):
    return next(t for t in app.tasks if (t.raw.get("title") or "") == title)

async def cursor_to(app, pilot, title):
    """Put the row cursor on a row by title, and give it back."""
    table = app.query_one(DataTable)
    want = row(app, title)
    at = next(i for i, t in enumerate(app.tasks) if t.id == want.id)
    table.move_cursor(row=at)
    await settle(pilot, 2)
    return want

def cell(app, task):
    """The row-mark cell as drawn."""
    return str(app.row_for(task)[1])

def titles_of(app):
    return [t.raw.get("title") or "" for t in app.marked_tasks()]

def status(app):
    return str(app.query_one("#status").content)


# ------------------------------------------------------------------ 3.1

async def group_3_1():
    print("3.1 the key marks a row, and takes the mark off again")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY),
                                      mk("t3", "third", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("the row is marked", titles_of(app), ["first"])
        await pilot.press("v")
        check("pressing it again takes the mark off", titles_of(app), [])

        print("\n  the order is the order of pressing, not the order drawn")
        await cursor_to(app, pilot, "third")
        await pilot.press("v")
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        check("three rows marked", len(app.marked), 3)
        check("in the order they were pressed", titles_of(app),
              ["third", "first", "second"])
        check("which is not the order the view drew them in",
              titles_of(app) != [t.raw.get("title") for t in app.tasks][:3], True)

        print("\n  and nothing was written")
        check("no write was queued", sum(len(q) for q in app._pending.values()), 0)

    print("\n  the key works in the other keyboard layout")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("м")
        check("the Russian twin marks too", titles_of(app), ["first"])


# ------------------------------------------------------------------ 3.2

async def group_3_2():
    print("\n3.2 a marked row is drawn as one")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY)])
    async with run(app) as pilot:
        first, second = row(app, "first"), row(app, "second")
        plain = cell(app, first)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        marked = cell(app, first)
        check("the marked row's cell differs from its unmarked one",
              marked != plain, True)
        check("it carries the copy mark", main.COPY_MARK in marked, True)
        check("it still carries the row's own mark", plain in marked, True)
        check("and it fits the two cells the column has", len(marked), 2)
        check("an unmarked row beside it carries no copy mark",
              main.COPY_MARK in cell(app, second), False)
        check("and is otherwise unchanged", cell(app, second), plain)

        print("\n  the mark survives being the selected row")
        # The cursor replaces a colour outright while leaving a glyph alone,
        # which is why this is a character.  If it were a colour the mark
        # would vanish on exactly the row a person is looking at.
        table = app.query_one(DataTable)
        at = next(i for i, t in enumerate(app.tasks) if t.id == first.id)
        check("the marked row is the selected one", table.cursor_row, at)
        # Compared against the unmarked cell rather than against what this
        # row drew a moment ago.  Comparing a cell with itself passes
        # whatever the drawing does, which a vacuity run caught: with the
        # mark removed altogether this check went on passing.
        check("and it still carries the copy mark while selected",
              main.COPY_MARK in cell(app, first), True)
        check("which is more than the unmarked row draws",
              cell(app, first) != plain, True)

        print("\n  the cursor and the mark are different things")
        await cursor_to(app, pilot, "second")
        check("the cursor moved", app.tasks[table.cursor_row].id, second.id)
        check("the first row is still marked", titles_of(app), ["first"])
        check("and still drawn marked, with the cursor elsewhere",
              main.COPY_MARK in cell(app, first), True)
        check("while the row under the cursor is not marked",
              main.COPY_MARK in cell(app, second), False)


# ------------------------------------------------------------------ 3.3

async def group_3_3():
    print("\n3.3 every row the board draws can be marked")
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "an own task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "a message")
        await pilot.press("v")
        check("a mail row is marked", titles_of(app), ["a message"])
        check("and it was not refused out loud", app._notice, None)
        check("nothing was written", sum(len(q) for q in app._pending.values()), 0)

    app = make(position=TODAY, tasks=[mk("t1", "an own task", TODAY)],
               events=[ev("an event")], issues=[issue("ZZA-1", "an issue")])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "an event")
        await pilot.press("v")
        await cursor_to(app, pilot, "ZZA-1 — an issue")
        await pilot.press("v")
        check("an event and a tracker issue are marked",
              titles_of(app), ["an event", "ZZA-1 — an issue"])
        check("and neither was refused out loud", app._notice, None)
        check("nothing was written", sum(len(q) for q in app._pending.values()), 0)


# ------------------------------------------------------------------ 3.4

async def group_3_4():
    print("\n3.4 how long a mark lasts")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        print("\n  a write landing rebuilds the table")
        await cursor_to(app, pilot, "second")
        await pilot.press("space")            # tick the other row
        await settle(pilot, 10)
        check("the mark is still on the row it was put on",
              titles_of(app), ["first"])
        check("and the row that was ticked is not marked",
              row(app, "second").checked, CHECKED)

    print("\n  marks gathered from several views")
    app = make(position=TODAY,
               tasks=[mk("t1", "on today", TODAY), mk("t2", "in the inbox"),
                      mk("t3", "in someday", deferred=True),
                      mk("t4", "on tomorrow", TOMORROW)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "on today")
        await pilot.press("v")
        await pilot.press("i")                # the inbox
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in the inbox")
        await pilot.press("v")
        await pilot.press("s")                # someday
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in someday")
        await pilot.press("v")
        check("three rows from three views are marked", len(app.marked), 3)
        check("and the copy can still reach every one of them",
              sorted(titles_of(app)), ["in someday", "in the inbox", "on today"])
        await pilot.press("t")                # back to today
        await settle(pilot, 6)
        check("they are still marked from a fourth view", len(app.marked), 3)

    print("\n  a mark on a row the board no longer holds")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "doomed", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        doomed = await cursor_to(app, pilot, "doomed")
        await pilot.press("v")
        check("both are marked", len(app.marked), 2)
        # The row leaves the board the way a deletion leaves it: gone from
        # what was fetched, with the next repaint noticing.
        app._base = [t for t in app._base if t.id != doomed.id]
        app.repaint()
        await settle(pilot)
        check("the mark on the row that went is forgotten", titles_of(app), ["first"])
        check("and the count no longer counts it", len(app.marked), 1)

    print("\n  escape clears every mark")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("marked", len(app.marked), 1)
        await pilot.press("escape")
        await settle(pilot)
        check("escape cleared it", app.marked, [])
        check("and forgot the row with it", app._marked_rows, {})


# ------------------------------------------------------------------ 3.5

async def group_3_5():
    print("\n3.5 the board says how many rows are marked")


    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY),
                                      mk("t3", "elsewhere")])
    async with run(app) as pilot:
        check("nothing is said with no row marked",
              "marked" in status(app), False)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("one marked is reported", "1 marked" in status(app), True)
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        check("two marked is reported", "2 marked" in status(app), True)

        print("\n  a mark this view cannot draw is still counted")
        await pilot.press("i")                # the inbox, which holds neither
        await settle(pilot, 6)
        check("the rows marked on today are not drawn here",
              [t.raw.get("title") for t in app.tasks], ["elsewhere"])
        check("but the count still says two", "2 marked" in status(app), True)

        print("\n  and one a search is hiding is counted too")
        await cursor_to(app, pilot, "elsewhere")
        await pilot.press("v")
        app.searching = "nothing matches this"
        app.repaint()
        await settle(pilot)
        check("the view is empty", app.tasks, [])
        check("the count still says three", "3 marked" in status(app), True)

        await pilot.press("escape")
        await settle(pilot)
        check("escape clears the search and the marks together",
              (app.searching, app.marked), (None, []))
        check("and the count says nothing again",
              "marked" in status(app), False)


def main_():
    asyncio.run(group_3_1())
    asyncio.run(group_3_2())
    asyncio.run(group_3_3())
    asyncio.run(group_3_4())
    asyncio.run(group_3_5())
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main_())
