"""Groups 2-5 -- the block, read-only, opening, and the tracker being down."""
import sys, asyncio, threading, time
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
import main as M, tracker
from main import TaskApp, KeyBar
from singularity import Bucket
from textual.widgets import DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
WORK="P-work-0001"
TODAY=datetime.now(TZ).date()
def so(t,v): t.raw["scheduleOrder"]=v; return t
def issue(k,summ="s",proj="TASKR"):
    return tracker.Issue(key=k, summary=summ, project=proj, state="In progress",
                         assignee="me", base_url="https://tracker.example")
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
def patch_stub(stub):
    def sso(tid,order):
        stub._record("set_schedule_order",tid,order); stub.store[tid].raw["scheduleOrder"]=order
        return stub.store[tid]
    stub.set_schedule_order=sso; return stub
def prep(app, stub, issues=(), err=None):
    app.client=stub; app.work_project=WORK; app.projects={WORK:"Work"}
    app.tracker_config=tracker.Config("https://tracker.example","t","me",("TASKR",),("In progress",))
    app.tracker_issues=list(issues); app.tracker_error=err
    # the board fetches on load; serve the injected issues instead of the network
    wanted=list(issues)
    def fake_load():
        app.tracker_issues=list(wanted); app.tracker_error=err; app.repaint()
    app.load_tracker=fake_load
    return app
async def settle(p,a,n=120):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

def day_tasks():
    now=datetime.now(TZ)
    return [so(mk("T-late","late",TODAY-timedelta(days=2)),100),
            so(mk("T-a","aaa",TODAY),1000),
            so(mk("T-done","zzz",TODAY,checked=1),2000)]

