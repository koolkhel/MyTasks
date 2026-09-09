"""Every write the board makes, against the live store: shown at once, then agreed.

Rewritten after the original was lost from the scratchpad mid-import, from
the check names and values its last run recorded.  A new suite under an old
name: its code cannot be compared against the original's, because the
original is gone.  The 21 check names are reproduced from that record.

Works on a far-future probe day, names its tasks so they are recognisable,
and deletes them in a `finally`.
"""
import asyncio
import os
import sys
import time
from datetime import date, datetime, timedelta
from datetime import time as _t

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)          # the shared support beside the suites
sys.path.insert(0, _REPO)           # the board itself
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt()
from main import TaskApp
from singularity import (SingularityClient, iso_z, CHECKED, CANCELLED, EMPTY)
from textual.widgets import DataTable

api = SingularityClient()
TZ = api.tz
DAY = date(2099, 5, 3)
#: The picker's "tomorrow" and done-for-today both move a task relative to
#: the real today, not to whichever day the board is showing -- so a probe
#: day far in the future lands here, and this is where to look for it and to
#: clean up after it.
TODAY = datetime.now(TZ).date()
TOMORROW = TODAY + timedelta(days=1)
P = "zz-probe-"
ok = []


def check(l, c, e=""):
    ok.append(bool(c))
    print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))


def ours(day):
    return [t for t in api.tasks_for_day(day).tasks if t.title.startswith(P)]


def seed(name, order):
    return api.create_task(
        f"{P}{name}",
        start=iso_z(datetime.combine(DAY, _t.min, tzinfo=TZ)),
        useTime=False, scheduleOrder=order)


def cleanup():
    n = 0
    for day in (DAY, TODAY, TOMORROW):
        for t in ours(day):
            for _ in range(5):
                try:
                    api.delete_task(t.id)
                    n += 1
                    break
                except Exception:
                    time.sleep(1.5)
    return n


async def ready(app, pilot):
    for _ in range(400):
        await pilot.pause()
        if app._fetched and app.tasks:
            break
    for _ in range(20):
        await pilot.pause()


async def quiet(app, pilot, tries=400):
    for _ in range(tries):
        await pilot.pause()
        if not app._pending and not app._draining:
            return True
    return False


def on_screen(app, task_id):
    """The row as drawn, which is where a write shows before it is confirmed.

    `_base` holds what the store last said; the pending patches are applied
    when the table is rebuilt, so `tasks` is the only place an optimistic
    write is visible.  Looking in `_base` reports the change only once the
    store has agreed, which is the opposite of what is being checked.
    """
    return next((t for t in app.tasks if t.id == task_id), None)


async def until(app, pilot, predicate, tries=60):
    """Pause until the predicate holds, answering whether it ever did."""
    for _ in range(tries):
        await pilot.pause()
        if predicate():
            return True
    return False


async def dialog(app, pilot, text):
    """Fill the open prompt and accept it, once it is actually there."""
    await until(app, pilot, lambda: app.screen.query("#dialog-input"))
    app.screen.query_one("#dialog-input").value = text
    await pilot.pause()
    await pilot.press("enter")
    for _ in range(6):
        await pilot.pause()


async def select(app, pilot, task_id):
    row = next(i for i, t in enumerate(app.tasks) if t.id == task_id)
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = task_id
    await pilot.pause()


