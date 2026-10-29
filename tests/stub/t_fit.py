"""Groups 1-4 -- the widths, the shortening, the resize, and what must not move."""
import sys, asyncio, re, html
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import StubClient, mk, TZ, run_parts
from datetime import datetime as dt, timedelta
import main as M, tracker, singularity
# The table by name, not the module: `board` is a helper defined below and
# importing the module under that name would shadow it.
from board import MARKS
from main import TaskApp
from textual.widgets import DataTable
from rich.text import Text
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
NOW = dt.now(TZ); TODAY = NOW.date()
LONG = "a synthetic title of considerable length that will certainly not fit in the room any terminal can give it"
SHORT = "short one"

def t(name, title, late=None, done=0, project=None):
    x = mk(name, title, start=TODAY - timedelta(days=late) if late else TODAY,
           checked=done, project=project)
    return x

async def board(tasks, term=(120, 30), projects=None, issues=()):
    stub = StubClient(tasks, reference=NOW)
    app = TaskApp(TODAY)
    async with app.run_test(size=term) as pilot:
        app.client = stub; app.projects = projects or {}
        app.green_tag = None; app.green_checked = True
        app.tracker_config = (tracker.Config("https://x","t","me",("P",),("In progress",))
                              if issues else None)
        wanted = list(issues)
        if issues:
            app.load_tracker = lambda: (setattr(app, "tracker_issues", list(wanted)),
                                        setattr(app, "tracker_error", None), app.repaint())
        app.load()
        for _ in range(150): await pilot.pause()
        table = app.query_one(DataTable)
        rows = [(x.id, app.row_for(x)) for x in app.tasks]
        status = str(app.query_one("#status").content)
        widths = {(c.label.plain or "?"): c.width for c in table.columns.values()}
        # measured inside the context: once it exits, the table reports 0
        fit = (table.virtual_size.width, table.size.width)
        return app, table, rows, status, widths, fit

