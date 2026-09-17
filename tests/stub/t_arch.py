"""The archive: what the store is asked, what is drawn, and what is refused.

Nothing here reaches an account. The store is a stub that answers pages from
rows made up in this file, and the parts that check what is drawn build a
`board.Board` directly, with no user interface started at all.

Every task below is invented.
"""
import datetime as dt
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import *
import board
import ical
import mail
import singularity
import tracker
from singularity import (ARCHIVE, Archive, Bucket, CANCELLED, CHECKED,
                         SingularityClient, Task)

TZ = local_tz()
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.combine(TODAY, dt.time(12, 0), tzinfo=TZ)

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

def archived(tid, title, days_ago, checked=CHECKED, at=dt.time(9, 0),
             project=None):
    """A task the store archived `days_ago` days back."""
    t = mk(tid, title, None, checked=checked, project=project)
    when = dt.datetime.combine(TODAY - dt.timedelta(days=days_ago), at, tzinfo=TZ)
    t.raw["journalDate"] = iso_z(when)
    return t


class Paged(SingularityClient):
    """A store that answers a fixed set of pages and records what it was asked.

    Built without the real client's `__init__` on purpose: that one reads a
    token, and a suite in this tier has none and must not look for one.
    """

    def __init__(self, pages, total=None):
        self.tz = TZ
        self.pages = [list(p) for p in pages]
        self.total = sum(len(p) for p in self.pages) if total is None else total
        self.asked = []

    def get(self, path, **params):
        self.asked.append((path, params))
        offset = params.get("offset", 0)
        seen, rows = 0, []
        for page in self.pages:
            if seen == offset:
                rows = page
                break
            seen += len(page)
        return {"tasks": [t.raw for t in rows],
                "pagination": {"total": self.total, "count": len(rows),
                               "offset": offset}}


CAL = ical.Config(work="WorkAcc", personal=("Me",))
TRACK = tracker.Config(base_url="https://tracker.invalid", token="zz",
                       assignee="me", projects=("ZZA",), states=("open",))


def painting(rows, *, searching="", marked=(), width=60, loading=False,
             error=None, position=ARCHIVE, hiding_work=False, green_tag=None,
             threads=(), issues=(), events=(), **paint):
    """A board holding an archive, and what it would draw.

    No application, no table: the point of the parts below is that what is
    drawn is decided from the state alone, and a check that reached for a
    running interface would pass while proving nothing.
    """
    made = board.Board(
        base=[], pending={}, tasks=[], position=position, reference=None,
        tz=TZ, now=NOW, projects={"P-x": "Sales"}, marked=list(marked),
        marked_rows={t.id: t for t in rows}, searching=searching,
        hiding_work=hiding_work, work_project="P-work",
        window_reason_now=None, work_override=None, green_tag=green_tag,
        tracker_issues=list(issues), tracker_config=TRACK,
        events=list(events), events_day=None, calendar_config=CAL,
        mail_threads=list(threads), notice=None, fetched=True,
        title_width=width, late_colour="#d17e92",
        archive=list(rows), archive_loading=loading, archive_error=error,
    )
    return made, made.paint(**paint)


def titles(answer):
    return [t.display_title for t in answer.rows]


# --------------------------------------------- 1. the date the store carries

def the_archive_date_is_read():
    print("\n2.1 the store's archive date, read off a task")
    when = dt.datetime(2026, 9, 16, 21, 0, 1, tzinfo=dt.timezone.utc)
    t = Task({"id": "T-1", "title": "x", "checked": CHECKED,
              "journalDate": "2026-09-16T21:00:01.000Z"})
    check("the date is answered as an instant", t.archived_at, when)
    check("and the task says it is archived", t.archived, True)
    check("it is the same instant in any zone",
          t.archived_at.astimezone(TZ), when.astimezone(TZ))

    print("\n     a task the store has not archived")
    plain = Task({"id": "T-2", "title": "x", "checked": 0})
    check("answers no date", plain.archived_at, None)
    check("and says it is not archived", plain.archived, False)
    check("an empty value is the same as none",
          Task({"id": "T-3", "journalDate": ""}).archived_at, None)

    print("\n     a stamp the board cannot read is not an error")
    # Four years of rows, written by versions of the app older than the
    # field's present shape: one that cannot be parsed must cost its own row
    # and not the whole archive.
    for bad in ("nonsense", "2026-13-45", 17, [], {"a": 1}):
        check(f"{bad!r} answers no date", Task({"journalDate": bad}).archived_at, None)
    check("and such a task does not say it is archived",
          Task({"journalDate": "nonsense"}).archived, False)


