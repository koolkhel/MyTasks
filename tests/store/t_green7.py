"""6.2 -- mark then unmark, through the board, against the live store."""
import sys, asyncio, time as _t
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from datetime import datetime
import main as M, singularity
from main import TaskApp
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
api = singularity.SingularityClient(); G = api.green
TODAY = datetime.now(api.tz).date()
def tags(tid):
    r = api.get(f"/task/{tid}")
    t = r.get("task") if isinstance(r, dict) and "task" in r else r
    return t.get("tags")

async def settle(p, a, n=900):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

async def one(tid, trial):
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        for _ in range(600):
            await pilot.pause()
            if any(t.id == tid for t in app.tasks) and app.green_checked: break
        app._selected_id = tid; app.repaint(); await pilot.pause()
        t0 = _t.monotonic()
        await pilot.press("g")               # mark
        await pilot.pause()
        app._selected_id = tid
        await pilot.press("g")               # unmark, at once
        await pilot.pause()
        gone = next(app.row_for(t)[0] for t in app.tasks if t.id == tid) == ""
        answered = app.query_one("#status") is not None
        drained = await settle(pilot, app)
        took = _t.monotonic() - t0
        chk(f"trial {trial}: the rail went at once, before the write", gone)
        chk(f"trial {trial}: the board kept answering while it waited", answered)
        chk(f"trial {trial}: every write drained", drained)
        for _ in range(20):
            if tags(tid) == []: break
            _t.sleep(0.5)
        chk(f"trial {trial}: unmarked where the tasks are kept", tags(tid) == [], str(tags(tid)))
        print(f"        (the pair took {took:.1f}s)")

for trial in (1, 2, 3):
    task = api.create_task(f"zz-green-wait-{trial}", start=singularity.iso_z(
        datetime.combine(TODAY, datetime.min.time(), tzinfo=api.tz)))
    try:
        asyncio.run(one(task.id, trial))
    finally:
        api.delete_task(task.id)
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
