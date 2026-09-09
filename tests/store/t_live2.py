"""A hand-set sequence survives the store: moving, reloading, refetching.

Rewritten after the original was lost from the scratchpad mid-import, from
the check names and values its last run recorded.  A new suite under an old
name: its code cannot be compared against the original's, because the
original is gone.  The 9 check names are reproduced from that record, and its
recorded sequences are what this asserts.
"""
import asyncio
import os
import sys
import time
from datetime import date, datetime
from datetime import time as _t

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)          # the shared support beside the suites
sys.path.insert(0, _REPO)           # the board itself
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt()
from main import TaskApp
from singularity import SingularityClient, iso_z, sort_for_display
from textual.widgets import DataTable

api = SingularityClient()
TZ = api.tz
DAY = date(2099, 7, 7)
P = "zz-live2-"
NAMES = list("abcde")
ok = []


def check(l, c, e=""):
    ok.append(bool(c))
    print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))


def ours():
    return [t for t in api.tasks_for_day(DAY).tasks if t.title.startswith(P)]


def cleanup():
    n = 0
    for t in ours():
        for _ in range(5):
            try:
                api.delete_task(t.id)
                n += 1
                break
            except Exception:
                time.sleep(1.5)
    return n


def letters(tasks):
    """The one-letter names, in the order given."""
    return [t.title[len(P):] for t in tasks if t.title.startswith(P)]


async def ready(app, pilot):
    for _ in range(400):
        await pilot.pause()
        if app._fetched and app.tasks:
            break
    for _ in range(20):
        await pilot.pause()


async def quiet(app, pilot, tries=500):
    for _ in range(tries):
        await pilot.pause()
        if not app._pending and not app._draining:
            return True
    return False


async def select(app, pilot, task_id):
    row = next(i for i, t in enumerate(app.tasks) if t.id == task_id)
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = task_id
    await pilot.pause()


async def walk(app, pilot, task_id, key, times):
    """Move one task with K or J, waiting for each write to land."""
    for _ in range(times):
        await select(app, pilot, task_id)
        await pilot.press(key)
        await quiet(app, pilot)
        for _ in range(6):
            await pilot.pause()


async def run():
    cleanup()
    seeded = {n: api.create_task(
        f"{P}{n}", start=iso_z(datetime.combine(DAY, _t.min, tzinfo=TZ)),
        useTime=False, scheduleOrder=i * 1000)
        for i, n in enumerate(NAMES)}

    app = TaskApp(DAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        await ready(app, pilot)
        check("6.1 starts a,b,c,d,e", letters(app.tasks) == NAMES,
              str(letters(app.tasks)))

        # 'e' to the top: four moves up.
        await walk(app, pilot, seeded["e"].id, "K", 4)
        check("6.1 'e' walked to the top",
              letters(app.tasks) == ["e", "a", "b", "c", "d"],
              str(letters(app.tasks)))

        # 'a' to the bottom: four moves down from where it now sits.
        await walk(app, pilot, seeded["a"].id, "J", 4)
        moved = ["e", "b", "c", "d", "a"]
        check("6.1 'a' walked to the bottom", letters(app.tasks) == moved,
              str(letters(app.tasks)))

        app.load()
        await ready(app, pilot)
        check("6.1 the sequence survives a reload", letters(app.tasks) == moved,
              str(letters(app.tasks)))

        # away to another day and back
        await pilot.press("l")
        for _ in range(120):
            await pilot.pause()
        await pilot.press("h")
        for _ in range(400):
            await pilot.pause()
            if app._fetched and app.tasks:
                break
        for _ in range(20):
            await pilot.pause()
        check("6.1 and leaving the day and returning", letters(app.tasks) == moved,
              str(letters(app.tasks)))

    print("6.2 the store itself, not the board's copy")
    fresh = api.tasks_for_day(DAY).tasks
    check("6.2 a fresh fetch gives the moved sequence", letters(fresh) == moved,
          str(letters(fresh)))
    by_order = sorted(ours(), key=lambda t: t.schedule_order)
    check("6.2 sorting by stored order alone gives the same",
          letters(by_order) == moved, str(letters(by_order)))
    orders = [t.schedule_order for t in by_order]
    check("6.2 every stored order is distinct",
          len(set(orders)) == len(orders), str(orders))


try:
    asyncio.run(run())
finally:
    cleanup()
    check("nothing left behind", ours() == [], str([t.title for t in ours()]))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