async def run():
    print("1.1/1.2 the widths, and whether the table fits")
    app, table, rows, status, widths, fit = await board([t("a", SHORT)])
    # Twenty-four: what the longest project name in use needs.  It was eleven
    # and cut that name to a stump; the title gives up the room.
    chk("the project column is 24", widths.get("Project") == 24, str(widths))
    want = 120 - M._ROW_OVERHEAD - M._SCROLLBAR_ROOM
    chk("the title column takes what is left",
        widths.get("Task") == want, f"{widths.get('Task')} vs {want}")
    chk("the overhead is the measured 48", M._ROW_OVERHEAD == 48, str(M._ROW_OVERHEAD))
    # The room the table keeps for its own scrollbar, which the fit must take
    # off before the title gets the rest.  Pinned against what the widget
    # actually reserves: the board laid out two cells more than could be shown
    # for as long as this went uncounted, and a framework that changes the
    # number must fail here rather than clip every row in silence.
    reserved = table.styles.scrollbar_size_vertical
    chk("the reserved room matches what the table keeps",
        M._SCROLLBAR_ROOM == reserved, f"constant {M._SCROLLBAR_ROOM} vs widget {reserved}")

    print("\n     ...at a range of widths, does the table fit the viewport?")
    for term_w in (50, 60, 65, 80, 120, 160):
        app2, tbl, _, _st, _w, fit = await board([t("a", LONG)], term=(term_w, 30))
        virt, view = fit
        want = max(M._TITLE_MIN, term_w - M._ROW_OVERHEAD - M._SCROLLBAR_ROOM)
        fits = virt <= view
        expect_fit = term_w >= M._TITLE_MIN + M._ROW_OVERHEAD + M._SCROLLBAR_ROOM
        chk(f"terminal {term_w}: title {want}, {'fits' if fits else 'scrolls'}",
            fits == expect_fit, f"wants {virt}, has {view}")

    print("\n2.1 a long title is shortened and says so; a short one is untouched")
    app, table, rows, status, widths, fit = await board([t("a", LONG), t("b", SHORT)])
    cells = {i: r[3] for i, r in rows}
    long_cell, short_cell = cells["a"], cells["b"]
    chk("the long one is a Text, not raw markup", isinstance(long_cell, Text))
    chk("it ends with the ellipsis", long_cell.plain.endswith(M._ELLIPSIS), repr(long_cell.plain[-12:]))
    chk("it is exactly the column's width", len(long_cell.plain) == app.title_width,
        f"{len(long_cell.plain)} vs {app.title_width}")
    chk("the short one is not marked", not short_cell.plain.endswith(M._ELLIPSIS), repr(short_cell.plain))
    chk("and is shown in full", short_cell.plain == SHORT, repr(short_cell.plain))

    print("\n2.2 shortening keeps a title readable")
    linked = "see [link='https://example.com/a-very-long-address']this page[/link] " + LONG
    app, table, rows, status, widths, fit = await board([t("a", "x")])
    cut = app.shortened(Text.from_markup(linked), 40)
    chk("the link survives the cut", any("link" in str(sp.style) for sp in cut.spans),
        str([(s.start, s.end, str(s.style)[:26]) for s in cut.spans]))
    chk("the address is kept whole in the style",
        any("example.com/a-very-long-address" in str(sp.style) for sp in cut.spans))
    chk("no markup is left as text", "[link" not in cut.plain and "[/" not in cut.plain, repr(cut.plain))
    app, table, rows, status, widths, fit = await board([t("late", LONG, late=9), t("done", LONG, done=1)])
    cells = {i: r[3] for i, r in rows}
    chk("a past-due title keeps its colour",
        any(str(s.style) not in ("", "none") for s in cells["late"].spans), str(cells["late"].spans[:2]))
    chk("a finished title keeps its strike",
        any("strike" in str(s.style) for s in cells["done"].spans), str(cells["done"].spans[:2]))
    for i in ("late", "done"):
        chk(f"{i}: still shortened with the mark", cells[i].plain.endswith(M._ELLIPSIS))

    print("\n2.3 the project column is shortened the same way")
    P = {"P-1": "a project name far too long for eleven cells"}
    app, table, rows, status, widths, fit = await board([t("a", SHORT, project="P-1")], projects=P)
    proj = rows[0][1][4]
    chk("the project cell is a Text", isinstance(proj, Text))
    chk("it ends with the ellipsis", proj.plain.endswith(M._ELLIPSIS), repr(proj.plain))
    chk("and fits the column", len(proj.plain) <= M._PROJECT_WIDTH, f"{len(proj.plain)}")
    P2 = {"P-1": "Личное"}
    app, table, rows, status, widths, fit = await board([t("a", SHORT, project="P-1")], projects=P2)
    chk("a short project name is untouched", rows[0][1][4].plain == "Личное", repr(rows[0][1][4].plain))

    print("\n2.4 a row is one line, whatever the title")
    app, table, rows, status, widths, fit = await board([t("a", LONG)])
    chk("no newline in the cell", "\n" not in rows[0][1][3].plain)
    chk("every row is one line high", all(table.rows[k].height == 1 for k in table.rows),
        str([table.rows[k].height for k in table.rows]))

    print("\n3.1/3.2 the widths follow the terminal")
    stub = StubClient([t("a", LONG)], reference=NOW)
    app = TaskApp(TODAY)
    async with app.run_test(size=(80, 30)) as pilot:
        app.client = stub; app.projects = {}; app.green_tag = None; app.green_checked = True
        app.tracker_config = None
        app.load()
        for _ in range(150): await pilot.pause()
        narrow = app.title_width
        # Thirty, the minimum: at eighty columns the wider project column and
        # the scrollbar's room leave less than that, so the list scrolls.
        chk("at 80 the title gets its minimum", narrow == M._TITLE_MIN, str(narrow))
        calls_before = len([c for c in stub.calls if c[0] == "tasks_at"])
        await pilot.resize_terminal(160, 30)
        for _ in range(60): await pilot.pause()
        wide = app.title_width
        chk("widening gives the title more room",
            wide == 160 - M._ROW_OVERHEAD - M._SCROLLBAR_ROOM, str(wide))
        chk("and a title that now fits is shown whole, with no mark",
            not app.row_for(app.tasks[0])[3].plain.endswith(M._ELLIPSIS),
            repr(app.row_for(app.tasks[0])[3].plain[-14:]))
        await pilot.resize_terminal(50, 30)
        for _ in range(60): await pilot.pause()
        chk("narrowing past the floor keeps the minimum", app.title_width == M._TITLE_MIN,
            str(app.title_width))
        chk("a resize costs no fetch",
            len([c for c in stub.calls if c[0] == "tasks_at"]) == calls_before,
            str([c[0] for c in stub.calls]))
        chk("and no write", not any(c[0].startswith("set_") or c[0].startswith("create")
                                    for c in stub.calls), str([c[0] for c in stub.calls]))

    print("\n4.1 what this must not disturb")
    app, table, rows, status, widths, fit = await board(
        [t("late", "late one", late=9), t("timed", "timed one"), t("done", "done one", done=1)])
    ids = [i for i, _ in rows]
    chk("the same tasks in the same order", ids == ["late", "timed", "done"], str(ids))
    want = [MARKS[singularity.EMPTY], MARKS[singularity.EMPTY],
            MARKS[singularity.CHECKED]]
    chk("the marks are unchanged", [r[1] for _, r in rows] == want, str([r[1] for _, r in rows]))
    chk("the when column is unchanged", rows[0][1][2] == "9d ago", repr(rows[0][1][2]))
    chk("the counts are unchanged", "3 task(s)" in status, status)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
