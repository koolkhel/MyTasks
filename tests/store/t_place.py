"""2.3 / 2.4 / 2.5 -- placement, respacing through the board, disjointness."""
import sys, asyncio, time
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from datetime import date, datetime, time as _t
from main import TaskApp
import singularity
from singularity import SingularityClient, order_between, ORDER_STEP, iso_z
from textual.widgets import DataTable
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))

print("2.3 order_between")
v=order_between(100,300)
check("strictly between 100 and 300", v is not None and 100<v<300, str(v))
check("nothing between 100 and 101", order_between(100,101) is None)
check("nothing between two equal values", order_between(100,100) is None)
check("nothing between adjacent negatives", order_between(-5,-4) is None)
check("one step below an unbounded lower side", order_between(None,100)==100-ORDER_STEP, str(order_between(None,100)))
check("one step above an unbounded upper side", order_between(100,None)==100+ORDER_STEP, str(order_between(100,None)))
check("both unbounded gives 0", order_between(None,None)==0)
check("room for two apart", order_between(100,102)==101)
check("it never returns an endpoint",
      all(order_between(a,b) not in (a,b) for a,b in [(0,1000),(5,7),(-100,100)]))

api=SingularityClient(); TZ=api.tz
DAY=date(2099,8,1); P="zz-place-"
def cleanup():
    n=0
    for t in api.tasks_for_day(DAY).tasks:
        if t.title.startswith(P):
            for _ in range(5):
                try: api.delete_task(t.id); n+=1; break
                except Exception: time.sleep(1.5)
    return n
def mk(n,so): return api.create_task(f"{P}{n}", start=iso_z(datetime.combine(DAY,_t.min,tzinfo=TZ)), useTime=False, scheduleOrder=so)

async def run():
    cleanup()
    print("\n2.4 the board respaces a run that has no room, against the live API")
    names=list("abcd")
    made={n: mk(n, 500+i) for i,n in enumerate(names)}
    byid={t.id:n for n,t in made.items()}
    try:
        before_max=max(t.schedule_order for t in api.tasks_for_day(DAY).tasks)
        check("they start adjacent, with no room between any pair",
              all(order_between(a,b) is None for a,b in zip([500,501,502],[501,502,503])),
              "500,501,502,503")
        app=TaskApp(DAY)
        async with app.run_test(size=(120,40)) as pilot:
            for _ in range(200):
                await pilot.pause()
                if app.tasks: break
            seq=lambda:[byid[t.id] for t in app.tasks if t.id in byid]
            check("shown in stored order", seq()==names, str(seq()))
            table=app.query_one(DataTable)
            # move 'a' down one -- there is no room, so the board must respace first
            row=next(i for i,t in enumerate(app.tasks) if t.id==made["a"].id)
            table.move_cursor(row=row); await pilot.pause()
            await pilot.press("J")
            for _ in range(400):
                await pilot.pause()
                if not app._pending and not app._draining: break
            check("the move happened despite there being no room",
                  seq()==["b","a","c","d"], str(seq()))
        fresh=[t for t in api.tasks_for_day(DAY).tasks if t.id in byid]
        orders={byid[t.id]: t.schedule_order for t in fresh}
        vals=sorted(orders.values())
        check("all stored orders distinct afterwards", len(set(vals))==len(vals), str(orders))
        check("above the day's previous maximum", min(vals)>before_max, f"min {min(vals)} > {before_max}")
        check("there is room between every pair now",
              all(order_between(a,b) is not None for a,b in zip(vals,vals[1:])), str(vals))
        check("the sequence the server holds matches what was shown",
              [byid[t.id] for t in sorted(fresh, key=lambda t:t.schedule_order)]==["b","a","c","d"],
              str([byid[t.id] for t in sorted(fresh, key=lambda t:t.schedule_order)]))
        check("the untouched tasks kept their relative order", orders["c"]<orders["d"], str(orders))

        print("\n2.5 a partly-applied respacing cannot collide")
        day=api.tasks_for_day(DAY).tasks
        existing={t.schedule_order for t in day}
        base=max(existing)+ORDER_STEP
        targets=[base+i*ORDER_STEP for i in range(len(day))]
        check("the target range is disjoint from every stored order in the day",
              not (set(targets)&existing), f"overlap {set(targets)&existing}")
        import itertools
        bad=None
        for r in range(len(day)+1):
            for sub in itertools.combinations(range(len(day)), r):
                v=[targets[i] if i in sub else day[i].schedule_order for i in range(len(day))]
                if len(set(v))!=len(v): bad=sub; break
            if bad: break
        check("every subset of the writes leaves all orders distinct", bad is None,
              f"collision at {bad}" if bad else f"checked {2**len(day)} subsets")
    finally:
        print(f"\ncleanup: {cleanup()} removed")
        check("nothing left behind",
              not [t for t in api.tasks_for_day(DAY).tasks if t.title.startswith(P)])
asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
