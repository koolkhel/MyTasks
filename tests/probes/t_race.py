"""Which write settles first decides whether an undo entry survives.

A probe: it asserts nothing and prints what happened. It exists because
`t_undo1`'s check "the entry survives the one refusal" turned out to depend
on a race, and this is the instrument that showed it.

The scenario is `t_undo1` 1.2b -- one action writing four rows, one of them
refused -- run twice, with the refusal forced to settle first and then last.

    refusal first  ->  the entry is LOST
    refusal last   ->  the entry is kept

Both outcomes were identical on the commit before the change that made the
first ordering common, so the product loses an undo entry whenever a refusal
is processed before any of the action's other writes confirms. `forget()`
drops an entry when nothing of it has been applied, and at the first refusal
the rest of the group is still in flight, so "nothing was applied" is a
question it cannot answer yet. Its own docstring says the entry should go
only when nothing of it was applied.

Not a suite, because it has no right answer to assert: it shows a product
defect that wants its own change, and the fix belongs in the write
machinery -- a group's entry should be dropped only once every write in it
has settled.
"""
import asyncio, datetime as dt, sys
from time import sleep
import os as _os
# Where this probe is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import *
from main import TaskApp
from singularity import SingularityError

DAY = dt.datetime.now(TZ).date()
#: Long enough that the refusal certainly settles on the far side of the
#: others, and short enough that the probe finishes.
DAWDLE = 0.4


def ordered(task, value):
    task.raw["scheduleOrder"] = value
    return task


async def once(refusal_first: bool) -> int:
    """Run the scenario, and answer how many undo entries survived."""
    tasks = [ordered(mk(f"T-{i}", chr(97 + i) * 3, DAY), 100 + i)
             for i in range(4)]
    stub = StubClient(tasks)
    recorded = stub._record

    def paced(name, *args):
        # Whichever side is meant to lose the race dawdles.
        mine = bool(args) and args[0] == "T-2"
        if name == "set_schedule_order" and mine is not refusal_first:
            sleep(DAWDLE)
        return recorded(name, *args)

    stub._record = paced
    stub.fail_ids[("set_schedule_order", "T-2")] = SingularityError("transient")

    def set_order(tid, order):
        stub._record("set_schedule_order", tid, order)
        stub.store[tid].raw["scheduleOrder"] = order
        return stub.store[tid]

    stub.set_schedule_order = set_order
    app = TaskApp(DAY)
    app.client = stub
    async with app.run_test() as pilot:
        await pilot.pause()
        # One keypress, one action, four writes.
        await pilot.press("J")
        for _ in range(400):
            await pilot.pause()
            if not app._pending and not app._draining:
                break
        return len(app._undo)


async def main_():
    for first in (True, False):
        left = await once(refusal_first=first)
        print(f"  refusal settles {'first' if first else 'last ':<5}  ->  "
              f"{left} undo entr{'y' if left == 1 else 'ies'} left  "
              f"({'LOST' if not left else 'kept'})")
    print()
    print("  The two differ, and nothing but timing separates them.")


asyncio.run(main_())
