"""Opening a tracker issue a task mentions, and choosing among several.

Project keys here are invented (AAA, BBB) -- never the real configured ones,
which are deliberately absent from this repository.
"""
import asyncio, datetime as dt, sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import main, tracker, ical, singularity
from contextlib import asynccontextmanager

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
BASE = "https://tr.example"
CFG = tracker.Config(base_url=BASE, token="t", assignee="me",
                     projects=("AAA", "BBB"), states=("In progress",))
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def task(tid, title, note=None):
    t = mk(tid, title, TODAY)
    if note is not None:
        t.raw["note"] = singularity.note_document(note)
    return t

@asynccontextmanager
async def board(tasks, tracker_cfg=CFG):
    app = main.TaskApp()
    app.client = StubClient(tasks, reference=NOW)
    app.calendar_config = None
    app.tracker_config = tracker_cfg
    opened = []
    app.open_url = lambda url: opened.append(url)
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        yield app, pilot, opened

async def select(app, pilot, tid):
    row = next(i for i, t in enumerate(app.tasks) if t.id == tid)
    app.query_one(main.DataTable).move_cursor(row=row)
    app._selected_id = tid
    await pilot.pause()

def status(app): return str(app.query_one("#status").render())

# ------------------------------------------------------- one candidate
async def one():
    print("exactly one thing to open, opened at once")
    rows = [task("t1", "fix AAA-1234"),
            task("t2", "read https://a.example/x"),
            task("t3", "nothing here", "nor here"),
            task("t4", "plain", "but BBB-77 in the note")]
    async with board(rows) as (app, pilot, opened):
        await select(app, pilot, "t1")
        await pilot.press("o"); await pilot.pause()
        check("a mentioned issue opens its page", opened[-1:], [f"{BASE}/issue/AAA-1234"])
        check("no choice was presented",
              [type(s).__name__ for s in app.screen_stack], ["Screen"])
        await select(app, pilot, "t2")
        await pilot.press("o"); await pilot.pause()
        check("an address still opens as before", opened[-1:], ["https://a.example/x"])
        await select(app, pilot, "t4")
        await pilot.press("o"); await pilot.pause()
        check("a key in the note opens too", opened[-1:], [f"{BASE}/issue/BBB-77"])
        before = list(opened)
        await select(app, pilot, "t3")
        await pilot.press("o"); await pilot.pause()
        check("a task with none opens nothing", opened, before)
        check("and says so, unchanged", status(app), "That task has no link")
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written by any of it", writes, [])

# ------------------------------------------------------ several candidates
async def several():
    print("several things to open, so it asks")
    rows = [task("t1", "AAA-1 and https://a.example/x"),
            task("t2", "https://one.example and https://two.example"),
            task("t3", "AAA-9", "then https://note.example")]
    async with board(rows) as (app, pilot, opened):
        await select(app, pilot, "t1")
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        check("the chooser opens", type(app.screen_stack[-1]).__name__, "LinkPicker")
        shown = [str(o.prompt) for o in
                 app.screen_stack[-1].query_one(main.OptionList).options]
        check("listing an issue by key and an address by the address",
              shown, ["AAA-1", "https://a.example/x"])
        check("nothing opened yet", opened, [])
        await pilot.press("escape")
        for _ in range(8): await pilot.pause()
        check("leaving opens nothing", opened, [])
        check("and the board is back", [type(s).__name__ for s in app.screen_stack], ["Screen"])

        await select(app, pilot, "t1")
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        await pilot.press("down"); await pilot.press("enter")
        for _ in range(10): await pilot.pause()
        check("choosing the second opens exactly it", opened, ["https://a.example/x"])
        check("and only it", len(opened), 1)

        await select(app, pilot, "t2")
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        check("two addresses also ask, rather than taking the first",
              type(app.screen_stack[-1]).__name__, "LinkPicker")
        shown = [str(o.prompt) for o in
                 app.screen_stack[-1].query_one(main.OptionList).options]
        check("both are offered", shown, ["https://one.example", "https://two.example"])
        await pilot.press("enter")
        for _ in range(10): await pilot.pause()
        check("the first can still be chosen", opened[-1:], ["https://one.example"])

        await select(app, pilot, "t3")
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        shown = [str(o.prompt) for o in
                 app.screen_stack[-1].query_one(main.OptionList).options]
        check("the title's candidate is offered before the note's",
              shown, ["AAA-9", "https://note.example"])
        await pilot.press("escape")
        for _ in range(6): await pilot.pause()
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("still nothing written", writes, [])

