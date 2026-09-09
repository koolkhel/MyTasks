"""Groups 2, 3 and 4 -- the block on top, the state label, the count."""
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
from datetime import datetime, timedelta
import main as M, tracker
from main import TaskApp, MARKS, _state_label
from textual.widgets import DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
WORK="P-work-0001"; TODAY=datetime.now(TZ).date()
def so(t,v): t.raw["scheduleOrder"]=v; return t
def issue(k,state="In progress",proj="TASKR"):
    return tracker.Issue(k,f"summary of {k}",proj,state,"me","https://tracker.example")
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
def day():
    return [so(mk("T-late","late",TODAY-timedelta(days=2)),100),
            so(mk("T-a","aaa",TODAY),1000),
            so(mk("T-done","zzz",TODAY,checked=1),2000)]
def prep(app, stub, issues=()):
    now=datetime.now(TZ)
    app.client=stub; app.work_project=WORK; app.projects={WORK:"Work"}
    app.tracker_config=tracker.Config("https://tracker.example","t","me",("TASKR",),
                                      ("In progress","In review"))
    wanted=list(issues)
    def fake(): app.tracker_issues=list(wanted); app.tracker_error=None; app.repaint()
    app.load_tracker=fake; app.tracker_issues=list(issues)
    return app
async def settle(p,a,n=150):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

async def t_on_top():
    print("2.1 the block precedes every task")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day(), reference=now),
             [issue("TASKR-1"), issue("BOL-9","In review","BOL")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        rows=ids(app)
        yt=[r for r in rows if r.startswith(M.TRACKER_PREFIX)]
        own=[r for r in rows if not r.startswith(M.TRACKER_PREFIX)]
        # The block now sits where the day's unfinished work ends:
        # after every unfinished row, before the first finished one.
        live=[t.id for t in app.tasks
              if not app.is_tracker(t) and not (t.done or t.cancelled)]
        dead=[t.id for t in app.tasks
              if not app.is_tracker(t) and (t.done or t.cancelled)]
        chk("the block follows every unfinished task", rows==live+yt+dead, str(rows))
        chk("and precedes every finished one",
            all(rows.index(d)>rows.index(yt[-1]) for d in dead), str(rows))
        chk("in progress leads review",
            [t.raw[M.TRACKER_STATE] for t in app.tasks if app.is_tracker(t)]
            ==["In progress","In review"], str(yt))

async def t_filter_and_order():
    print("2.2 + 2.3 the filter still reaches it; ticking does not disturb it")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day(), reference=now),
             [issue("TASKR-1"), issue("TASKR-2","In review")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        before=ids(app)
        await pilot.press("w"); await pilot.pause()
        chk("hiding work removes the tracker rows",
            not any(i.startswith(M.TRACKER_PREFIX) for i in ids(app)), str(ids(app)))
        chk("the hidden count includes them", app.hidden_work>=2, str(app.hidden_work))
        await pilot.press("w"); await pilot.pause()
        chk("and they come back where they were", ids(app)==before, str(ids(app)))
        # ticking reorders the tasks, not the block
        yt_before=[i for i in ids(app) if i.startswith(M.TRACKER_PREFIX)]
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-a")
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        yt_after=[i for i in ids(app) if i.startswith(M.TRACKER_PREFIX)]
        chk("the block keeps its sequence", yt_after==yt_before, f"{yt_before} -> {yt_after}")
        live=[t.id for t in app.tasks
              if not app.is_tracker(t) and not (t.done or t.cancelled)]
        chk("and still follows the unfinished tasks",
            ids(app)[:len(live)]==live and ids(app)[len(live):len(live)+len(yt_after)]==yt_after,
            str(ids(app)))

async def t_day_untouched():
    print("2.4 the day's own tasks are untouched by the block")
    now=datetime.now(TZ)
    a=prep(TaskApp(TODAY), StubClient(day(), reference=now), [issue("TASKR-1")])
    b=TaskApp(TODAY); b.client=StubClient(day(), reference=now)
    b.work_project=WORK; b.projects={WORK:"Work"}; b.tracker_config=None
    async with a.run_test() as pa:
        await pa.pause(); a.repaint()
        with_block=[i for i in ids(a) if not i.startswith(M.TRACKER_PREFIX)]
    async with b.run_test() as pb:
        await pb.pause()
        without=ids(b)
    chk("identical tasks in identical order", with_block==without, f"{with_block} vs {without}")

async def t_cursor():
    print("2.5 the cursor starts on the first row and the refusal reads clearly")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day(), reference=now), [issue("TASKR-1")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        chk("the cursor is on row one", table.cursor_row==0)
        # The block no longer leads the day, so the row that refuses has to
        # be selected rather than assumed.
        row=next(i for i,t in enumerate(app.tasks) if app.is_tracker(t))
        table.move_cursor(row=row); app._selected_id=app.tasks[row].id
        await pilot.pause()
        chk("a tracker row can be selected", app.is_tracker(app.selected), str(ids(app)))
        await pilot.press("space"); await pilot.pause()
        st=status(app)
        chk("the refusal names the tracker", "lives in the tracker" in st, st)
        chk("and says it is not editable", "not editable here" in st, st)

def t_label():
    print("3.1 the state label")
    # the last word, lowercased -- the leading words are shared between states
    for s,want in [("In progress","progress"),("In review","review"),("In queue","queue"),
                   ("Blocked","blocked"),("Requires improvement","improvement")]:
        chk(f"{s!r} -> {want!r}", _state_label(s)==want, _state_label(s))
    chk("nothing exceeds the column width",
        all(len(_state_label(s))<=M._WHEN_WIDTH for s in
            ["In progress","In review","Requires improvement","A very long state name"]))

async def t_row():
    print("3.2 + 3.3 a tracker row is distinguishable, and still carries its facts")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day(), reference=now),
             [issue("TASKR-1"), issue("BOL-9","In review","BOL")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        rows=[app.row_for(t) for t in app.tasks if app.is_tracker(t)]
        chk("the mark differs from every task mark",
            all(r[1]==M.TRACKER_ROW_MARK and r[1] not in MARKS.values() for r in rows),
            str([r[1] for r in rows]))
        chk("each row says its state", [r[2] for r in rows]==["progress","review"],
            str([r[2] for r in rows]))
        chk("the key and summary are shown",
            "TASKR-1" in rows[0][3] and "summary" in rows[0][3], rows[0][3][:40])
        chk("the tracker's project is shown", "TASKR" in rows[0][4] and "BOL" in rows[1][4],
            f"{rows[0][4]} {rows[1][4]}")
        chk("a tracker row carries no rail", all(r[0] == "" for r in rows), str([r[0] for r in rows]))
        chk("no colour is applied for being from the tracker",
            not any("[#" in r[3] or "[red" in r[3] or "[green" in r[3] for r in rows),
            str([r[3][:20] for r in rows]))

async def t_count():
    print("4.1-4.3 what the board reports")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day(), reference=now),
             [issue("TASKR-1"), issue("BOL-9","In review","BOL")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        st=status(app)
        chk("the count does not name a state",
            "in progress" not in st and "in review" not in st, st)
        chk("it reports how many are tracked", "2 tracked" in st, st)
        chk("the task count excludes them", "3 task(s)" in st, st)
        chk("the past-due count is still there", "1 past due" in st, st)
        await pilot.press("w"); await pilot.pause()
        st=status(app)
        chk("hidden work is reported too", "work hidden" in st, st)
for fn in (t_on_top, t_filter_and_order, t_day_untouched, t_cursor, t_row, t_count):
    asyncio.run(fn())
t_label()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
