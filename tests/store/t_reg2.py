"""6.3 / 6.4 / 6.5 -- nothing regressed."""
import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_TESTS)
sys.path.insert(0,_REPO)
import baseline
import sys, asyncio, json, threading
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from harness import StubClient, mk, TZ
from datetime import date, datetime, timedelta
from main import TaskApp
import singularity
from singularity import SingularityClient, Bucket
from textual.widgets import DataTable
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
base=baseline.load(TZ)
api=SingularityClient(); TODAY=datetime.now(TZ).date()

print("6.3 today's real view")
l=api.tasks_for_day()
ids=[t.id for t in l.tasks]
check("same set of tasks as before the change", set(ids)==set(base["today_ids"]),
      f"{len(ids)} vs {len(base['today_ids'])}")
check("past-due count unchanged", l.past_due==base["today_past_due"], str(l.past_due))
check("finished count unchanged",
      sum(1 for t in l.tasks if t.done or t.cancelled)==base["today_done"])
# ascending WITHIN each ordering group: a finished task sinks below an
# unfinished one whatever its time, which is the first ordering key
from collections import defaultdict
_now=datetime.now(TZ)
_g=defaultdict(list)
for t in l.tasks:
    if t.timed: _g[singularity.group_key(t,TZ,_now)[:5]].append(t.local_start(TZ).strftime("%H:%M"))
check("timed tasks ascend within each ordering group",
      all(v==sorted(v) for v in _g.values()), str(dict(_g)))
starts=[t.local_start(TZ).strftime("%H:%M") for t in l.tasks if t.timed]
check("timed tasks in the same sequence as before", starts==base["today_timed_starts"], str(starts))
# the grouping above the manual key is untouched: same partition, same group order
now=datetime.now(TZ)
def groups(tasks): 
    seen=[]; 
    for t in tasks:
        g=singularity.group_key(t,TZ,now,api.green)
        if not seen or seen[-1]!=g: seen.append(g)
    return seen
check("the groups appear in the same sequence as before",
      groups(l.tasks)==groups(sorted(l.tasks,
          key=lambda t: singularity.sort_key(t,TZ,now,green=api.green))),
      "consistent")
# Distinct per underlying task, not per row.  A recurring task shows one
# row per occurrence -- "<id>-20260907" and "<id>-20260908" both land in
# today's view when one is past due -- and both carry the same stored order,
# because there is one task behind them.  Counting rows called that a
# collision.
def _base(tid):
    head, _, tail = tid.rpartition("-")
    return head if (head and tail.isdigit() and len(tail) == 8) else tid
by_task = {_base(t.id): t.schedule_order for t in l.tasks}
vals = list(by_task.values())
check("today's stored orders are all distinct, per task",
      len(set(vals)) == len(vals), f"{len(set(vals))} of {len(vals)}")

print("6.4 the dateless views")
for b in Bucket:
    lb=api.tasks_in_bucket(b)
    bids=[t.id for t in lb.tasks]
    check(f"{b.name.lower()}: ids and order identical to before",
          bids==base[f"{b.name}_ids"],
          f"{sum(1 for i,j in zip(bids,base[f'{b.name}_ids']) if i!=j)} rows differ")
    check(f"{b.name.lower()}: withheld count unchanged", lb.filed_out==base[f"{b.name}_filed_out"])
for d in (TODAY-timedelta(days=1), TODAY+timedelta(days=1)):
    ids=[t.id for t in api.tasks_for_day(d).tasks]
    check(f"day {d}: same set of tasks", set(ids)==set(base[f"day_{d}_ids"]),
          f"{len(ids)} vs {len(base[f'day_{d}_ids'])}")

print("6.5 the previous change's guarantees")
D=date(2099,12,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def patch_stub(stub):
    def sso(tid, order):
        stub._record("set_schedule_order", tid, order)
        stub.store[tid].raw["scheduleOrder"]=order
        return stub.store[tid]
    stub.set_schedule_order=sso; return stub

async def burst():
    tasks=[so(mk(f"T-{i}",chr(97+i)*3,D),(i+1)*1000) for i in range(5)]
    app=TaskApp(D); stub=patch_stub(StubClient(tasks)); app.client=stub
    stub.gate=threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-4")
        table.move_cursor(row=row); await pilot.pause()
        for _ in range(4):                      # walk T-4 to the top, fast
            await pilot.press("K"); await pilot.pause()
        check("a burst of moves is all queued, none dropped",
              sum(len(q) for q in app._pending.values())==4,
              str({k:len(v) for k,v in app._pending.items()}))
        check("the view already shows it at the top",
              [t.id for t in app.tasks][0]=="T-4", str([t.id for t in app.tasks]))
        # a refresh mid-move must not revert it
        app.load()
        for _ in range(60): await pilot.pause()
        check("a refresh arriving mid-move does not revert it",
              [t.id for t in app.tasks][0]=="T-4", str([t.id for t in app.tasks]))
        stub.gate.set()
        for _ in range(200):
            await pilot.pause()
            if not app._pending and not app._draining: break
        check("all four writes reached the API", stub.count("set_schedule_order")==4,
              str(stub.count("set_schedule_order")))
        check("the final sequence is the intended one",
              [t.id for t in app.tasks]==["T-4","T-0","T-1","T-2","T-3"],
              str([t.id for t in app.tasks]))
        vals=[t.schedule_order for t in app.tasks]
        check("no two tasks share a stored order", len(set(vals))==len(vals), str(sorted(vals)))
asyncio.run(burst())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