# ------------------------------------------------- 2. what the store is asked

def the_query_pages_and_drops():
    print("\n2.2 the archive is paged until the store runs out")
    pages = [[archived(f"T-{i}", f"row {i}", i) for i in range(3)],
             [archived(f"T-{i}", f"row {i}", i) for i in range(3, 6)],
             [archived(f"T-{i}", f"row {i}", i) for i in range(6, 8)]]
    api = Paged(pages)
    got = list(api.iter_archived(page_size=3))
    check("every page arrives", [len(p) for p in got], [3, 3, 2])
    check("and every row with it",
          [t.id for p in got for t in p], [f"T-{i}" for i in range(8)])
    check("one request per page", len(api.asked), 3)
    check("the archived rows are asked for",
          api.asked[0][1].get("journalDate.isSet"), True)
    check("with the archived ones included",
          api.asked[0][1].get("includeArchived"), True)
    check("and recurrences forced on, as every paged query does",
          api.asked[0][1].get("includeAllRecurrenceInstances"), True)
    check("the offset walks by what arrived",
          [a[1]["offset"] for a in api.asked], [0, 3, 6])

    print("\n     paging stops where the store says it has finished")
    api = Paged([[archived("T-a", "a", 1)]], total=1)
    check("one page, one request", len(list(api.iter_archived(page_size=1))), 1)
    check("and it did not ask again", len(api.asked), 1)

    print("\n     archived is not the same as finished")
    rows = [archived("T-done", "done", 1),
            archived("T-cancelled", "cancelled", 2, checked=CANCELLED),
            archived("T-neither", "never ticked", 3, checked=0)]
    api = Paged([rows])
    got = [t.id for p in api.iter_archived() for t in p]
    check("the finished and the cancelled are kept", got,
          ["T-done", "T-cancelled"])
    check("the one that was never ticked is dropped", "T-neither" in got, False)

    print("\n     the whole archive, for a caller that cannot take it in pages")
    api = Paged(pages)
    listing = api.archived_tasks()
    check("holds every row", len(listing.tasks), 8)
    check("and is a listing like any other view's",
          [t.id for t in listing.tasks][:3], ["T-0", "T-1", "T-2"])


# ------------------------------------------------------- 3. its own position

def the_archive_is_its_own_position():
    print("\n3.1 the archive is a position, and not a bucket")
    check("it is not a Bucket", isinstance(ARCHIVE, Bucket), False)
    check("iterating the buckets still yields the two dateless queues",
          list(Bucket), [Bucket.INBOX, Bucket.SOMEDAY])
    check("it answers a label, as a bucket does", ARCHIVE.label, "Archive")
    check("it is one object", ARCHIVE is singularity.ARCHIVE, True)
    check("and a fresh one is a different object, so `is` is the test",
          Archive() is ARCHIVE, False)
    check("it is not a date either",
          isinstance(ARCHIVE, dt.date), False)


def asking_for_the_shown_view():
    print("\n3.3 asking the store for whichever view is shown")
    rows = [archived("T-1", "one", 1), archived("T-2", "two", 2),
            archived("T-3", "never ticked", 3, checked=0)]
    api = Paged([rows])
    listing = api.tasks_at(ARCHIVE)
    check("the archive answers its finished rows",
          sorted(t.id for t in listing.tasks), ["T-1", "T-2"])
    check("by the same query the pages come from",
          api.asked[0][1].get("journalDate.isSet"), True)


# ------------------------------------------------ 4. what would be drawn

