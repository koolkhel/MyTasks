"""Group 4 -- moving from the board."""
import sys, asyncio, threading
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
from datetime import date, datetime, timedelta
from main import TaskApp, KeyBar
from singularity import SingularityError, Bucket
import singularity
from textual.widgets import DataTable
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
async def settle(p,a,n=80):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False
def three(): return [so(mk("T-a","aaa",D),1000), so(mk("T-b","bbb",D),2000), so(mk("T-c","ccc",D),3000)]

# add scheduleOrder support to the stub
def patch_stub(stub):
    def set_schedule_order(tid, order):
        stub._record("set_schedule_order", tid, order)
        stub.store[tid].raw["scheduleOrder"] = order
        return stub.store[tid]
    stub.set_schedule_order = set_schedule_order
    return stub

async def t_move():
    print("4.1 + 4.3  moving is instant and writes one task")
    app = TaskApp(D); stub = patch_stub(StubClient(three())); app.client = stub
    stub.gate = threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one(DataTable)
        check("starts in stored order", ids(app)==["T-a","T-b","T-c"], str(ids(app)))
        before = {t.id: t.schedule_order for t in app.tasks}
        await pilot.press("J")                      # move T-a down
        await pilot.pause()
        check("the rows swapped within a frame", ids(app)==["T-b","T-a","T-c"], str(ids(app)))
        check("the selection stayed on the moved task",
              app.tasks[table.cursor_row].id=="T-a", f"on {app.tasks[table.cursor_row].id}")
        check("a write is in flight", "saving" in status(app), status(app))
        stub.gate.set(); await settle(pilot, app)
        check("exactly one task was written", stub.count("set_schedule_order")==1,
              str(stub.count("set_schedule_order")))
        after = {t.id: t.schedule_order for t in app.tasks}
        changed = [k for k in before if before[k]!=after[k]]
        check("exactly one stored order changed", changed==["T-a"], str(changed))
        check("orders remain distinct", len(set(after.values()))==3, str(sorted(after.values())))
        check("the order persisted in the store",
              stub.store["T-a"].schedule_order == after["T-a"])
        # and back up again
        await pilot.press("K"); await pilot.pause(); await settle(pilot, app)
        check("moving back up restores the sequence", ids(app)==["T-a","T-b","T-c"], str(ids(app)))

async def t_lowercase():
    print("4.2  lowercase still only moves the cursor")
    app = TaskApp(D); stub = patch_stub(StubClient(three())); app.client = stub
    async with app.run_test() as pilot:
        await pilot.pause()
        before = ids(app)
        await pilot.press("j"); await pilot.pause()
        await pilot.press("k"); await pilot.pause()
        check("the sequence is unchanged", ids(app)==before, str(ids(app)))
        check("no write was sent", stub.count("set_schedule_order")==0)
        # a binding lists several keys now, so test membership not identity
        allkeys={k.strip() for b in app.BINDINGS for k in b.key.split(",")}
        check("both keys are bound", {"K","J"} <= allkeys,
              str(sorted(k for k in allkeys if k in ("K","J","Л","О"))))
        bar = app.query_one(KeyBar)
        entries = dict(bar.entries())
        check("the key bar names both", entries.get("K")=="Move up" and entries.get("J")=="Move down",
              str([e for e in bar.entries() if e[0] in ("K","J")]))
        for width in (60, 80, 120):
            rows = KeyBar.pack(bar.entries(), width)
            flat = [k for r in rows for k,_ in r]
            check(f"nothing is dropped at width {width}",
                  len(flat)==len(bar.entries()) and "K" in flat and "J" in flat,
                  f"{len(rows)} rows")

