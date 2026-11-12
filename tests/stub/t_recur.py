"""The recurring view: what it holds, what it says, and what it refuses.

Two halves, deliberately. What the view *would* draw is decided from the
state alone and is checked without an application at all, the way the
archive's rows are: a check that reached for a running interface would pass
while proving nothing about the decision. What needs a running board -- the
key, the fetch held until a reload, the refusals -- gets one, driven by the
pilot with a stubbed store.

Nothing here reaches the real store. Every series, occurrence and plain task
is invented, and the store is a stub that records what it was asked.
"""
import asyncio
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
from harness import StubClient, iso_z, local_tz, mk, run_parts
import board
import ical
import singularity
import tracker
from singularity import SERIES, Task
from main import TaskApp
from textual import events
from textual.widgets import Static

TZ = local_tz()
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.combine(TODAY, dt.time(12, 0), tzinfo=TZ)

ok = []
def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

CAL = ical.Config(work="WorkAcc", personal=("Me",))
TRACK = tracker.Config(base_url="https://tracker.invalid", token="zz",
                       assignee="me", projects=("ZZA",), states=("open",))
WEEKLY = {"everyweek": {"days": [2], "interval": 1, "type": 1}}
WORKWEEK = {"everyweek": {"days": [1, 2, 3, 4, 5], "interval": 1, "type": 1}}
DAILY = {"everyday": {"interval": 1}}
ENDLESS = {"limit": 5, "date": "2024-09-03T21:00:00.000Z", "iterations": 9}


def series(tid, title, *, repeat=WEEKLY, in_days=1, waits=False, time=None,
           project=None):
    """A series: a task carrying a rule, next coming round in `in_days`."""
    when = None
    if in_days is not None:
        when = iso_z(dt.datetime.combine(TODAY + dt.timedelta(days=in_days),
                                         dt.time(9, 0), tzinfo=TZ))
    rec = {"repeat": repeat, "ending": ENDLESS,
           "startTime": "2024-09-03T21:00:00.000Z",
           "lastGeneratedTaskId": "T-far"}
    if when is not None:
        rec["nextTime"] = when
    if waits:
        rec["onlyOnComplete"] = True
    if time is not None:
        rec["time"] = time
    raw = {"id": tid, "title": title, "checked": 0, "deferred": False,
           "useTime": False, "recurrence": rec,
           "start": iso_z(dt.datetime.combine(TODAY, dt.time(9, 0), tzinfo=TZ))}
    if project:
        raw["projectId"] = project
    return Task(raw)


def occurrence(tid, of, days_ahead):
    """An occurrence: a parent and no rule of its own."""
    return Task({"id": tid, "title": f"occurrence {tid}", "checked": 0,
                 "deferred": False, "useTime": False,
                 "recurrenceGeneratorId": of,
                 "start": iso_z(dt.datetime.combine(
                     TODAY + dt.timedelta(days=days_ahead),
                     dt.time(9, 0), tzinfo=TZ))})


def painting(rows=(), kids=(), *, loading=False, error=None, marked=(),
             width=60, projects=None, **paint):
    """A board holding a swept set of series, and what it would draw."""
    made = board.Board(
        base=[], pending={}, tasks=[], position=SERIES, reference=None,
        tz=TZ, now=NOW, projects=projects or {"P-x": "Sales"},
        marked=list(marked), marked_rows={t.id: t for t in rows},
        searching="", hiding_work=False, work_project="P-work",
        window_reason_now=None, work_override=None, green_tag=None,
        tracker_issues=[], tracker_config=TRACK, events=[], events_day=None,
        calendar_config=CAL, mail_threads=[], notice=None, fetched=True,
        title_width=width, late_colour="#d17e92",
        series=list(rows), occurrences=list(kids),
        series_loading=loading, series_error=error,
    )
    return made, made.paint(**paint)


def app_with(*tasks):
    """A board whose store holds exactly these rows."""
    # `tz` is the app's own read-only property; it derives the machine's
    # zone, which is the one the fixtures above are built in.
    app = TaskApp()
    app.client = StubClient(list(tasks), reference=NOW)
    return app


# ------------------------------------------- 4.2 the rows, and what is queued

