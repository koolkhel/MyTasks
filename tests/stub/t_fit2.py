"""The layout assumption, the focus view, links, and what is actually drawn."""
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
from datetime import datetime as dt
import main as M
from main import TaskApp, TaskFocus
from textual.widgets import DataTable
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
NOW = dt.now(TZ); TODAY = NOW.date()
LONG = "a synthetic title so long that no terminal will ever show the whole of it in one row, not even a wide one"
LINKED = 'chase https://example.com/some/quite/long/address and then a great deal of further text besides'

async def app_with(tasks, term=(120, 30), projects=None):
    stub = StubClient(tasks, reference=NOW)
    app = TaskApp(TODAY)
    return app, stub

print("1.3/3.x the table fills the app's width -- the assumption title_width rests on")
async def pin():
    app, stub = await app_with([mk("T-a", LONG, start=TODAY)])
    async with app.run_test(size=(120, 30)) as pilot:
        app.client = stub; app.projects = {}; app.green_tag = None
        app.green_checked = True; app.tracker_config = None
        app.load()
        for _ in range(150): await pilot.pause()
        tbl = app.query_one(DataTable)
        for w in (60, 80, 120, 200):
            await pilot.resize_terminal(w, 30)
            for _ in range(80): await pilot.pause()
            chk(f"at {w}, the table spans the app", tbl.size.width == app.size.width,
                f"table {tbl.size.width} vs app {app.size.width}")
asyncio.run(pin())

print("\n4.2 the focus view still shows the whole title")
async def focus():
    app, stub = await app_with([mk("T-a", LONG, start=TODAY)])
    async with app.run_test(size=(120, 30)) as pilot:
        app.client = stub; app.projects = {}; app.green_tag = None
        app.green_checked = True; app.tracker_config = None
        app.load()
        for _ in range(150): await pilot.pause()
        row = app.row_for(app.tasks[0])[3]
        chk("the row's title is shortened", row.plain.endswith(M._ELLIPSIS), repr(row.plain[-10:]))
        app._selected_id = "T-a"; app.repaint(); await pilot.pause()
        await pilot.press("enter")
        for _ in range(40): await pilot.pause()
        node = next(iter(app.screen.query("#focus-title")), None)
        shown = str(node.render()) if node is not None else ""
        chk("the focus view holds the whole title", LONG in shown, repr(shown[:70]))
        chk("and it is not shortened there", not shown.endswith(M._ELLIPSIS), repr(shown[-14:]))
        await pilot.press("escape")
        for _ in range(20): await pilot.pause()
asyncio.run(focus())

print("\n4.3 a link in a shortened row still opens the right address")
async def links():
    app, stub = await app_with([mk("T-a", LINKED, start=TODAY)])
    async with app.run_test(size=(80, 30)) as pilot:
        app.client = stub; app.projects = {}; app.green_tag = None
        app.green_checked = True; app.tracker_config = None
        app.load()
        for _ in range(150): await pilot.pause()
        cell = app.row_for(app.tasks[0])[3]
        chk("the row was shortened", cell.plain.endswith(M._ELLIPSIS), repr(cell.plain[-10:]))
        styles = [str(s.style) for s in cell.spans]
        chk("the link span survives", any("link" in s for s in styles), str(styles))
        chk("with the whole address, not a cut one",
            any("example.com/some/quite/long/address" in s for s in styles), str(styles))
        chk("and the task still reports that address",
            app.tasks[0].link == "https://example.com/some/quite/long/address", str(app.tasks[0].link))
asyncio.run(links())

print("\n5.2 what a person actually sees, at several widths")
async def drawn(term_w):
    app, stub = await app_with([mk("T-a", LONG, start=TODAY, project="P-1")])
    async with app.run_test(size=(term_w, 14)) as pilot:
        app.client = stub; app.projects = {"P-1": "a project name far too long"}
        app.green_tag = None; app.green_checked = True; app.tracker_config = None
        app.load()
        for _ in range(150): await pilot.pause()
        svg = app.export_screenshot()
        rows = {}
        for m in re.finditer(r'<text[^>]*\by="([\d.]+)"[^>]*>(.*?)</text>', svg, re.S):
            rows.setdefault(m.group(1), []).append(html.unescape(m.group(2)))
        lines = ["".join(v).replace("\xa0", " ").rstrip() for _, v in sorted(rows.items(), key=lambda kv: float(kv[0]))]
        return [l for l in lines if "synthetic" in l]

for w in (80, 120):
    got = asyncio.run(drawn(w))
    if got:
        line = got[0]
        print(f"    {w}: |{line[:w]}|")
        chk(f"at {w}: the drawn row is no wider than the terminal", len(line) <= w, f"{len(line)}")
        chk(f"at {w}: the row shows the ellipsis", M._ELLIPSIS in line, repr(line[-24:]))
        chk(f"at {w}: the project column is still on screen",
            "project" in line or "a project" in line, repr(line[-24:]))
    else:
        chk(f"at {w}: a row was drawn", False, "no row captured")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