def the_board_paints_an_archive():
    print("\n4.1 an archive is painted from the state it was given")
    rows = [archived("T-1", "wrote the report", 1),
            archived("T-2", "called the supplier", 2),
            archived("T-3", "cancelled the order", 3, checked=CANCELLED)]
    made, answer = painting(rows)
    check("every finished row is drawn", len(answer.rows), 3)
    check("and each has its cells", len(answer.cells), 3)
    check("the board knows how many it holds", answer.archive_held, 3)
    check("and how many it drew", answer.archive_drawn, 3)

    print("\n     the archive is its own body of rows, not a day's fetch")
    made, answer = painting(rows, position=TODAY)
    check("a day's view draws none of them", len(answer.rows), 0)
    check("and reports no archive", (answer.archive_held, answer.archive_drawn), (0, 0))

    print("\n     nothing arrives from the other three sources")
    made, answer = painting(rows, threads=[1], issues=[2], events=[3])
    check("no event, issue or mail row is drawn", len(answer.rows), 3)
    check("none is counted either",
          (answer.shown_issues, answer.shown_events, answer.shown_mail), (0, 0, 0))

    print("\n     an archive not yet asked for is not an empty one")
    made = board.Board(
        base=[], pending={}, tasks=[], position=ARCHIVE, reference=None,
        tz=TZ, now=NOW, projects={}, marked=[], marked_rows={}, searching="",
        hiding_work=False, work_project=None, window_reason_now=None,
        work_override=None, green_tag=None, tracker_issues=[],
        tracker_config=None, events=[], events_day=None, calendar_config=None,
        mail_threads=[], notice=None, fetched=True, title_width=60,
        late_colour="#d17e92")
    check("it paints nothing and does not fall over",
          len(made.paint().rows), 0)


def the_order_is_by_when_it_was_archived():
    print("\n4.2 most recently archived first")
    rows = [archived("T-old", "oldest", 30), archived("T-new", "newest", 1),
            archived("T-mid", "middle", 10)]
    made, answer = painting(rows)
    check("whatever order the store answered in",
          [t.id for t in answer.rows], ["T-new", "T-mid", "T-old"])

    print("\n     rows sharing a date are ordered by title")
    same = [archived("T-c", "cherry", 5, at=dt.time(9, 0)),
            archived("T-a", "apple", 5, at=dt.time(9, 0)),
            archived("T-b", "banana", 5, at=dt.time(9, 0))]
    made, answer = painting(same)
    check("so the order does not depend on the store", titles(answer),
          ["apple", "banana", "cherry"])

    print("\n     which rows are the archive's was decided when they were fetched")
    # The fetch drops what was never finished (part 2.2); the board draws
    # what it was handed and takes nothing away, so a task brought back
    # stays on its row, drawn as brought back, until the archive is re-read.
    rows = [archived("T-1", "ticked", 1),
            archived("T-2", "cancelled", 2, checked=CANCELLED),
            archived("T-3", "brought back a moment ago", 3, checked=0)]
    made, answer = painting(rows)
    check("every held row is drawn, the brought-back one included",
          [t.id for t in answer.rows], ["T-1", "T-2", "T-3"])
    check("and it is drawn as unfinished", answer.cells[2][1], board.MARKS[0])

    print("\n     a stamp the board cannot read does not take the view down")
    bad = archived("T-bad", "unreadable stamp", 2)
    bad.raw["journalDate"] = "not a date"
    rows = [archived("T-1", "one", 1), bad, archived("T-2", "two", 3)]
    made, answer = painting(rows)
    check("it is still drawn", len(answer.rows), 3)
    check("and it sorts to the end",
          [t.id for t in answer.rows], ["T-1", "T-2", "T-bad"])

    print("\n     the green tag does not lift a row here")
    tagged = archived("T-tag", "tagged but older", 9)
    tagged.raw["tags"] = ["A-green"]
    rows = [tagged, archived("T-plain", "untagged but newer", 2)]
    made, answer = painting(rows, green_tag="A-green")
    check("recency alone decides",
          [t.id for t in answer.rows], ["T-plain", "T-tag"])


