"""What a write key does to a marked set.

Everything here is stubbed -- no account, no network, no mailbox. The calendar
is reached through a replaced `ical.fetch` rather than the real one, because
this shell has no macOS Calendar grant and a suite that asked for it would fail
for a reason that has nothing to do with writing to a set.
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
from main import TaskApp, Confirm, DatePicker, ProjectPicker
from singularity import Bucket, CANCELLED, CHECKED, EMPTY
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


async def settle(pilot, n=12):
    for _ in range(n):
        await pilot.pause()

def make(position=None, tasks=(), mails=(), events=(), issues=(), projects=None):
    app = TaskApp(position) if position is not None else TaskApp()
    app.client = StubClient(list(tasks), reference=dt.datetime.now(TZ))
    app.mail_config = None
    app.tracker_config = None
    app.calendar_config = CFG if events else None
    app.projects = dict(projects or {})
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


def ordered(tid, title, n, day=None, **kw):
    """A task whose place in the day is set, so the view's order is known."""
    task = mk(tid, title, TODAY if day is None else day, **kw)
    task.raw["scheduleOrder"] = n * 100
    return task

def row(app, title):
    return next(t for t in app.tasks if (t.raw.get("title") or "") == title)

async def cursor_to(app, pilot, title):
    table = app.query_one(DataTable)
    want = row(app, title)
    at = next(i for i, t in enumerate(app.tasks) if t.id == want.id)
    table.move_cursor(row=at)
    await settle(pilot, 2)
    return want

async def mark(app, pilot, *titles):
    """Mark rows by title.  The key steps the cursor on, so each is sought."""
    for title in titles:
        await cursor_to(app, pilot, title)
        await pilot.press("v")
    await settle(pilot, 4)

def status(app):
    return str(app.query_one("#status").content)

def titles_of(rows):
    return [t.raw.get("title") or "" for t in rows]

def stored(app, title):
    """A task as the store holds it.

    Read from the stub's own store rather than from the board's base, which
    holds only the fetch for the view on screen -- so a task moved to another
    day, or marked in a view the board has since left, is not in it.  What
    these checks are about is whether the write landed, and that is what the
    store answers.
    """
    return next(t for t in app.client.store.values()
                if (t.raw.get("title") or "") == title)


# ------------------------------------------------------------------ 1.1

async def group_1_1():
    print("1.1 which rows a key is about")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "third", 3)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "second")
        rows, passed = app.acting_on()
        check("with nothing marked it is the selected row",
              (titles_of(rows), passed), (["second"], 0))

        await mark(app, pilot, "first", "third")
        await cursor_to(app, pilot, "second")
        rows, passed = app.acting_on()
        check("with rows marked it is those rows",
              (titles_of(rows), passed), (["first", "third"], 0))
        check("and not the row under the cursor",
              "second" in titles_of(rows), False)

    print("\n  rows the board does not own are set aside and counted")
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "a task"), mk("t2", "another")],
               mails=[thread("m1", "a message"), thread("m2", "a second message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a task", "a message", "another", "a second message")
        rows, passed = app.acting_on()
        check("the tasks come back", sorted(titles_of(rows)), ["a task", "another"])
        check("and the rest are counted, not returned", passed, 2)

    app = make(position=Bucket.INBOX, tasks=[mk("t1", "a task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a message")
        rows, passed = app.acting_on()
        check("a set holding nothing the board owns answers nothing",
              (titles_of(rows), passed), ([], 1))

    print("\n  an empty board asks about nothing")
    app = make(position=TODAY, tasks=[])
    async with run(app) as pilot:
        rows, passed = app.acting_on()
        check("no rows, nothing selected", (rows, passed), ([], 0))


# ------------------------------------------------------------------ 1.2

async def group_1_2():
    print("\n1.2 one way of saying what happened")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1)])
    async with run(app) as pilot:
        app.say_what_happened("Cancelled", 4, 2)
        said = status(app)
        check("it names how many were written", "4" in said, True)
        check("and how many were passed over", "2" in said, True)
        check("saying why they were", "not this board's to change" in said, True)

        app.say_what_happened("Cancelled", 3, 0)
        said = status(app)
        check("with none passed over it says nothing about them",
              "not this board's" in said, False)
        check("and still names the count", "3" in said, True)