async def run():
    cleanup()
    probes = {n: seed(n, i * 1000)
              for i, n in enumerate(("tick", "cancel", "rename", "date",
                                     "today", "delete"), 1)}

    app = TaskApp(DAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        await ready(app, pilot)
        check("the day shows the six probes",
              len([t for t in app.tasks if t.title.startswith(P)]) == 6,
              f"{len([t for t in app.tasks if t.title.startswith(P)])} rows")

        # -- tick, then untick -------------------------------------------
        await select(app, pilot, probes["tick"].id)
        await pilot.press("space")
        # Polled for the first frame in which the row reads as ticked, and
        # the queue inspected at that instant.  A fixed number of pauses
        # cannot express this: too few and the key has not been dispatched,
        # too many and the store has already answered -- and then the check
        # passes whether the board is optimistic or merely quick.
        optimistic = False
        for _ in range(60):
            await pilot.pause()
            shown = on_screen(app, probes["tick"].id)
            if shown is not None and shown.done:
                optimistic = probes["tick"].id in app._pending
                break
        check("tick is on screen before the API answered", optimistic)
        await quiet(app, pilot)
        check("server agrees the task is complete",
              api.get_task(probes["tick"].id).raw.get("checked") == CHECKED,
              f"checked={api.get_task(probes['tick'].id).raw.get('checked')}")
        await select(app, pilot, probes["tick"].id)
        await pilot.press("space")
        await quiet(app, pilot)
        check("server agrees it is open again",
              api.get_task(probes["tick"].id).raw.get("checked") == EMPTY,
              f"checked={api.get_task(probes['tick'].id).raw.get('checked')}")

        # -- cancel -------------------------------------------------------
        await select(app, pilot, probes["cancel"].id)
        await pilot.press("x")
        cancelled = False
        for _ in range(60):
            await pilot.pause()
            shown = on_screen(app, probes["cancel"].id)
            if shown is not None and shown.cancelled:
                cancelled = probes["cancel"].id in app._pending
                break
        check("cancel is on screen at once", cancelled)
        await quiet(app, pilot)
        check("server agrees it is cancelled",
              api.get_task(probes["cancel"].id).raw.get("checked") == CANCELLED,
              f"checked={api.get_task(probes['cancel'].id).raw.get('checked')}")

        # -- rename -------------------------------------------------------
        await select(app, pilot, probes["rename"].id)
        await pilot.press("e")
        await dialog(app, pilot, f"{P}renamed")
        renamed = await until(app, pilot, lambda: (
            (on_screen(app, probes["rename"].id) or probes["rename"]).title
            == f"{P}renamed"))
        shown = [t.title for t in app.tasks if t.id == probes["rename"].id]
        check("rename is on screen at once", renamed and shown == [f"{P}renamed"],
              str(shown))
        await quiet(app, pilot)
        check("server agrees the title changed",
              api.get_task(probes["rename"].id).title == f"{P}renamed",
              api.get_task(probes["rename"].id).title)

        # -- a date, through the picker -----------------------------------
        before = len([t for t in app.tasks if t.title.startswith(P)])
        await select(app, pilot, probes["date"].id)
        await pilot.press("d")
        for _ in range(10):
            await pilot.pause()
        await pilot.press("m")            # tomorrow; "t" is today
        for _ in range(8):
            await pilot.pause()
        now = len([t for t in app.tasks if t.title.startswith(P)])
        check("the row leaves the day at once", now == before - 1, str(now))
        await quiet(app, pilot)
        moved = api.get_task(probes["date"].id)
        check("server has it on tomorrow, as the picker offered",
              moved.local_start(TZ).date() == TOMORROW,
              f"{moved.local_start(TZ).date()} vs {TOMORROW}")

        # -- done for today -----------------------------------------------
        before = len([t for t in app.tasks if t.title.startswith(P)])
        await select(app, pilot, probes["today"].id)
        await pilot.press("full_stop")
        for _ in range(8):
            await pilot.pause()
        check("the row leaves the day at once",
              len([t for t in app.tasks if t.title.startswith(P)]) == before - 1)
        await quiet(app, pilot)
        did = api.get_task(probes["today"].id)
        check("server has it on tomorrow",
              did.local_start(TZ).date() == TOMORROW, str(did.local_start(TZ).date()))
        check("and it is still unfinished", not did.done and not did.cancelled)
        check("no failure was reported despite the refused record",
              "failed" not in str(app.query_one("#status").content).lower(),
              str(app.query_one("#status").content))

        # -- add -----------------------------------------------------------
        await pilot.press("a")
        await dialog(app, pilot, f"{P}added")
        check("the new row appears under a placeholder id",
              any(t.id.startswith("tmp:") for t in app._base),
              str([t.id[:13] for t in app._base]))
        await quiet(app, pilot)
        check("no placeholder survives",
              not any(t.id.startswith("tmp:") for t in app._base))
        added = [t for t in ours(DAY) if t.title == f"{P}added"]
        check("server has the new task on the day", len(added) == 1, f"{len(added)} found")
        check("the board adopted the server's id",
              bool(added) and any(t.id == added[0].id for t in app._base),
              added[0].id if added else "-")

        # -- delete ---------------------------------------------------------
        await select(app, pilot, probes["delete"].id)
        await pilot.press("backspace")
        for _ in range(10):
            await pilot.pause()
        await pilot.press("y")
        for _ in range(8):
            await pilot.pause()
        check("the row goes at once",
              not any(t.id == probes["delete"].id for t in app.tasks))
        await quiet(app, pilot)
        gone = False
        try:
            api.get_task(probes["delete"].id)
        except Exception:
            gone = True
        check("server 404s the deleted task", gone)


try:
    asyncio.run(run())
finally:
    cleanup()
    left = [t.title for t in ours(DAY)] + [t.title for t in ours(TOMORROW)]
    check("nothing of ours is left behind on the probe day", left == [], str(left))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