def the_bound_draws_the_newest():
    print("\n4.3 the archive is held whole and drawn in part")
    rows = [archived(f"T-{i:04d}", f"row number {i}", i // 4) for i in range(1200)]
    made, answer = painting(rows)
    check("what is drawn is bounded", len(answer.rows), board.ARCHIVE_ROWS)
    check("and it is the newest of them", answer.rows[0].id, "T-0000")
    check("the whole of it is still held", answer.archive_held, 1200)
    check("and the drawn count says how many came through",
          answer.archive_drawn, board.ARCHIVE_ROWS)
    check("the cells are only for what is drawn",
          len(answer.cells), board.ARCHIVE_ROWS)

    print("\n     a search reaches a row the bound withheld")
    hidden = [t for t in rows if t.id == "T-0900"][0]
    check("the row is not drawn without one",
          hidden.id in [t.id for t in answer.rows], False)
    made, found = painting(rows, searching="number 900")
    check("and searching finds it", [t.id for t in found.rows], ["T-0900"])
    check("the archive still holds every row", found.archive_held, 1)
    check("what the search removed is reported",
          found.hidden_by_search, 1199)

    print("\n     a search wider than the bound is bounded too")
    made, wide = painting(rows, searching="row number")
    check("it draws the bound", len(wide.rows), board.ARCHIVE_ROWS)
    check("the newest of the matches first", wide.rows[0].id, "T-0000")
    check("and says how many matched", wide.archive_held, 1200)


def the_cell_carries_the_date():
    print("\n4.4 the column says when the store archived the row")
    when = dt.datetime.combine(TODAY - dt.timedelta(days=400), dt.time(9, 0),
                               tzinfo=TZ)
    rows = [archived("T-1", "long ago", 400)]
    made, answer = painting(rows)
    cell = answer.cells[0][2]
    check("it reads as a date with its year", cell, f"{when:%d %b %Y}")
    check("and fits the column it is drawn in",
          len(cell) <= board._WHEN_WIDTH, True)

    print("\n     the marks and the strike are what they are everywhere else")
    rows = [archived("T-done", "finished", 1),
            archived("T-cancel", "cancelled", 2, checked=CANCELLED)]
    made, answer = painting(rows)
    check("the completed row keeps its mark", answer.cells[0][1], "☑")
    check("the cancelled row keeps its own", answer.cells[1][1], "☒")
    # The cell is drawn text by the time it is here, not the markup it was
    # built from, so the strike is read off the span that carries it.
    check("both are struck through",
          [any("strike" in str(sp.style) for sp in c[3].spans)
           for c in answer.cells], [True, True])

    print("\n     a row whose stamp could not be read says nothing it does not know")
    bad = archived("T-bad", "unreadable", 1)
    bad.raw["journalDate"] = "not a date"
    made, answer = painting([bad])
    check("the cell is empty rather than wrong", answer.cells[0][2], "")


def the_line_counts_the_archive():
    print("\n4.5 what the line under the rows says")
    rows = [archived(f"T-{i:04d}", f"row number {i}", i // 4) for i in range(1200)]
    made, answer = painting(rows)
    check("it says how many are held and how many drawn",
          answer.status, "1200 archived · 500 shown")

    print("\n     with fewer rows than the bound, nothing is withheld to report")
    made, answer = painting(rows[:10])
    check("so it says only how many there are", answer.status, "10 archived")

    print("\n     while the pages are still arriving")
    made, answer = painting(rows[:600], loading=True)
    check("it says so, beside what has arrived",
          answer.status, "Reading the archive… · 600 archived · 500 shown")
    check("and that is not an error", answer.status_error, False)

    print("\n     when the fetch failed")
    made, answer = painting([], error="The archive could not be read · x")
    check("the failure is what the line says",
          answer.status, "The archive could not be read · x")
    check("and it is an error", answer.status_error, True)

    print("\n     a search, and the marks, are reported as they are elsewhere")
    made, answer = painting(rows, searching="number 90")
    check("the search's removals are counted",
          answer.status.endswith("hidden by search"), True)
    made, answer = painting(rows[:10], marked=["T-0000", "T-0001"])
    check("the marks are counted", answer.status, "10 archived · 2 marked")

    print("\n     and a mark made here survives the next page arriving")
    # The repaint that draws an arriving page is the one that would drop it:
    # a mark the view cannot account for is taken off, and the archive is
    # what this view has in hand.
    made, answer = painting(rows[:10], marked=["T-0000", "T-0009"])
    check("both marks are kept", made.surviving_marks(), ["T-0000", "T-0009"])
    # A mark made on a day and carried in here is not the archive's to drop:
    # marks follow a person between views, and this view can say nothing
    # about a row that was never archived.
    elsewhere = mk("T-day", "marked on a day", TODAY)
    made = board.Board(
        base=[], pending={}, tasks=[], position=ARCHIVE, reference=None,
        tz=TZ, now=NOW, projects={}, marked=["T-0000", "T-day"],
        marked_rows={"T-day": elsewhere, "T-0000": rows[0]}, searching="",
        hiding_work=False, work_project=None, window_reason_now=None,
        work_override=None, green_tag=None, tracker_issues=[],
        tracker_config=None, events=[], events_day=None, calendar_config=None,
        mail_threads=[], notice=None, fetched=True, title_width=60,
        late_colour="#d17e92", archive=rows[:10])
    check("a mark carried in from another view is kept too",
          made.surviving_marks(), ["T-0000", "T-day"])


def nothing_here_touched_a_screen():
    print("\n4.1 the whole of the above was decided with no interface at all")
    # The suite that proves the seam holds: `main` is where the application
    # lives, and nothing above may have needed it.  If this fails, something
    # here started a board rather than asking one what it would draw.
    check("main was never imported", "main" in sys.modules, False)


# ------------------------------------------------- 5. the board itself

async def settle(pilot, n=10):
    for _ in range(n):
        await pilot.pause()


class Slow(StubClient):
    """A store that hands the archive over one page at a time, on command.

    A suite cannot see a page land by waiting and hoping: the requirement is
    that rows are drawn before the last page arrives, and the only way to
    check that is to hold the pages and look in between.
    """

    def __init__(self, tasks, per_page=2):
        super().__init__(tasks)
        self.per_page = per_page
        self.let_go = __import__("threading").Event()

    def iter_archived(self, page_size=None, **filters):
        self._record("iter_archived")
        rows = [t for t in self.store.values()
                if t.archived and (t.done or t.cancelled)]
        for i in range(0, len(rows) or 1, self.per_page):
            self.let_go.wait(5)
            self.let_go.clear()
            yield rows[i:i + self.per_page]


def board_with(rows, client=None):
    from main import TaskApp
    app = TaskApp(TODAY)
    app.client = client or StubClient(list(rows))
    app.calendar_config = None
    app.tracker_config = None
    app.mail_config = None
    app.green_tag = None
    app.green_checked = True
    return app


def the_key_reaches_the_view():
    import asyncio
    from main import TaskApp, KEY_TWINS
    print("\n5.1 the key, in both alphabets")
    bound = {b.key if hasattr(b, "key") else b for b in ()}
    keys_for = {}
    for b in TaskApp.BINDINGS:
        keys_for[b.action] = b.key
    check("the archive has a key", "archive" in keys_for, True)
    check("it is A", keys_for["archive"].split(",")[0], "A")
    check("with the twin the Russian layout types",
          KEY_TWINS["A"] in keys_for["archive"].split(","), True)
    check("and it is named on the key bar",
          [b.description for b in TaskApp.BINDINGS if b.action == "archive"],
          ["Archive"])

    rows = [archived("T-1", "one", 1), archived("T-2", "two", 2)]

    async def run():
        app = board_with(rows)
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 20)
            was = (app.position, len(app.tasks))
            await pilot.press("t")
            await settle(pilot, 20)
            back = app.position
            await pilot.press(KEY_TWINS["A"])
            await settle(pilot, 20)
            return was, back, app.position

    was, back, twin = asyncio.run(run())
    check("pressing it shows the archive", was[0] is ARCHIVE, True)
    check("with the archived rows drawn", was[1], 2)
    check("today takes a person back out of it", back, TODAY)
    check("and the twin reaches it too", twin is ARCHIVE, True)


def it_fills_as_the_pages_arrive():
    import asyncio
    print("\n5.2 the view fills while it is still being read")
    rows = [archived(f"T-{i}", f"row {i}", i) for i in range(6)]

    async def run():
        api = Slow(rows, per_page=2)
        app = board_with(rows, client=api)
        seen = []
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 12)
            seen.append((len(app.tasks), app.archive_loading,
                         str(app.query_one("#status").content)))
            for _ in range(3):
                api.let_go.set()
                await settle(pilot, 14)
                seen.append((len(app.tasks), app.archive_loading,
                             str(app.query_one("#status").content)))
            api.let_go.set()
            await settle(pilot, 14)
            # Away and back: what is held is not a reason to ask again.
            await pilot.press("t")
            await settle(pilot, 16)
            await pilot.press("A")
            await settle(pilot, 16)
            came_back = (len(app.tasks), api.count("iter_archived"))
            # A reload is the one thing that asks again.
            api.let_go.set()
            await pilot.press("r")
            await settle(pilot, 10)
            for _ in range(4):
                api.let_go.set()
                await settle(pilot, 12)
            return seen, came_back, api.count("iter_archived"), len(app.tasks)

    seen, came_back, asked, ended = asyncio.run(run())
    check("nothing is drawn before the first page", seen[0][0], 0)
    check("and the board says it is reading", "Reading the archive…" in seen[0][2], True)
    check("the first page is drawn before the rest arrive", seen[1][0], 2)
    check("it is still reading while it draws", seen[1][1], True)
    check("and it says so beside what has arrived",
          "Reading the archive…" in seen[1][2], True)
    check("the second page joins the first", seen[2][0], 4)
    check("and the third", seen[3][0], 6)
    check("coming back draws what was held", came_back[0], 6)
    check("without asking the store again", came_back[1], 1)
    check("a reload does ask again", asked, 2)
    check("and ends with the archive drawn again", ended, 6)


def every_other_write_is_refused():
    import asyncio
    print("\n5.3 no key but two writes from this view")
    WRITES = ("x", "e", "n", "p", "g", "full_stop")

    async def run():
        rows = [archived("T-1", "finished long ago", 3)]
        today = mk("T-live", "still to do", TODAY)
        api = StubClient(rows + [today])
        app = board_with([], client=api)
        said = []
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 20)
            for key in WRITES:
                await pilot.press(key)
                await settle(pilot, 10)
                said.append(str(app.query_one("#status").content))
                await pilot.press("escape")
                await settle(pilot, 6)
            wrote = [c for c, _ in api.calls if c not in StubClient.READS
                     and c != "iter_archived"]
            await pilot.press("u")
            await settle(pilot, 10)
            undone = [c for c, _ in api.calls if c not in StubClient.READS
                      and c != "iter_archived"]
            # The same board, a calendar day: the task there is the board's
            # to change and still is.
            await pilot.press("t")
            await settle(pilot, 20)
            await pilot.press("space")
            await settle(pilot, 20)
            ticked = [c for c, _ in api.calls if c in ("set_done", "complete_task",
                                                       "update_task")]
            return said, wrote, undone, ticked

    said, wrote, undone, ticked = asyncio.run(run())
    check("every other writing key says what the archive allows",
          all("archive" in t and "only un-ticking and dating" in t
              for t in said), True)
    check("one message for all of them", len(set(said)), 1)
    check("and nothing was sent", wrote, [])
    check("undo has nothing to reverse either", undone, [])
    check("the same board still writes on a calendar day", bool(ticked), True)


def nothing_is_added_and_no_day_is_next():
    import asyncio
    print("\n5.4 adding, pasting, moving between days, reordering")

    async def run():
        rows = [archived("T-1", "one", 1), archived("T-2", "two", 2)]
        api = StubClient(rows)
        app = board_with([], client=api)
        out = {}
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 20)
            await pilot.press("a")
            await settle(pilot, 12)
            out["add"] = str(app.query_one("#status").content)
            out["created"] = api.count("create_task")
            out["screens"] = len(app.screen_stack)
            app.paste_tasks("one\ntwo")
            await settle(pilot, 12)
            out["paste"] = str(app.query_one("#status").content)
            out["created_by_paste"] = api.count("create_task")
            await pilot.press("h")
            await settle(pilot, 10)
            out["after_h"] = app.position
            await pilot.press("l")
            await settle(pilot, 10)
            out["after_l"] = app.position
            out["day_said"] = str(app.query_one("#status").content)
            await pilot.press("K")
            await settle(pilot, 10)
            out["move"] = str(app.query_one("#status").content)
            await pilot.press("t")
            await settle(pilot, 20)
            out["after_t"] = app.position
            await pilot.press("A")
            await settle(pilot, 20)
            await pilot.press("i")
            await settle(pilot, 20)
            out["after_i"] = app.position
            await pilot.press("A")
            await settle(pilot, 20)
            await pilot.press("s")
            await settle(pilot, 20)
            out["after_s"] = app.position
        return out

    out = asyncio.run(run())
    check("the add key creates nothing", out["created"], 0)
    check("and says what the view is", "nothing is added to it" in out["add"], True)
    check("no prompt was opened to be refused afterwards", out["screens"], 1)
    check("a paste creates nothing either", out["created_by_paste"], 0)
    check("and says the same thing", "nothing is added to it" in out["paste"], True)
    check("the previous day is not a place to go", out["after_h"] is ARCHIVE, True)
    check("nor the next", out["after_l"] is ARCHIVE, True)
    check("and the board says the archive has no days",
          "has no days" in out["day_said"], True)
    check("reordering says what this view is ordered by",
          "when things were archived" in out["move"], True)
    check("today is the way back", out["after_t"], TODAY)
    check("and so are the other two views",
          (out["after_i"], out["after_s"]), (Bucket.INBOX, Bucket.SOMEDAY))


