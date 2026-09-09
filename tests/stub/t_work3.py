"""Groups 3 and 4 -- hiding work, and saying so."""
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
from datetime import date, datetime, timedelta
import main as M
from main import TaskApp, KeyBar
from singularity import Bucket
from textual.widgets import DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1); WORK="P-work-0001"; OTHER="P-other-002"
def so(t,v): t.raw["scheduleOrder"]=v; return t
def team():
    return [so(mk("T-a","aaa",D),1000),
            so(mk("T-w1","www one",D,project=WORK),2000),
            so(mk("T-b","bbb",D),3000),
            so(mk("T-w2","www two",D,project=WORK),4000),
            so(mk("T-o","other proj",D,project=OTHER),5000)]
def ids(a): return [t.id for t in a.tasks]
def daybar(a): return str(a.query_one("#daybar").content)
def status(a): return str(a.query_one("#status").content)
def prep(app, stub, work=WORK, projects=None):
    app.client=stub; app.work_project=work
    app.projects = projects if projects is not None else {WORK:"Work", OTHER:"Other"}
    return app

async def t_hide():
    print("3.1 + 3.3 hiding and showing again")
    app=prep(TaskApp(D), StubClient(team()))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work", OTHER:"Other"}
        before=ids(app)
        chk("all five rows to start", len(before)==5, str(before))
        await pilot.press("w"); await pilot.pause()
        chk("the two work rows are gone", ids(app)==["T-a","T-b","T-o"], str(ids(app)))
        chk("the other project's task stays", "T-o" in ids(app))
        # The invariant behind the count, asserted here for a board of plain
        # tasks: with the mode on, nothing on screen counts as work.  Its
        # point is sources -- a source appended after the filter escapes the
        # key, which is what happened to the mail rows -- and it is checked
        # for each source where that source's own board is built.  A sum of
        # shown and hidden would not do: an escaped source is missing from
        # both sides of it.
        chk("nothing on screen counts as work",
            [t.id for t in app.tasks if app.is_work(t)]==[],
            str([t.id for t in app.tasks if app.is_work(t)]))
        chk("and shown plus hidden is what there was",
            len(app.tasks)+app.hidden_work==len(before),
            f"{len(app.tasks)}+{app.hidden_work} vs {len(before)}")
        await pilot.press("w"); await pilot.pause()
        chk("pressing again restores them exactly", ids(app)==before, str(ids(app)))

async def t_belongs_unchanged():
    print("3.1 belongs answers identically either way")
    app=prep(TaskApp(D), StubClient(team()))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        off={t.id: app.belongs(t) for t in app.patched()}
        app.hiding_work=True; app.repaint()
        on={t.id: app.belongs(t) for t in app.patched()}
        chk("belongs is unaffected by the mode", off==on, f"{off} vs {on}")
        chk("but the rendered rows differ", len(app.tasks)==3, str(ids(app)))

async def t_counts():
    print("3.2 + 4.1 the hidden count and what is reported")
    app=prep(TaskApp(D), StubClient(team()))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        total=len(app.tasks)
        await pilot.press("w"); await pilot.pause()
        chk("hidden count equals the work rows the view held", app.hidden_work==2, str(app.hidden_work))
        chk("shown plus hidden equals the unfiltered total",
            len(app.tasks)+app.hidden_work==total, f"{len(app.tasks)}+{app.hidden_work} vs {total}")
        chk("the daybar says work is hidden, with the count",
            "work hidden (2)" in daybar(app), daybar(app))
        chk("the status reports it beside the other counts",
            "2 work hidden" in status(app) and f"{len(app.tasks)} task(s)" in status(app), status(app))

async def t_hides_nothing():
    print("4.2 the mode is reported even when it hides nothing")
    app=prep(TaskApp(D), StubClient([so(mk("T-a","aaa",D),1000)]))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        await pilot.press("w"); await pilot.pause()
        chk("no rows removed", app.hidden_work==0 and len(app.tasks)==1)
        chk("but the daybar still says work is hidden",
            "work hidden" in daybar(app), daybar(app))
        print("4.3 and nothing when the mode is off")
        await pilot.press("w"); await pilot.pause()
        chk("no mention when off", "work hidden" not in daybar(app), daybar(app))
        chk("nor in the status", "work hidden" not in status(app), status(app))

async def t_beside_pastdue():
    print("4.4 beside the past-due count, not instead of it")
    now=datetime.now(TZ); today=now.date()
    tasks=[so(mk("T-late","late",today-timedelta(days=3)),100),
           so(mk("T-w","work",today,project=WORK),200),
           so(mk("T-n","now",today),300)]
    app=prep(TaskApp(today), StubClient(tasks, reference=now))
    app.tracker_config=None   # the tracker is not the subject here
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        await pilot.press("w"); await pilot.pause()
        st=status(app)
        chk("past-due count present", "1 past due" in st, st)
        chk("hidden-work count present", "1 work hidden" in st, st)
        chk("neither replaced the other", "past due" in st and "work hidden" in st)

