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
from harness import StubClient, mk, TZ
from datetime import datetime as dt, timedelta
import main as M, tracker, singularity
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
    chk("the project column is 11", widths.get("Project") == 11, str(widths))
    chk("the title column takes what is left",
        widths.get("Task") == 120 - M._ROW_OVERHEAD, f"{widths.get('Task')} vs {120-M._ROW_OVERHEAD}")
    chk("the overhead is the measured 35", M._ROW_OVERHEAD == 35, str(M._ROW_OVERHEAD))

    print("\n     ...at a range of widths, does the table fit the viewport?")
    for term_w in (50, 60, 65, 80, 120, 160):
        app2, tbl, _, _st, _w, fit = await board([t("a", LONG)], term=(term_w, 30))
        virt, view = fit
        want = max(M._TITLE_MIN, term_w - M._ROW_OVERHEAD)
        fits = virt <= view
        expect_fit = term_w >= M._TITLE_MIN + M._ROW_OVERHEAD
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
    cut = app.shortened(linked, 40)
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
        chk("at 80 the title gets 45", narrow == 45, str(narrow))
        calls_before = len([c for c in stub.calls if c[0] == "tasks_at"])
        await pilot.resize_terminal(160, 30)
        for _ in range(60): await pilot.pause()
        wide = app.title_width
        chk("widening gives the title more room", wide == 125, str(wide))
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
    chk("the marks are unchanged", [r[1] for _, r in rows] == ["☐", "☐", "☑"], str([r[1] for _, r in rows]))
    chk("the when column is unchanged", rows[0][1][2] == "9d ago", repr(rows[0][1][2]))
    chk("the counts are unchanged", "3 task(s)" in status, status)

asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