async def t_edges():
    print("4.4  edges report and write nothing")
    now=datetime.now(TZ); today=now.date()
    timed = so(mk("T-timed","meeting",today,timed=True), 500)
    timed.raw["start"]=singularity.iso_z(datetime.combine(today, datetime.min.time().replace(hour=9), tzinfo=TZ))
    a1 = so(mk("T-ad1","alpha",today),1000); a2 = so(mk("T-ad2","bravo",today),2000)
    app=TaskApp(today); stub=patch_stub(StubClient([timed,a1,a2], reference=now)); app.client=stub
    app.tracker_config=None   # not the subject here
    async with app.run_test() as pilot:
        await pilot.pause()
        table=app.query_one(DataTable)
        before=ids(app)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-ad1")
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("K")                       # up, into the timed task
        await pilot.pause()
        check("moving an all-day task up under a timed one reports",
              "cannot move up" in status(app), status(app))
        check("the sequence is unchanged", ids(app)==before, str(ids(app)))
        check("no write was sent", stub.count("set_schedule_order")==0)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-ad2")
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("J")                       # down, off the end
        await pilot.pause()
        check("moving the last task down reports", "cannot move down" in status(app), status(app))
        check("still nothing written", stub.count("set_schedule_order")==0)
        check("the sequence is still unchanged", ids(app)==before, str(ids(app)))

async def t_buckets():
    print("4.5  the dateless views report and write nothing")
    for bucket in (Bucket.INBOX, Bucket.SOMEDAY):
        tasks=[mk("T-p","aaa"), mk("T-q","bbb")]
        for t in tasks: t.raw["deferred"]=bucket.deferred
        app=TaskApp(date.today()); stub=patch_stub(StubClient(tasks)); app.client=stub
        app.tracker_config=None   # not the subject here
        async with app.run_test() as pilot:
            await pilot.pause()
            app.position=bucket; app.load()
            for _ in range(40):
                await pilot.pause()
                if app.tasks: break
            before=ids(app)
            await pilot.press("J"); await pilot.pause()
            check(f"{bucket.name.lower()}: reports that reordering is for days",
                  "calendar days" in status(app), status(app))
            check(f"{bucket.name.lower()}: nothing written", stub.count("set_schedule_order")==0)
            check(f"{bucket.name.lower()}: order unchanged", ids(app)==before)

async def t_fail():
    print("4.6  a refused move is rolled back")
    app=TaskApp(D); stub=patch_stub(StubClient(three())); app.client=stub
    app.tracker_config=None   # not the subject here
    stub.gate=threading.Event(); stub.fail["set_schedule_order"]=SingularityError("nope")
    async with app.run_test() as pilot:
        await pilot.pause()
        before=ids(app); orders={t.id:t.schedule_order for t in app.tasks}
        await pilot.press("J"); await pilot.pause()
        check("shown moved first", ids(app)==["T-b","T-a","T-c"], str(ids(app)))
        stub.gate.set(); await settle(pilot, app)
        check("the sequence returns to what it was", ids(app)==before, str(ids(app)))
        check("no stored order changed",
              {t.id:t.schedule_order for t in app.tasks}==orders,
              str({t.id:t.schedule_order for t in app.tasks}))
        check("the failure is reported", "failed" in status(app) and "nope" in status(app), status(app))

async def t_respace():
    print("4.1  a move with no room respaces first")
    tasks=[so(mk("T-a","aaa",D),100), so(mk("T-b","bbb",D),101), so(mk("T-c","ccc",D),102)]
    app=TaskApp(D); stub=patch_stub(StubClient(tasks)); app.client=stub
    app.tracker_config=None   # not the subject here
    async with app.run_test() as pilot:
        await pilot.pause()
        check("they start with no room between them",
              all(singularity.order_between(a,b) is None
                  for a,b in zip([100,101,102],[101,102])), "")
        await pilot.press("J")
        await settle(pilot, app)
        for _ in range(40):
            await pilot.pause()
            if not app._pending and not app._draining: break
        vals=[t.schedule_order for t in app.tasks]
        check("orders are distinct after respacing", len(set(vals))==3, str(vals))
        check("there is room between every pair now",
              all(singularity.order_between(a,b) is not None for a,b in zip(sorted(vals),sorted(vals)[1:])),
              str(sorted(vals)))
        check("all three were written", stub.count("set_schedule_order")>=3,
              str(stub.count("set_schedule_order")))

for fn in (t_move, t_lowercase, t_edges, t_buckets, t_fail, t_respace):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