async def t_block():
    print("2.1 + 2.2 the block sits below every task the board manages")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now),
             [issue("TASKR-10","first"), issue("TASKR-2","second")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        rows=ids(app)
        own=[i for i in rows if not i.startswith("yt:")]
        yt=[i for i in rows if i.startswith("yt:")]
        # the block moved to where the day's unfinished work ends, by design
        live=[t.id for t in app.tasks
              if not app.is_tracker(t) and not (t.done or t.cancelled)]
        dead=[t.id for t in app.tasks
              if not app.is_tracker(t) and (t.done or t.cancelled)]
        chk("the block follows every unfinished task", rows==live+yt+dead, str(rows))
        chk("and the day's own finished tasks come after it",
            all(rows.index(d)>rows.index(yt[-1]) for d in dead), str(rows))
        chk("both issues are shown", len(yt)==2, str(yt))
        chk("ordered by key, not by summary", yt==["yt:TASKR-10","yt:TASKR-2"], str(yt))
        table=app.query_one(DataTable)
        r=app.row_for(next(t for t in app.tasks if app.is_tracker(t)))
        chk("the row shows the key and the summary",
            "TASKR-10" in r[3] and "first" in r[3], str(r[3]))
        chk("it has its own mark, not a checkbox", r[1]==M.TRACKER_ROW_MARK, r[1])
        chk("the project column shows the tracker's project", "TASKR" in r[4], r[4])
        # the column carries the issue's state now, not the word "tracker"
        chk("the when column says the state", r[2]=="progress", r[2])

async def t_only_today():
    print("2.4 today only")
    app=prep(TaskApp(TODAY+timedelta(days=1)), StubClient(day_tasks()), [issue("TASKR-1")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        chk("another day shows no tracker row", not any(i.startswith("yt:") for i in ids(app)),
            str(ids(app)))
    for b in (Bucket.INBOX, Bucket.SOMEDAY):
        app=prep(TaskApp(TODAY), StubClient(day_tasks()), [issue("TASKR-1")])
        async with app.run_test() as pilot:
            await pilot.pause()
            app.position=b; app.repaint()
            chk(f"{b.name.lower()} shows no tracker row",
                not any(i.startswith("yt:") for i in ids(app)), str(ids(app)))

async def t_unmoved():
    print("2.3 the block does not move when the day reorders")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now),
             [issue("TASKR-1"), issue("TASKR-2")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        before=[i for i in ids(app) if i.startswith("yt:")]
        await pilot.press("space"); await settle(pilot, app)
        after=[i for i in ids(app) if i.startswith("yt:")]
        chk("the tracker rows keep their sequence", after==before, f"{before} -> {after}")
        # recomputed: ticking a past-due task stops it being past due, so it
        # leaves today entirely -- the count of own tasks is not what it was
        own_now=len([i for i in ids(app) if not i.startswith("yt:")])
        live=[t.id for t in app.tasks
              if not app.is_tracker(t) and not (t.done or t.cancelled)]
        chk("and still follow the unfinished tasks",
            ids(app)[len(live):len(live)+len(after)]==after, str(ids(app)))

async def t_work_filter():
    print("2.5 + 2.6 the work filter reaches the block")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now),
             [issue("TASKR-1"), issue("TASKR-2")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        before=ids(app)
        await pilot.press("w"); await pilot.pause()
        chk("hiding work removes the tracker rows",
            not any(i.startswith("yt:") for i in ids(app)), str(ids(app)))
        chk("the hidden count includes them", app.hidden_work>=2, str(app.hidden_work))
        chk("the daybar says so", "work hidden" in str(app.query_one("#daybar").content),
            str(app.query_one("#daybar").content))
        await pilot.press("w"); await pilot.pause()
        chk("pressing again brings them back", ids(app)==before, str(ids(app)))

async def t_counts():
    print("2.7 issues counted separately from tasks")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now),
             [issue("TASKR-1"), issue("TASKR-2")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        st=status(app)
        chk("the task count excludes the issues", "3 task(s)" in st, st)
        chk("the issues are reported beside it", "2 tracked" in st, st)
        chk("the past-due count survives", "1 past due" in st, st)

async def t_readonly():
    print("3.1 + 3.2 every writing action refuses")
    now=datetime.now(TZ)
    stub=patch_stub(StubClient(day_tasks(), reference=now))
    app=prep(TaskApp(TODAY), stub, [issue("TASKR-1","an issue")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if app.is_tracker(t))
        table.move_cursor(row=row); await pilot.pause()
        chk("a tracker row is selected", app.is_tracker(app.selected))
        n0=len([c for c,_ in stub.calls if c not in ("tasks_at","project_names")])
        for key,label in [("space","tick"),("full_stop","done for today"),("x","cancel"),
                          ("backspace","delete")]:
            await pilot.press(key); await pilot.pause()
            chk(f"{label} refuses", "not editable here" in status(app), f"{label}: {status(app)}")
        writes=len([c for c,_ in stub.calls if c not in ("tasks_at","project_names")])-n0
        chk("nothing was sent by any of them", writes==0, str(writes))
        chk("the undo stack is still empty", app._undo==[], str(len(app._undo)))

async def t_reorder():
    print("3.3 reordering says why")
    now=datetime.now(TZ)
    stub=patch_stub(StubClient(day_tasks(), reference=now))
    app=prep(TaskApp(TODAY), stub, [issue("TASKR-1"), issue("TASKR-2")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if app.is_tracker(t))
        table.move_cursor(row=row); await pilot.pause()
        before=ids(app)
        await pilot.press("J"); await pilot.pause()
        chk("it says the issue lives in the tracker", "lives in the tracker" in status(app),
            status(app))
        chk("nothing moved", ids(app)==before, str(ids(app)))
        chk("no order was written", stub.count("set_schedule_order")==0)

async def t_tasks_still_work():
    print("3.5 the day's own tasks stay editable")
    now=datetime.now(TZ)
    stub=StubClient(day_tasks(), reference=now)
    app=prep(TaskApp(TODAY), stub, [issue("TASKR-1")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if t.id=="T-a")
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        chk("ticking a real task still works", stub.store["T-a"].done)
        chk("and it was recorded for undo", len(app._undo)==1, str(len(app._undo)))

async def t_open():
    print("4.1 + 4.2 opening an issue")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now), [issue("TASKR-1")])
    opened=[]
    app.open_url=lambda u: opened.append(u)
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint()
        table=app.query_one(DataTable)
        row=next(i for i,t in enumerate(app.tasks) if app.is_tracker(t))
        table.move_cursor(row=row); await pilot.pause()
        await pilot.press("o"); await pilot.pause()
        chk("the issue's page was opened", opened==["https://tracker.example/issue/TASKR-1"],
            str(opened))
        chk("built from base, /issue/ and the key",
            opened and opened[0].endswith("/issue/TASKR-1"))
        chk("nothing about the issue changed",
            any(app.is_tracker(t) for t in app.tasks))

async def t_down():
    print("5.2 + 5.3 the tracker being unreachable")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.tracker_failed("could not reach the tracker: no route")
        await pilot.pause()
        chk("the day's own tasks are still there",
            len([i for i in ids(app) if not i.startswith("yt:")])==3, str(ids(app)))
        chk("no tracker block", not any(i.startswith("yt:") for i in ids(app)))
        chk("the board says the tracker could not be reached",
            "could not reach the tracker" in status(app), status(app))
        chk("it names the tracker, not the day",
            "today" not in status(app).lower() and "failed to load" not in status(app).lower(),
            status(app))
        # distinguishable from nothing in progress
        app.tracker_loaded([])
        await pilot.pause()
        chk("5.3 an empty result says something different",
            "could not reach" not in status(app), status(app))
        chk("5.5 and recovery shows the issues",
            (app.tracker_loaded([issue("TASKR-9")]), app.tracker_error is None,
             any(i.startswith("yt:") for i in ids(app)))[1:]==(True,True), str(ids(app)))

async def t_unconfigured():
    print("5.4 no tracker configured is an ordinary board")
    now=datetime.now(TZ)
    app=prep(TaskApp(TODAY), StubClient(day_tasks(), reference=now))
    app.tracker_config=None
    async with app.run_test() as pilot:
        await pilot.pause()
        app.load_tracker()
        for _ in range(40): await pilot.pause()
        chk("no tracker rows", not any(i.startswith("yt:") for i in ids(app)))
        chk("and no failure reported", "could not reach" not in status(app), status(app))
        chk("the day is normal", "3 task(s)" in status(app), status(app))

# ------------------------------------------------------------- the priority
#: The tracker's own words, and the API's English names beside them.  Both
#: come from the real tracker's vocabulary; the letters are what a person
#: already reads off its interface.
PRIORITIES = (
    ("Неотложная",     "Show-stopper", "Н"),
    ("Критический",    "Critical",     "К"),
    ("Серьезная",      "Major",        "С"),
    ("Обычный",        "Normal",       "О"),
    ("Незначительный", "Minor",        "н"),
)


def prio_issue(k, word="", value="", proj="TASKR"):
    i = issue(k, proj=proj)
    return tracker.Issue(key=i.key, summary=i.summary, project=i.project,
                         state=i.state, assignee=i.assignee,
                         base_url=i.base_url, priority=word,
                         priority_value=value)


def cell(app, key, i):
    t = next(x for x in app.tasks if x.id == f"yt:{key}")
    return str(app.row_for(t)[i])


async def t_priority():
    print("2.9 a tracker row says how urgent the tracker calls it")
    issues = [prio_issue(f"TASKR-{n}", w, v)
              for n, (w, v, _) in enumerate(PRIORITIES, start=1)]
    app = prep(TaskApp(TODAY), StubClient(day_tasks(), reference=datetime.now(TZ)), issues)
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint(); await pilot.pause()
        for n, (word, value, letter) in enumerate(PRIORITIES, start=1):
            chk(f"{value} shows as {letter!r}",
                cell(app, f"TASKR-{n}", 0) == letter,
                f"{cell(app, f'TASKR-{n}', 0)!r}")
        # The pair that share a letter: the most urgent and the least.
        top, low = cell(app, "TASKR-1", 0), cell(app, "TASKR-5", 0)
        chk("the two priorities sharing a letter are told apart", top != low,
            f"{top!r} vs {low!r}")
        chk("and differ only in case", top.lower() == low.lower(),
            f"{top!r} vs {low!r}")
        # Legible from the text alone: the cell carries the letter, not a style.
        import re as _re
        for n, (_, value, letter) in enumerate(PRIORITIES, start=1):
            plain = _re.sub(r"\[/?[^\]]*\]", "", cell(app, f"TASKR-{n}", 0))
            chk(f"{value} is legible without colour", plain == letter,
                f"{plain!r}")
        chk("no markup is used in that cell at all",
            all("[" not in cell(app, f"TASKR-{n}", 0)
                for n in range(1, len(PRIORITIES) + 1)))
        # One character each: the column is one cell wide, and a Cyrillic
        # capital is East Asian Width Ambiguous, which design.md records as a
        # deliberate departure from the rule the mailbox marks follow.
        chk("every letter is a single character",
            all(len(cell(app, f"TASKR-{n}", 0)) == 1
                for n in range(1, len(PRIORITIES) + 1)))

    print("2.10 an issue with no priority shows nothing there")
    app = prep(TaskApp(TODAY), StubClient(day_tasks(), reference=datetime.now(TZ)), [prio_issue("TASKR-9")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint(); await pilot.pause()
        chk("the cell is empty", cell(app, "TASKR-9", 0) == "",
            f"{cell(app, 'TASKR-9', 0)!r}")

    print("2.11 nothing else about the row changes")
    #: The same issue with and without a priority: every other cell identical.
    plain_app = prep(TaskApp(TODAY), StubClient(day_tasks(), reference=datetime.now(TZ)), [prio_issue("TASKR-7")])
    async with plain_app.run_test() as pilot:
        await pilot.pause(); plain_app.repaint(); await pilot.pause()
        without = [cell(plain_app, "TASKR-7", i) for i in range(1, 5)]
    with_app = prep(TaskApp(TODAY), StubClient(day_tasks()),
                    [prio_issue("TASKR-7", "Критический", "Critical")])
    async with with_app.run_test() as pilot:
        await pilot.pause(); with_app.repaint(); await pilot.pause()
        withp = [cell(with_app, "TASKR-7", i) for i in range(1, 5)]
        chk("mark, state, title and project are untouched", withp == without,
            f"{withp} vs {without}")

    print("2.12 the block's order is what it was")
    #: Ordered by state then key, and priority must not reach that.
    mixed = [prio_issue("TASKR-3", "Обычный", "Normal"),
             prio_issue("TASKR-1", "Неотложная", "Show-stopper"),
             prio_issue("TASKR-2", "Незначительный", "Minor")]
    app = prep(TaskApp(TODAY), StubClient(day_tasks(), reference=datetime.now(TZ)), mixed)
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint(); await pilot.pause()
        withp = [t.id for t in app.tasks if app.is_tracker(t)]
    app = prep(TaskApp(TODAY), StubClient(day_tasks(), reference=datetime.now(TZ)),
               [prio_issue(k) for k in ("TASKR-3", "TASKR-1", "TASKR-2")])
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint(); await pilot.pause()
        without = [t.id for t in app.tasks if app.is_tracker(t)]
        chk("priorities do not reorder the block", withp == without,
            f"{withp} vs {without}")

    print("2.13 a task's leftmost cell is still the tag's")
    #: The one cell now means two things, and the two cannot meet on one row:
    #: a task has no priority and a tracker row has no tags.
    #: A tag id, shaped the way the green suites shape one.
    GREEN = "A-zzgreen"
    tagged = mk("T-tag", "a tagged task", TODAY)
    tagged.raw["tags"] = [GREEN]
    app = prep(TaskApp(TODAY), StubClient([tagged] + day_tasks(), reference=datetime.now(TZ)),
               [prio_issue("TASKR-1", "Неотложная", "Show-stopper")])
    app.green_tag = GREEN
    async with app.run_test() as pilot:
        await pilot.pause(); app.repaint(); await pilot.pause()
        task_cell = str(app.row_for(
            next(t for t in app.tasks if t.id == "T-tag"))[0])
        chk("the tagged task still shows the tag's mark",
            task_cell == M.GREEN_MARK, f"{task_cell!r}")
        chk("and the tracker row still shows its priority",
            cell(app, "TASKR-1", 0) == "Н", f"{cell(app, 'TASKR-1', 0)!r}")

    print("2.14 the letter is the same at any width")
    #: The column is one cell wide and a Cyrillic capital is East Asian Width
    #: Ambiguous -- the class the mailbox marks avoid, and a deliberate
    #: departure here.  So the letter must not be clipped or padded by the
    #: width the board happens to be at, and the row must keep its five cells.
    seen = {}
    for width in (120, 80):
        app = prep(TaskApp(TODAY),
                   StubClient(day_tasks(), reference=datetime.now(TZ)),
                   [prio_issue("TASKR-1", "Неотложная", "Show-stopper"),
                    prio_issue("TASKR-5", "Незначительный", "Minor")])
        async with app.run_test(size=(width, 40)) as pilot:
            await pilot.pause(); app.repaint(); await pilot.pause()
            chk(f"{width} cols: the board really is that wide",
                app.size.width == width, str(app.size.width))
            row = app.row_for(next(t for t in app.tasks
                                   if t.id == "yt:TASKR-1"))
            chk(f"{width} cols: the row still has its five cells",
                len(row) == 5, str(len(row)))
            seen[width] = (str(row[0]), cell(app, "TASKR-5", 0))
    chk("the letters read the same at both widths",
        seen[120] == seen[80], f"{seen}")
    chk("and are still one character each",
        all(len(c) == 1 for pair in seen.values() for c in pair), f"{seen}")


for fn in (t_block, t_only_today, t_unmoved, t_work_filter, t_counts, t_readonly,
           t_reorder, t_tasks_still_work, t_open, t_down, t_unconfigured, t_priority):
    asyncio.run(fn())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
