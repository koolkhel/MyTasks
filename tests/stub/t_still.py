"""The list stays where it is when it is redrawn.

Ticking a row used to scroll the list: rebuilding the table loses its scroll
position, and revealing the cursor's row afterwards puts that row on the last
visible line. On a 600-row inbox that meant one press moved the view thirteen
rows and left the cursor at the bottom with nothing below it.

Everything here is about the view's position: that a redraw does not change
it, that the next row lands on the line the last one had, and that a row the
restored view cannot show is still found -- away from the bottom edge.

Self-contained: a stubbed store, no mailbox, no calendar, no tracker, no
network. Every row is generated.
"""
import asyncio, datetime as dt, os, sys
from time import monotonic

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import main
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def triage(n):
    """`n` undated tasks, which is what the inbox shows."""
    return [mk(f"i{i:04d}", f"triage {i}") for i in range(n)]


async def inbox(tasks=None, size=(100, 44)):
    """A board showing the inbox, with the cursor wherever it starts."""
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else triage(600),
                            reference=NOW)
    app.calendar_config = app.tracker_config = app.mail_config = None
    return app, size


async def settle(pilot, n=12):
    for _ in range(n): await pilot.pause()


def table_of(app):
    return app.query_one(DataTable)


def top(app):
    return int(table_of(app).scroll_y)


def line(app):
    """Which line of the viewport the cursor is on."""
    return table_of(app).cursor_row - top(app)


def top_row_title(app):
    return app.tasks[top(app)].raw.get("title")


async def park(app, pilot, row, at_line):
    """Put the cursor on `row` and the view so it sits on `at_line`."""
    table = table_of(app)
    table.move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await settle(pilot, 8)
    table.scroll_to(y=row - at_line, animate=False)
    await settle(pilot, 8)
    return top(app)


# -- a redraw does not move the view --------------------------------------
async def a_redraw_holds():
    print("a redraw with the selection unchanged does not move the view")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        check("the inbox is long enough for position to mean anything",
              len(app.tasks) > 500, True)
        was = await park(app, pilot, 300, 7)
        check("parked with the cursor on line 7", line(app), 7)
        check("and the view scrolled down", was > 0, True)
        first = top_row_title(app)
        app.repaint()
        await settle(pilot, 10)
        check("the view has not moved", top(app), was)
        check("the cursor is on the same line", line(app), 7)
        check("and the same row is on the top line", top_row_title(app), first)

    print("nor does a redraw driven the way a background load drives one")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        was = await park(app, pilot, 250, 5)
        for _ in range(3):
            app.repaint()
            await settle(pilot, 6)
        check("three redraws later it is where it was", top(app), was)
        check("with the cursor still on line 5", line(app), 5)


# -- ticking leaves the list alone ----------------------------------------
async def ticking_holds():
    print("ticking the selected row leaves the list where it was")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        was = await park(app, pilot, 300, 7)
        first = top_row_title(app)
        after = app.tasks[301].raw.get("title")
        await pilot.press("space")
        await settle(pilot, 20)
        check("the view has not scrolled", top(app), was)
        check("the same row is on the top line", top_row_title(app), first)
        check("the cursor is on the line the ticked row had", line(app), 7)
        check("and the row that followed it is selected",
              app.selected.raw.get("title"), after)

    print("five in succession move the selection's line not at all")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        await park(app, pilot, 300, 9)
        lines, counts = [], []
        for _ in range(5):
            await pilot.press("space")
            await settle(pilot, 18)
            lines.append(line(app))
            counts.append(len(app.tasks))
        check("the cursor stayed on one line throughout", set(lines), {9})
        check("and each press removed exactly one row",
              [counts[0] - c for c in counts], [0, 1, 2, 3, 4])


