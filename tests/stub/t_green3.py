"""Groups 4 and 5 -- the key and the count."""
import sys, asyncio
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
from datetime import datetime
import main as M, tracker, singularity
from main import TaskApp
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
G = "A-green"; OTHER = "A-other"; WORK = "P-work-0001"
NOW = datetime.now(TZ); TODAY = NOW.date()

def t(name, green=False, tags=None, done=0):
    x = mk(name, name, start=TODAY, checked=done)
    tg = list(tags or [])
    if green: tg.append(G)
    if tg: x.raw["tags"] = tg
    return x

def issue(k):
    return tracker.Issue(key=k, summary="s", project="TASKR", state="In progress",
                         assignee="me", base_url="https://x")

def patch_stub(stub):
    return stub          # the harness stub carries set_tags itself now

async def settle(p, a, n=150):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return
    for _ in range(20): await p.pause()

async def make(tasks, tag=G, title="Зеленая", issues=()):
    stub = patch_stub(StubClient(tasks, reference=NOW)); stub.green = tag
    app = TaskApp(TODAY)
    return app, stub, tag, title, list(issues)

async def run():
    print("4.1 one press marks, a second unmarks")
    app, stub, *_ = await make([t("a"), t("b")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.work_project = WORK; app.projects = {WORK: "Work"}
        app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("marked after one press", stub.store["a"].raw.get("tags") == [G],
            str(stub.store["a"].raw.get("tags")))
        chk("the rail is on its row",
            next(app.row_for(x)[0] for x in app.tasks if x.id == "a") == M.GREEN_MARK)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("unmarked after a second press", stub.store["a"].raw.get("tags") == [],
            str(stub.store["a"].raw.get("tags")))
        chk("the other task was never written",
            not any(c[0] == "set_tags" and c[1] == "b" for c in stub.calls), str(stub.calls))

    print("\n4.1b marking moves the task, and the selection goes with it")
    app, stub, *_ = await make([t(c) for c in "abcd"])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.green_checked = True; app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "d"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("the marked task moved to the top", app.tasks[0].id == "d",
            str([x.id for x in app.tasks]))
        chk("the selection followed the task, not the row", app._selected_id == "d",
            str(app._selected_id))
        await pilot.press("g"); await settle(pilot, app)
        chk("so a second press unmarks the same task",
            stub.store["d"].raw.get("tags") == [], str(stub.store["d"].raw.get("tags")))
        chk("and no other task was written",
            all(not stub.store[i].raw.get("tags") for i in "abc"),
            str({i: stub.store[i].raw.get("tags") for i in "abc"}))

    print("\n6.3 the wait applies only to a removal behind a recent write")
    import time as _t
    # a task already marked, with nothing written this sitting: no wait
    app, stub, *_ = await make([t("a", green=True)])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.green_checked = True; app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        t0 = _t.monotonic(); await pilot.press("g"); await settle(pilot, app)
        took = _t.monotonic() - t0
        chk("unmarking a task marked earlier is sent at once",
            took < M.TAG_SETTLE_SECONDS, f"{took:.1f}s")
        chk("and it did come off", stub.store["a"].raw.get("tags") == [])
    # marking is never held back, however recent the last write
    app, stub, *_ = await make([t("a")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.green_checked = True; app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        app._selected_id = "a"; await pilot.press("g"); await pilot.pause()
        app._selected_id = "a"
        t0 = _t.monotonic(); await pilot.press("g")     # mark again
        await settle(pilot, app)
        chk("a sequence ending in a mark is not delayed by the removal rule",
            stub.store["a"].raw.get("tags") == [G], str(stub.store["a"].raw.get("tags")))
        # behaviour, not source text.  The task is marked here, so take the
        # mark off first -- that one is allowed to read back -- and then
        # measure the mark that follows it.
        app._selected_id = "a"; await pilot.press("g"); await settle(pilot, app)
        chk("the removal did read back to check it took",
            any(c[0] == "task_tags" for c in stub.calls), str(stub.calls[-3:]))
        reads = len([c for c in stub.calls if c[0] == "task_tags"])
        t0 = _t.monotonic()
        app._selected_id = "a"; await pilot.press("g"); await settle(pilot, app)
        chk("marking is not delayed even straight after a removal",
            _t.monotonic() - t0 < M.TAG_SETTLE_SECONDS, f"{_t.monotonic() - t0:.1f}s")
        chk("and a mark is not read back",
            len([c for c in stub.calls if c[0] == "task_tags"]) == reads,
            str([c for c in stub.calls if c[0] == "task_tags"]))
        chk("the mark took", stub.store["a"].raw.get("tags") == [G],
            str(stub.store["a"].raw.get("tags")))

    print("\n4.2 other tags survive the toggle")
    app, stub, *_ = await make([t("a", tags=[OTHER])])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("the unrelated tag is still there and green was added",
            set(stub.store["a"].raw["tags"]) == {OTHER, G}, str(stub.store["a"].raw["tags"]))
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("and survives the unmark", stub.store["a"].raw["tags"] == [OTHER],
            str(stub.store["a"].raw["tags"]))

    print("\n4.3 the write is optimistic")
    import threading
    app, stub, *_ = await make([t("a")])
    stub.gate = threading.Event()
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load()
        for _ in range(60): await pilot.pause()
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        before = len([c for c in stub.calls if c[0] == "tasks_at"])
        await pilot.press("g")
        for _ in range(30): await pilot.pause()
        chk("the rail shows before the API answers",
            next(app.row_for(x)[0] for x in app.tasks if x.id == "a") == M.GREEN_MARK)
        chk("the view was not refetched",
            len([c for c in stub.calls if c[0] == "tasks_at"]) == before)
        stub.gate.set(); await settle(pilot, app)

    print("\n4.4 undoable, and not confirmed")
    app, stub, *_ = await make([t("a")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("g"); await settle(pilot, app)
        chk("nothing was confirmed", not app.screen_stack[1:], str(app.screen_stack))
        chk("marked", stub.store["a"].raw.get("tags") == [G])
        await pilot.press("u"); await settle(pilot, app)
        chk("undo took the mark off", stub.store["a"].raw.get("tags") == [],
            str(stub.store["a"].raw.get("tags")))
        chk("and said what it undid", "ark" in str(app.query_one("#status").content),
            str(app.query_one("#status").content))

    print("\n4.5 a tracker row is refused")
    app, stub, *_ = await make([t("a")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.work_project = WORK; app.projects = {WORK: "W"}
        app.tracker_config = tracker.Config("https://x", "t", "me", ("TASKR",), ("In progress",))
        app.load_tracker = lambda: (setattr(app, "tracker_issues", [issue("TASKR-1")]),
                                    setattr(app, "tracker_error", None), app.repaint())
        app.load(); await settle(pilot, app)
        app._selected_id = "yt:TASKR-1"; app.repaint(); await pilot.pause()
        n = len(stub.calls)
        await pilot.press("g"); await settle(pilot, app)
        chk("nothing was written", len(stub.calls) == n, str(stub.calls[n:]))
        chk("and the board said why", "tracker" in str(app.query_one("#status").content).lower(),
            str(app.query_one("#status").content))

    print("\n4.6 no tag configured")
    app, stub, *_ = await make([t("a")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = None; app.green_title = None
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        n = len(stub.calls)
        await pilot.press("g"); await settle(pilot, app)
        chk("nothing was written", len(stub.calls) == n)
        chk("the board said so", "GREEN_TAG" in str(app.query_one("#status").content),
            str(app.query_one("#status").content))

    print("\n4.7 the key answers a Russian layout")
    app, stub, *_ = await make([t("a")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        app._selected_id = "a"; app.repaint(); await pilot.pause()
        await pilot.press("п"); await settle(pilot, app)
        chk("п marks too", stub.store["a"].raw.get("tags") == [G],
            str(stub.store["a"].raw.get("tags")))

    print("\n5.1/5.2 the count")
    app, stub, *_ = await make([t("a", green=True), t("b", green=True), t("c"), t("d", done=1)])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        st = str(app.query_one("#status").content)
        chk("green is reported", "2 green" in st, st)
        chk("beside the other counts, not instead", "4 task(s)" in st and "1 done" in st, st)
    app, stub, *_ = await make([t("a"), t("b")])
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G; app.green_title = "Зеленая"
        app.projects = {}; app.tracker_config = None
        app.load(); await settle(pilot, app)
        st = str(app.query_one("#status").content)
        chk("nothing marked means no count", "green" not in st, st)

asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
