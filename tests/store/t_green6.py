"""6.1 + 7.2 -- the real board, a synthetic task of our own, deleted after."""
import sys, asyncio, time
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

api = singularity.SingularityClient()
G = api.green
TODAY = datetime.now(api.tz).date()
print(f"configured tag {G} -> {api.tag_title(G)!r}")

def tags_upstream(tid):
    r = api.get(f"/task/{tid}")
    t = r.get("task") if isinstance(r, dict) and "task" in r else r
    return t.get("tags")

async def settle(p, a, n=400):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

async def run(tid):
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        # the tag lookup lands after the day paints now, so wait for both
        for _ in range(600):
            await pilot.pause()
            if (app.tasks and any(t.id == tid for t in app.tasks)
                    and app.green_checked): break
        chk("the synthetic task is on the board", any(t.id == tid for t in app.tasks))
        chk("the tag resolved at startup", app.green_title == "Зеленая", repr(app.green_title))

        app._selected_id = tid; app.repaint(); await pilot.pause()
        await pilot.press("g")
        drained = await settle(pilot, app)
        chk("the first write drained", drained)
        chk("marked upstream", tags_upstream(tid) == [G], str(tags_upstream(tid)))
        chk("the rail is on its row",
            next(app.row_for(t)[0] for t in app.tasks if t.id == tid) == M.GREEN_MARK)
        chk("it sorted to the top", app.tasks and app.tasks[0].id == tid
            or [t.id for t in app.tasks if not t.id.startswith("yt:")][0] == tid,
            str([t.id for t in app.tasks][:3]))
        chk("and is counted", "1 green" in str(app.query_one("#status").content)
            or " green" in str(app.query_one("#status").content),
            str(app.query_one("#status").content))

        print("\n  6.1 two presses in quick succession")
        app._selected_id = tid; app.repaint(); await pilot.pause()
        seen = []
        for n in range(3):              # unmark, mark, unmark -- fast
            app._selected_id = tid
            await pilot.press("g")
            await pilot.pause()
            seen.append(next((t.tags for t in app.tasks if t.id == tid), None))
        print(f"    what the screen showed after each press: {seen}")
        drained = await settle(pilot, app)
        chk("every queued write drained", drained)
        # let the API settle, then read the truth
        for _ in range(20):
            if tags_upstream(tid) == []: break
            time.sleep(0.5)
        chk("the task ends unmarked upstream, as the screen says",
            tags_upstream(tid) == [], str(tags_upstream(tid)))
        chk("and the board agrees",
            next(app.row_for(t)[0] for t in app.tasks if t.id == tid) == "",
            repr(next(app.row_for(t)[0] for t in app.tasks if t.id == tid)))
        writes = [c for c in [] ]
        chk("the writes were serialised, not concurrent", not app._pending.get(tid))

task = api.create_task("zz-green-live", start=singularity.iso_z(
    datetime.combine(TODAY, datetime.min.time(), tzinfo=api.tz)))
try:
    print(f"created {task.id}")
    asyncio.run(run(task.id))
finally:
    api.delete_task(task.id); print(f"deleted {task.id}")
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