async def quiet(pilot, app, n=300):
    """Wait until nothing is queued, in flight or waiting for room.

    Some writes sleep in a worker before they send -- taking a tag off waits
    for the store to settle -- so a fixed number of pauses is not enough to
    know a set has finished.
    """
    for _ in range(n):
        await pilot.pause()
        if not app._pending and not app._draining and not app._paced:
            for _ in range(10):
                await pilot.pause()
            return True
    return False

async def until(pilot, ready, n=40):
    for _ in range(n):
        await pilot.pause()
        if ready():
            return True
    return False

def prompt_text(app):
    return " ".join(str(w.render()) for w in app.screen.query("Label, Static"))

def pending(app):
    return sum(len(q) for q in app._pending.values())


# ------------------------------------------------------------------ 2.1

async def group_2_1():
    print("\n2.1 cancelling a marked set")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "third", 3),
                                      ordered("t4", "untouched", 4)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second", "third")
        await cursor_to(app, pilot, "untouched")
        await pilot.press("x")
        await settle(pilot, 40)
        check("every marked task is cancelled",
              [stored(app, t).checked for t in ("first", "second", "third")],
              [CANCELLED] * 3)
        check("the row under the cursor is not",
              stored(app, "untouched").checked, EMPTY)
        check("the board said what it did", "3" in status(app), True)

        await pilot.press("u")
        await settle(pilot, 40)
        check("one press of undo brings all three back",
              [stored(app, t).checked for t in ("first", "second", "third")],
              [EMPTY] * 3)

    print("\n  and with nothing marked it is still one row")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "second")
        await pilot.press("x")
        await settle(pilot, 30)
        check("the selected row is cancelled", stored(app, "second").checked,
              CANCELLED)
        check("and the other is not", stored(app, "first").checked, EMPTY)


# ------------------------------------------------------------------ 2.2

async def group_2_2():
    print("\n2.2 dating a marked set, asked once")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "elsewhere", 3)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        await cursor_to(app, pilot, "elsewhere")
        await pilot.press("d")
        opened = await until(pilot, lambda: isinstance(app.screen, DatePicker))
        check("the date picker opens", opened, True)
        check("and names the set rather than a task",
              "2 marked" in prompt_text(app), True)
        await pilot.press("m")               # "m" is tomorrow; "t" is today
        await settle(pilot, 40)
        check("both marked tasks moved to tomorrow",
              [stored(app, t).local_start(TZ).date()
               for t in ("first", "second")], [TOMORROW] * 2)
        check("the row under the cursor did not",
              stored(app, "elsewhere").local_start(TZ).date(), TODAY)
        # The paste had to space its tasks apart because it sent an order.
        # Dating sends none, which is what lets a set land on a day without
        # disturbing the sequence already there.
        sent = [a for c, a in app.client.calls if c == "set_schedule"]
        check("two schedule writes were sent", len(sent), 2)
        check("and no stored order went with them",
              any("scheduleOrder" in str(a) for a in sent), False)

    print("\n  a set marked across two views is dated in both")
    app = make(position=TODAY, tasks=[ordered("t1", "on today", 1),
                                      mk("t2", "in the inbox")])
    async with run(app) as pilot:
        await mark(app, pilot, "on today")
        await pilot.press("i")
        await settle(pilot, 8)
        await mark(app, pilot, "in the inbox")
        await pilot.press("d")
        if await until(pilot, lambda: isinstance(app.screen, DatePicker)):
            await pilot.press("m")
            await settle(pilot, 40)
        check("both were moved, from whichever view was shown",
              sorted(str(stored(app, t).local_start(TZ).date())
                     for t in ("on today", "in the inbox")),
              [str(TOMORROW), str(TOMORROW)])


# ------------------------------------------------------------------ 3.1

async def group_3_1():
    print("\n3.1 ticking drives a set to one state")
    app = make(position=TODAY,
               tasks=[ordered("t1", "open one", 1),
                      ordered("t2", "done one", 2, checked=CHECKED),
                      ordered("t3", "open two", 3),
                      ordered("t4", "done two", 4, checked=CHECKED)])
    async with run(app) as pilot:
        await mark(app, pilot, "open one", "done one", "open two", "done two")
        await pilot.press("space")
        await settle(pilot, 60)
        # This is the check that matters: a loop over the single-row code
        # would have flipped each row against its own state and brought the
        # two finished ones back.
        check("every task in the set is finished",
              [stored(app, t).checked for t in
               ("open one", "done one", "open two", "done two")], [CHECKED] * 4)

        await pilot.press("space")
        await settle(pilot, 60)
        check("a set finished throughout comes back on one press",
              [stored(app, t).checked for t in
               ("open one", "done one", "open two", "done two")], [EMPTY] * 4)