# ------------------------------------------------------------- refusals
async def refused():
    print("what is not offered")
    rows = [task("t1", "GPT-4 and ISO-8601 and ZZZ-9"),
            task("t2", "plain", "mailto:x@example.com"),
            task("t3", "AAA-7 " + f"{BASE}/issue/AAA-7")]
    async with board(rows) as (app, pilot, opened):
        await select(app, pilot, "t1")
        await pilot.press("o"); await pilot.pause()
        check("text shaped like a key is not an issue", status(app), "That task has no link")
        await select(app, pilot, "t2")
        await pilot.press("o"); await pilot.pause()
        check("a refused scheme in a note is not offered",
              status(app), "That task has no link")
        await select(app, pilot, "t3")
        await pilot.press("o"); await pilot.pause()
        check("a key and its own link are one candidate, so no choice is asked",
              [type(s).__name__ for s in app.screen_stack], ["Screen"])
        check("and it opens the issue", opened[-1:], [f"{BASE}/issue/AAA-7"])

    print("with no tracker configured")
    async with board([task("t1", "AAA-1"), task("t2", "https://a.example")],
                     tracker_cfg=None) as (app, pilot, opened):
        await select(app, pilot, "t1")
        await pilot.press("o"); await pilot.pause()
        check("a key is not recognised", status(app), "That task has no link")
        await select(app, pilot, "t2")
        await pilot.press("o"); await pilot.pause()
        check("but an address still opens", opened[-1:], ["https://a.example"])

# ------------------------------------------- events and tracker rows untouched
async def other_rows():
    print("an event and a tracker row are unaffected")
    E = ical.Event(title="a meeting", account="Me", calendar="c",
                   start=dt.datetime.combine(TODAY, dt.time(9, 0)),
                   end=dt.datetime.combine(TODAY, dt.time(10, 0)),
                   all_day=False, location="https://meet.example/r",
                   notes="also https://other.example and AAA-1")
    app = main.TaskApp()
    app.client = StubClient([task("t1", "a task")], reference=NOW)
    app.calendar_config = ical.Config(work="W", personal=("Me",))
    app.tracker_config = CFG
    opened = []
    app.open_url = lambda url: opened.append(url)
    saved = ical.fetch; ical.fetch = lambda c, d: [E]
    try:
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(14): await pilot.pause()
            app.tracker_issues = [tracker.Issue(key="AAA-5", summary="an issue",
                                                project="AAA", state="In progress",
                                                assignee="me", base_url=BASE)]
            app.repaint(); await pilot.pause()
            row = next(i for i, t in enumerate(app.tasks) if app.is_event(t))
            app.query_one(main.DataTable).move_cursor(row=row)
            app._selected_id = app.tasks[row].id
            await pilot.pause()
            await pilot.press("o")
            for _ in range(8): await pilot.pause()
            check("an event opens its own address, with no choice",
                  (opened[-1:], [type(s).__name__ for s in app.screen_stack]),
                  (["https://meet.example/r"], ["Screen"]))
            row = next(i for i, t in enumerate(app.tasks) if app.is_tracker(t))
            app.query_one(main.DataTable).move_cursor(row=row)
            app._selected_id = app.tasks[row].id
            await pilot.pause()
            await pilot.press("o")
            for _ in range(8): await pilot.pause()
            check("a tracker row opens its own page, with no choice",
                  (opened[-1:], [type(s).__name__ for s in app.screen_stack]),
                  ([f"{BASE}/issue/AAA-5"], ["Screen"]))
    finally:
        ical.fetch = saved

async def main_():
    await one()
    await several()
    await refused()
    await other_rows()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
