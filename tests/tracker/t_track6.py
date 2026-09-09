"""Group 6 -- against the live tracker and the live API."""
import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import baseline
import sys, asyncio, json, os
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from datetime import datetime
import main as M, tracker
from main import TaskApp
from singularity import SingularityClient, Bucket
from textual.widgets import DataTable
api=SingularityClient(); TZ=api.tz; TODAY=datetime.now(TZ).date()
base=baseline.load(TZ)
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))

async def run(expect_tracker=True):
    app=TaskApp(TODAY)
    async with app.run_test(size=(140,45)) as pilot:
        for _ in range(400):
            await pilot.pause()
            if app.tasks and (app.tracker_issues or app.tracker_error is not None
                              or not expect_tracker): break
        for _ in range(120): await pilot.pause()
        # Tracker rows are kept -- this suite reasons about them by their
        # prefix -- but calendar and mail rows are not the board's own
        # tasks and were not there when this was written.  Counting them
        # against a capture of tasks made it fail by exactly the number
        # of events on the day.
        rows = [t.id for t in app.tasks
                if not (app.is_event(t) or app.is_mail(t))]
        return app, rows, str(app.query_one("#status").content)

print("6.1 the real issues appear under today")
cfg=tracker.load_config()
expected=[i.key for i in tracker.fetch(cfg)]
app, rows, st = asyncio.run(run())
shown=[r[len(M.TRACKER_PREFIX):] for r in rows if r.startswith(M.TRACKER_PREFIX)]
chk("the board shows exactly the issues the tracker reports",
    sorted(shown)==sorted(expected), f"{shown} vs {expected}")
own=[r for r in rows if not r.startswith(M.TRACKER_PREFIX)]
# compare like with like: prefixed ids on both sides
yt=[r for r in rows if r.startswith(M.TRACKER_PREFIX)]
# The block sits where the day's unfinished work ends, not at the top.
_at = rows.index(yt[0]) if yt else 0
chk("every issue is contiguous, wherever the block sits",
    rows[_at:_at+len(yt)]==yt, f"{len(own)} own, {len(yt)} issues")
# Filtered the same way `rows` is, or the positions below index into a
# list that no longer holds calendar rows.
_own_rows=[t for t in app.tasks if not (app.is_event(t) or app.is_mail(t))]
_live=[t.id for t in _own_rows
       if not app.is_tracker(t) and not (t.done or t.cancelled)]
_dead=[t.id for t in _own_rows
       if not app.is_tracker(t) and (t.done or t.cancelled)]
chk("the block follows every unfinished task",
    all(rows.index(i) < _at for i in _live), f"block at {_at}, {len(_live)} unfinished")
chk("and precedes every finished one",
    all(rows.index(i) > _at + len(yt) - 1 for i in _dead), f"{len(_dead)} finished")
chk("the day's own tasks match the capture", set(own)==set(base["today_ids"]),
    f"{len(own)} vs {len(base['today_ids'])}")
_green = [i for i in own if app.is_green(next(t for t in app.tasks if t.id==i))]
chk("and once the marked ones are set aside, in the same order",
    [i for i in own if i not in _green] == [i for i in base["today_ids"] if i not in _green],
    f"{len(_green)} marked")
chk("the task count is the tasks, not including issues",
    f"{len(own)} task(s)" in st, st)
if expected:
    chk("the issue count is reported", f"{len(expected)} tracked" in st, st)
chk("the past-due count is unchanged", f"{base['today_past_due']} past due" in st, st)

print("\n6.2 the board is unharmed with the tracker unreachable")
os.environ["YOUTRACK_BASE_URL"]="https://track.unreachable.invalid"
app2, rows2, st2 = asyncio.run(run())
own2=[r for r in rows2 if not r.startswith(M.TRACKER_PREFIX)]
chk("today's own tasks are identical", set(own2)==set(base["today_ids"]),
    f"{len(own2)} vs {len(base['today_ids'])}")
chk("no tracker rows", not [r for r in rows2 if r.startswith(M.TRACKER_PREFIX)])
chk("the board says the tracker could not be reached",
    "could not reach the tracker" in st2, st2)
chk("the message is short enough for a status line", len(st2) < 120, f"{len(st2)} chars")
chk("the past-due count still right", app2.past_due==base["today_past_due"], str(app2.past_due))
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
