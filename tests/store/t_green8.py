"""Mark-then-unmark, many times, through the board. Synthetic tasks, deleted."""
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
api = singularity.SingularityClient(); G = api.green
TODAY = datetime.now(api.tz).date()
def tags(tid):
    r = api.get(f"/task/{tid}")
    t = r.get("task") if isinstance(r, dict) and "task" in r else r
    return t.get("tags")

async def one(tid):
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        for _ in range(700):
            await pilot.pause()
            if any(t.id == tid for t in app.tasks) and app.green_checked: break
        app._selected_id = tid; app.repaint(); await pilot.pause()
        t0 = _t.monotonic()
        await pilot.press("g")                    # mark
        await pilot.pause()
        app._selected_id = tid
        await pilot.press("g")                    # unmark, straight after
        for _ in range(1500):
            await pilot.pause()
            if not app._pending and not app._draining: break
        return _t.monotonic() - t0

good = bad = 0; times = []
N = 10
for i in range(1, N + 1):
    task = api.create_task(f"zz-rel-{i}", start=singularity.iso_z(
        datetime.combine(TODAY, datetime.min.time(), tzinfo=api.tz)))
    try:
        took = asyncio.run(one(task.id))
        for _ in range(20):
            if tags(task.id) == []: break
            _t.sleep(0.5)
        ok = tags(task.id) == []
        good += ok; bad += not ok; times.append(took)
        print(f"  {i:2}/{N}  {'ok ' if ok else 'LEFT MARKED'}  ({took:.1f}s)")
    finally:
        api.delete_task(task.id)
    _t.sleep(2)
print(f"\n  {good}/{N} ended unmarked upstream"
      f"   median pair {sorted(times)[len(times)//2]:.1f}s  slowest {max(times):.1f}s")
sys.exit(0 if bad == 0 else 1)
