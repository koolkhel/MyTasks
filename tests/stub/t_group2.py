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
from datetime import date, datetime, timedelta
from collections import deque
import main as M
from main import TaskApp, Pending
from singularity import Task, CHECKED, CANCELLED

DAY = date(2099, 3, 1)
ok = []
def check(label, cond, extra=""):
    ok.append(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

async def run():
    tasks = [mk("T-a", "alpha", DAY), mk("T-b", "bravo", DAY), mk("T-c", "charlie", DAY)]
    app = TaskApp(DAY)
    stub = StubClient(tasks)
    app.client = stub
    async with app.run_test() as pilot:
        await pilot.pause()
        # ---- 2.1 applying and dropping a record ----
        print("2.1 pending record applies and reverts")
        base = app._base[0]
        before_title, before_checked = base.title, base.checked
        pend = Pending(task_id=base.id, label="x", run=lambda tid: None,
                       patch={"title": "renamed", "checked": CHECKED},
                       previous={k: base.raw.get(k) for k in ("title", "checked")})
        app._pending[base.id] = deque([pend])
        got = {t.id: t for t in app.patched()}[base.id]
        check("patched Task reads the new title", got.title == "renamed", got.title)
        check("patched Task reads done", got.done is True)
        check("the fetched task itself is untouched",
              app._base[0].title == before_title and app._base[0].checked == before_checked)
        app._pending.pop(base.id)
        got = {t.id: t for t in app.patched()}[base.id]
        check("dropping the record restores the originals",
              got.title == before_title and got.checked == before_checked)

        # ---- 2.2 per-task queues ----
        print("2.2 per-task queues")
        app._pending.clear()
        p1 = Pending("T-a", "one", lambda tid: None)
        p2 = Pending("T-a", "two", lambda tid: None)
        p3 = Pending("T-b", "three", lambda tid: None)
        for p in (p1, p2, p3):
            app._pending.setdefault(p.task_id, deque()).append(p)
        check("two ids queue independently",
              list(app._pending) == ["T-a", "T-b"] and len(app._pending["T-a"]) == 2)
        check("one id keeps insertion order",
              [p.label for p in app._pending["T-a"]] == ["one", "two"])
        check("in-flight is answered per task",
              bool(app._pending.get("T-a")) and not app._pending.get("T-zz"))
        app._pending.clear()

        # ---- 2.3 derivations run over the patched tasks ----
        print("2.3 ordering and counts come from the patched view")
        app._selected_id = "T-a"
        app._pending["T-a"] = deque([Pending("T-a", "tick", lambda tid: None,
                                             patch={"checked": CHECKED})])
        app.repaint()
        ids = [t.id for t in app.tasks]
        check("a patched-done task sorts into the finished group",
              ids[-1] == "T-a", str(ids))
        done_rows = sum(1 for t in app.tasks if t.done)
        status = str(app.query_one("#status").content)
        check("reported done count agrees with the rows",
              f"{done_rows} done" in status, status)
        check("row count agrees", f"{len(app.tasks)} task(s)" in status, status)
        app._pending.clear(); app.repaint()

        # ---- 2.4 an orphan patch keeps no row alive ----
        print("2.4 a patch is never a reason for a row to exist")
        app._pending.clear()
        before = len(app.tasks)
        app._pending["T-does-not-exist"] = deque([
            Pending("T-does-not-exist", "ghost", lambda tid: None,
                    patch={"title": "ghost", "checked": 0})])
        app.repaint()
        check("no row appears for an id absent from the base",
              len(app.tasks) == before
              and not any(t.id == "T-does-not-exist" for t in app.tasks),
              f"{before} -> {len(app.tasks)}")
        app._pending.clear(); app.repaint()

async def run_pastdue():
        print("2.3b past-due is re-derived over the patched tasks")
        now = datetime.now(TZ)
        today = now.date()
        late = [mk("T-late1", "late one", today - timedelta(days=3)),
                mk("T-late2", "late two", today - timedelta(days=1)),
                mk("T-today", "todays", today)]
        app2 = TaskApp(today)
        app2.tracker_config=None   # the tracker is not the subject here
        s2 = StubClient(late, reference=now)
        app2.client = s2
        async with app2.run_test() as p2i:
            await p2i.pause()
            check("two rows start past due", app2.past_due == 2, f"past_due={app2.past_due}")
            app2._selected_id = "T-late1"
            # ticking a past-due task must drop it out of the past-due count
            app2._pending["T-late1"] = deque([Pending("T-late1", "tick",
                                    lambda tid: None, patch={"checked": CHECKED})])
            app2.repaint()
            check("ticking a late task lowers the past-due count",
                  app2.past_due == 1, f"past_due={app2.past_due}")
            marked = sum(1 for t in app2.tasks
                         if t.past_due_since(app2.reference, app2.tz))
            check("the count agrees with the rows on screen",
                  marked == app2.past_due, f"{marked} vs {app2.past_due}")
            st = str(app2.query_one("#status").content)
            check("and with what is reported", "1 past due" in st, st)

asyncio.run(run())
asyncio.run(run_pastdue())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
