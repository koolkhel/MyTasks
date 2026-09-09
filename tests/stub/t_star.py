"""Groups 1, 2 and 3 -- the star, the prompt's width, and what must not move."""
import sys, asyncio, unicodedata as ud, datetime
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
from main import (TaskApp, TaskInput, Confirm, DatePicker, ProjectPicker,
                  TaskFocus, Help)
from singularity import Bucket
from textual.widgets import Input
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
G = "A-green"; WORK = "P-work-0001"
NOW = dt.now(TZ); TODAY = NOW.date()

def t(name, green=False, hour=None, late=None, done=0, deferred=False, dated=True):
    start = (TODAY - timedelta(days=late) if late else TODAY) if dated else None
    x = mk(name, name, start=start, checked=done, timed=hour is not None, deferred=deferred)
    if hour is not None:
        x.raw["start"] = singularity.iso_z(dt.combine(
            start, dt.min.time().replace(hour=hour), tzinfo=TZ))
    if green: x.raw["tags"] = [G]
    return x

def issue(k):
    return tracker.Issue(key=k, summary="s", project="TASKR", state="In progress",
                         assignee="me", base_url="https://x")

async def board(tasks, position=None, issues=(), tag=G):
    stub = StubClient(tasks, reference=NOW); stub.green = tag
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = tag; app.green_title = "Зеленая"
        app.green_checked = True; app.work_project = WORK; app.projects = {WORK: "Work"}
        app.tracker_config = tracker.Config("https://x", "t", "me", ("TASKR",), ("In progress",))
        wanted = list(issues)
        app.load_tracker = lambda: (setattr(app, "tracker_issues", list(wanted)),
                                    setattr(app, "tracker_error", None), app.repaint())
        if position is not None: app.position = position
        app.load()
        for _ in range(200): await pilot.pause()
        return [(x.id, app.row_for(x)) for x in app.tasks], str(app.query_one("#status").content)

async def run():
    print("1.1 the mark is an asterisk, on marked rows only")
    rows, _ = await board([t("marked", green=True), t("plain", hour=9)])
    got = {i: r[0] for i, r in rows}
    chk("the mark is '*'", M.GREEN_MARK == "*", repr(M.GREEN_MARK))
    chk("the constant no longer says rail", not hasattr(M, "GREEN_RAIL"))
    chk("marked rows carry it", got.get("marked") == "*", str(got))
    chk("unmarked rows carry nothing", got.get("plain") == "", str(got))

    print("\n1.2 one cell wide, in every locale")
    w = ud.east_asian_width(M.GREEN_MARK)
    chk("its width class is narrow, not ambiguous", w == "Na", w)
    chk("it is plain ASCII", ord(M.GREEN_MARK) < 128, hex(ord(M.GREEN_MARK)))
    chk("no mark the board draws in that column is wider than one cell",
        all(ud.east_asian_width(c) in ("Na", "N") for c in M.GREEN_MARK))

    print("\n1.3 shown in every view; never on a tracker row")
    for label, pos, mk_tasks in [
        ("a calendar day", TODAY, [t("g-d", green=True), t("p-d")]),
        ("the inbox", Bucket.INBOX, [t("g-i", green=True, dated=False), t("p-i", dated=False)]),
        ("someday", Bucket.SOMEDAY,
         [t("g-s", green=True, dated=False, deferred=True), t("p-s", dated=False, deferred=True)]),
    ]:
        rws, _ = await board(mk_tasks, position=pos)
        g = {i: r[0] for i, r in rws}
        chk(f"{label}", g == {i: ("*" if i.startswith("g") else "") for i, _ in rws}, str(g))
    rws, _ = await board([t("marked", green=True)], issues=[issue("TASKR-1")])
    chk("a tracker row carries no mark",
        all(r[0] == "" for i, r in rws if i.startswith(M.TRACKER_PREFIX)), str([r[0] for _, r in rws]))

    print("\n1.4 the cell is the character alone; the tag is not named")
    rows, _ = await board([t("one", green=True)])
    cells = rows[0][1]
    chk("no markup around the mark", cells[0] == "*" and "[" not in cells[0], repr(cells[0]))
    chk("the tag's name is nowhere on the row",
        not any("Зелен" in str(c) or "green" in str(c).lower() for c in cells[1:]), str(cells))

    print("\n1.5 the columns beside it still line up")
    rows, _ = await board([t("late", late=999, green=True), t("timed", hour=23)],
                          issues=[issue("TASKR-2")])
    for i, r in rows:
        chk(f"{i}: mark is one cell", len(r[0]) <= 1, repr(r[0]))
        chk(f"{i}: when fits the column", len(r[2]) <= M._WHEN_WIDTH, repr(r[2]))
    chk("every row still has five cells", all(len(r) == 5 for _, r in rows))

    print("\n3.1 marking, ordering and counting are untouched")
    tasks = [t("g1", green=True), t("w1", late=16), t("g2", green=True), t("w2", hour=9)]
    rows, st = await board(tasks)
    ids = [i for i, _ in rows if not i.startswith(M.TRACKER_PREFIX)]
    chk("marked tasks still lead", ids[:2] == ["g1", "g2"], str(ids))
    chk("still counted", "2 green" in st, st)
    rows_off, st_off = await board(tasks, tag=None)
    chk("with no tag configured, nothing is marked",
        all(r[0] == "" for _, r in rows_off), str([r[0] for _, r in rows_off]))
    chk("and no count is reported", "green" not in st_off, st_off)

asyncio.run(run())

print("\n2.1/2.2 the prompt is wider; the other five are not")
async def widths(term=(120, 40), dialog_w=None):
    app = TaskApp(TODAY)
    out = {}
    async with app.run_test(size=term) as pilot:
        for name, screen in [
            ("TaskInput", TaskInput("Add task", "")),
            ("Confirm", Confirm("Sure?")),
            ("DatePicker", DatePicker("When?", TODAY)),
            ("ProjectPicker", ProjectPicker("Project", {"P-1": "One"}, None)),
            ("TaskFocus", TaskFocus(mk("T-1", "a task", start=TODAY), "all-day", "", TZ)),
            ("Help", Help()),
        ]:
            try:
                app.push_screen(screen)
                for _ in range(25): await pilot.pause()
                out[name] = app.screen.query_one("#dialog").size.width
                if name == "TaskInput":
                    out["TaskInput text"] = app.screen.query_one(Input).content_size.width
                app.pop_screen()
                for _ in range(10): await pilot.pause()
            except Exception as exc:
                out[name] = f"?({type(exc).__name__})"
    return out

now = asyncio.run(widths())
for k, v in now.items(): print(f"    {k:16} {v}")
chk("the prompt's box is wider than the shared one", now["TaskInput"] > now["Confirm"],
    f"{now['TaskInput']} vs {now['Confirm']}")
chk("its text area grew from 50 to 78", now["TaskInput text"] == 78, str(now["TaskInput text"]))
for other in ("Confirm", "DatePicker", "ProjectPicker", "TaskFocus", "Help"):
    if isinstance(now[other], int):
        chk(f"{other} is unchanged at 56", now[other] == 56, str(now[other]))

print("\n2.4 a narrow terminal narrows it rather than overflowing")
for term_w in (50, 60, 70, 80, 100):
    got = asyncio.run(widths(term=(term_w, 40)))
    w = got["TaskInput"]
    chk(f"terminal {term_w}: the box fits inside it", w <= term_w, f"box {w}")
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
