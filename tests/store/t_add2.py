"""What stored order a created task gets, against the live store.

Rewritten after the original was lost from the scratchpad mid-import, from
the check names and values its last run recorded.  A new suite under an old
name: its code cannot be compared against the original's, because the
original is gone.  The 13 check names are reproduced from that record.

Works on a far-future day of its own so it cannot disturb a real one, names
everything it creates so it is recognisable, and deletes it in a `finally`.
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
from singularity import SingularityClient, Bucket, iso_z

api = SingularityClient()
TZ = api.tz
DAY = date(2099, 4, 2)
P = "zz-add2-"
ok = []


def check(l, c, e=""):
    ok.append(bool(c))
    print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))


def made(day=DAY):
    return [t for t in api.tasks_for_day(day).tasks if t.title.startswith(P)]


def seed(name, order):
    return api.create_task(
        f"{P}{name}",
        start=iso_z(datetime.combine(DAY, _t.min, tzinfo=TZ)),
        useTime=False, scheduleOrder=order)


def cleanup():
    n = 0
    for where in (made(), [t for t in api.tasks_at(Bucket.INBOX).tasks
                           if t.title.startswith(P)]):
        for t in where:
            for _ in range(5):
                try:
                    api.delete_task(t.id)
                    n += 1
                    break
                except Exception:
                    time.sleep(1.5)
    return n


async def add_on(position, title):
    """Add a task through the board, on whichever view it is showing."""
    app = TaskApp(position if not isinstance(position, Bucket) else DAY)
    async with app.run_test(size=(120, 40)) as pilot:
        if isinstance(position, Bucket):
            app.position = position
        app.load()
        for _ in range(300):
            await pilot.pause()
            if app._fetched:
                break
        for _ in range(20):
            await pilot.pause()
        await pilot.press("a")
        for _ in range(10):
            await pilot.pause()
        app.screen.query_one("#dialog-input").value = title
        await pilot.pause()
        await pilot.press("enter")
        for _ in range(400):
            await pilot.pause()
            if not app._pending and not app._draining:
                break
        for _ in range(20):
            await pilot.pause()


async def run():
    cleanup()

    print("a task added to a day whose orders are already set")
    for i, name in enumerate(("one", "two", "three"), 1):
        seed(name, i * 1000)
    held = sorted(t.schedule_order for t in made())
    await add_on(DAY, f"{P}fourth")
    fourth = [t for t in made() if t.title.endswith("fourth")]
    check("the task was created", len(fourth) == 1, f"{len(fourth)} found")
    check("its stored order exceeds all three existing",
          bool(fourth) and fourth[0].schedule_order > max(held),
          str(fourth[0].schedule_order if fourth else None))
    order = sorted(made(), key=lambda t: t.schedule_order)
    check("it is last in the day's order",
          bool(order) and order[-1].title.endswith("fourth"))
    check("the existing three did not move",
          sorted(t.schedule_order for t in made()
                 if not t.title.endswith("fourth")) == held, str(held))

    await add_on(DAY, f"{P}fifth")
    fifth = [t for t in made() if t.title.endswith("fifth")]
    check("their stored orders differ",
          bool(fifth) and bool(fourth) and fifth[0].schedule_order != fourth[0].schedule_order,
          f"{fourth[0].schedule_order if fourth else '-'} vs "
          f"{fifth[0].schedule_order if fifth else '-'}")
    check("the second sorts after the first",
          bool(fifth) and bool(fourth) and fifth[0].schedule_order > fourth[0].schedule_order,
          f"{fourth[0].schedule_order if fourth else '-'} then "
          f"{fifth[0].schedule_order if fifth else '-'}")
    orders = sorted(t.schedule_order for t in made())
    check("every order on the day is distinct",
          len(set(orders)) == len(orders), str(orders))

    print("a task added to a day that holds nothing")
    cleanup()
    check("the day starts empty", len(made()) == 0, str(len(made())))
    await add_on(DAY, f"{P}only")
    only = made()
    check("the task was created", len(only) == 1)
    check("it carries the order the board chose, not 0",
          bool(only) and only[0].schedule_order != 0,
          str(only[0].schedule_order if only else None))

    print("a task added to the inbox")
    cleanup()
    await add_on(Bucket.INBOX, f"{P}unfiled")
    inbox = [t for t in api.tasks_at(Bucket.INBOX).tasks if t.title.startswith(P)]
    check("the task was created in the inbox", len(inbox) == 1, f"{len(inbox)} found")
    check("its stored order is the API's own default of 0",
          bool(inbox) and inbox[0].schedule_order == 0,
          str(inbox[0].schedule_order if inbox else None))


try:
    asyncio.run(run())
finally:
    removed = cleanup()
    left = [t.title for t in made()]
    left += [t.title for t in api.tasks_at(Bucket.INBOX).tasks
             if t.title.startswith(P)]
    print(f"cleanup: {removed} removed")
    check("nothing left behind", left == [], str(left))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
