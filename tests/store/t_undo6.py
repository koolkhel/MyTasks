"""6.1 + 6.2 -- undo end to end against the real API."""
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
from singularity import SingularityClient, iso_z, CHECKED
from textual.widgets import DataTable, Input
api=SingularityClient(); TZ=api.tz
DAY=date(2099,5,15); P="zz-undo-"
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
def cleanup():
    n=0
    for t in api.tasks_for_day(DAY).tasks:
        if t.title.startswith(P):
            for _ in range(6):
                try: api.delete_task(t.id); n+=1; break
                except Exception: time.sleep(1.5)
    return n
def mk(n,so):
    last=None
    for _ in range(6):
        try:
            return api.create_task(f"{P}{n}", start=iso_z(datetime.combine(DAY,_t.min,tzinfo=TZ)),
                                   useTime=False, scheduleOrder=so)
        except Exception as e:
            last=e; time.sleep(3)
    raise last
def fetch(tid):
    for _ in range(6):
        try: return api.get_task(tid)
        except Exception: time.sleep(2)
    return None

async def run():
    print(f"  cleaned up {cleanup()} leftovers")
    # 6.1 uses roomy orders; 6.2 needs adjacent ones, so do them separately
    made={n: mk(n,(i+1)*1000) for i,n in enumerate(["a","b","c"])}
    try:
        app=TaskApp(DAY)
        async with app.run_test(size=(120,40)) as pilot:
            async def settle(n=400):
                for _ in range(n):
                    await pilot.pause()
                    if not app._pending and not app._draining: return
            for _ in range(200):
                await pilot.pause()
                if app.tasks: break
            async def select(tid):
                table=app.query_one(DataTable)
                row=next(i for i,t in enumerate(app.tasks) if t.id==tid)
                table.move_cursor(row=row); await pilot.pause()
                assert app.selected.id==tid

            print("6.1 tick, then undo")
            await select(made["a"].id)
            await pilot.press("space"); await settle()
            chk("the server has it complete", fetch(made["a"].id).checked==CHECKED,
                str(fetch(made["a"].id).checked))
            await pilot.press("u"); await settle()
            chk("undo made it open again", fetch(made["a"].id).checked==0,
                str(fetch(made["a"].id).checked))

            print("6.1 rename, then undo")
            await select(made["b"].id)
            await pilot.press("e")
            for _ in range(60):
                await pilot.pause()
                if app.screen.query(Input): break
            inp=app.screen.query_one(Input); inp.value=""; await pilot.pause()
            await pilot.press(*f"{P}renamed"); await pilot.press("enter")
            await settle()
            chk("the server has the new title", fetch(made["b"].id).title==f"{P}renamed",
                fetch(made["b"].id).title)
            await pilot.press("u"); await settle()
            chk("undo restored the old title", fetch(made["b"].id).title==f"{P}b",
                fetch(made["b"].id).title)

            print("6.1 move, then undo")
            orders={n:fetch(t.id).schedule_order for n,t in made.items()}
            await select(made["a"].id)
            await pilot.press("J"); await settle()
            after={n:fetch(t.id).schedule_order for n,t in made.items()}
            chk("the move changed a's order", after["a"]!=orders["a"], f"{orders['a']} -> {after['a']}")
            await pilot.press("u"); await settle()
            back={n:fetch(t.id).schedule_order for n,t in made.items()}
            chk("undo restored every order", back==orders, f"{orders} vs {back}")
    finally:
        print(f"  cleanup: {cleanup()} removed")

async def run_cramped():
    print("6.2 a move that respaces its run is reversed by one press")
    cleanup()
    made={n: mk(n,500+i) for i,n in enumerate(["a","b","c","d"])}
    try:
        before={n:fetch(t.id).schedule_order for n,t in made.items()}
        chk("they start adjacent", sorted(before.values())==[500,501,502,503], str(before))
        app=TaskApp(DAY)
        async with app.run_test(size=(120,40)) as pilot:
            async def settle(n=500):
                for _ in range(n):
                    await pilot.pause()
                    if not app._pending and not app._draining: return
            for _ in range(200):
                await pilot.pause()
                if app.tasks: break
            table=app.query_one(DataTable)
            row=next(i for i,t in enumerate(app.tasks) if t.id==made["a"].id)
            table.move_cursor(row=row); await pilot.pause()
            await pilot.press("J"); await settle()
            mid={n:fetch(t.id).schedule_order for n,t in made.items()}
            chk("the run was respaced, so several tasks changed",
                sum(1 for n in before if before[n]!=mid[n])>=3,
                f"{sum(1 for n in before if before[n]!=mid[n])} changed")
            chk("exactly one undo entry", len(app._undo)==1, str(len(app._undo)))
            await pilot.press("u"); await settle()
            after={n:fetch(t.id).schedule_order for n,t in made.items()}
            chk("one press restored every one of them", after==before, f"{before} vs {after}")
    finally:
        print(f"  cleanup: {cleanup()} removed")
        chk("nothing left behind",
            not [t for t in api.tasks_for_day(DAY).tasks if t.title.startswith(P)])
asyncio.run(run())
asyncio.run(run_cramped())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