def the_view_holds_the_series_alone():
    print("\n4.2 the view lists series, once each, and no occurrence")
    a = series("S-a", "weekly one", in_days=3)
    b = series("S-b", "daily one", repeat=DAILY, in_days=1)
    kids = [occurrence("T-1", "S-a", 3), occurrence("T-2", "S-a", 10),
            occurrence("T-3", "S-b", 1)]
    made, answer = painting([a, b], kids)
    check("both series are drawn", len(answer.rows), 2)
    check("and no occurrence is", [t.id for t in answer.rows], ["S-b", "S-a"])
    check("each appears once",
          len({t.id for t in answer.rows}), len(answer.rows))

    print("\n     soonest first, and no-next last")
    rows = [series("S-far", "far off", in_days=30),
            series("S-none", "no next at all", in_days=None),
            series("S-soon", "very soon", in_days=1)]
    made, answer = painting(rows)
    check("ordered by when each next comes round",
          [t.id for t in answer.rows], ["S-soon", "S-far", "S-none"])

    print("\n     the queued count is what is held, not what the rule implies")
    made, _ = painting([a, b], kids)
    check("a series with two occurrences held reports two",
          made.queued_for(a), (2, TODAY + dt.timedelta(days=10)))
    check("one with a single occurrence reports one",
          made.queued_for(b), (1, TODAY + dt.timedelta(days=1)))
    made, _ = painting([a], [])
    check("one with none held reports none", made.queued_for(a), (0, None))

    print("\n     a waiting series reports one however often its rule repeats")
    waiting = series("S-w", "waits", repeat=DAILY, waits=True, in_days=1)
    made, _ = painting([waiting], [occurrence("T-w", "S-w", -2)])
    check("the count follows the store, not the rule",
          made.queued_for(waiting)[0], 1)
    check("and the facts line says it waits",
          "waits for completion" in made.series_facts_for(waiting))


# ------------------------------------------------ 4.4 what the view says it is

def the_view_says_what_it_holds():
    print("\n4.4 the line under the rows counts series, and says when there are none")
    made, answer = painting([series("S-a", "one"), series("S-b", "two")])
    check("series, not tasks", answer.status.startswith("2 series"), True)
    check("and they are not called tasks", "task(s)" in answer.status, False)

    made, answer = painting([])
    check("an empty view says so rather than saying nothing",
          answer.status.startswith("no recurring tasks"), True)

    print("\n     what the view is doing outranks its counts")
    made, answer = painting([series("S-a", "one")], loading=True)
    check("a sweep in progress is said", "Reading every task" in answer.status)
    made, answer = painting([], error="The repeating tasks could not be read · nope")
    check("a failure is said, as an error",
          (answer.status, answer.status_error),
          ("The repeating tasks could not be read · nope", True))


# ------------------------------------------------------- 4.5 a series' columns

def a_series_row_carries_the_next_occurrence():
    print("\n4.5 the column a start time uses carries the next occurrence")
    s = series("S-a", "weekly one", in_days=2, project="P-x")
    made, answer = painting([s])
    cells = answer.cells[0]
    want = f"{TODAY + dt.timedelta(days=2):%d %b}"
    check("the when column is the next occurrence", cells[2], want)
    check("the title column is the title alone",
          cells[3].plain.startswith("↻ weekly one"), True)
    check("and holds no part of the repeat's phrase",
          "every week" in cells[3].plain, False)
    check("the project column is the project", cells[4].plain.strip(), "Sales")

    print("\n     a time of day goes in the facts line, not the column")
    # The column is eleven cells and shared with the tracker's state labels;
    # "22 Sep 09:15" is twelve and was cut to "22 Sep 09:1" until a picture
    # of the view showed it.  The time is reported beside the rule instead.
    timed = series("S-t", "at six", in_days=2, time="18:00")
    made, answer = painting([timed])
    check("the column is the date alone", answer.cells[0][2], want)
    check("it fits the column it is drawn in",
          len(answer.cells[0][2]) <= board._WHEN_WIDTH, True)
    check("and the time is in the facts line",
          "at 18:00" in made.series_facts_for(timed), True)

    print("\n     a series the store gives no next time for says so")
    made, answer = painting([series("S-n", "nothing", in_days=None)])
    check("rather than leaving the column blank", answer.cells[0][2], "no next")

    print("\n     the facts line is where the repeat is read")
    made, _ = painting([s], [occurrence("T-1", "S-a", 2)])
    check("it carries the phrase, the stacking, the queue and the end",
          made.series_facts_for(s),
          f"every week on Tue  ·  piles up  ·  1 queued to "
          f"{TODAY + dt.timedelta(days=2):%d %b %Y}  ·  no end")


