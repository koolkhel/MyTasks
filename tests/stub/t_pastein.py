"""Pasting lines onto the board: what is made, where, in what order, and how
it is taken back.

Everything here is stubbed -- no account, no network, no clipboard. Pastes are
delivered as the event a terminal sends, so the board's own handler is what is
being exercised rather than a function called directly.
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
import main, ical
from main import TaskApp, TaskInput
from singularity import ApiError, Bucket, CHECKED, EMPTY
from textual import events
from textual.widgets import DataTable, Input, Label

TODAY = dt.datetime.now(TZ).date()
TOMORROW = TODAY + dt.timedelta(days=1)

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


async def settle(pilot, n=12):
    for _ in range(n):
        await pilot.pause()

def make(position=None, tasks=()):
    app = TaskApp(position) if position is not None else TaskApp()
    app.client = StubClient(list(tasks), reference=dt.datetime.now(TZ))
    app.mail_config = None
    app.tracker_config = None
    app.calendar_config = None
    return app

class run:
    def __init__(self, app, size=(120, 40)):
        self.app, self.size = app, size

    async def __aenter__(self):
        self.saved = ical.fetch
        ical.fetch = lambda cfg, day: []
        self.ctx = self.app.run_test(size=self.size)
        self.pilot = await self.ctx.__aenter__()
        await settle(self.pilot, 12)
        return self.pilot

    async def __aexit__(self, *exc):
        ical.fetch = self.saved
        return await self.ctx.__aexit__(*exc)


async def paste(app, pilot, text, settle_for=25):
    """Deliver text the way a terminal delivers a paste."""
    app.post_message(events.Paste(text))
    await settle(pilot, settle_for)

def titles(app):
    return [t.raw.get("title") or "" for t in app.tasks]

def status(app):
    return str(app.query_one("#status").content)

def created(app):
    return [a[0] for name, a in app.client.calls if name == "create_task"]


# ------------------------------------------------------------------ 5.1

async def group_5_1():
    print("5.1 pasted lines become tasks in the shown view")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "- first\n- second\n- third\n")
        check("one task per line", sorted(created(app)),
              ["first", "second", "third"])
        check("they are on the board", sorted(titles(app)),
              ["first", "second", "third"])
        check("the board says what it pasted", "Pasted 3" in status(app), True)

    print("\n  and land where the add key would have put them")
    app = make(position=Bucket.INBOX)
    async with run(app) as pilot:
        await paste(app, pilot, "- inbox one\n- inbox two")
        made = [t for t in app._base if t.title.startswith("inbox")]
        check("two in the inbox", len(made), 2)
        check("undated", [t.raw.get("start") for t in made], [None, None])
        check("and not deferred", [t.raw.get("deferred") for t in made],
              [False, False])

    app = make(position=Bucket.SOMEDAY)
    async with run(app) as pilot:
        await paste(app, pilot, "- put off")
        made = [t for t in app._base if t.title == "put off"]
        check("someday gives a deferred task",
              [t.raw.get("deferred") for t in made], [True])

    app = make(position=TOMORROW)
    async with run(app) as pilot:
        await paste(app, pilot, "- on tomorrow")
        made = [t for t in app._base if t.title == "on tomorrow"]
        check("a day gives a task dated to it",
              [t.local_start(TZ).date() for t in made], [TOMORROW])
        check("and it is not timed", [t.raw.get("useTime") for t in made],
              [False])

    print("\n  blank lines are not tasks, and one line is one task")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "- first\n\n- second\n   \n\n")
        check("two tasks from five lines", sorted(created(app)),
              ["first", "second"])

    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "just the one")
        check("a single line makes a single task", created(app), ["just the one"])

    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "\n   \n\n")
        check("a paste with nothing in it makes nothing", created(app), [])
        check("and says nothing", "Pasted" in status(app), False)


# ------------------------------------------------------------------ 5.2

async def group_5_2():
    print("\n5.2 each pasted task gets a place of its own")
    existing = mk("t1", "already here", TODAY)
    existing.raw["scheduleOrder"] = 500
    app = make(position=TODAY, tasks=[existing])
    async with run(app) as pilot:
        await paste(app, pilot, "- one\n- two\n- three")
        made = [t for t in app._base if t.title in ("one", "two", "three")]
        orders = [t.schedule_order for t in made]
        check("three distinct stored orders", len(set(orders)), 3)
        check("in the order they were pasted", orders, sorted(orders))
        # Guarded rather than assumed: with the reader neutered for a
        # vacuity run nothing matches, and an unguarded min() aborted the
        # suite before it could report the rest of what it had caught.
        check("all past the task already there",
              bool(orders) and min(orders) > 500, True)
        # Had the day's last place been read once per task rather than once
        # per paste, every one of these would hold the same number and the
        # view would fall back to ordering them by title.
        check("so the view keeps the pasted sequence",
              [t for t in titles(app) if t in ("one", "two", "three")],
              ["one", "two", "three"])

    print("\n  and a dateless view asks for no order at all")
    app = make(position=Bucket.INBOX)
    async with run(app) as pilot:
        await paste(app, pilot, "- a\n- b")
        made = [t for t in app._base if t.title in ("a", "b")]
        check("no stored order was sent",
              [("scheduleOrder" in t.raw) for t in made], [False, False])


# ------------------------------------------------------------------ 5.3

async def group_5_3():
    print("\n5.3 a ticked line becomes a finished task")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "- [ ] open one\n- [x] closed one")
        check("both were created", sorted(created(app)),
              ["closed one", "open one"])
        completed = [a[0] for name, a in app.client.calls
                     if name == "complete_task"]
        check("one completion followed", len(completed), 1)
        # The completion is queued under the placeholder and must reach the
        # identity the creation handed back, not the one that never existed.
        # Guarded for the same reason as the orders above: a vacuity run
        # leaves this list empty, and indexing it aborted the suite before
        # it could report the rest.
        check("against the identity the store gave back",
              bool(completed) and completed[0].startswith("T-new-"), True)
        finished = [t for t in app._base if t.title == "closed one"]
        check("and the row is drawn finished",
              [t.checked for t in finished], [CHECKED])
        open_one = [t for t in app._base if t.title == "open one"]
        check("the unticked line is not",
              [t.checked for t in open_one], [EMPTY])


# ------------------------------------------------------------------ 5.4

async def group_5_4():
    print("\n5.4 a long paste is sent a few at a time")
    app = make(position=TODAY)
    async with run(app) as pilot:
        app.client.gate = threading.Event()      # hold every write open
        lines = "\n".join(f"- line {n:02d}" for n in range(20))
        app.post_message(events.Paste(lines))
        await settle(pilot, 20)
        check("every row is on the board at once",
              len([t for t in app._base if t.title.startswith("line ")]), 20)
        check("but only the cap is in flight",
              len(app._paced_out), main.PACED_AT_ONCE)
        check("and only the cap has been sent",
              len(created(app)), main.PACED_AT_ONCE)
        app.client.gate.set()                    # let them all through
        await settle(pilot, 120)
        check("every line was created in the end", len(created(app)), 20)
        check("nothing is left waiting", (len(app._paced), len(app._paced_out)),
              (0, 0))
        check("and no line was lost", len(set(created(app))), 20)


# ------------------------------------------------------------------ 5.5

async def group_5_5():
    print("\n5.5 a line the store refuses")
    app = make(position=TODAY)
    async with run(app) as pilot:
        app.client.fail_ids[("create_task", "doomed")] = ApiError(500, "Sync error: please try again later")
        await paste(app, pilot, "- kept one\n- doomed\n- kept two", settle_for=40)
        check("the two the store took are there",
              sorted(t.title for t in app._base), ["kept one", "kept two"])
        check("the refused line's row is gone",
              any(t.title == "doomed" for t in app._base), False)
        said = status(app)
        check("the board says which line failed", "doomed" in said, True)
        check("and what the store said", "HTTP 500" in said, True)


# ------------------------------------------------------------------ 5.6

async def group_5_6():
    print("\n5.6 one paste, one undo")
    app = make(position=TODAY, tasks=[mk("t1", "was here before", TODAY)])
    async with run(app) as pilot:
        await paste(app, pilot, "- one\n- two\n- three")
        check("three added", len([t for t in app._base
                                  if t.title in ("one", "two", "three")]), 3)
        await pilot.press("u")
        await settle(pilot, 40)
        deleted = [a[0] for name, a in app.client.calls if name == "delete_task"]
        check("all three were deleted", len(deleted), 3)
        check("and none of them is left on the board",
              [t.title for t in app._base], ["was here before"])
        check("the task that was there before is untouched",
              "was here before" in [t.title for t in app._base], True)
        check("and the undo said what it did",
              "Undid" in status(app), True)

    print("\n  pressing undo again reaches past the paste")
    app = make(position=TODAY, tasks=[mk("t1", "older", TODAY)])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        table.move_cursor(row=0)
        await settle(pilot, 4)
        await pilot.press("space")              # tick the older task
        await settle(pilot, 20)
        await paste(app, pilot, "- one\n- two")
        await pilot.press("u")                  # takes back the paste
        await settle(pilot, 40)
        check("the paste is gone", [t.title for t in app._base], ["older"])
        await pilot.press("u")                  # reaches the tick
        await settle(pilot, 20)
        older = next(t for t in app._base if t.title == "older")
        check("and the write before it is reversed", older.checked, EMPTY)

    print("\n  the undo deletes a few at a time too")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await paste(app, pilot, "\n".join(f"- line {n:02d}" for n in range(12)),
                    settle_for=90)
        check("twelve created", len(created(app)), 12)
        app.client.gate = threading.Event()
        await pilot.press("u")
        await settle(pilot, 20)
        check("only the cap is in flight", len(app._paced_out),
              main.PACED_AT_ONCE)
        app.client.gate.set()
        await settle(pilot, 120)
        deleted = [a[0] for name, a in app.client.calls if name == "delete_task"]
        check("and all twelve were deleted in the end", len(deleted), 12)


# ------------------------------------------------------------------ 5.7

async def group_5_7():
    print("\n5.7 a multi-line paste into the title prompt is not silently cut")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await pilot.press("a")
        await settle(pilot, 6)
        screen = app.screen
        check("the prompt is open", isinstance(screen, TaskInput), True)
        hint = screen.query_one("#dialog-hint", Label)
        before = str(hint.render())
        screen.query_one(Input).post_message(events.Paste("first\nsecond\nthird"))
        await settle(pilot, 8)
        after = str(hint.render())
        check("the prompt no longer says only what it said before",
              after != before, True)
        check("it says how many lines it did not take", "2 more line" in after,
              True)
        check("and where to paste them all", "board" in after, True)
        check("the first line is still in the box",
              screen.query_one(Input).value, "first")

    print("\n  a single-line paste says nothing new")
    app = make(position=TODAY)
    async with run(app) as pilot:
        await pilot.press("a")
        await settle(pilot, 6)
        screen = app.screen
        hint = screen.query_one("#dialog-hint", Label)
        before = str(hint.render())
        screen.query_one(Input).post_message(events.Paste("just one line"))
        await settle(pilot, 8)
        check("the hint is unchanged", str(hint.render()), before)
        check("and the line is in the box",
              screen.query_one(Input).value, "just one line")


def main_():
    for group in (group_5_1, group_5_2, group_5_3, group_5_4,
                  group_5_5, group_5_6, group_5_7):
        asyncio.run(group())
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main_())
