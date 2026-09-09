"""Adding a task: shown at once, the id traded, a refusal taken back.

Rewritten after the original was lost from the scratchpad mid-import, from
the check names and values its last run recorded.  It is therefore a new
suite under an old name: unlike every other suite here, it cannot be compared
against how the original behaved, because the original is gone.  The 18 check
names below are reproduced from that record.
"""
import asyncio
import os
import sys
import threading
import uuid
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from harness import StubClient, mk, TZ
import main as M
from main import TaskApp
from singularity import SingularityError
from textual.widgets import DataTable

DAY = date(2099, 3, 1)
ok = []


def check(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))


def rows(app):
    return [t.id for t in app.tasks]


def titles(app):
    return [t.title for t in app.tasks]


def status(app):
    return str(app.query_one("#status").content)


async def settle(pilot, app, tries=80):
    for _ in range(tries):
        await pilot.pause()
        if not app._pending and not app._draining:
            return True
    return False


async def type_title(pilot, app, text):
    """Press a, type a title, and accept it."""
    await pilot.press("a")
    for _ in range(8):
        await pilot.pause()
    screen = app.screen
    screen.query_one("#dialog-input").value = text
    await pilot.pause()
    await pilot.press("enter")
    for _ in range(6):
        await pilot.pause()


# ------------------------------------------------- shown before the answer
async def t_optimistic():
    print("the row is there before the store answers")
    app = TaskApp(DAY)
    stub = StubClient([mk("T-a", "alpha", DAY)])
    app.client = stub
    stub.gate = threading.Event()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await type_title(pilot, app, "zeta task")
        check("the new row is there before the API answered",
              len(rows(app)) == 2 and any(r.startswith("tmp:") for r in rows(app)),
              str(rows(app)))
        check("with the typed title", titles(app), str(titles(app)))
        check("counts include it", "2 task(s)" in status(app) and "saving" in status(app),
              status(app))
        placeholder = next(r for r in rows(app) if r.startswith("tmp:"))
        check("it is selected", app._selected_id == placeholder, str(app._selected_id))

        stub.gate.set()
        await settle(pilot, app)
        check("no placeholder id survives",
              not any(r.startswith("tmp:") for r in rows(app)), str(rows(app)))
        check("the server's id was adopted",
              any(r.startswith("T-new-") for r in rows(app)), str(rows(app)))
        real = next(r for r in rows(app) if r.startswith("T-new-"))
        check("selection followed to the real id", app._selected_id == real,
              str(app._selected_id))
        check("the title is still right", titles(app), str(titles(app)))


# ------------------------------------- a write queued behind the creation
async def t_queued_behind():
    print("a write queued behind a creation reaches the real id")
    app = TaskApp(DAY)
    stub = StubClient([])
    app.client = stub
    stub.gate = threading.Event()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await type_title(pilot, app, "first")
        placeholder = next(r for r in rows(app) if r.startswith("tmp:"))
        # Rename it while the creation is still in flight.
        await pilot.press("e")
        for _ in range(8):
            await pilot.pause()
        app.screen.query_one("#dialog-input").value = "second"
        await pilot.pause()
        await pilot.press("enter")
        for _ in range(6):
            await pilot.pause()
        check("both queued under the placeholder",
              {k: len(v) for k, v in app._pending.items()},
              str({k[:9]: len(v) for k, v in app._pending.items()}))
        check("the rename shows at once", titles(app), str(titles(app)))

        stub.gate.set()
        await settle(pilot, app)
        created = [a for c, a in stub.calls if c == "create_task"]
        check("the creation was sent once", len(created) == 1, str(created))
        renamed = [a for c, a in stub.calls if c == "update_task"]
        check("the rename was sent to the REAL id, not the placeholder",
              bool(renamed) and not renamed[0][0].startswith("tmp:"), str(renamed))
        check("and the stored title is the renamed one", titles(app), str(titles(app)))
        check("nothing is left pending", not app._pending, str(app._pending))


# ------------------------------------------------------- a refused creation
async def t_refused():
    print("a refused creation takes its row back and says so")
    app = TaskApp(DAY)
    stub = StubClient([mk("T-a", "alpha", DAY)])
    app.client = stub
    stub.fail["create_task"] = SingularityError("no room")
    # Held open, or the refusal lands before the row can be looked at.
    stub.gate = threading.Event()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await type_title(pilot, app, "doomed")
        check("the row is shown first",
              len(rows(app)) == 2 and any(r.startswith("tmp:") for r in rows(app)),
              str(rows(app)))
        stub.gate.set()
        await settle(pilot, app)
        check("the row is gone after the refusal",
              not any(r.startswith("tmp:") for r in rows(app)) and len(rows(app)) == 1,
              str(rows(app)))
        check("the original task is untouched", rows(app) == ["T-a"], str(rows(app)))
        check("the refusal is reported",
              "Adding failed" in status(app) and "no room" in status(app), status(app))


async def main_():
    for part in (t_optimistic, t_queued_behind, t_refused):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    sys.exit(0 if all(ok) else 1)


asyncio.run(main_())