# --------------------------------------------------- 4.1 the key, and the view

def the_key_reaches_the_view():
    print("\n4.1 R shows the view, and it is not a day")
    async def run():
        app = app_with(series("S-a", "weekly one"), mk("P-1", "a plain task", TODAY))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("R")
            for _ in range(8):
                await pilot.pause()
            said = str(app.query_one("#daybar", Static).render())
            rows = [t.id for t in app.tasks]
            before = app.position
            await pilot.press("l")
            for _ in range(4):
                await pilot.pause()
            after = app.position
            keybar = " ".join(str(b) for b in app.BINDINGS)
            return said, rows, before, after, keybar
    said, rows, before, after, keybar = asyncio.run(run())
    check("the view is shown", before is SERIES)
    check("it holds the series and not the plain task", rows, ["S-a"])
    check("the bar names it", "Recurring" in said)
    check("and says it is read only", "read only" in said)
    check("a day key does not turn it into a day", after is SERIES)
    # The label is five characters on purpose: six takes the key bar to a
    # sixth line at eighty columns, and that line comes out of the notes
    # area, which then has nothing.  Checked so a longer one cannot land
    # without the reason being met.
    check("the label fits the bar it is drawn in",
          len("Recur") <= 5, True)
    check("the key is bound and labelled",
          "recurring" in keybar and "Recur" in keybar)


# ------------------------------------------- 4.3 held until a reload

def the_sweep_happens_once_until_a_reload():
    print("\n4.3 read on first asking, held after, read again on a reload")
    async def run():
        app = app_with(series("S-a", "weekly one"),
                       occurrence("T-1", "S-a", 4),
                       mk("P-1", "a plain task", TODAY))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            first = app.client.count("iter_pages")
            await pilot.press("t")
            for _ in range(6):
                await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            again = app.client.count("iter_pages")
            held = [t.id for t in app.tasks]
            await pilot.press("r")
            for _ in range(12):
                await pilot.pause()
            after_reload = app.client.count("iter_pages")
            return first, again, held, after_reload
    first, again, held, after_reload = asyncio.run(run())
    check("the store is read when the view is first asked for", first >= 1)
    check("leaving and coming back reads nothing", again, first)
    check("the rows are still there", held, ["S-a"])
    check("a reload reads again", after_reload > again)


# ----------------------------------------------------- 4.6 nothing is written