# -- a row the restored view cannot show is still found -------------------
async def found_when_lost():
    print("a selection outside the restored view is brought into view")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        table = table_of(app)
        height = table.size.height
        await park(app, pilot, 300, 7)
        # A row far from the view, selected without moving the view: what a
        # redraw meets when the selected row has moved a long way.
        app._selected_id = app.tasks[500].id
        app.repaint()
        await settle(pilot, 10)
        check("the row is on screen", 0 <= line(app) < height, True)
        check("it is the row that was selected",
              table.cursor_row, 500)
        # Near the middle, not merely "not on the last line": revealing by
        # the shortest distance leaves the row on line 25 of 28 -- Textual
        # keeps a two-line margin -- so an edge test passes for the very
        # behaviour this change exists to remove.
        check("it is revealed near the middle, not at an edge",
              abs(line(app) - height // 2) <= 2, True)
        print(f"        viewport {height} rows, revealed on line {line(app)}, "
              f"middle is {height // 2}")

    print("ticking a task, whose completion re-sorts it, keeps it in view")
    # A day, where completion orders: the ticked task moves down among the
    # finished ones while the selection moves to the next unfinished one.
    app, size = await inbox([mk(f"d{i:03d}", f"today {i}", TODAY)
                             for i in range(60)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 18)
        height = table_of(app).size.height
        await park(app, pilot, 30, 6)
        await pilot.press("space")
        await settle(pilot, 24)
        check("the selection is still on screen",
              0 <= line(app) < height, True)
        check("and it is on an unfinished task",
              bool(app.selected) and not app.selected.done, True)

    print("a view that has become shorter shows its end, not past it")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        await park(app, pilot, 400, 7)
        keep = [t for t in app.client.store.values()][:10]
        app.client.store = {t.id: t for t in keep}
        app._base = keep
        app.repaint()
        await settle(pilot, 12)
        table = table_of(app)
        check("ten rows are shown", len(app.tasks), 10)
        check("the view is not scrolled past them",
              top(app) <= max(0, len(app.tasks) - table.size.height), True)
        check("and the cursor is on one of them",
              0 <= table.cursor_row < len(app.tasks), True)


# -- a different view begins at its beginning -----------------------------
async def a_new_view_begins():
    print("switching view starts the new one at its beginning")
    # A long day, deliberately: a short one clamps the carried-over row
    # number to zero and looks correct while proving nothing.
    # The inbox long enough to park part way down, and the day long enough
    # that a carried-over row number is not simply clamped to zero.
    tasks = (triage(600)
             + [mk(f"d{i:03d}", f"today {i}", TODAY) for i in range(60)])
    app, size = await inbox(tasks)
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 16)
        await pilot.press("i")
        await settle(pilot, 22)
        await park(app, pilot, 30, 7)
        check("parked part way down the inbox", line(app), 7)
        await pilot.press("t")
        await settle(pilot, 26)
        check("today opens at its first row", table_of(app).cursor_row, 0)
        check("and at the top of the view", top(app), 0)
        check("with more than a screenful in it, so this is not a clamp",
              len(app.tasks) > table_of(app).size.height, True)
        await pilot.press("i")
        await settle(pilot, 26)
        check("the inbox opens at its first row too",
              table_of(app).cursor_row, 0)
        check("and at the top", top(app), 0)

    print("stepping between days starts each one at its beginning")
    app, size = await inbox([mk(f"d{i:03d}", f"today {i}", TODAY)
                             for i in range(60)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 18)
        await park(app, pilot, 40, 6)
        check("parked part way down today", line(app), 6)
        await pilot.press("l")
        await settle(pilot, 24)
        check("tomorrow starts at the top", (table_of(app).cursor_row,
                                             top(app)), (0, 0))
        await pilot.press("h")
        await settle(pilot, 24)
        check("and so does today, coming back",
              (table_of(app).cursor_row, top(app)), (0, 0))

    print("but a redraw of the same view still holds its place")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        was = await park(app, pilot, 300, 7)
        app.repaint()
        await settle(pilot, 10)
        check("the view is where it was", top(app), was)
        check("and the cursor on its line", line(app), 7)
        # The same view asked for again is not a change of view.
        await pilot.press("i")
        await settle(pilot, 26)
        check("asking for the view you are in does not send you to the top",
              top(app), was)


# -- the key bar names the keys a person presses --------------------------
async def the_key_bar():
    print("the bar names the keys, not the toolkit's words for them")
    app, size = await inbox(triage(3))
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        bar = app.query_one(main.KeyBar)
        entries = dict((desc, key) for key, desc in bar.entries())
        check("the note keys are shown as characters",
              (entries.get("Note up"), entries.get("Note down")), ("[", "]"))
        named = [key for key, _desc in bar.entries()]
        check("no entry anywhere is a toolkit name",
              [k for k in named if "_" in k], [])
        print(f"        {len(named)} entries: {' '.join(named)}")
        # What the shipped requirement about the bar promises.
        overlay = main.Help.TEXT
        missing = [k for k in named
                   if k not in ("^p",) and k not in overlay]
        check("every key the bar names is described in the overlay",
              missing, [])


# -- and it costs nothing -------------------------------------------------
async def cost():
    print("holding the view costs nothing to draw")
    app, size = await inbox()
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        await park(app, pilot, 300, 7)
        started = monotonic()
        for _ in range(5):
            app.repaint()
        each = (monotonic() - started) / 5
        print(f"        {each:.3f}s a redraw of {len(app.tasks)} rows")
        # The same bound the other drawing suites use: this happens on a
        # keypress, so a person notices anything above a moment.
        check("a redraw stays under a second", each < 1.0, True)


async def main_():
    for part in (a_redraw_holds, ticking_holds, found_when_lost,
                 a_new_view_begins, the_key_bar, cost):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


sys.exit(asyncio.run(main_()))
