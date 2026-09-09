"""Group 3 -- the rail."""
import sys, asyncio, re
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
from datetime import datetime, timedelta
import main as M, tracker, singularity
from main import TaskApp
from singularity import Bucket
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
G = "A-green"; WORK = "P-work-0001"
NOW = datetime.now(TZ); TODAY = NOW.date()

def t(name, green=False, hour=None, late=None, done=0, deferred=False, dated=True):
    start = (TODAY - timedelta(days=late) if late else TODAY) if dated else None
    x = mk(name, name, start=start, checked=done, timed=hour is not None, deferred=deferred)
    if hour is not None:
        x.raw["start"] = singularity.iso_z(datetime.combine(
            start, datetime.min.time().replace(hour=hour), tzinfo=TZ))
    if green: x.raw["tags"] = [G]
    return x

def issue(k, state="In progress"):
    return tracker.Issue(key=k, summary="s", project="TASKR", state=state,
                         assignee="me", base_url="https://tracker.example")

async def board(tasks, position=None, issues=()):
    stub = StubClient(tasks, reference=NOW); stub.green = G
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.green_tag = G
        app.work_project = WORK; app.projects = {WORK: "Work"}
        app.tracker_config = tracker.Config("https://x", "t", "me", ("TASKR",), ("In progress",))
        wanted = list(issues)
        app.load_tracker = lambda: (setattr(app, "tracker_issues", list(wanted)),
                                    setattr(app, "tracker_error", None), app.repaint())
        if position is not None: app.position = position
        app.load()
        for _ in range(200): await pilot.pause()
        rows = [(x.id, app.row_for(x)) for x in app.tasks]
        return rows, str(app.query_one("#status").content)

async def run():
    print("3.1 exactly the marked tasks carry the rail")
    tasks = [t("GREEN-1", green=True), t("work-1", hour=9),
             t("GREEN-2", green=True), t("work-2")]
    rows, _ = await board(tasks)
    rail = {i: r[0] for i, r in rows}
    chk("marked rows carry it", all(rail[i] == M.GREEN_MARK for i in ("GREEN-1", "GREEN-2")), str(rail))
    chk("unmarked rows carry nothing", all(rail[i] == "" for i in ("work-1", "work-2")), str(rail))
    chk("the mark is an asterisk", M.GREEN_MARK == "*", repr(M.GREEN_MARK))

    print("\n3.2 adjacent marked tasks each carry their own mark")
    ids = [i for i, _ in rows]
    marked = [n for n, (i, _) in enumerate(rows) if rail[i]]
    # the marks no longer join; they are still adjacent because marked
    # tasks sort first, and each carries its own
    chk("the marked rows are adjacent", marked == list(range(len(marked))), f"{ids} marks at {marked}")
    chk("and each carries its own mark, not a joined shape",
        all(rail[i] == M.GREEN_MARK for i, _ in rows if rail[i]), str(rail))
    chk("and they are at the top", marked and marked[0] == 0, str(ids))

    print("     ...and the rail shows in every view")
    for label, pos, mk_tasks in [
        ("a calendar day", TODAY, [t("GREEN-d", green=True), t("plain-d")]),
        ("the inbox", Bucket.INBOX, [t("GREEN-i", green=True, dated=False), t("plain-i", dated=False)]),
        ("someday", Bucket.SOMEDAY,
         [t("GREEN-s", green=True, dated=False, deferred=True), t("plain-s", dated=False, deferred=True)]),
    ]:
        rws, _ = await board(mk_tasks, position=pos)
        got = {i: r[0] for i, r in rws}
        want = {i: (M.GREEN_MARK if "GREEN" in i else "") for i, _ in rws}
        chk(f"{label}", got == want and any(got.values()), str(got))

    print("\n3.3 no name, no colour")
    # a title with no telltale word in it, so the check is about the board
    rows, _ = await board([t("marked-one", green=True)])
    cells = rows[0][1]
    chk("no row prints the tag's name",
        not any("Зелен" in str(c) or "green" in str(c).lower() or "tag" in str(c).lower()
                for c in cells[1:]), str(cells))
    chk("the rail cell is the glyph alone, with no markup",
        cells[0] == M.GREEN_MARK and "[" not in cells[0], repr(cells[0]))

    print("\n3.4 the columns still fit")
    rows, _ = await board([t("late", late=999), t("GREEN-t", green=True, hour=23)],
                          issues=[issue("TASKR-1")])
    widths = {"rail": 1, "mark": 2, "when": M._WHEN_WIDTH}
    for i, r in rows:
        chk(f"{i}: rail is one cell", len(r[0]) <= 1, repr(r[0]))
        chk(f"{i}: when fits", len(r[2]) <= M._WHEN_WIDTH, repr(r[2]))
    chk("a tracker row can carry no rail", all(r[0] == "" for i, r in rows if i.startswith("yt:")))
    chk("row_for returns five cells now", all(len(r) == 5 for _, r in rows))

    print("\n3.5 the tracker block and the rail")
    rws, _ = await board([t("marked", green=True), t("plain")],
                         issues=[issue("TASKR-1"), issue("TASKR-2")])
    ids = [i for i, _ in rws]
    # The block now follows the day's unfinished tasks, so a marked task
    # leads it -- what matters is that the tag orders the tasks among
    # themselves and leaves the block whole.
    chk("marked tasks lead, the block follows",
        ids == ["marked", "plain", "yt:TASKR-1", "yt:TASKR-2"], str(ids))
    chk("the tag did not break the block apart",
        ids.index("yt:TASKR-2") - ids.index("yt:TASKR-1") == 1, str(ids))

asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
