"""Group 5 -- against the live tracker."""
import sys, asyncio, os, json
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
from datetime import datetime
import main as M, tracker, requests
from main import TaskApp
from textual.widgets import DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
cfg=tracker.load_config()
expected=tracker.fetch(cfg)
print(f"  the tracker reports {len(expected)}: {[(i.key,i.state) for i in expected][:3]} ...")

async def run(app):
    async with app.run_test(size=(140,45)) as pilot:
        for _ in range(500):
            await pilot.pause()
            if app.tasks and (app.tracker_issues or app.tracker_error): break
        for _ in range(150): await pilot.pause()
        return ([t.id for t in app.tasks], str(app.query_one("#status").content),
                [app.row_for(t) for t in app.tasks if app.is_tracker(t)], app)

print("\n5.1 the real issues, on top, in the configured order")
rows, st, trows, app = asyncio.run(run(TaskApp()))
yt=[r[len(M.TRACKER_PREFIX):] for r in rows if r.startswith(M.TRACKER_PREFIX)]
chk("exactly the issues the tracker reports",
    yt==[i.key for i in expected], f"{len(yt)} vs {len(expected)}")
_block=[M.TRACKER_PREFIX+k for k in yt]
chk("the block is contiguous, after the day's unfinished tasks",
    rows[rows.index(_block[0]):rows.index(_block[0])+len(_block)]==_block,
    str(rows[:2]))
chk("grouped by the configured state order",
    [cfg.rank(i.state) for i in expected]==sorted(cfg.rank(i.state) for i in expected))
chk("each row names its own state",
    [r[2] for r in trows]==[M._state_label(i.state) for i in expected],
    str(sorted(set(r[2] for r in trows))))
chk("the count is not named for a state",
    "tracked" in st and "in progress" not in st and "in review" not in st, st)
own=[r for r in rows if not r.startswith(M.TRACKER_PREFIX)]
chk("the task count is the tasks alone", f"{len(own)} task(s)" in st, st)

print("\n5.2 opening works for an issue in either state")
opened=[]
async def open_one(idx):
    a=TaskApp(); a.open_url=lambda u: opened.append(u)
    async with a.run_test(size=(140,45)) as pilot:
        for _ in range(500):
            await pilot.pause()
            if a.tasks and (a.tracker_issues or a.tracker_error): break
        for _ in range(150): await pilot.pause()
        t=a.query_one(DataTable)
        rowi=[i for i,x in enumerate(a.tasks) if a.is_tracker(x)][idx]
        t.move_cursor(row=rowi); await pilot.pause()
        await pilot.press("o"); await pilot.pause()
byst={}
for i,iss in enumerate(expected): byst.setdefault(iss.state, i)
for state, idx in byst.items():
    asyncio.run(open_one(idx))
    url=opened[-1]
    code=requests.get(url, headers={"Authorization": f"Bearer {cfg.token}"}, timeout=20).status_code
    chk(f"an issue in {state!r} opens and resolves", code==200, f"{url} -> {code}")

print("\n5.3 still unharmed with the tracker unreachable")
os.environ["YOUTRACK_BASE_URL"]="https://track.unreachable.invalid"
rows2, st2, _, _ = asyncio.run(run(TaskApp()))
chk("no tracker rows", not any(r.startswith(M.TRACKER_PREFIX) for r in rows2))
chk("the day's own tasks are the same", [r for r in rows2]==own, f"{len(rows2)} vs {len(own)}")
chk("and the board says it could not be reached", "could not reach the tracker" in st2, st2)
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