def nothing_is_written_from_the_view():
    print("\n4.6 every write is refused, and the board says why")
    # Every key the board binds to something that writes.  Named here so a
    # write added later without a thought for this view shows up as a failure
    # rather than as a silent hole.
    #
    # One board per key, deliberately.  Several of these open a dialog before
    # they write, and a dialog left standing swallows the next key -- so a
    # single board pressed fourteen times would report thirteen refusals it
    # never made.  It did, while this suite was being written, and the key
    # that really got through was the one it hid.
    WRITE_KEYS = ["space", "full_stop", "x", "d", "g", "p", "e", "n", "a",
                  "f", "backspace", "K", "J", "W"]
    WROTE = ("set_", "create", "complete", "uncomplete", "cancel", "delete",
             "move", "archive")

    async def press(key):
        app = app_with(series("S-a", "weekly one"))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            await pilot.press(key)
            for _ in range(6):
                await pilot.pause()
            said = str(app.query_one("#status").render())
            wrote = [c[0] for c in app.client.calls if c[0].startswith(WROTE)]
            # A dialog standing here is its own failure: the key was neither
            # refused nor carried out, it is waiting for a person.
            depth = len(app.screen_stack)
            return said, wrote, depth, [t.id for t in app.tasks]

    # Four of these never reach the view's own refusal, and correctly: they
    # are refused first for a reason of their own -- the row is not a mail
    # thread, not a tracker issue, or the view is not a day and so has no
    # order to move a row within.  What the spec asks is that no write lands
    # and that nothing fails quietly, so that is what is checked for every
    # key, with the view's own wording required of the rest.
    OWN_REFUSAL = {"f", "W", "K", "J"}
    for key in WRITE_KEYS:
        said, wrote, depth, rows = asyncio.run(press(key))
        check(f"{key}: nothing was written", wrote, [])
        check(f"{key}: the board said something rather than nothing",
              said.strip() != "", True)
        if key not in OWN_REFUSAL:
            check(f"{key}: and said the view is a reading",
                  "read here" in said, True)
        check(f"{key}: no dialog was left standing", depth, 1)
        check(f"{key}: the rows are untouched", rows, ["S-a"])

    print("\n     the four refused earlier are refused for their own reason")
    for key, wanted in (("f", "not one of those"),
                        ("W", "Only a tracker issue"),
                        ("K", "when each next comes round"),
                        ("J", "reordering applies to calendar days")):
        said, wrote, _, _ = asyncio.run(press(key))
        check(f"{key}: says why, and it is true of this view",
              wanted in said, True)

    print("\n     the refusal is decided by the view, not by the action")
    # It takes no action at all: the archive's refusal needs one because two
    # writes get through there, and none gets through here.
    async def in_view():
        app = app_with(series("S-a", "weekly one"))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            return app.refuse_series()
    check("asked in the view, it refuses", asyncio.run(in_view()))

    print("\n     the same task on its own day is still writable")
    async def on_its_day():
        app = app_with(series("S-a", "weekly one"))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            return app.refuse_series()
    check("outside the view nothing is refused", asyncio.run(on_its_day()), False)


# ------------------------------------------- 4.7 a paste and an undo

def a_paste_and_an_undo_are_refused_in_the_view():
    print("\n4.7 a paste and an undo are refused too, and the undo is kept")
    # Neither is a key in the list above: a paste is an event, and an undo
    # writes what an earlier action recorded.  A paste here used to end the
    # board, by reading the view as a day to date the new tasks with.
    WROTE = ("set_", "create", "complete", "cancel", "delete", "restore",
             "update")

    async def paste(marks):
        app = app_with(series("S-a", "weekly one"), series("S-b", "weekly two"))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            for _ in range(marks):
                await pilot.press("v")
            app.post_message(events.Paste("- one\n- two"))
            for _ in range(6):
                await pilot.pause()
            said = str(app.query_one("#status").render())
            wrote = [c[0] for c in app.client.calls if c[0].startswith(WROTE)]
            return said, wrote, sorted(t.id for t in app.tasks)

    for marks in (0, 2):
        said, wrote, rows = asyncio.run(paste(marks))
        check(f"a paste, {marks} marked: nothing was written", wrote, [])
        check(f"a paste, {marks} marked: the board says the view is a reading",
              "read here" in said)
        check(f"a paste, {marks} marked: the rows are untouched",
              rows, ["S-a", "S-b"])

    async def undo():
        app = app_with(mk("P-1", "a plain task", TODAY))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("space")
            for _ in range(8):
                await pilot.pause()
            await pilot.press("R")
            for _ in range(10):
                await pilot.pause()
            await pilot.press("u")
            for _ in range(6):
                await pilot.pause()
            said = str(app.query_one("#status").render())
            in_view = app.client.count("restore"), len(app._undo)
            await pilot.press("t")
            for _ in range(10):
                await pilot.pause()
            await pilot.press("u")
            for _ in range(8):
                await pilot.pause()
            return said, in_view, app.client.count("restore")

    said, (restored, kept), later = asyncio.run(undo())
    check("an undo in the view writes nothing", restored, 0)
    check("and says the view is a reading", "read here" in said)
    check("the undo is still there to use", kept, 1)
    check("and works once back on the day", later, 1)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_view_holds_the_series_alone,
    the_view_says_what_it_holds,
    a_series_row_carries_the_next_occurrence,
    the_key_reaches_the_view,
    the_sweep_happens_once_until_a_reload,
    nothing_is_written_from_the_view,
    a_paste_and_an_undo_are_refused_in_the_view,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