async def t_every_view():
    print("3.4 the mode follows between views")
    tasks=team()
    someday=mk("T-sw","work someday",None,project=WORK); someday.raw["deferred"]=True
    app=prep(TaskApp(D), StubClient(tasks+[someday]))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work", OTHER:"Other"}
        await pilot.press("w"); await pilot.pause()
        chk("hidden on the starting day", "T-w1" not in ids(app))
        await pilot.press("l")
        for _ in range(40): await pilot.pause()
        chk("still on after moving to another day", app.hiding_work)
        chk("and the daybar still says so there", "work hidden" in daybar(app), daybar(app))
        app.position=Bucket.SOMEDAY; app.load()
        for _ in range(60):
            await pilot.pause()
            if app.position is Bucket.SOMEDAY and "task(s)" in status(app): break
        chk("someday honours the mode too", "T-sw" not in ids(app), str(ids(app)))
        chk("and says so", "work hidden" in daybar(app), daybar(app))

async def t_inbox():
    # No mailbox is configured here, which is why this still holds whole.
    # The inbox's *tasks* are unaffected by construction -- a task with a
    # project is already outside the inbox -- but mail is work, and an inbox
    # with mail in it does change.  That half is in t_mailview, on a board
    # that has a mailbox.
    print("3.1 the inbox's tasks are unaffected by construction")
    inbox=[mk("T-i1","aaa"), mk("T-i2","bbb")]
    filed=mk("T-i3","filed", project=WORK)
    app=prep(TaskApp(D), StubClient(inbox+[filed]))
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        app.position=Bucket.INBOX; app.load()
        for _ in range(60):
            await pilot.pause()
            if app.position is Bucket.INBOX and "task(s)" in status(app): break
        off=ids(app)
        await pilot.press("w"); await pilot.pause()
        chk("the inbox shows the same tasks either way, there being no mail here",
            ids(app)==off, f"{off} -> {ids(app)}")
        chk("because a filed task was never in it", "T-i3" not in off, str(off))

async def t_no_writes():
    print("3.5 nothing is written")
    stub=StubClient(team())
    app=prep(TaskApp(D), stub)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work"}
        fields={t.id: dict(t.raw) for t in stub.store.values()}
        n0=len(stub.calls)
        for _ in range(6):
            await pilot.press("w"); await pilot.pause()
        writes=[c for c,_ in stub.calls[n0:] if c not in ("tasks_at","project_names")]
        chk("no write was sent", not writes, str(writes))
        chk("every task's fields are untouched",
            {t.id: dict(t.raw) for t in stub.store.values()}==fields)

def t_default_off():
    print("3.6 the mode does not outlive the board")
    chk("a fresh board has it off", TaskApp(D).hiding_work is False)

async def t_config():
    print("4.5 config problems are reported")
    app=prep(TaskApp(D), StubClient(team()), work=None)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("w"); await pilot.pause()
        chk("unset is reported", "No work project is set" in status(app), status(app))
        chk("and nothing is hidden", len(app.tasks)==5 and not app.hiding_work)
    app=prep(TaskApp(D), StubClient(team()), work="P-gone-9999",
             projects={WORK:"Work", OTHER:"Other"})
    async with app.run_test() as pilot:
        await pilot.pause()
        app.projects={WORK:"Work", OTHER:"Other"}
        await pilot.press("w"); await pilot.pause()
        chk("a stale setting is reported", "was not found" in status(app), status(app))
        chk("and nothing is hidden", len(app.tasks)==5 and not app.hiding_work)

async def t_keybar():
    print("3.3 the key bar and help")
    app=prep(TaskApp(D), StubClient(team()))
    async with app.run_test() as pilot:
        await pilot.pause()
        bar=app.query_one(KeyBar); entries=dict(bar.entries())
        chk("the bar names the key", entries.get("w")=="Hide work", str(entries.get("w")))
        chk("the help describes it", "hide the work project" in M.Help.TEXT)
        allk={k.strip() for b in app.BINDINGS for k in b.key.split(",")}
        chk("its Russian twin came free", "ц" in allk, str(sorted(k for k in allk if k in ("w","ц"))))

for fn in (t_hide, t_belongs_unchanged, t_counts, t_hides_nothing, t_beside_pastdue,
           t_every_view, t_inbox, t_no_writes, t_config, t_keybar):
    asyncio.run(fn())
t_default_off()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