async def drawn_rows_fit_the_room():
    """2.2/2.4 -- what is drawn, not what was computed.

    The arithmetic was right and the rows were still cut, because the width it
    was right about was not the width the table draws in.  So these read the
    screen back rather than recomputing what the code under test computes: a
    check that did the same sum would have agreed with the bug.
    """
    print("\n2.2 a drawn row ends inside the room the table has")
    NAME = "P" * 24
    for term_w in (104, 120, 160):
        for rows in (3, 60):
            tasks = [t(f"x{i}", SHORT, project="P-1") for i in range(rows)]
            stub = StubClient(tasks, reference=NOW)
            app = TaskApp(TODAY)
            async with app.run_test(size=(term_w, 20)) as pilot:
                app.client = stub; app.projects = {"P-1": NAME}
                app.green_tag = None; app.green_checked = True
                app.tracker_config = None
                app.load()
                for _ in range(80): await pilot.pause()
                table = app.query_one(DataTable)
                room = table.size.width - table.scrollbar_size_vertical
                laid = sum(c.width for c in table.columns.values()) + 2 * len(table.columns)
                lines = ["".join(seg.text for seg in strip)
                         for strip in app.screen._compositor.render_strips()[3:8]]
                whole = any(NAME in line for line in lines)
            chk(f"{term_w} cols, {rows} rows: the columns fit the room",
                laid <= room, f"laid {laid} into {room}")
            chk(f"{term_w} cols, {rows} rows: a full-width name survives whole",
                whole, f"lines ended {[len(l.rstrip()) for l in lines]}")

    print("\n2.4 the fit does not depend on whether the list is scrolling")
    widths = {}
    for rows in (3, 60):
        _app, _tbl, _rows, _st, w, _fit = await board(
            [t(f"y{i}", SHORT) for i in range(rows)], term=(120, 20))
        widths[rows] = w
    chk("the same columns either way", widths[3] == widths[60],
        f"{widths[3]} vs {widths[60]}")


async def the_project_column_holds_its_names():
    """3.1-3.4 -- the column that names a project, and who pays for it."""
    print("\n3.1 the title is the column that gives up the room")
    _app, _tbl, _rows, _st, w, _fit = await board([t("a", SHORT)], term=(120, 30))
    chk("project 24, when 11, marks 1 and 2 -- only the title moved",
        (w.get("Project"), w.get("When")) == (24, 11), str(w))
    chk("and the title is what the rest leave",
        w.get("Task") == 120 - M._ROW_OVERHEAD - M._SCROLLBAR_ROOM, str(w))

    print("\n3.2 names of the lengths an account really holds")
    # Display cells, not characters: every name on the account this was
    # written for opens with an emoji, which costs two cells before a letter.
    for name, fits in (("\U0001F9E0 \u0420\u0430\u0431\u043e\u0442\u0430", True),
                       ("P" * 24, True),
                       ("P" * 30, False)):
        _a, _t, rows, _s, _w, _f = await board(
            [t("a", SHORT, project="P-1")], term=(120, 30), projects={"P-1": name})
        cell = rows[0][1][4].plain.strip()
        if fits:
            chk(f"a name of {len(name)} chars is shown whole", cell == name, repr(cell))
        else:
            chk("a name too long is shortened", cell != name, repr(cell))
            chk("and says that it was", cell.endswith("\u2026"), repr(cell))

    print("\n3.3 the width does not follow what is on screen")
    short = await board([t("a", SHORT, project="P-1")], term=(120, 30),
                        projects={"P-1": "\u041a\u043b\u0443\u0431"})
    longer = await board([t("a", SHORT, project="P-1")], term=(120, 30),
                         projects={"P-1": "P" * 24})
    chk("a day of short names and a day of long ones fit alike",
        short[4] == longer[4], f"{short[4]} vs {longer[4]}")

    print("\n3.4 every kind of row shortens that column to the same width")
    from board import _PROJECT_WIDTH
    chk("one constant, shared", _PROJECT_WIDTH == 24, str(_PROJECT_WIDTH))
    import board as B, inspect
    src = inspect.getsource(B)
    chk("and every column that names a source uses it",
        src.count("_PROJECT_WIDTH,") + src.count("_PROJECT_WIDTH)") >= 4,
        f"{src.count('_PROJECT_WIDTH')} mentions")


PARTS = (
    run,
    drawn_rows_fit_the_room,
    the_project_column_holds_its_names,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