def a_marked_set_is_refused_too():
    import asyncio
    print("\n5.3 a marked set is refused before anything is reported")
    # The hole this was written for: every write is refused one row at a time
    # by the funnel, but a key acting on a marked set reports what it did
    # before those refusals land -- so the board said "Brought back 3" of
    # three rows it had not touched, and no check here would have known.
    WRITES = ("x", "p", "g", "full_stop")

    async def run():
        rows = [archived(f"T-{i}", f"row {i}", i) for i in range(4)]
        api = StubClient(list(rows))
        app = board_with([], client=api)
        said = []
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 25)
            for _ in range(3):
                await pilot.press("v")
                await settle(pilot, 6)
            marked = len(app.marked)
            for key in WRITES:
                await pilot.press(key)
                await settle(pilot, 25)
                said.append(str(app.query_one("#status").content))
                await pilot.press("escape")
                await settle(pilot, 8)
                for ident in [t.id for t in rows][:3]:
                    if ident not in app.marked:
                        app.marked.append(ident)
                        app._marked_rows[ident] = api.store[ident]
                app.repaint()
                await settle(pilot, 6)
            wrote = [c for c, _ in api.calls if c not in StubClient.READS
                     and c != "iter_archived"]
            state = {t.id: t.checked for t in api.store.values()}
        return marked, said, wrote, state

    marked, said, wrote, state = asyncio.run(run())
    check("three rows were marked", marked, 3)
    check("every key says what the archive allows",
          all("archive" in t and "only un-ticking and dating" in t
              for t in said), True)
    check("none of them reports having done anything",
          [t for t in said if "Brought back" in t or "Finished" in t
           or "Moved" in t or "Cancelled" in t], [])
    check("and nothing was sent", wrote, [])
    check("every row is exactly as it was",
          state, {f"T-{i}": CHECKED for i in range(4)})


