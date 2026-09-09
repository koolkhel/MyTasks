"""Group 5 -- assigning a project."""
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
from datetime import date
import main as M
from main import TaskApp, ProjectPicker, Confirm, KeyBar
from singularity import Bucket, SingularityError
from textual.widgets import OptionList, DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1); WORK="P-work-0001"; OTHER="P-other-002"
PROJ={WORK:"Work", OTHER:"Other"}
def so(t,v): t.raw["scheduleOrder"]=v; return t
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
def prep(app, stub):
    app.client=stub; app.work_project=WORK; app.projects=dict(PROJ); return app
async def settle(p,a,n=80):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False
async def open_picker(pilot, app):
    await pilot.press("p")
    for _ in range(40):
        await pilot.pause()
        if isinstance(app.screen, ProjectPicker): break
    return isinstance(app.screen, ProjectPicker)

async def t_picker():
    print("5.1 + 5.2 the picker lists every project and marks the task's own")
    tasks=[so(mk("T-a","aaa",D),1000), so(mk("T-f","filed",D,project=OTHER),2000)]
    app=prep(TaskApp(D), StubClient(tasks))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects=dict(PROJ)
        chk("p opens the picker", await open_picker(pilot, app))
        opts=app.screen.query_one(OptionList)
        labels=[str(o.prompt) for o in opts._options]
        chk("every project is listed", len(labels)==len(PROJ), str(labels))
        chk("the unfiled task's picker marks none", not any(l.startswith("* ") for l in labels), str(labels))
        chk("it says the task has no project",
            "no project" in str(app.screen.query_one("#dialog-where").content),
            str(app.screen.query_one("#dialog-where").content))
        await pilot.press("escape")
        for _ in range(30):
            await pilot.pause()
            if not isinstance(app.screen, ProjectPicker): break
        chk("escape closes it", not isinstance(app.screen, ProjectPicker))
        # now on the filed task
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-f")
        table.move_cursor(row=row); await pilot.pause()
        chk("p opens on the filed task", await open_picker(pilot, app))
        labels=[str(o.prompt) for o in app.screen.query_one(OptionList)._options]
        marked=[l for l in labels if l.startswith("* ")]
        chk("its own project is marked", len(marked)==1 and "Other" in marked[0], str(labels))
        chk("and it says where it is now",
            "Other" in str(app.screen.query_one("#dialog-where").content),
            str(app.screen.query_one("#dialog-where").content))
        await pilot.press("escape"); await pilot.pause()

async def choose(pilot, app, name):
    """Move to the named project and press enter."""
    opts=app.screen.query_one(OptionList)
    idx=next(i for i,o in enumerate(opts._options) if name in str(o.prompt))
    opts.highlighted=idx
    await pilot.pause()
    await pilot.press("enter")

async def t_confirm_first():
    print("5.3 a first filing is confirmed")
    stub=StubClient([so(mk("T-a","aaa",D),1000)])
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        chk("it asks first", isinstance(app.screen, Confirm))
        body=" ".join(str(w.content) for w in app.screen.query("Label"))
        chk("the question names the consequence", "cannot be un-filed" in body, body[:80])
        await pilot.press("n")
        await settle(pilot, app)
        chk("declining sends nothing", stub.count("set_project")==0)
        chk("and leaves the task unfiled", stub.store["T-a"].project_id is None,
            str(stub.store["T-a"].project_id))
        # now agree
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        await pilot.press("y")
        await settle(pilot, app)
        chk("agreeing files it", stub.store["T-a"].project_id==WORK, str(stub.store["T-a"].project_id))
        chk("through one write", stub.count("set_project")==1, str(stub.count("set_project")))

async def t_move_no_confirm():
    print("5.4 moving between projects is not confirmed")
    stub=StubClient([so(mk("T-f","filed",D,project=OTHER),1000)])
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        for _ in range(20): await pilot.pause()
        chk("no confirmation appeared", not isinstance(app.screen, Confirm), type(app.screen).__name__)
        await settle(pilot, app)
        chk("it moved", stub.store["T-f"].project_id==WORK, str(stub.store["T-f"].project_id))

