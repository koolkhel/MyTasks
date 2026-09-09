"""The calendar in the board: ordering, refusals, the work filter, config."""
import asyncio, datetime as dt, sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import main, ical

TODAY = dt.datetime.now(TZ).date()
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

CFG = ical.Config(work="WorkAcc", personal=("Me",))

def ev(title, hh=None, mm=0, account="Me", cal="c"):
    start = dt.datetime.combine(TODAY, dt.time(hh or 0, mm))
    return ical.Event(title=title, account=account, calendar=cal, start=start,
                      end=start + dt.timedelta(hours=1), all_day=hh is None)

async def board(tasks, events, work_project="P-work", fail=None, config=CFG):
    app = main.TaskApp()
    app.client = StubClient(tasks, reference=dt.datetime.now(TZ))
    app.work_project = work_project
    app.calendar_config = config
    app.tracker_config = None
    calls = []
    def fetch(cfg, day):
        calls.append(day)
        if fail is not None:
            raise fail
        return list(events)
    ical_fetch, ical.fetch = ical.fetch, fetch
    return app, calls, ical_fetch

def titles(app):
    return [t.raw.get("title") for t in app.tasks]

async def run(tasks, events, **kw):
    app, calls, saved = await board(tasks, events, **kw)
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            yield_state = (list(app.tasks), app.query_one("#status").render(), app, pilot, calls)
            return yield_state
    finally:
        ical.fetch = saved

# ---------------------------------------------------------------- ordering
async def ordering():
    print("events fall in the day in the order they happen")
    tasks = [mk("t1", "task at 08", TODAY, timed=True),
             mk("t2", "task at 11", TODAY, timed=True)]
    tasks[0].raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(8, 0), tzinfo=TZ))
    tasks[1].raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(11, 0), tzinfo=TZ))
    events = [ev("event at 09", 9), ev("event at 13", 13), ev("whole day")]
    app, calls, saved = await board(tasks, events)
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            got = titles(app)
            check("all-day leads, then rows in clock order", got,
                  ["whole day", "task at 08", "event at 09", "task at 11", "event at 13"])
            check("the day is read for", calls, [TODAY])
            status = str(app.query_one("#status").render())
            check("events counted apart from tasks", "2 task(s)" in status and "3 event(s)" in status, True)
            # the tasks' own order, with every event disregarded
            app.calendar_config = None
            app.repaint()
            alone = titles(app)
            check("tasks alone", alone, ["task at 08", "task at 11"])
            check("the tasks keep their order among themselves",
                  [t for t in got if t in alone], alone)
            # A task naming no time has no place on the clock, so it sits
            # below the events -- the board's own "timed before all-day"
            # rule, applied to rows rather than only to tasks.
            app.calendar_config = CFG
            app.repaint()
            untimed = mk("t3", "no time at all", TODAY)
            app._base = list(app._base) + [untimed]
            app.repaint()
            got2 = titles(app)
            check("a timed event sits above a task naming no time",
                  got2.index("event at 09") < got2.index("no time at all"), True)
            check("and an all-day event still leads everything",
                  got2[0], "whole day")
    finally:
        ical.fetch = saved

# ------------------------------------------------------- the row an event gets
async def row_shape():
    print("an event is shown with its time and its name, marked apart")
    tasks = [mk("t1", "a task", TODAY)]
    app, calls, saved = await board(tasks, [ev("a meeting", 9, 30), ev("a whole day")])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            rows = {t.raw["title"]: app.row_for(t) for t in app.tasks}
            timed, whole, task = rows["a meeting"], rows["a whole day"], rows["a task"]
            check("the time it starts", timed[2], "09:30")
            check("a whole day says so rather than showing midnight", whole[2], "all-day")
            check("what it is called", str(timed[3]), "a meeting")
            check("its own mark, not a checkbox", (timed[1], whole[1]),
                  (main.EVENT_ROW_MARK, main.EVENT_ROW_MARK))
            check("which the tasks do not share", task[1] != main.EVENT_ROW_MARK, True)
            check("nor the tracker", main.EVENT_ROW_MARK != main.TRACKER_ROW_MARK, True)
            check("and it is told apart without colour",
                  main.EVENT_ROW_MARK.isprintable() and "[" not in main.EVENT_ROW_MARK, True)
            check("the calendar it came from stands where a project would",
                  str(timed[4]).strip(), "c")
    finally:
        ical.fetch = saved