def a_task_is_brought_back():
    import asyncio
    from datetime import date as _date
    print("\n5.6 un-ticking brings a task back, and dating sends it somewhere")

    async def run():
        rows = [archived(f"T-{i}", f"row {i}", 10 + i) for i in range(4)]
        api = StubClient(list(rows))
        app = board_with([], client=api)
        out = {}
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 25)
            # a single row, un-ticked
            first = app.tasks[0].id
            await pilot.press("space")
            await settle(pilot, 25)
            out["unticked"] = [c for c in api.calls if c[0] == "set_done"]
            out["still_there"] = [t.id for t in app.tasks]
            out["drawn_as"] = app.query_one("#status").content, \
                              str(app.board().paint().cells[0][1])
            out["store"] = api.store[first].checked
            out["pending"] = sum(len(q) for q in app._pending.values())
            out["count_line"] = str(app.query_one("#status").content)
            # dated, from the archive, to today
            await pilot.press("d")
            await settle(pilot, 10)
            await pilot.press("t")
            await settle(pilot, 25)
            out["dated"] = [c for c in api.calls if c[0] == "set_schedule"]
            out["after_date"] = [t.id for t in app.tasks]
            started = api.store[first].local_start(TZ)
            out["start"] = started.date() if started else None
            # undo takes the date back, and again the un-tick
            await pilot.press("u")
            await settle(pilot, 25)
            started = api.store[first].local_start(TZ)
            out["undo_1"] = started.date() if started else None
            await pilot.press("u")
            await settle(pilot, 25)
            out["undo_2"] = api.store[first].checked
            out["after_undo"] = str(app.board().paint().cells[0][1])
            # a marked set, un-ticked together
            await pilot.press("v")
            await settle(pilot, 6)
            await pilot.press("v")
            await settle(pilot, 6)
            await pilot.press("space")
            await settle(pilot, 30)
            out["set_said"] = str(app.query_one("#status").content)
            out["set_store"] = [api.store[t.id].checked for t in rows[0:2]]
            out["set_rows"] = len(app.tasks)
            # and a reload re-reads: the brought-back rows leave
            await pilot.press("r")
            await settle(pilot, 30)
            out["after_reload"] = len(app.tasks)
        return out

    out = asyncio.run(run())
    today = TODAY
    check("space un-ticks the row", [c[1][1] for c in out["unticked"]], [False])
    check("the store agrees", out["store"], 0)
    check("nothing is left pending", out["pending"], 0)
    check("the row stays on screen", len(out["still_there"]), 4)
    check("drawn as unfinished", out["drawn_as"][1], board.MARKS[0])
    check("the line still counts the archive", out["count_line"].startswith("4 archived"), True)
    check("d dates it from here", [c[1][1] for c in out["dated"]], [today])
    check("the store has the date", out["start"], today)
    check("and the row is still on screen", len(out["after_date"]), 4)
    check("undo takes the date back", out["undo_1"] != today, True)
    check("undo again re-ticks it", out["undo_2"], CHECKED)
    check("and it is drawn finished once more", out["after_undo"], board.MARKS[CHECKED])
    check("a marked set is brought back together", out["set_store"], [0, 0])
    check("and the board says so, truthfully", out["set_said"], "Brought back 2")
    check("with every row still drawn", out["set_rows"], 4)
    # Two were brought back by the set and two are still finished.
    check("a reload re-reads, and the brought-back rows leave", out["after_reload"], 2)


