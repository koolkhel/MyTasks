"""Groups 3 and 4 -- what the change must not disturb, and colliding states."""
import sys, asyncio
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import StubClient, mk, TZ
from datetime import datetime, timedelta
import main as M, tracker
from main import TaskApp
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
WORK = "P-work-0001"
TODAY = datetime.now(TZ).date()

def issue(k, state, proj="TASKR"):
    return tracker.Issue(key=k, summary=f"summary of {k}", project=proj, state=state,
                         assignee="me", base_url="https://tracker.example")

def prep(app, stub, issues=(), states=("In progress", "In review")):
    app.client = stub; app.work_project = WORK; app.projects = {WORK: "Work"}
    app.tracker_config = tracker.Config("https://tracker.example", "t", "me", ("TASKR",), states)
    wanted = list(issues)
    def fake_load():
        app.tracker_issues = list(wanted); app.tracker_error = None; app.repaint()
    app.load_tracker = fake_load
    return app

NOW = datetime.now(TZ)

def ordered(issues, states):
    """The order tracker.parse would hand the board."""
    cfg = tracker.Config("https://tracker.example", "t", "me", ("TASKR",), states)
    return sorted(issues, key=lambda i: (cfg.rank(i.state), i.key))

async def board(tasks, issues=(), states=("In progress", "In review")):
    stub = StubClient(tasks, reference=NOW)
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        prep(app, stub, ordered(issues, states), states)
        app.load()
        for _ in range(200): await pilot.pause()
        rows = [app.row_for(t) for t in app.tasks]
        return ([t.id for t in app.tasks], rows,
                str(app.query_one("#status").content))

late = mk("T-late", "late one", start=TODAY - timedelta(days=3))
today_all = mk("T-a", "an all-day task", start=TODAY)
timed = mk("T-t", "a timed task", start=TODAY, timed=True)
done = mk("T-done", "a finished task", start=TODAY, checked=1)
TASKS = [late, today_all, timed, done]

async def run():
    print("3.2 the day's own tasks are unchanged, tracker or no tracker")
    ids_off, rows_off, st_off = await board(TASKS, ())
    ids_on, rows_on, st_on = await board(TASKS, [issue("TASKR-1", "In progress")])
    own_on = [i for i in ids_on if not i.startswith(M.TRACKER_PREFIX)]
    when_off = [r[2] for r in rows_off]
    when_on = [r[2] for i, r in zip(ids_on, rows_on) if not i.startswith(M.TRACKER_PREFIX)]
    chk("same rows, in the same order", own_on == ids_off, f"{own_on} vs {ids_off}")
    chk("same when-labels", when_on == when_off, f"{when_on} vs {when_off}")
    chk("a task's when-label is untouched by the rule",
        set(when_off) >= {"all-day", "3d ago"}, str(when_off))
    chk("the past-due task is still gathered in", "T-late" in ids_off, str(ids_off))
    chk("the task count is the tasks alone",
        f"{len(ids_off)} task(s)" in st_on and f"{len(ids_off)} task(s)" in st_off, st_on)
    chk("the past-due count is unchanged",
        "1 past due" in st_off and "1 past due" in st_on, f"{st_off} || {st_on}")
    chk("no when-label is cut", all(len(w) <= M._WHEN_WIDTH for w in when_off + when_on),
        str(max(len(w) for w in when_off + when_on)))

    print("\n3.3 the block still groups by the configured order, and is still counted")
    states = ("In progress", "In review", "Requires improvement")
    iss = [issue("TASKR-9", "Requires improvement"), issue("TASKR-2", "In review"),
           issue("TASKR-1", "In progress"), issue("TASKR-5", "In review")]
    ids_, rows_, st_ = await board(TASKS, iss, states)
    yt = [i for i in ids_ if i.startswith(M.TRACKER_PREFIX)]
    labels = [r[2] for i, r in zip(ids_, rows_) if i.startswith(M.TRACKER_PREFIX)]
    chk("the block is contiguous, after the unfinished tasks",
        ids_[ids_.index(yt[0]):ids_.index(yt[0]) + len(yt)] == yt, str(ids_))
    chk("grouped in the configured order of the states",
        labels == ["progress", "review", "review", "improvement"], str(labels))
    chk("which is the order the tracker module produces",
        [i.key for i in ordered(iss, states)] == ["TASKR-1", "TASKR-2", "TASKR-5", "TASKR-9"],
        str([i.key for i in ordered(iss, states)]))
    chk("and by key within a state",
        yt == ["yt:TASKR-1", "yt:TASKR-2", "yt:TASKR-5", "yt:TASKR-9"], str(yt))
    chk("still counted as tracked", f"{len(iss)} tracked" in st_, st_)
    chk("the count names no single state",
        not any(s.lower() in st_.lower() for s in states), st_)
    chk("every label fits the column", all(len(l) <= M._WHEN_WIDTH for l in labels), str(labels))
    chk("'improvement' reads in full", "improvement" in labels, str(labels))

    print("\n4.1 two configured states ending in the same word")
    states = ("In review", "Needs review")
    iss = [issue("TASKR-7", "Needs review"), issue("TASKR-3", "In review"),
           issue("TASKR-8", "Needs review"), issue("TASKR-4", "In review")]
    ids_, rows_, st_ = await board(TASKS, iss, states)
    yt = [i for i in ids_ if i.startswith(M.TRACKER_PREFIX)]
    labels = [r[2] for i, r in zip(ids_, rows_) if i.startswith(M.TRACKER_PREFIX)]
    chk("their labels coincide", labels == ["review"] * 4, str(labels))
    chk("their rows still form separate runs, in the configured order",
        yt == ["yt:TASKR-3", "yt:TASKR-4", "yt:TASKR-7", "yt:TASKR-8"], str(yt))
    chk("all four are still shown", len(yt) == 4 and f"4 tracked" in st_, st_)

asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
