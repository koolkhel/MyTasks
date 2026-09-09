"""Group 3 -- which neighbour a move may carry a task past."""
import sys, asyncio
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
from main import TaskApp
import singularity
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D = date(2099,9,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def by(app,tid): return next(t for t in app.tasks if t.id==tid)

async def t_boundaries():
    print("3.1 boundaries are derived from the sort key")
    now = datetime.now(TZ); today = now.date()
    timed = so(mk("T-timed","meeting",today,timed=True), 500)
    timed.raw["start"] = singularity.iso_z(datetime.combine(today, datetime.min.time().replace(hour=9), tzinfo=TZ))
    allday1 = so(mk("T-ad1","alpha",today), 1000)
    allday2 = so(mk("T-ad2","bravo",today), 2000)
    late    = so(mk("T-late","late",today-timedelta(days=3)), 100)
    fin     = so(mk("T-fin","fin",today,checked=1), 50)
    app = TaskApp(today); app.client = StubClient([timed,allday1,allday2,late,fin], reference=now)
    app.tracker_config=None   # the tracker is not the subject here
    async with app.run_test() as pilot:
        await pilot.pause()
        print("   shown:", [t.id for t in app.tasks])
        a1 = by(app,"T-ad1")
        up = app.neighbour_to_pass(a1, -1)
        check("an all-day task offers no neighbour upward past a timed one",
              up is None, f"got {up.id if up else None}")
        down = app.neighbour_to_pass(a1, 1)
        check("two equal all-day tasks do offer each other",
              down is not None and down.id == "T-ad2", f"got {down.id if down else None}")
        check("and the reverse holds",
              app.neighbour_to_pass(by(app,"T-ad2"), -1).id == "T-ad1")
        pd = by(app,"T-late")
        check("a past-due task offers no neighbour downward into today's own",
              app.neighbour_to_pass(pd, 1) is None,
              str(getattr(app.neighbour_to_pass(pd,1),'id',None)))
        check("a past-due task offers none upward either (it is first)",
              app.neighbour_to_pass(pd, -1) is None)
        f = by(app,"T-fin")
        check("a finished task offers no neighbour upward into the unfinished",
              app.neighbour_to_pass(f, -1) is None)
        check("the timed task offers none downward into the all-day run",
              app.neighbour_to_pass(by(app,"T-timed"), 1) is None)
        check("the last task offers no neighbour downward",
              app.neighbour_to_pass(app.tasks[-1], 1) is None)

async def t_ties():
    print("3.2 tasks that already share a stored order")
    tasks = [so(mk("T-a","aaa",D),0), so(mk("T-b","bbb",D),0), so(mk("T-c","ccc",D),0)]
    app = TaskApp(D); app.client = StubClient(tasks)
    async with app.run_test() as pilot:
        await pilot.pause()
        check("three tied tasks fall back to title", [t.id for t in app.tasks]==["T-a","T-b","T-c"],
              str([t.id for t in app.tasks]))
        a = by(app,"T-a")
        check("moving down past a tied neighbour has no room", app.order_for_move(a,1) is None,
              str(app.order_for_move(a,1)))
        run = app.run_around(a)
        check("the run is all three", [t.id for t in run]==["T-a","T-b","T-c"], str([t.id for t in run]))
        # after respacing, room exists and a move is possible
        base = max(t.schedule_order for t in app.tasks) + singularity.ORDER_STEP
        for i,t in enumerate(run):
            t.raw["scheduleOrder"] = base + i*singularity.ORDER_STEP
        app.repaint()
        vals = [t.schedule_order for t in app.tasks]
        check("respacing leaves distinct values", len(set(vals))==len(vals), str(vals))
        a = by(app,"T-a")
        v = app.order_for_move(a,1)
        check("now there is room to move down", v is not None and by(app,"T-b").schedule_order < v, str(v))

async def t_only_one():
    print("3.3 an ordinary move writes exactly one task")
    tasks = [so(mk(f"T-{i}", chr(97+i)*3, D), (i+1)*1000) for i in range(8)]
    app = TaskApp(D); app.client = StubClient(tasks)
    async with app.run_test() as pilot:
        await pilot.pause()
        before = {t.id: t.schedule_order for t in app.tasks}
        check("eight tasks in stored order", [t.id for t in app.tasks]==[f"T-{i}" for i in range(8)],
              str([t.id for t in app.tasks]))
        t3 = by(app,"T-3")
        v = app.order_for_move(t3, 1)
        # the moved task lands past its neighbour, i.e. between T-4 and T-5
        check("a value exists between T-4 and T-5", v is not None and 5000 < v < 6000, str(v))
        # apply it the way the board will: one field on one task
        t3.raw["scheduleOrder"] = v
        app.repaint()
        after = {t.id: t.schedule_order for t in app.tasks}
        changed = [k for k in before if before[k] != after[k]]
        check("exactly one stored order changed", changed == ["T-3"], str(changed))
        check("the other seven are untouched", len(changed)==1 and len(before)==8)
        check("the sequence is the intended one",
              [t.id for t in app.tasks]==["T-0","T-1","T-2","T-4","T-3","T-5","T-6","T-7"],
              str([t.id for t in app.tasks]))
        check("all orders still distinct", len(set(after.values()))==8, str(sorted(after.values())))

for fn in (t_boundaries, t_ties, t_only_one):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
