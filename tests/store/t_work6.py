"""6.1 -- the whole flow against the real API, on a far-future day."""
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
from main import TaskApp, ProjectPicker, Confirm
from singularity import SingularityClient, load_work_project, iso_z
from textual.widgets import DataTable, OptionList
api=SingularityClient(); TZ=api.tz
DAY=date(2099,3,20); P="zz-work-"
WORK=load_work_project()
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
def mk(n,so): return api.create_task(f"{P}{n}", start=iso_z(datetime.combine(DAY,_t.min,tzinfo=TZ)),
                                    useTime=False, scheduleOrder=so)
def fetch(tid):
    try: return api.get_task(tid)
    except Exception: return None

async def run():
    print(f"  cleaned up {cleanup()} leftovers")
    made={n: mk(n,(i+1)*1000) for i,n in enumerate(["a","b","c"])}
    byid={t.id:n for n,t in made.items()}
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
            seq=lambda:[byid[t.id] for t in app.tasks if t.id in byid]
            chk("the day shows the three probes", seq()==["a","b","c"], str(seq()))
            chk("the work project was read from .env", app.work_project==WORK, str(app.work_project))
            chk("and it resolves to a real project", WORK in app.projects,
                str(app.projects.get(WORK)))

            async def select(tid):
                table=app.query_one(DataTable)
                row=next(i for i,t in enumerate(app.tasks) if t.id==tid)
                table.move_cursor(row=row); await pilot.pause()
                assert app.selected.id==tid

            # --- file 'b' under work, through the picker and its confirmation
            await select(made["b"].id)
            await pilot.press("p")
            for _ in range(60):
                await pilot.pause()
                if isinstance(app.screen, ProjectPicker): break
            chk("p opened the picker", isinstance(app.screen, ProjectPicker))
            opts=app.screen.query_one(OptionList)
            idx=next(i for i,o in enumerate(opts._options) if o.id==WORK)
            opts.highlighted=idx; await pilot.pause()
            await pilot.press("enter")
            for _ in range(60):
                await pilot.pause()
                if isinstance(app.screen, Confirm): break
            chk("filing an unfiled task asked first", isinstance(app.screen, Confirm))
            await pilot.press("y")
            await settle()
            got=fetch(made["b"].id)
            chk("the server has it under the work project",
                got is not None and got.project_id==WORK, str(got.project_id if got else "gone"))

            # --- hide work
            await pilot.press("w"); await pilot.pause()
            chk("the work row disappears", "b" not in seq(), str(seq()))
            chk("the other two remain", seq()==["a","c"], str(seq()))
            chk("the hidden count is one", app.hidden_work==1, str(app.hidden_work))
            chk("the daybar says so", "work hidden (1)" in str(app.query_one("#daybar").content),
                str(app.query_one("#daybar").content))
            chk("nothing was written by hiding",
                fetch(made["b"].id).project_id==WORK)

            # --- and back
            await pilot.press("w"); await pilot.pause()
            chk("pressing again brings it back", seq()==["a","b","c"], str(seq()))
            chk("and the daybar stops saying it",
                "work hidden" not in str(app.query_one("#daybar").content),
                str(app.query_one("#daybar").content))

            # --- moving between projects asks nothing
            others=[p for p in app.projects if p!=WORK]
            if others:
                await select(made["b"].id)
                await pilot.press("p")
                for _ in range(60):
                    await pilot.pause()
                    if isinstance(app.screen, ProjectPicker): break
                opts=app.screen.query_one(OptionList)
                idx=next(i for i,o in enumerate(opts._options) if o.id==others[0])
                opts.highlighted=idx; await pilot.pause()
                await pilot.press("enter")
                for _ in range(30): await pilot.pause()
                chk("moving between projects asked nothing",
                    not isinstance(app.screen, Confirm), type(app.screen).__name__)
                await settle()
                chk("the server has it in the other project",
                    fetch(made["b"].id).project_id==others[0],
                    str(fetch(made["b"].id).project_id))
    finally:
        print(f"  cleanup: {cleanup()} removed")
        chk("nothing left behind",
            not [t for t in api.tasks_for_day(DAY).tasks if t.title.startswith(P)])
asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
