"""Groups 3, 4 and 5 -- what cannot be undone, done-for-today, and the key."""
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
import main as M
from main import TaskApp, KeyBar, ProjectPicker, Confirm
from singularity import Bucket, ApiError
from textual.widgets import DataTable, Input, OptionList
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1); WORK="P-work-0001"; OTHER="P-other-002"; PROJ={WORK:"Work",OTHER:"Other"}
def so(t,v): t.raw["scheduleOrder"]=v; return t
def three(): return [so(mk("T-a","aaa",D),1000), so(mk("T-b","bbb",D),2000), so(mk("T-c","ccc",D),3000)]
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
async def settle(p,a,n=200):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False
def prep(app,stub):
    app.client=stub; app.projects=dict(PROJ); app.work_project=WORK; return app

async def t_delete():
    print("3.1 a deletion cannot be undone")
    stub=StubClient(three()); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        n0=len(app.tasks)
        await pilot.press("backspace")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        await pilot.press("y"); await settle(pilot, app)
        chk("the task is gone", len(app.tasks)==n0-1)
        await pilot.press("u"); await pilot.pause()
        chk("the board says a deletion cannot be undone",
            "deletion cannot be undone" in status(app), status(app))
        chk("no task appeared", len(app.tasks)==n0-1, str(len(app.tasks)))
        chk("nothing was created", len(stub.store)==n0-1, str(len(stub.store)))

async def t_first_filing():
    print("3.2 a first filing cannot be undone")
    stub=StubClient([so(mk("T-a","aaa",D),1000)]); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await pilot.press("p")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, ProjectPicker): break
        opts=app.screen.query_one(OptionList)
        opts.highlighted=next(i for i,o in enumerate(opts._options) if o.id==WORK)
        await pilot.pause(); await pilot.press("enter")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        await pilot.press("y"); await settle(pilot, app)
        chk("it is filed", stub.store["T-a"].project_id==WORK)
        await pilot.press("u"); await pilot.pause()
        chk("the board says so", "cannot be undone" in status(app), status(app))
        chk("the task keeps its project", stub.store["T-a"].project_id==WORK)

async def t_add():
    print("3.3 adding cannot be undone")
    stub=StubClient([so(mk("T-a","aaa",D),1000)]); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("a")
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        await pilot.press(*"zeta"); await pilot.press("enter")
        await settle(pilot, app)
        n=len(app.tasks)
        await pilot.press("u"); await pilot.pause()
        chk("the board says adding cannot be undone",
            "adding cannot be undone" in status(app), status(app))
        chk("it points at deleting instead", "backspace" in status(app), status(app))
        chk("the task still exists", len(app.tasks)==n, str(len(app.tasks)))

async def t_never_destroys():
    print("3.4 the key never destroys anything")
    stub=StubClient(three()); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        await pilot.press("x"); await settle(pilot, app)
        n=len(stub.store)
        for _ in range(8):
            await pilot.press("u"); await settle(pilot, app)
        chk("no task was deleted", len(stub.store)==n, f"{n} -> {len(stub.store)}")
        chk("delete_task was never called", stub.count("delete_task")==0)

async def t_move_projects():
    print("3.5 moving between projects can be undone")
    t=so(mk("T-f","filed",D,project=OTHER),1000)
    stub=StubClient([t]); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await pilot.press("p")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, ProjectPicker): break
        opts=app.screen.query_one(OptionList)
        opts.highlighted=next(i for i,o in enumerate(opts._options) if o.id==WORK)
        await pilot.pause(); await pilot.press("enter")
        await settle(pilot, app)
        chk("it moved", stub.store["T-f"].project_id==WORK)
        await pilot.press("u"); await settle(pilot, app)
        chk("undo returned it to the first project",
            stub.store["T-f"].project_id==OTHER, str(stub.store["T-f"].project_id))