# --------------------------------------------------------------- refusals
async def refusals():
    print("an event cannot be changed from the board")
    tasks = [mk("t1", "a real task", TODAY)]
    app, calls, saved = await board(tasks, [ev("a meeting", 9)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            row = next(i for i, t in enumerate(app.tasks) if app.is_event(t))
            app.query_one(main.DataTable).move_cursor(row=row)
            app._selected_id = app.tasks[row].id
            await pilot.pause()
            writes_before = [c for c, _ in app.client.calls if c not in StubClient.READS]
            for key in ["space", "x", "d", "g", "p", "1", "j"]:
                await pilot.press(key)
                await pilot.pause()
            writes_after = [c for c, _ in app.client.calls if c not in StubClient.READS]
            check("no key that writes wrote anything", writes_after, writes_before)
            said = str(app.query_one("#status").render())
            check("and the board says why", "calendar" in said.lower(), True)
            check("the event is still on the board", sum(1 for t in app.tasks if app.is_event(t)), 1)
            # reordering
            app.query_one(main.DataTable).move_cursor(row=row)
            app._selected_id = app.tasks[row].id
            before = titles(app)
            await pilot.press("K")
            await pilot.pause()
            check("moving does not reach an event", titles(app), before)
            check("and says why", "calendar" in str(app.query_one("#status").render()).lower(), True)
    finally:
        ical.fetch = saved

# ------------------------------------------------------------ work filter
async def work_filter():
    print("work events are hidden with the rest of the work")
    tasks = [mk("t1", "work task", TODAY, project="P-work"),
             mk("t2", "own task", TODAY)]
    events = [ev("work meeting", 9, account="WorkAcc"), ev("my thing", 10, account="Me")]
    app, calls, saved = await board(tasks, events)
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            check("all four rows", len(app.tasks), 4)
            await pilot.press("w")
            await pilot.pause()
            check("the work account's event goes with the work task",
                  titles(app), ["my thing", "own task"])
            status = str(app.query_one("#status").render())
            check("the hidden count includes the event", "2 work hidden" in status, True)
            await pilot.press("w")
            await pilot.pause()
            check("pressing again brings them back", len(app.tasks), 4)
            writes = [c for c, _ in app.client.calls
                      if c not in StubClient.READS | {"tag_title"}]
            check("and nothing was written either way", writes, [])
    finally:
        ical.fetch = saved

# ---------------------------------------------------------- configuration
async def configuration():
    print("when the calendar cannot be read")
    tasks = [mk("t1", "still here", TODAY)]
    app, calls, saved = await board(
        tasks, [], fail=ical.CalendarUnreadable("permission to read the calendar was refused"))
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            check("the day's tasks are shown regardless", titles(app), ["still here"])
            said = str(app.query_one("#status").render())
            check("and the trouble is said once", "refused" in said, True)
            # recovering
            ical.fetch = lambda cfg, day: [ev("back again", 9)]
            await pilot.press("r")
            for _ in range(12):
                await pilot.pause()
            check("recovers on a refresh without a restart",
                  titles(app), ["back again", "still here"])
            check("and the message goes",
                  "refused" not in str(app.query_one("#status").render()), True)
    finally:
        ical.fetch = saved

    print("no calendar configured")
    app, calls, saved = await board([mk("t1", "alone", TODAY)], [ev("never", 9)], config=None)
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            check("no events, and nothing asked of the calendar", (titles(app), calls), (["alone"], []))
            check("and no failure reported", app.calendar_error, None)
    finally:
        ical.fetch = saved

    print("a day that is not a day")
    app, calls, saved = await board([mk("i1", "in the inbox")], [ev("never", 9)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            await pilot.press("i")
            for _ in range(12):
                await pilot.pause()
            check("the inbox holds no events", [t for t in app.tasks if app.is_event(t)], [])
    finally:
        ical.fetch = saved

# ------------------------------------------------------------- day change
async def day_change():
    print("the day being viewed is the day read")
    by_day = {TODAY: [ev("today's own", 9)],
              TODAY + dt.timedelta(days=1): [ev("tomorrow's own", 9)]}
    app = main.TaskApp()
    app.client = StubClient([mk("t1", "a task", TODAY)], reference=dt.datetime.now(TZ))
    app.calendar_config = CFG
    app.tracker_config = None
    saved = ical.fetch
    ical.fetch = lambda cfg, day: list(by_day.get(day, []))
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            check("today's event", "today's own" in titles(app), True)
            await pilot.press("l")
            for _ in range(15):
                await pilot.pause()
            got = titles(app)
            check("moving on shows that day's events", "tomorrow's own" in got, True)
            check("and not the day before's", "today's own" in got, False)
    finally:
        ical.fetch = saved

# ------------------------------------------------- the calendar never waits
async def never_waits():
    print("the calendar does not delay the day")
    import threading, time
    gate = threading.Event()
    app = main.TaskApp()
    app.client = StubClient([mk("t1", "wants the screen", TODAY)],
                            reference=dt.datetime.now(TZ))
    app.calendar_config = CFG
    app.tracker_config = None
    saved = ical.fetch
    def slow(cfg, day):
        gate.wait(10)
        return [ev("late arrival", 9)]
    ical.fetch = slow
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(15):
                await pilot.pause()
            check("the tasks are on screen with the calendar still reading",
                  titles(app), ["wants the screen"])
            check("and the board is not saying it is loading",
                  "Loading" in str(app.query_one("#status").render()), False)
            gate.set()
            for _ in range(20):
                await pilot.pause()
            check("the event joins when it arrives",
                  titles(app), ["late arrival", "wants the screen"])
    finally:
        gate.set()
        ical.fetch = saved

# ------------------------------------------------ all-day events lead the day
async def all_day_leads():
    print("an all-day event leads every other row")
    import tracker
    past = mk("p1", "past due", TODAY - dt.timedelta(days=2))
    untimed = mk("u1", "untimed today", TODAY)
    at8 = mk("t1", "at 08", TODAY, timed=True)
    at8.raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(8, 0), tzinfo=TZ))
    done = mk("d1", "finished", TODAY, checked=CHECKED)
    events = [ev("all A", None), ev("all B", None), ev("at 09", 9)]
    app, calls, saved = await board([past, untimed, at8, done], events)
    try:
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(12):
                await pilot.pause()
            app.tracker_issues = [tracker.Issue(key="AB-1", summary="an issue",
                                                project="P", state="In progress",
                                                assignee="me", base_url="https://tr.example")]
            app.repaint()
            await pilot.pause()
            rows = [("EVENT" if app.is_event(t) else
                     "ISSUE" if app.is_tracker(t) else "task", t.raw.get("title"))
                    for t in app.tasks]
            for line in rows: print("     ", line)
            allday = [i for i, t in enumerate(app.tasks)
                      if app.is_event(t) and t.raw.get(main.EVENT_MINUTES) is None]
            check("every all-day event leads the list", allday, [0, 1])
            check("above the past-due task",
                  rows.index(("task", "past due")) > max(allday), True)
            check("above the day's own untimed task",
                  rows.index(("task", "untimed today")) > max(allday), True)
            check("above the tracker block",
                  rows.index(("ISSUE", "AB-1 \u2014 an issue")) > max(allday), True)
            check("and the two kinds are not mixed together",
                  [k for k, _ in rows[:2]], ["EVENT", "EVENT"])
            check("several keep a stable order among themselves",
                  [t for k, t in rows[:2]], ["all A", "all B"])
            app.repaint()
            await pilot.pause()
            again = [t.raw.get("title") for t in app.tasks[:2]]
            check("and keep it across a repaint", again, ["all A", "all B"])
            # the timed event's own placement is untouched
            check("the timed event still falls after the 08:00 task",
                  rows.index(("EVENT", "at 09")) > rows.index(("task", "at 08")), True)
            check("and above the finished task",
                  rows.index(("EVENT", "at 09")) < rows.index(("task", "finished")), True)
    finally:
        ical.fetch = saved


async def main_():
    await all_day_leads()
    await never_waits()
    await ordering()
    await row_shape()
    await refusals()
    await work_filter()
    await configuration()
    await day_change()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
