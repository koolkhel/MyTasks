"""The tracker block below the day's unfinished work.

Every task and issue here is invented; no tracker is contacted.
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
import main, tracker, ical

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def timed(tid, title, hh, checked=0):
    t = mk(tid, title, TODAY, checked=checked, timed=True)
    t.raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(hh, 0), tzinfo=TZ))
    return t

def untimed(tid, title, day=None, checked=0):
    return mk(tid, title, day or TODAY, checked=checked)

def issue(key, state="In progress"):
    return tracker.Issue(key=key, summary=f"summary of {key}", project="P",
                         state=state, assignee="me", base_url="https://tr.example")

from contextlib import asynccontextmanager

@asynccontextmanager
async def board(tasks, issues):
    """A live board, kept open for the caller -- reading an app after
    run_test has exited gives nothing, which is the whole reason for this."""
    app = main.TaskApp()
    app.client = StubClient(tasks, reference=NOW)
    app.calendar_config = None
    app.tracker_config = None          # nothing fetches over us
    app.work_project = "P-work"
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        app.tracker_issues = list(issues)
        app.repaint()
        await pilot.pause()
        yield app, pilot

def shown(app):
    return [("ISSUE" if app.is_tracker(t) else "task", t.raw.get("title"))
            for t in app.tasks]

def kinds(seq): return [k for k, _ in seq]

async def select(app, pilot, pred):
    row = next(i for i, t in enumerate(app.tasks) if pred(t))
    app.query_one(main.DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()

# ------------------------------------------------------ where the block lands
async def placement():
    print("the block sits after the unfinished work and before the finished")
    tasks = [untimed("p1", "past due", TODAY - dt.timedelta(days=2)),
             timed("t1", "at 08", 8),
             untimed("u1", "untimed A"), untimed("u2", "untimed B"),
             timed("d1", "done at 07", 7, checked=CHECKED),
             untimed("c1", "cancelled", checked=CANCELLED)]
    async with board(tasks, [issue("AB-1"), issue("AB-2")]) as (app, pilot):
        seq = shown(app)
    for line in seq: print("     ", line)
    first_issue = kinds(seq).index("ISSUE")
    last_issue = len(kinds(seq)) - 1 - kinds(seq)[::-1].index("ISSUE")
    unfinished = [i for i, (k, t) in enumerate(seq)
                  if k == "task" and t not in ("done at 07", "cancelled")]
    finished = [i for i, (k, t) in enumerate(seq)
                if k == "task" and t in ("done at 07", "cancelled")]
    check("every unfinished task is above the block", max(unfinished) < first_issue, True)
    check("every finished task is below it", min(finished) > last_issue, True)
    check("the block is contiguous", last_issue - first_issue + 1, 2)
    check("no unfinished task sits between the block and the untimed run",
          seq[first_issue - 1], ("task", "untimed B"))

async def edges():
    print("a day with nothing finished, and a day with everything finished")
    async with board([timed("t1", "at 08", 8), untimed("u1", "untimed")],
                     [issue("AB-1"), issue("AB-2")]) as (app, pilot):
        seq = shown(app)
    check("with nothing finished, the block ends the list",
          kinds(seq), ["task", "task", "ISSUE", "ISSUE"])
    async with board([timed("d1", "done at 08", 8, checked=CHECKED),
                      untimed("c1", "cancelled", checked=CANCELLED)],
                     [issue("AB-1"), issue("AB-2")]) as (app, pilot):
        seq = shown(app)
    check("with everything finished, the block leads them",
          kinds(seq), ["ISSUE", "ISSUE", "task", "task"])
    async with board([timed("t1", "at 08", 8)], []) as (app, pilot):
        seq = shown(app)
    check("with no issues at all, nothing is inserted", kinds(seq), ["task"])
    async with board([], [issue("AB-1")]) as (app, pilot):
        seq = shown(app)
    check("with no tasks at all, the block is the list", kinds(seq), ["ISSUE"])

# -------------------------------------------------- what must not change
async def unchanged():
    print("the block's own sequence, wherever it sits")
    issues = [issue("AB-2", "In progress"), issue("AB-1", "In progress"),
              issue("CD-9", "In review")]
    async with board([untimed("u1", "a task"),
                      untimed("d1", "done", checked=CHECKED)], issues) as (app, pilot):
        seq = shown(app)
    check("the sequence given is the sequence shown",
          [t.split(" \u2014 ")[0] for k, t in seq if k == "ISSUE"],
          ["AB-2", "AB-1", "CD-9"])

    print("ticking a task moves it past the block")
    tasks = [untimed("u1", "will be ticked"), untimed("u2", "stays")]
    async with board(tasks, [issue("AB-1"), issue("AB-2")]) as (app, pilot):
        check("before: both tasks above the block",
              kinds(shown(app)), ["task", "task", "ISSUE", "ISSUE"])
        await select(app, pilot, lambda t: t.raw.get("title") == "will be ticked")
        await pilot.press("space")
        for _ in range(20): await pilot.pause()
        after = shown(app)
    for line in after: print("     ", line)
    check("the ticked task passes below the block",
          kinds(after), ["task", "ISSUE", "ISSUE", "task"])
    check("the ticked one is last", after[-1][1], "will be ticked")
    check("and the block keeps its sequence",
          [t.split(" \u2014 ")[0] for k, t in after if k == "ISSUE"], ["AB-1", "AB-2"])

    print("counts, the work filter, and the day's own order")
    tasks = [untimed("w1", "work task"), untimed("o1", "own task"),
             untimed("d1", "done", checked=CHECKED)]
    tasks[0].raw["projectId"] = "P-work"
    async with board(tasks, [issue("AB-1")]) as (app, pilot):
        status = str(app.query_one("#status").render())
        check("the tracked count is still reported", "1 tracked" in status, True)
        check("the day's own tasks are in the order they would be alone",
              [t for k, t in shown(app) if k == "task"], ["own task", "work task", "done"])
        await pilot.press("w")
        for _ in range(10): await pilot.pause()
        hidden = str(app.query_one("#status").render())
        check("hiding work hides the issue and the work task",
              ("1 tracked" in hidden, "2 work hidden" in hidden), (False, True))
        check("what is left is the own task and the done one",
              [t.raw.get("title") for t in app.tasks], ["own task", "done"])
        # The invariant, not only the case: with the mode on, nothing on
        # screen counts as work.  It is what catches a source appended past
        # the work filter -- which happened to the mail rows -- for whichever
        # sources a board happens to hold.  Not "shown plus hidden is what
        # there was": a source that escapes the filter adds nothing to the
        # hidden count either, so that sum balances while the rows are still
        # on screen.
        check("nothing on screen counts as work",
              [t.raw.get("title") for t in app.tasks if app.is_work(t)], [])
        check("and shown plus hidden is what there was",
              len(app.tasks) + app.hidden_work, 4)
        await pilot.press("w")
        for _ in range(10): await pilot.pause()
        check("pressing again brings them back", len(app.tasks), 4)

    print("a tracker row still refuses what it always refused")
    async with board([untimed("u1", "a task")], [issue("AB-1")]) as (app, pilot):
        opened = []
        app.open_url = lambda url: opened.append(url)
        await select(app, pilot, app.is_tracker)
        for key in ["space", "x", "d", "e", "n", "J", "K", "backspace"]:
            await pilot.press(key); await pilot.pause()
            check(f"{key} opens no dialog",
                  [type(s).__name__ for s in app.screen_stack], ["Screen"])
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written", writes, [])
        await select(app, pilot, app.is_tracker)
        await pilot.press("o"); await pilot.pause()
        check("and o still opens the issue", opened, ["https://tr.example/issue/AB-1"])

async def main_():
    await placement()
    await edges()
    await unchanged()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
