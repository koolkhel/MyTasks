"""The remaining checks: undo, the slow fetch, and every action refusing."""
import sys, asyncio, time, threading
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_TESTS)
sys.path.insert(0,_REPO)
from harness import StubClient, mk, TZ
from datetime import datetime, timedelta
import main as M, tracker
from main import TaskApp, ProjectPicker, Confirm
from textual.widgets import DataTable, Input, OptionList
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
WORK="P-work-0001"; TODAY=datetime.now(TZ).date()
def so(t,v): t.raw["scheduleOrder"]=v; return t
def issue(k): return tracker.Issue(k,"summary","TASKR","In progress","me","https://tracker.example")
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
def prep(app, stub, issues=()):
    app.client=stub; app.work_project=WORK; app.projects={WORK:"Work"}
    app.tracker_config=tracker.Config("https://tracker.example","t","me",("TASKR",),("In progress",))
    wanted=list(issues)
    def fake(): app.tracker_issues=list(wanted); app.tracker_error=None; app.repaint()
    app.load_tracker=fake; app.tracker_issues=list(issues)
    return app
async def settle(p,a,n=150):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False
def tasks(): return [so(mk("T-a","aaa",TODAY),1000), so(mk("T-b","bbb",TODAY),2000)]

async def t_all_actions():
    print("3.2 every writing action refuses, including the modal ones")
    stub=StubClient(tasks()); app=prep(TaskApp(TODAY), stub, [issue("TASKR-1")])
    async with app.run_test(size=(120,40)) as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if app.is_tracker(t))
        table.move_cursor(row=row); await pilot.pause()
        n0=len([c for c,_ in stub.calls if c not in ("tasks_at","project_names")])
        # rename opens a prompt first, so drive it through
        await pilot.press("e")
        for _ in range(30): await pilot.pause()
        if app.screen.query(Input):
            inp=app.screen.query_one(Input); inp.value=""
            await pilot.press(*"zzz"); await pilot.press("enter")
            await pilot.pause()
        chk("renaming refuses", "not editable here" in status(app), status(app))
        # date
        await pilot.press("d")
        for _ in range(30): await pilot.pause()
        if isinstance(app.screen, M.DatePicker):
            await pilot.press("t")
            for _ in range(30): await pilot.pause()
        chk("dating refuses", "not editable here" in status(app), status(app))
        # project
        await pilot.press("p")
        for _ in range(30): await pilot.pause()
        if isinstance(app.screen, ProjectPicker):
            opts=app.screen.query_one(OptionList); opts.highlighted=0
            await pilot.pause(); await pilot.press("enter")
            for _ in range(30): await pilot.pause()
            if isinstance(app.screen, Confirm):
                await pilot.press("y"); await pilot.pause()
        chk("filing refuses", "not editable here" in status(app), status(app))
        await settle(pilot, app)
        writes=len([c for c,_ in stub.calls if c not in ("tasks_at","project_names")])-n0
        chk("no write of any kind was sent", writes==0, str(writes))
        chk("3.4 undo has nothing to reverse", app._undo==[], str(len(app._undo)))
        await pilot.press("u"); await pilot.pause()
        chk("and pressing undo says so", "Nothing left to undo" in status(app), status(app))
        chk("the issue is unchanged and still shown",
            any(app.is_tracker(t) for t in app.tasks))

async def t_slow():
    print("5.1 the day does not wait for the tracker")
    stub=StubClient(tasks())
    app=TaskApp(TODAY); app.client=stub; app.work_project=WORK; app.projects={WORK:"Work"}
    app.tracker_config=tracker.Config("https://tracker.example","t","me",("TASKR",),("In progress",))
    gate=threading.Event()
    slow_started=threading.Event()
    class SlowSession:
        def get(self,*a,**k):
            slow_started.set(); gate.wait(10)
            class R:
                status_code=200
                def json(self): return []
            return R()
    real_fetch=tracker.fetch
    tracker.fetch=lambda cfg, session=None: real_fetch(cfg, session=SlowSession())
    try:
        async with app.run_test() as pilot:
            for _ in range(200):
                await pilot.pause()
                if app.tasks: break
            chk("the day's tasks are on screen", len(app.tasks)==2, str(ids(app)))
            chk("while the tracker is still being fetched", slow_started.is_set())
            chk("and nothing claims the day failed", "failed" not in status(app), status(app))
            gate.set()
            for _ in range(200):
                await pilot.pause()
                if app.tracker_error is None and not app.tracker_issues: break
    finally:
        tracker.fetch=real_fetch
        gate.set()

async def t_failure_isolated():
    print("5.2 a tracker failure is not a failure to load the day")
    stub=StubClient(tasks())
    app=TaskApp(TODAY); app.client=stub; app.work_project=WORK; app.projects={WORK:"Work"}
    app.tracker_config=tracker.Config("https://tracker.invalid","t","me",("TASKR",),("In progress",))
    async with app.run_test() as pilot:
        for _ in range(400):
            await pilot.pause()
            if app.tracker_error: break
        chk("the day loaded normally", len(app.tasks)==2, str(ids(app)))
        chk("the tracker reported its own failure", app.tracker_error is not None)
        chk("the message names the tracker",
            "tracker" in status(app).lower(), status(app))
        chk("and not the day", "task(s)" not in status(app) or "could not reach" in status(app))
        # 5.6 -- actions still work with the tracker down
        await pilot.press("space"); await settle(pilot, app)
        chk("5.6 ticking still works with the tracker down", stub.store["T-a"].done)
        await pilot.press("u"); await settle(pilot, app)
        chk("5.6 undo still works too", not stub.store["T-a"].done)

for fn in (t_all_actions, t_slow, t_failure_isolated):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