# ------------------------------------------------------------------ 3.3

async def group_3_3():
    print("\n3.3 ticking a set moves the selection nowhere")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "third", 3)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        parked = await cursor_to(app, pilot, "third")
        await pilot.press("space")
        await settle(pilot, 60)
        table = app.query_one(DataTable)
        check("the selection is where it was",
              app.tasks[table.cursor_row].id, parked.id)
        check("and the set was finished",
              [stored(app, t).checked for t in ("first", "second")],
              [CHECKED] * 2)


# ------------------------------------------------------------------ 2.3

WORK, OTHER = "P-work-0001", "P-other-002"
# The picker lists projects by name, so the one these checks expect `enter`
# to take has to sort first.  Named for that rather than for flavour: the
# first run picked "Other" and every filing check failed on the wrong id.
PROJECTS = {WORK: "Alpha", OTHER: "Beta"}

async def pick_project(app, pilot):
    """Open the picker and take the first project it offers."""
    await pilot.press("p")
    if not await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
        return False
    await pilot.press("enter")
    return True

async def group_2_3():
    print("\n2.3 filing a marked set, asked once")
    app = make(position=TODAY, projects=PROJECTS,
               tasks=[ordered("t1", "first", 1), ordered("t2", "second", 2),
                      ordered("t3", "elsewhere", 3)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        await cursor_to(app, pilot, "elsewhere")
        await pilot.press("p")
        opened = await until(pilot, lambda: isinstance(app.screen, ProjectPicker))
        check("the picker opens once", opened, True)
        check("and names the set rather than a task",
              "2 marked" in prompt_text(app), True)
        await pilot.press("enter")
        # Every row here has no project, so the board asks before filing.
        asked = await until(pilot, lambda: isinstance(app.screen, Confirm))
        check("a first filing is confirmed", asked, True)
        check("and the question counts the rows with no project",
              "2 task(s) with no project" in prompt_text(app), True)
        await pilot.press("y")
        await settle(pilot, 40)
        check("both marked tasks are filed",
              [stored(app, t).project_id for t in ("first", "second")],
              [WORK] * 2)
        check("the row under the cursor is not",
              stored(app, "elsewhere").project_id, None)

    print("\n  answering no files none of them")
    app = make(position=TODAY, projects=PROJECTS,
               tasks=[ordered("t1", "first", 1), ordered("t2", "second", 2)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        await pick_project(app, pilot)
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            await pilot.press("n")
        await settle(pilot, 30)
        check("neither was filed",
              [stored(app, t).project_id for t in ("first", "second")],
              [None, None])
        check("and nothing was sent", app.client.count("set_project"), 0)

    print("\n  a set already filed moves without being asked, and undoes")
    app = make(position=TODAY, projects=PROJECTS,
               tasks=[ordered("t1", "first", 1, project=OTHER),
                      ordered("t2", "second", 2, project=OTHER)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        await pick_project(app, pilot)
        await settle(pilot, 40)
        check("nothing was confirmed", isinstance(app.screen, Confirm), False)
        check("both moved to the chosen project",
              [stored(app, t).project_id for t in ("first", "second")],
              [WORK] * 2)
        await pilot.press("u")
        await settle(pilot, 40)
        check("and one press of undo returns both",
              [stored(app, t).project_id for t in ("first", "second")],
              [OTHER] * 2)

    print("\n  a mixed set: the count is of what is new to the project")
    app = make(position=TODAY, projects=PROJECTS,
               tasks=[ordered("t1", "already filed", 1, project=OTHER),
                      ordered("t2", "unfiled one", 2),
                      ordered("t3", "unfiled two", 3)])
    async with run(app) as pilot:
        await mark(app, pilot, "already filed", "unfiled one", "unfiled two")
        await pilot.press("p")
        if await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
            await pilot.press("enter")
        asked = await until(pilot, lambda: isinstance(app.screen, Confirm))
        check("it asks, because some rows have no project", asked, True)
        check("and counts those rows, not the whole set",
              "2 task(s) with no project" in prompt_text(app), True)
        await pilot.press("y")
        await settle(pilot, 50)
        check("all three end up in the chosen project",
              [stored(app, t).project_id for t in
               ("already filed", "unfiled one", "unfiled two")], [WORK] * 3)
        await pilot.press("u")
        await settle(pilot, 30)
        check("and undo refuses for the whole set",
              "cannot be undone" in status(app), True)
        check("leaving every row where the filing put it",
              [stored(app, t).project_id for t in
               ("already filed", "unfiled one", "unfiled two")], [WORK] * 3)

    print("\n  rows already in the chosen project are left out")
    app = make(position=TODAY, projects=PROJECTS,
               tasks=[ordered("t1", "already there", 1, project=WORK),
                      ordered("t2", "moving", 2, project=OTHER)])
    async with run(app) as pilot:
        await mark(app, pilot, "already there", "moving")
        await pick_project(app, pilot)
        await settle(pilot, 40)
        check("only the row that had to move was written",
              app.client.count("set_project"), 1)
        check("and the report counts one, not two", "1" in status(app), True)


# ------------------------------------------------------------------ 2.4

async def group_2_4():
    print("\n2.4 recording a day's work on a marked set")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "elsewhere", 3)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        await cursor_to(app, pilot, "elsewhere")
        await pilot.press("full_stop")
        await settle(pilot, 50)
        check("both were recorded", app.client.count("complete_today"), 2)
        check("and rescheduled to tomorrow",
              [stored(app, t).local_start(TZ).date()
               for t in ("first", "second")], [TOMORROW] * 2)
        check("the row under the cursor was not touched",
              stored(app, "elsewhere").local_start(TZ).date(), TODAY)

        await pilot.press("u")
        await settle(pilot, 40)
        said = status(app)
        # The board's existing note about this being only half reversible is
        # carried by the undo entry, which the writes share -- so it is said
        # once for the set rather than once per row.
        check("undo says the record cannot be withdrawn",
              "cannot be withdrawn" in said, True)
        check("and says it once", said.count("cannot be withdrawn"), 1)


# ------------------------------------------------------------------ 2.5

async def group_2_5():
    print("\n2.5 deleting a marked set, behind one question")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "third", 3),
                                      ordered("t4", "kept", 4)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second", "third")
        await cursor_to(app, pilot, "kept")
        await pilot.press("backspace")
        asked = await until(pilot, lambda: isinstance(app.screen, Confirm))
        check("one question is asked", asked, True)
        text = prompt_text(app)
        check("and it names how many rows will go", "3 marked task(s)" in text,
              True)
        check("this set is all on screen, so it does not say otherwise",
              "not in this view" in text, False)
        await pilot.press("n")
        await settle(pilot, 20)
        check("answering no deletes nothing", app.client.count("delete_task"), 0)

        await pilot.press("backspace")
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            await pilot.press("y")
        await settle(pilot, 60)
        check("answering yes removes them all",
              app.client.count("delete_task"), 3)
        check("and the row under the cursor stays",
              "kept" in [t.raw.get("title") for t in app.client.store.values()],
              True)

        await pilot.press("u")
        await settle(pilot, 20)
        check("undo says a deletion cannot be undone",
              "cannot be undone" in status(app), True)


# ------------------------------------------------------------------ 3.2

async def group_3_2():
    print("\n3.2 the green mark drives a set to one state")
    app = make(position=TODAY, tasks=[ordered("t1", "plain one", 1),
                                      ordered("t2", "plain two", 2)])
    app.client.green = "tag-green"
    async with run(app) as pilot:
        app.green_tag = "tag-green"
        app.green_checked = False
        await mark(app, pilot, "plain one", "plain two")
        await pilot.press("g")
        await quiet(pilot, app)
        check("both carry the mark",
              [stored(app, t).has_tag("tag-green") for t in
               ("plain one", "plain two")], [True, True])
        await pilot.press("g")
        await quiet(pilot, app)
        check("and one more press takes it off both",
              [stored(app, t).has_tag("tag-green") for t in
               ("plain one", "plain two")], [False, False])

    print("\n  a mixed set is driven to marked, not flipped")
    app = make(position=TODAY, tasks=[ordered("t1", "plain", 1),
                                      ordered("t2", "green already", 2)])
    async with run(app) as pilot:
        app.green_tag = "tag-green"
        app.green_checked = False
        stored(app, "green already").raw["tags"] = ["tag-green"]
        for t in app._base:
            if t.title == "green already":
                t.raw["tags"] = ["tag-green"]
        await mark(app, pilot, "plain", "green already")
        await pilot.press("g")
        await quiet(pilot, app)
        check("both are green",
              [stored(app, t).has_tag("tag-green") for t in
               ("plain", "green already")], [True, True])

    print("\n  every other tag a row holds survives")
    # The board's one read-modify-write: the store replaces a task's tags
    # outright, so each write carries that row's other tags back with it.
    # One list built for the set would have put the first row's tags on
    # every row and silently dropped the rest.
    app = make(position=TODAY, tasks=[ordered("t1", "has one tag", 1),
                                      ordered("t2", "has another", 2)])
    async with run(app) as pilot:
        app.green_tag = "tag-green"
        app.green_checked = False
        for t in list(app._base) + list(app.client.store.values()):
            if t.title == "has one tag":
                t.raw["tags"] = ["tag-alpha"]
            elif t.title == "has another":
                t.raw["tags"] = ["tag-beta"]
        await mark(app, pilot, "has one tag", "has another")
        await pilot.press("g")
        await quiet(pilot, app)
        check("the first row kept its own tag",
              sorted(stored(app, "has one tag").tags),
              sorted(["tag-alpha", "tag-green"]))
        check("and the second kept its own, not the first's",
              sorted(stored(app, "has another").tags),
              sorted(["tag-beta", "tag-green"]))


# ------------------------------------------------------------------ 4

def mixed(app):
    """A board holding two tasks and one row from somewhere else."""
    return app

async def group_4_1():
    print("\n4.1 every write key passes over what it does not own")
    # The mailbox's row is the one every key can meet, because mail and the
    # board's own tasks share the inbox.  Each key is checked by name: the
    # rule is written once but applied seven times, and a key that forgot to
    # ask would go on acting on the selected row with nothing failing.
    for key, name, landed in (
        ("x", "cancelling", lambda a: a.client.count("cancel_task")),
        ("space", "ticking", lambda a: a.client.count("set_done")),
        ("full_stop", "recording a day's work",
         lambda a: a.client.count("complete_today")),
        ("g", "the green mark", lambda a: a.client.count("set_tags")),
    ):
        app = make(position=Bucket.INBOX,
                   tasks=[mk("t1", "a task"), mk("t2", "another task")],
                   mails=[thread("m1", "a message")])
        async with run(app) as pilot:
            app.green_tag = "tag-green"
            app.green_checked = False
            await mark(app, pilot, "a task", "a message", "another task")
            await pilot.press(key)
            await quiet(pilot, app)
            check(f"{name}: both tasks were written", landed(app), 2)
            check(f"{name}: and the report counts the row passed over",
                  "1 not this board" in status(app), True)
            check(f"{name}: nothing reached the mailbox",
                  app.mail_busy, 0)

    print("\n  the two that ask something first")
    app = make(position=Bucket.INBOX, projects=PROJECTS,
               tasks=[mk("t1", "a task"), mk("t2", "another task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a task", "a message", "another task")
        await pilot.press("d")
        if await until(pilot, lambda: isinstance(app.screen, DatePicker)):
            check("dating: the prompt counts only the rows it can write",
                  "2 marked" in prompt_text(app), True)
            await pilot.press("m")
        await quiet(pilot, app)
        check("dating: both tasks were written",
              app.client.count("set_schedule"), 2)
        check("dating: and one row was passed over",
              "1 not this board" in status(app), True)

    app = make(position=Bucket.INBOX, projects=PROJECTS,
               tasks=[mk("t1", "a task"), mk("t2", "another task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a task", "a message", "another task")
        await pilot.press("p")
        if await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
            check("filing: the prompt counts only the rows it can write",
                  "2 marked" in prompt_text(app), True)
            await pilot.press("enter")
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            await pilot.press("y")
        await quiet(pilot, app)
        check("filing: both tasks were written",
              app.client.count("set_project"), 2)

    print("\n  and deleting")
    app = make(position=Bucket.INBOX,
               tasks=[mk("t1", "a task"), mk("t2", "another task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a task", "a message", "another task")
        await pilot.press("backspace")
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            check("deleting: the question counts only what it can delete",
                  "2 marked task(s)" in prompt_text(app), True)
            await pilot.press("y")
        await quiet(pilot, app)
        check("deleting: both tasks went", app.client.count("delete_task"), 2)
        check("deleting: and the message is still there",
              len(app.mail_threads), 1)


async def group_4_2():
    print("\n4.2 a set holding nothing the board owns")
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "a task")],
               mails=[thread("m1", "a message"),
                      thread("m2", "a second message")])
    async with run(app) as pilot:
        await mark(app, pilot, "a message", "a second message")
        await cursor_to(app, pilot, "a task")
        for key in ("x", "space", "full_stop", "backspace"):
            await pilot.press(key)
            await settle(pilot, 10)
        # Named rather than counted: the board makes reads of its own on
        # startup -- the projects, the day, the green tag's title -- and
        # counting every call measured those instead of these keys.
        writes = ("cancel_task", "set_done", "complete_today", "set_tags",
                  "delete_task", "set_schedule", "set_project", "update_task")
        check("no write of any kind was sent",
              [w for w in writes if app.client.count(w)], [])
        check("and the board says nothing was written",
              "Nothing marked here" in status(app), True)
        check("the row under the cursor was never touched",
              stored(app, "a task").checked, EMPTY)


async def group_4_3():
    print("\n4.3 ticking a set does not file the mail in it")
    app = make(position=Bucket.INBOX,
               tasks=[mk("t1", "a task"), mk("t2", "another task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        # No gateway is configured under the harness, so nothing here could
        # reach a server -- but the board would still have started the
        # review and counted it busy, which is what this watches for.
        started = []
        app.review = lambda task: started.append(task)
        await mark(app, pilot, "a task", "a message", "another task")
        await pilot.press("space")
        await quiet(pilot, app)
        check("no review was started", started, [])
        check("the message is still in the inbox", len(app.mail_threads), 1)
        check("and the tasks were finished", app.client.count("set_done"), 2)


# ------------------------------------------------------------------ 5

async def group_5_1():
    print("\n5.1 one action, one undo, sent at the width the store takes")
    wide = main.PACED_AT_ONCE
    names = [f"row {n:02d}" for n in range(wide * 3)]
    app = make(position=TODAY,
               tasks=[ordered(f"t{n}", name, n + 1)
                      for n, name in enumerate(names)])
    async with run(app) as pilot:
        await mark(app, pilot, *names)
        check("every row is marked", len(app.marked), len(names))
        app.client.gate = threading.Event()      # hold every write open
        await pilot.press("x")
        await settle(pilot, 25)
        check("no more than the cap is in flight at once",
              len(app._paced_out), wide)
        check("and only that many have been sent",
              app.client.count("cancel_task"), wide)
        app.client.gate.set()
        await quiet(pilot, app, 600)
        check("every row was written in the end",
              app.client.count("cancel_task"), len(names))
        check("nothing is left waiting",
              (len(app._paced), len(app._paced_out)), (0, 0))

        await pilot.press("u")
        await quiet(pilot, app, 600)
        check("and one press of undo reverses all of it",
              [stored(app, n).checked for n in names], [EMPTY] * len(names))


async def group_5_2():
    print("\n5.2 the question says when the set reaches past this view")
    app = make(position=TODAY, tasks=[ordered("t1", "on today", 1),
                                      mk("t2", "in the inbox")])
    async with run(app) as pilot:
        await mark(app, pilot, "on today")
        await pilot.press("i")
        await settle(pilot, 8)
        await mark(app, pilot, "in the inbox")
        check("the view is not drawing both marked rows",
              app.marks_off_screen(), True)
        await pilot.press("backspace")
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            text = prompt_text(app)
            check("the question names the count",
                  "2 marked task(s)" in text, True)
            check("and says the set is not all in this view",
                  "not in this view" in text, True)
            await pilot.press("n")
        else:
            check("the question is asked", False, True)

    print("\n  and does not say it when every marked row is drawn")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2)])
    async with run(app) as pilot:
        await mark(app, pilot, "first", "second")
        check("every marked row is on screen", app.marks_off_screen(), False)
        await pilot.press("backspace")
        if await until(pilot, lambda: isinstance(app.screen, Confirm)):
            text = prompt_text(app)
            check("it names the count", "2 marked task(s)" in text, True)
            check("and claims nothing about other views",
                  "not in this view" in text, False)
            await pilot.press("n")
        else:
            check("the question is asked", False, True)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    group_1_1,
    group_1_2,
    group_2_1,
    group_2_2,
    group_3_1,
    group_2_3,
    group_2_4,
    group_2_5,
    group_3_2,
    group_3_3,
    group_4_1,
    group_4_2,
    group_4_3,
    group_5_1,
    group_5_2,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
