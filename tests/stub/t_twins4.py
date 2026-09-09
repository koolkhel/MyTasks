"""Group 4 -- typing is unaffected, and the reported flow works."""
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
from harness import StubClient, mk
from datetime import date
import main as M
from main import TaskApp, DatePicker
from textual.widgets import Input
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def one(): return [so(mk("T-a","aaa",D),1000)]

# a synthetic Russian title made only of characters the board binds to actions
TITLE = "фувщчйелдышкрою"     # add rename date link cancel quit today next... all bound

async def settle(p,a,n=80):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

async def t_add_typing():
    print("4.1 typing a Russian title into the add prompt")
    app=TaskApp(D); stub=StubClient(one()); app.client=stub
    async with app.run_test(size=(120,40)) as pilot:
        await pilot.pause()
        n0=len(app.tasks)
        await pilot.press("ф")                       # RU a -> add
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        chk("the prompt opened on ф", bool(app.screen.query(Input)))
        for ch in TITLE:
            await pilot.press(ch)
        await pilot.pause()
        inp=app.screen.query_one(Input)
        chk("every character reached the prompt", inp.value==TITLE, f"{inp.value!r}")
        chk("no action ran while typing", app.position==D and len(app.tasks)==n0,
            f"pos={app.position} tasks={len(app.tasks)}")
        await pilot.press("escape"); await pilot.pause()

async def t_rename_typing():
    print("4.2 typing into the rename prompt, and the picker's date field")
    app=TaskApp(D); stub=StubClient(one()); app.client=stub
    async with app.run_test(size=(120,40)) as pilot:
        await pilot.pause()
        await pilot.press("у")                       # RU e -> rename
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        chk("the rename prompt opened on у", bool(app.screen.query(Input)))
        inp=app.screen.query_one(Input); inp.value=""
        await pilot.pause()
        for ch in TITLE:
            await pilot.press(ch)
        await pilot.pause()
        chk("every character reached the rename prompt",
            app.screen.query_one(Input).value==TITLE, f"{app.screen.query_one(Input).value!r}")
        await pilot.press("escape"); await pilot.pause()
        # the picker's typed-date field
        await pilot.press("в")                       # RU d -> picker
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, DatePicker): break
        await pilot.press("з")                       # RU p -> pick a date
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        chk("з opened the typed-date field", bool(app.screen.query(Input)))
        inp=app.screen.query_one(Input); inp.value=""
        await pilot.pause()
        for ch in "2099-12-31":
            await pilot.press(ch)
        await pilot.pause()
        chk("the date typed in full", app.screen.query_one(Input).value=="2099-12-31",
            f"{app.screen.query_one(Input).value!r}")
        await pilot.press("escape"); await pilot.pause()

async def t_reported_flow():
    print("4.3 the reported flow: add, type Russian, confirm, add again")
    app=TaskApp(D); stub=StubClient(one()); app.client=stub
    async with app.run_test(size=(120,40)) as pilot:
        await pilot.pause()
        n0=len(app.tasks)
        await pilot.press("ф")
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        for ch in "Купить молоко":
            await pilot.press(ch)
        await pilot.press("enter")
        await settle(pilot, app)
        chk("the task was added", len(app.tasks)==n0+1, f"{n0} -> {len(app.tasks)}")
        chk("with the Russian title",
            any(t.title=="Купить молоко" for t in app.tasks),
            str([t.title for t in app.tasks]))
        # and now the crux: press the Russian add key again, no layout switch
        await pilot.press("ф")
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        chk("ф opened the prompt again with no layout change",
            bool(app.screen.query(Input)))
        for ch in "Вторая задача":
            await pilot.press(ch)
        await pilot.press("enter")
        await settle(pilot, app)
        chk("a second task was added the same way", len(app.tasks)==n0+2,
            f"{n0} -> {len(app.tasks)}")
        chk("both Russian titles are there",
            {"Купить молоко","Вторая задача"} <= {t.title for t in app.tasks},
            str(sorted(t.title for t in app.tasks)))

for fn in (t_add_typing, t_rename_typing, t_reported_flow):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
