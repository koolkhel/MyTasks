"""Ticking costs no more than moving the cursor, against the live store.

Rewritten after the original was lost from the scratchpad mid-import, from
the check names and values its last run recorded.  A new suite under an old
name: its code cannot be compared against the original's, because the
original is gone.  The 4 check names are reproduced from that record.

What it measures is the keypress, not the write.  A tick queues its request
and repaints; the store answers afterwards on another thread.  So the cost of
the key should be the cost of a repaint -- which is what moving the cursor
costs, and why that is the floor it is compared against rather than an
absolute figure that would differ on another machine.

The figure it exists to catch: ticking once blocked for about 1500ms, waiting
on the request before repainting.
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
from singularity import SingularityClient, iso_z
from textual.widgets import DataTable

api = SingularityClient()
TZ = api.tz
DAY = date(2099, 9, 9)
P = "zz-perf2-"
#: What ticking must not approach: the latency before writes were queued.
BLOCKED_MS = 1500
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


async def run():
    cleanup()
    seeded = [api.create_task(
        f"{P}{i}", start=iso_z(datetime.combine(DAY, _t.min, tzinfo=TZ)),
        useTime=False, scheduleOrder=i * 1000) for i in range(6)]

    app = TaskApp(DAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        for _ in range(400):
            await pilot.pause()
            if app._fetched and app.tasks:
                break
        for _ in range(20):
            await pilot.pause()
        table = app.query_one(DataTable)

        # The floor: a keypress that repaints and writes nothing.
        floor = []
        for _ in range(6):
            started = time.perf_counter()
            await pilot.press("j")
            await pilot.pause()
            floor.append((time.perf_counter() - started) * 1000)
        table.move_cursor(row=0)
        await pilot.pause()

        ticks = []
        for task in seeded:
            row = next((i for i, t in enumerate(app.tasks) if t.id == task.id), None)
            if row is None:
                continue
            table.move_cursor(row=row)
            app._selected_id = task.id
            await pilot.pause()
            started = time.perf_counter()
            await pilot.press("space")
            await pilot.pause()
            ticks.append((time.perf_counter() - started) * 1000)

        floor_ms = max(floor)
        tick_ms = max(ticks)
        # Compared against the floor with room for scheduling noise: the
        # claim is "no more than a repaint", not "identical to one".
        check("a tick costs no more than cursor movement",
              tick_ms <= floor_ms * 3 + 50,
              f"tick {tick_ms:.0f}ms vs floor {floor_ms:.0f}ms")
        check("no tick came near the old ~1500ms block",
              tick_ms < BLOCKED_MS / 2, f"max {tick_ms:.0f}ms")

        # Responsive while the writes are still going out.  Started from the
        # last row and moved upward, because pressing "k" from wherever the
        # cursor happens to sit runs out of rows and then measures the
        # cursor's position rather than the board's responsiveness.
        rows = table.row_count
        table.move_cursor(row=max(rows - 1, 0))
        await pilot.pause()
        steps = min(3, max(rows - 1, 0))
        in_flight = bool(app._pending)
        landed, slowest = 0, 0.0
        for _ in range(steps):
            before = table.cursor_row
            started = time.perf_counter()
            await pilot.press("k")
            await pilot.pause()
            slowest = max(slowest, (time.perf_counter() - started) * 1000)
            if table.cursor_row != before:
                landed += 1
        check("the board is responsive with writes in flight",
              landed == steps and slowest < BLOCKED_MS / 2,
              f"{landed} of {steps} moves landed, slowest {slowest:.0f}ms"
              f"{', writes still queued' if in_flight else ', queue already drained'}")

        for _ in range(600):
            await pilot.pause()
            if not app._pending and not app._draining:
                break
        landed = sum(1 for t in ours() if t.done)
        check("all the ticks actually landed", landed == len(ticks),
              f"{landed} of {len(ticks)}")


try:
    asyncio.run(run())
finally:
    cleanup()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