def nothing_of_it_is_written_down():
    import asyncio
    print("\n5.2 the archive is held and never written")
    rows = [archived(f"T-{i}", f"row {i}", i) for i in range(4)]

    def files_under(root):
        found = {}
        for here, _dirs, names in _os.walk(root):
            if "__pycache__" in here or "/.git" in here:
                continue
            for name in names:
                path = _os.path.join(here, name)
                try:
                    found[path] = _os.stat(path).st_mtime_ns
                except OSError:
                    pass
        return found

    async def run():
        app = board_with(rows)
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            before = files_under(_REPO)
            await pilot.press("A")
            await settle(pilot, 30)
            held = len(app.tasks)
            after = files_under(_REPO)
        return held, before, after

    held, before, after = asyncio.run(run())
    check("the archive was read", held, 4)
    check("and no file was added", sorted(set(after) - set(before)), [])
    check("and none was written to",
          [f for f in before if f in after and after[f] != before[f]], [])

    print("\n     a board opened again holds none of it until it is asked for")
    app = board_with(rows)
    check("nothing is held at the start", app.archive, None)
    check("which is not the same as an archive that is empty",
          app.archive == [], False)


def a_failure_is_the_archives_own():
    import asyncio
    from singularity import SingularityError
    print("\n5.5 when the store will not answer for the archive")

    async def run():
        api = StubClient([mk("T-live", "still to do", TODAY)])
        api.fail["iter_archived"] = SingularityError("the store said no")
        app = board_with([], client=api)
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot, 14)
            await pilot.press("A")
            await settle(pilot, 20)
            said = str(app.query_one("#status").content)
            await pilot.press("t")
            await settle(pilot, 20)
            day = (app.position, len(app.tasks),
                   str(app.query_one("#status").content))
            await pilot.press("A")
            await settle(pilot, 20)
            asked = api.count("iter_archived")
            del api.fail["iter_archived"]
            await pilot.press("r")
            await settle(pilot, 20)
            return said, day, asked, str(app.query_one("#status").content)

    said, day, asked, after = asyncio.run(run())
    check("the board says the archive could not be read",
          said.startswith("The archive could not be read"), True)
    check("and why", "the store said no" in said, True)
    check("a calendar day still loads", day[0], TODAY)
    check("with its own tasks on it", day[1], 1)
    check("and says nothing about the archive",
          "archive" in day[2].lower(), False)
    check("asking again tries again", asked, 2)
    check("and a reload that succeeds leaves the failure behind",
          "could not be read" in after, False)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_archive_date_is_read,
    the_query_pages_and_drops,
    the_archive_is_its_own_position,
    asking_for_the_shown_view,
    the_board_paints_an_archive,
    the_order_is_by_when_it_was_archived,
    the_bound_draws_the_newest,
    the_cell_carries_the_date,
    the_line_counts_the_archive,
    # Before the parts below, and not last: they start a board, which is the
    # one thing this check exists to prove the ones above never did.
    nothing_here_touched_a_screen,
    the_key_reaches_the_view,
    it_fills_as_the_pages_arrive,
    every_other_write_is_refused,
    a_marked_set_is_refused_too,
    a_task_is_brought_back,
    nothing_of_it_is_written_down,
    nothing_is_added_and_no_day_is_next,
    a_failure_is_the_archives_own,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
