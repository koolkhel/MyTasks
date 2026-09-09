"""6.1 -- the whole flow driven by Russian keys, against the real API.

Far-future day, synthetic titles, cursor placed by task id before every
keypress, everything deleted afterwards.
"""
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
from datetime import date, datetime, time as _t, timedelta
from main import TaskApp, DatePicker, Confirm
from singularity import SingularityClient, iso_z
from textual.widgets import DataTable, Input
api=SingularityClient(); TZ=api.tz
DAY=date(2099,2,1); P="zz-ru-"
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
def cleanup():
    n=0
    for d in (DAY, DAY+timedelta(days=1), datetime.now(TZ).date(), datetime.now(TZ).date()+timedelta(days=1)):
        for t in api.tasks_for_day(d).tasks:
            if t.title.startswith(P):
                for _ in range(5):
                    try: api.delete_task(t.id); n+=1; break
                    except Exception: time.sleep(1.5)
    return n
def fetch(tid):
    try: return api.get_task(tid)
    except Exception: return None

async def run():
    print(f"  cleaned up {cleanup()} leftovers")
    app=TaskApp(DAY)
    made=None
    try:
        async with app.run_test(size=(120,40)) as pilot:
            async def settle(n=400):
                for _ in range(n):
                    await pilot.pause()
                    if not app._pending and not app._draining: return
            for _ in range(200):
                await pilot.pause()
                if "task(s)" in str(app.query_one("#status").content): break

            # --- add, with the Russian add key and a Russian title ---
            await pilot.press("ф")
            for _ in range(60):
                await pilot.pause()
                if app.screen.query(Input): break
            chk("ф opened the add prompt", bool(app.screen.query(Input)))
            for ch in f"{P}Купить молоко":
                await pilot.press(ch)
            await pilot.press("enter")
            await settle()
            fresh=[t for t in api.tasks_for_day(DAY).tasks if t.title==f"{P}Купить молоко"]
            chk("the server has the task with its Russian title", len(fresh)==1, f"{len(fresh)} found")
            if not fresh: return
            made=fresh[0].id
            print(f"  probe id {made[:14]}")

            async def select(tid):
                table=app.query_one(DataTable)
                row=next(i for i,t in enumerate(app.tasks) if t.id==tid)
                table.move_cursor(row=row); await pilot.pause()
                assert app.selected.id==tid, f"cursor on {app.selected.id}"

            # --- rename, with the Russian rename key ---
            await select(made)
            await pilot.press("у")
            for _ in range(60):
                await pilot.pause()
                if app.screen.query(Input): break
            chk("у opened the rename prompt", bool(app.screen.query(Input)))
            inp=app.screen.query_one(Input); inp.value=""
            await pilot.pause()
            for ch in f"{P}Переименовано":
                await pilot.press(ch)
            await pilot.press("enter")
            await settle()
            got=fetch(made)
            chk("the server has the new Russian title",
                got is not None and got.title==f"{P}Переименовано",
                got.title if got else "gone")

            # --- date, through the picker with Russian keys ---
            await select(made)
            await pilot.press("в")
            for _ in range(60):
                await pilot.pause()
                if isinstance(app.screen, DatePicker): break
            chk("в opened the date picker", isinstance(app.screen,DatePicker))
            await pilot.press("ь")                      # RU m -> tomorrow
            await settle()
            got=fetch(made)
            want=datetime.now(TZ).date()+timedelta(days=1)
            chk("ь set it to tomorrow on the server",
                got is not None and got.local_start(TZ).date()==want,
                str(got.local_start(TZ).date()) if got else "gone")

            # --- delete, confirming with the Russian yes key ---
            app.position=want; app.load()
            for _ in range(300):
                await pilot.pause()
                if any(t.id==made for t in app.tasks): break
            chk("the task is on tomorrow's view", any(t.id==made for t in app.tasks))
            await select(made)
            await pilot.press("backspace")
            for _ in range(60):
                await pilot.pause()
                if isinstance(app.screen, Confirm): break
            chk("the confirmation opened", isinstance(app.screen,Confirm))
            await pilot.press("н")                      # RU y -> yes
            await settle()
            chk("н confirmed, and the server 404s the task", fetch(made) is None)
            made=None
    finally:
        print(f"  cleanup: {cleanup()} removed")
        left=[t for d in (DAY, datetime.now(TZ).date()+timedelta(days=1))
              for t in api.tasks_for_day(d).tasks if t.title.startswith(P)]
        chk("nothing left behind", not left, str(len(left)))
asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