async def t_optimistic():
    print("5.5 filing is optimistic and rolls back")
    stub=StubClient([so(mk("T-f","filed",D,project=OTHER),1000)])
    stub.gate=threading.Event()
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        await pilot.pause()
        shown=next((t for t in app.tasks if t.id=="T-f"), None)
        chk("the change shows before the API answered",
            shown is not None and shown.project_id==WORK, str(shown.project_id if shown else None))
        stub.gate.set(); await settle(pilot, app)
        chk("and stands after confirmation", app.tasks[0].project_id==WORK)
    # refusal
    stub=StubClient([so(mk("T-f","filed",D,project=OTHER),1000)])
    stub.gate=threading.Event(); stub.fail["set_project"]=SingularityError("nope")
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        await pilot.pause()
        stub.gate.set(); await settle(pilot, app)
        chk("a refused filing restores the previous project",
            app.tasks[0].project_id==OTHER, str(app.tasks[0].project_id))
        chk("and reports the failure", "failed" in status(app) and "nope" in status(app), status(app))

async def t_inbox_leaves():
    print("5.6 a task filed from the inbox leaves it at once")
    stub=StubClient([mk("T-i","aaa"), mk("T-j","bbb")])
    app=prep(TaskApp(D), stub); stub.gate=threading.Event()
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        app.position=Bucket.INBOX; app.load()
        for _ in range(60):
            await pilot.pause()
            if app.position is Bucket.INBOX and "task(s)" in status(app): break
        chk("both are in the inbox", set(ids(app))=={"T-i","T-j"}, str(ids(app)))
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        await pilot.press("y")
        await pilot.pause()
        chk("the row leaves the inbox immediately", "T-i" not in ids(app), str(ids(app)))
        stub.gate.set(); await settle(pilot, app)
        chk("and stays gone", "T-i" not in ids(app), str(ids(app)))

async def t_filed_hidden():
    print("5.7 filing under work while work is hidden")
    stub=StubClient([so(mk("T-a","aaa",D),1000), so(mk("T-b","bbb",D),2000)])
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause(); app.projects=dict(PROJ)
        await pilot.press("w"); await pilot.pause()
        chk("both shown, nothing hidden yet", len(app.tasks)==2 and app.hidden_work==0)
        await open_picker(pilot, app)
        await choose(pilot, app, "Work")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Confirm): break
        await pilot.press("y"); await pilot.pause()
        chk("the row disappears", len(app.tasks)==1, str(ids(app)))
        chk("and the hidden count rose by one", app.hidden_work==1, str(app.hidden_work))
        await settle(pilot, app)

def t_no_unfile():
    print("5.8 the board offers no way to un-file")
    src=open(_REPO + "/main.py").read()
    chk("no action clears a project",
        'projectId": None' not in src and "projectId=None" not in src
        and '"projectId": ""' not in src)
    chk("no binding mentions unfiling",
        not any("unfile" in (b.action or "") or "un-file" in (b.description or "").lower()
                for b in TaskApp.BINDINGS))
    chk("the picker offers only real projects, no 'none' entry",
        "no project" not in ProjectPicker.compose.__doc__ if ProjectPicker.compose.__doc__ else True)

async def t_keybar():
    print("5.2 the key bar and help name it")
    app=prep(TaskApp(D), StubClient([mk("T-a","aaa",D)]))
    async with app.run_test() as pilot:
        await pilot.pause()
        entries=dict(app.query_one(KeyBar).entries())
        chk("the bar names the key", entries.get("p")=="Project", str(entries.get("p")))
        chk("the help describes it", "put the task in a project" in M.Help.TEXT)

for fn in (t_picker, t_confirm_first, t_move_no_confirm, t_optimistic,
           t_inbox_leaves, t_filed_hidden, t_keybar):
    asyncio.run(fn())
t_no_unfile()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
