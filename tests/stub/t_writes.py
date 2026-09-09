import sys, asyncio, threading
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import StubClient, mk, TZ
from datetime import date, datetime, timedelta
import main as M
from main import TaskApp
from singularity import SingularityError, ApiError, Bucket, CHECKED
from textual.widgets import DataTable

DAY = date(2099, 3, 1)
ok = []
def check(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

def rows(app):   return [t.id for t in app.tasks]
def status(app): return str(app.query_one("#status").content)

async def settle(pilot, app, tries=60):
    """Wait until nothing is pending."""
    for _ in range(tries):
        await pilot.pause()
        if not app._pending and not app._draining:
            return True
    return False

def three(day=DAY):
    return [mk("T-a", "alpha", day), mk("T-b", "bravo", day), mk("T-c", "charlie", day)]

# ---------------------------------------------------------------- 3.1 / 4.2
async def t_tick():
    print("3.1 + 4.2  ticking: instant, reordered, cursor follows the task")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()          # writes block until released
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        check("three rows, cursor on the first", rows(app) == ["T-a","T-b","T-c"] and table.cursor_row == 0, str(rows(app)))
        reads_before = stub.count("tasks_at")
        await pilot.press("space")
        await pilot.pause()
        # the write is still blocked in the stub
        check("row shows finished before the API answered", app.tasks[-1].done and app.tasks[-1].id == "T-a", str(rows(app)))
        check("it moved to the finished group", rows(app) == ["T-b","T-c","T-a"], str(rows(app)))
        check("selection advanced to the next unfinished task", app.tasks[table.cursor_row].id == "T-b", f"on={app.tasks[table.cursor_row].id}")
        check("and not to a row number", table.cursor_row == 0 and app.tasks[0].id == "T-b", f"row={table.cursor_row}")
        check("done count rose at once", "1 done" in status(app), status(app))
        check("and it says a write is in flight", "1 saving" in status(app), status(app))
        stub.gate.set()
        await settle(pilot, app)
        check("4.3 no refetch after a successful write", stub.count("tasks_at") == reads_before, f"{reads_before} -> {stub.count('tasks_at')}")
        check("the tick stands after confirmation", app.tasks[-1].id == "T-a" and app.tasks[-1].done, str(rows(app)))
        check("nothing left saving", "saving" not in status(app), status(app))

# ---------------------------------------------------------------- 4.1 burst
async def t_burst():
    print("4.1  a burst of ticks: none dropped, each on the visible task")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        acted = []
        for _ in range(3):
            acted.append(app.tasks[table.cursor_row].id)   # what the person sees selected
            await pilot.press("space")
            await pilot.pause()
        check("three writes queued, none dropped", sum(len(q) for q in app._pending.values()) == 3, str({k: len(v) for k,v in app._pending.items()}))
        check("each keypress hit a different task", len(set(acted)) == 3, str(acted))
        stub.gate.set()
        await settle(pilot, app)
        sent = sorted(a[0] for c, a in stub.calls if c == "set_done")
        check("all three reached the API", sent == ["T-a","T-b","T-c"], str(sent))
        check("all three are done", all(t.done for t in app.tasks), str([(t.id,t.done) for t in app.tasks]))

# ------------------------------------------------------- 4.4 order on one task
async def t_order():
    print("4.4  rename then cancel on one task keep their order")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        def by_id(tid): return next(t for t in app.tasks if t.id == tid)
        task = by_id("T-a")
        client = app.client
        app.submit_write("Renaming", task, lambda tid: client.update_task(tid, title="renamed"), {"title": "renamed"})
        await pilot.pause()
        check("rename is visible before the API answered", by_id("T-a").title == "renamed", by_id("T-a").title)
        after = by_id("T-a")
        app.submit_write("Cancelling", after, lambda tid: client.cancel_task(tid), {"checked": 2})
        await pilot.pause()
        check("cancel is visible too", any(t.id=="T-a" and t.cancelled for t in app.tasks), str([(t.id,t.checked) for t in app.tasks]))
        check("both queued on the one task", len(app._pending.get("T-a", ())) == 2)
        stub.gate.set()
        await settle(pilot, app)
        seq = [c for c, a in stub.calls if c in ("update_task","cancel_task")]
        check("rename reached the API before the cancel", seq == ["update_task","cancel_task"], str(seq))

# --------------------------------------------------- 4.5 membership by the view
async def t_membership():
    print("4.5  the view decides whether a moved task still belongs")
    now = datetime.now(TZ); today = now.date()
    late = mk("T-late", "late one", today - timedelta(days=3))
    here = mk("T-today", "todays", today)
    app = TaskApp(today); stub = StubClient([late, here], reference=now); app.client = stub
    app.tracker_config=None   # the tracker is not the subject here
    async with app.run_test() as pilot:
        await pilot.pause()
        check("today shows both", set(rows(app)) == {"T-late","T-today"}, str(rows(app)))
        client = app.client
        # (a) reschedule today's task to today -> stays
        app._selected_id = "T-today"
        t = [x for x in app.tasks if x.id == "T-today"][0]
        app.submit_write("Moving", t, lambda tid: client.set_schedule(tid, today),
                         {"start": M.singularity.iso_z(datetime.combine(today, M.time.min, tzinfo=TZ)), "useTime": False, "deferred": False})
        await pilot.pause()
        check("today -> today keeps the row", "T-today" in rows(app), str(rows(app)))
        await settle(pilot, app)
        # (b) a past-due task moved further into the past stays in today
        t = [x for x in app.tasks if x.id == "T-late"][0]
        further = today - timedelta(days=10)
        app.submit_write("Moving", t, lambda tid: client.set_schedule(tid, further),
                         {"start": M.singularity.iso_z(datetime.combine(further, M.time.min, tzinfo=TZ)), "useTime": False, "deferred": False})
        await pilot.pause()
        check("past-due moved further back stays in today", "T-late" in rows(app), str(rows(app)))
        await settle(pilot, app)
        # (c) reschedule to another day -> leaves
        t = [x for x in app.tasks if x.id == "T-today"][0]
        other = today + timedelta(days=5)
        app._selected_id = "T-today"
        app.submit_write("Moving", t, lambda tid: client.set_schedule(tid, other),
                         {"start": M.singularity.iso_z(datetime.combine(other, M.time.min, tzinfo=TZ)), "useTime": False, "deferred": False})
        await pilot.pause()
        check("moved to another day, the row leaves at once", "T-today" not in rows(app), str(rows(app)))
        check("counts follow", f"{len(app.tasks)} task(s)" in status(app), status(app))
        check("3.1 selection moved to a neighbour", app._selected_id in rows(app), str(app._selected_id))
        await settle(pilot, app)

# --------------------------------------------------------- 4.5 delete + 3.2
async def t_delete_and_empty():
    print("4.5 + 3.2  deleting the only task empties the view")
    app = TaskApp(DAY); stub = StubClient([mk("T-only", "only one", DAY)]); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        t = app.tasks[0]; client = app.client
        app.submit_write("Deleting", t, lambda tid: client.delete_task(tid), removes=True)
        await pilot.pause()
        check("the row goes at once", rows(app) == [], str(rows(app)))
        check("nothing is selected", app._selected_id is None and app.selected is None)
        check("the view reports itself empty", "0 task(s)" in status(app), status(app))
        stub.gate.set(); await settle(pilot, app)
        check("still empty after confirmation", rows(app) == [] and app._base == [], str(rows(app)))

# --------------------------------------------------------------- 4.6
async def t_dft():
    print("4.6  done for today: an accepted 422 undoes nothing")
    now = datetime.now(TZ); today = now.date(); tomorrow = today + timedelta(days=1)
    app = TaskApp(today)
    app.tracker_config=None   # the tracker is not the subject here
    stub = StubClient([mk("T-x", "worked on", today - timedelta(days=2))], reference=now)
    app.client = stub
    # the record is refused for a task not dated today -- expected, absorbed
    stub.fail["complete_today"] = ApiError(422, "not dated today")
    async with app.run_test() as pilot:
        await pilot.pause()
        check("it starts past due", app.past_due == 1, f"past_due={app.past_due}")
        await pilot.press("full_stop")
        await pilot.pause()
        check("it leaves today at once", "T-x" not in rows(app), str(rows(app)))
        settled = await settle(pilot, app)
        check("the queue drained", settled, str(app._pending))
        check("no failure was reported", "failed" not in status(app), status(app))
        moved = stub.store["T-x"].local_start(TZ).date()
        check("the task is scheduled for tomorrow", moved == tomorrow, str(moved))
        check("and is still unfinished", not stub.store["T-x"].done)

# --------------------------------------------------------------- 5.1
async def t_fail():
    print("5.1  a refused write is undone and reported")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    stub.fail["set_done"] = SingularityError("server said no")
    async with app.run_test() as pilot:
        await pilot.pause()
        before = rows(app)
        await pilot.press("space")
        await pilot.pause()
        check("shown as ticked first", app.tasks[-1].id == "T-a" and app.tasks[-1].done, str(rows(app)))
        stub.gate.set()
        await settle(pilot, app)
        check("the row is back as it was", rows(app) == before, f"{before} -> {rows(app)}")
        check("nothing is done", not any(t.done for t in app.tasks))
        check("the refusal is reported", "failed" in status(app) and "server said no" in status(app), status(app))
        check("the status shows as an error", app.query_one("#status").has_class("error"))

# --------------------------------------------------------------- 5.2
async def t_one_of_three():
    print("5.2  one failure among three leaves the others standing")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    stub.fail_ids[("set_done", "T-b")] = SingularityError("only bravo refused")
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        for _ in range(3):
            await pilot.press("space"); await pilot.pause()
        check("three in flight", sum(len(q) for q in app._pending.values()) == 3)
        stub.gate.set(); await settle(pilot, app)
        done = {t.id for t in app.tasks if t.done}
        check("the other two stand", done == {"T-a","T-c"}, str(done))
        check("the refused one is back to unfinished", "T-b" in {t.id for t in app.tasks if not t.done}, str(done))
        check("the failure is reported", "only bravo refused" in status(app), status(app))

# --------------------------------------------------------------- 6.1 / 6.2
async def t_refresh():
    print("6.1 + 6.2  a refresh does not revert a write in flight")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space")           # tick T-a, write blocked
        await pilot.pause()
        check("shown ticked", app.tasks[-1].id == "T-a" and app.tasks[-1].done)
        # the stub's store still says unfinished; a refresh fetches that
        check("the server's copy is still unfinished", not stub.store["T-a"].done)
        app.load()                            # same code path as pressing r
        for _ in range(40):
            await pilot.pause()
            if stub.count("tasks_at") >= 2: break
        await pilot.pause()
        check("the refresh happened", stub.count("tasks_at") >= 2, str(stub.count("tasks_at")))
        check("the tick survives the refresh", any(t.id=="T-a" and t.done for t in app.tasks), str([(t.id,t.done) for t in app.tasks]))
        stub.gate.set(); await settle(pilot, app)
        check("and stands after confirmation", any(t.id=="T-a" and t.done for t in app.tasks))
        # 6.2 -- with nothing pending, a fetch replaces the view wholesale
        stub.store["T-c"].raw["title"] = "charlie renamed elsewhere"
        stub.store.pop("T-b")
        app.load()
        for _ in range(40):
            await pilot.pause()
            if "T-b" not in rows(app): break
        check("a fetch with nothing pending shows exactly what came back",
              "T-b" not in rows(app) and any(t.title == "charlie renamed elsewhere" for t in app.tasks),
              str([(t.id,t.title) for t in app.tasks]))

async def t_cursor_cases():
    print("3.1  unticking stays put; ticking the last one lands somewhere real")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        await pilot.press("space")                       # tick T-a
        await pilot.pause(); stub.gate.set(); await settle(pilot, app)
        row = next(i for i, t in enumerate(app.tasks) if t.id == "T-a")
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("space")                       # untick T-a
        await pilot.pause()
        check("unticking keeps the task selected", app.tasks[table.cursor_row].id == "T-a", f"on={app.tasks[table.cursor_row].id}")
        await settle(pilot, app)
        # tick everything; the last tick must still leave a real selection
        for _ in range(3):
            await pilot.press("space"); await settle(pilot, app)
        check("all finished", all(t.done for t in app.tasks), str([(t.id,t.done) for t in app.tasks]))
        check("selection is still on a shown task", app._selected_id in [t.id for t in app.tasks], str(app._selected_id))
        check("and the cursor is in range", 0 <= table.cursor_row < len(app.tasks), f"row={table.cursor_row}")

async def t_rename_keeps():
    print("3.1  a write other than ticking keeps the task selected")
    app = TaskApp(DAY); stub = StubClient(three()); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        client = app.client
        t = next(x for x in app.tasks if x.id == "T-a")
        app.submit_write("Renaming", t, lambda tid: client.update_task(tid, title="zulu"), {"title": "zulu"})
        await pilot.pause()
        check("rename re-sorted the list", [x.id for x in app.tasks] == ["T-b","T-c","T-a"], str([x.id for x in app.tasks]))
        check("selection stayed on the renamed task", app.tasks[table.cursor_row].id == "T-a", f"on={app.tasks[table.cursor_row].id}")
        stub.gate.set(); await settle(pilot, app)

for fn in (t_tick, t_cursor_cases, t_rename_keeps, t_burst, t_order, t_membership, t_delete_and_empty, t_dft, t_fail, t_one_of_three, t_refresh):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