def t_symmetry():
    print("3.6 undo and confirmation cover the same set")
    src=open(_REPO + "/main.py").read()
    import re
    unrev=set(re.findall(r'undo_reason=\(?\s*\n?\s*"([^"]{0,40})', src))
    chk("three actions declare themselves unreversible",
        len([m for m in re.finditer(r'undo_reason=', src)])==3,
        str(len([m for m in re.finditer(r'undo_reason=', src)])))
    # each of the three confirms first
    for action, marker in [("action_delete","Confirm("), ("action_add","TaskInput("),
                           ("action_project","Confirm(")]:
        body=src.split(f"def {action}",1)[1].split("\n    def ",1)[0]
        chk(f"{action} asks before writing", marker in body, marker)
    # the class definition is not a call site
    calls=src.count("Confirm(") - src.count("class Confirm(")
    chk("and no reversible action is behind a Confirm it does not need",
        calls==2, f"{calls} call sites")

async def t_dft():
    print("4.1-4.3 done for today is undone in part")
    now=datetime.now(TZ); today=now.date(); tomorrow=today+timedelta(days=1)
    t=so(mk("T-x","worked",today),1000)
    stub=StubClient([t], reference=now); app=prep(TaskApp(today), stub)
    app.tracker_config=None   # the tracker is not the subject here
    stub.fail["complete_today"]=ApiError(422,"not dated today")
    async with app.run_test() as pilot:
        await pilot.pause()
        start_before=stub.store["T-x"].raw.get("start")
        await pilot.press("full_stop"); await settle(pilot, app)
        chk("it moved to tomorrow",
            stub.store["T-x"].local_start(TZ).date()==tomorrow,
            str(stub.store["T-x"].local_start(TZ).date()))
        chk("it left today's view", "T-x" not in ids(app), str(ids(app)))
        await pilot.press("u"); await settle(pilot, app)
        chk("the date came back", stub.store["T-x"].raw.get("start")==start_before,
            str(stub.store["T-x"].local_start(TZ).date()))
        chk("it is back in the view it came from", "T-x" in ids(app), str(ids(app)))
        chk("and the board says the record could not be withdrawn",
            "record of the day's work" in status(app), status(app))
        chk("without implying a full reversal", "cannot be withdrawn" in status(app), status(app))

async def t_key():
    print("5.1-5.5 the key and what it says")
    stub=StubClient(three()); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        allk={k.strip() for b in app.BINDINGS for k in b.key.split(",")}
        chk("u is bound", "u" in allk)
        chk("its Russian twin came free", "г" in allk, str(sorted(k for k in allk if k in ("u","г"))))
        entries=dict(app.query_one(KeyBar).entries())
        chk("the bar names it, in English", entries.get("u")=="Undo", str(entries.get("u")))
        chk("no Cyrillic in the bar",
            not any(any('Ѐ'<=ch<='ӿ' for ch in k+d) for k,d in entries.items()))
        chk("the help describes it", "undo the last change" in M.Help.TEXT)
        # 5.3 nothing left
        await pilot.press("u"); await pilot.pause()
        chk("says when there is nothing left", "Nothing left to undo" in status(app), status(app))
        # the Russian twin reaches the action too
        await pilot.press("space"); await settle(pilot, app)
        await pilot.press("г"); await settle(pilot, app)
        chk("the Russian character undoes too", not stub.store["T-a"].done,
            str(stub.store["T-a"].checked))
        # 5.5 the bar still packs
        for width in (50,70,90,120,160):
            rows=KeyBar.pack(list(entries.items()), width)
            flat=[k for r in rows for k,_ in r]
            chk(f"nothing dropped or repeated at width {width}",
                len(flat)==len(entries) and len(set(flat))==len(flat), f"{len(rows)} rows")

async def t_across_views():
    print("5.4 the key needs no selection and works across views")
    stub=StubClient(three()); app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        chk("ticked on this day", stub.store["T-a"].done)
        await pilot.press("l")            # move to another day
        for _ in range(60): await pilot.pause()
        chk("the view is empty there", not app.tasks, str(ids(app)))
        await pilot.press("u"); await settle(pilot, app)
        chk("the undo still reached the task", not stub.store["T-a"].done,
            str(stub.store["T-a"].checked))
        chk("and the message names it", "aaa" in status(app), status(app))

for fn in (t_delete, t_first_filing, t_add, t_never_destroys, t_move_projects,
           t_dft, t_key, t_across_views):
    asyncio.run(fn())
t_symmetry()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
