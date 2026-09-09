"""An event that has ended shows as past; the clock shows the time.

Synthetic events only.
"""
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
from contextlib import asynccontextmanager
from textual.widgets import DataTable
from textual.widgets._header import HeaderClock

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
CFG = ical.Config(work="W", personal=("Me",))
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def ev(title, start_h, end_h, day=None, all_day=False):
    d = day or TODAY
    return ical.Event(title=title, account="Me", calendar="c",
                      start=dt.datetime.combine(d, dt.time(start_h % 24, 0)),
                      end=(dt.datetime.combine(d, dt.time(end_h, 0)) if end_h < 24
                           else dt.datetime.combine(d + dt.timedelta(days=1), dt.time.min)),
                      all_day=all_day)

@asynccontextmanager
async def board(events, tasks=None, day=None):
    app = main.TaskApp(day) if day else main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [mk("t1", "a task", TODAY)],
                            reference=NOW)
    app.calendar_config = CFG
    app.tracker_config = None
    saved = ical.fetch
    ical.fetch = lambda cfg, d: list(events)
    try:
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(14): await pilot.pause()
            yield app, pilot
    finally:
        ical.fetch = saved

def dimmed(app, title):
    """Is this event's NAME drawn receded?

    The name, not the row: an event's calendar column is dim for every
    event, ended or not, so asking whether anything in the row is dim would
    always answer yes.
    """
    t = next(x for x in app.tasks if x.raw.get("title") == title)
    name = app.row_for(t)[3]
    spans = getattr(name, "spans", ())
    return bool(any("dim" in str(sp.style) for sp in spans))

def cell(app, title, i):
    t = next(x for x in app.tasks if x.raw.get("title") == title)
    return str(app.row_for(t)[i])

# ------------------------------------------------------- the three positions
async def positions():
    print("the three positions in time")
    h = NOW.hour
    events = []
    if h >= 2: events.append(ev("over", h - 2, h - 1))
    events.append(ev("under way", max(h - 1, 0), min(h + 1, 23)))
    if h <= 21: events.append(ev("to come", h + 1, h + 2))
    async with board(events) as (app, pilot):
        titles = [e.title for e in events]
        for t in titles:
            print(f"      {t:10} dim={dimmed(app, t)}")
        if "over" in titles:
            check("an event that is over is receded", dimmed(app, "over"), True)
        check("one under way is not", dimmed(app, "under way"), False)
        if "to come" in titles:
            check("one still to come is not", dimmed(app, "to come"), False)
        # nothing else about the row changed
        if "over" in titles:
            check("it keeps its mark", cell(app, "over", 1), main.EVENT_ROW_MARK)
            check("it keeps its start time",
                  cell(app, "over", 2), f"{(h-2)%24:02d}:00")
            check("its name is all there", "over" in cell(app, "over", 3), True)
            check("it keeps its calendar", "c" in cell(app, "over", 4), True)
            check("it is not struck out", "strike" in cell(app, "over", 3), False)

# --------------------------------------------------------- days either side
async def other_days():
    print("a day behind, and a day ahead")
    y = TODAY - dt.timedelta(days=1)
    async with board([ev("yesterday 09", 9, 10, day=y),
                      ev("yesterday all", 0, 24, day=y, all_day=True)],
                     tasks=[], day=y) as (app, pilot):
        check("every event on an earlier day is past",
              [dimmed(app, t) for t in ("yesterday 09", "yesterday all")], [True, True])
    print("with no reference at all, as every day but today really has")
    h = NOW.hour
    async with board([ev("over", max(h - 2, 0), max(h - 1, 1)),
                      ev("to come", min(h + 1, 22), 23)]) as (app, pilot):
        app.reference = None          # what the store returns for any other day
        app.repaint()
        await pilot.pause()
        if h >= 2:
            check("an ended event is still receded", dimmed(app, "over"), True)
        check("and one to come is still not", dimmed(app, "to come"), False)

    n = TODAY + dt.timedelta(days=1)
    async with board([ev("tomorrow 09", 9, 10, day=n),
                      ev("tomorrow all", 0, 24, day=n, all_day=True)],
                     tasks=[], day=n) as (app, pilot):
        check("no event on a later day is past",
              [dimmed(app, t) for t in ("tomorrow 09", "tomorrow all")], [False, False])

# ------------------------------------------------------------ selected row
async def selected():
    print("still legible while selected")
    h = NOW.hour
    if h < 2:
        print("      (skipped: too early in the day to place a finished event)")
        return
    async with board([ev("over", h - 2, h - 1), ev("to come", min(h + 1, 22), 23)]) as (app, pilot):
        row = next(i for i, t in enumerate(app.tasks) if t.raw.get("title") == "over")
        table = app.query_one(DataTable)
        table.move_cursor(row=row)
        await pilot.pause()
        def name_is_dim(line, text):
            """Is the segment carrying this name dim, on the rendered line?"""
            return any(s.style.dim for s in table.render_line(line)
                       if text in s.text)
        check("the selected ended row keeps its name dim",
              name_is_dim(1 + row, "over"), True)
        other = next(i for i, t in enumerate(app.tasks) if t.raw.get("title") == "to come")
        table.move_cursor(row=other)
        await pilot.pause()
        check("while a selected one still to come does not",
              name_is_dim(1 + other, "to come"), False)
        # and the distinction survives BOTH being unselected vs selected
        check("the two differ while one of them is selected",
              name_is_dim(1 + row, "over") != name_is_dim(1 + other, "to come"), True)

# ----------------------------------------------------------------- the timer
async def keeping_up():
    print("keeping up as the hour passes")
    h = NOW.hour
    async with board([ev("crosses", max(h - 1, 0), min(h + 1, 23)),
                      ev("to come", min(h + 2, 22), 23)]) as (app, pilot):
        check("not yet past", dimmed(app, "crosses"), False)
        counted = app._ended_shown
        # the row list is untouched by a tick that changes nothing
        before = [t.id for t in app.tasks]
        app.recheck_elapsed()
        await pilot.pause()
        check("a tick that changes nothing leaves the rows alone",
              [t.id for t in app.tasks], before)
        check("and does not move the count", app._ended_shown, counted)
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("and fetches nothing", writes, [])
        reads_before = app.client.count("tasks_at")
        # now let the clock appear to move past its end
        real = main.datetime
        class Later(real):
            @classmethod
            def now(cls, tz=None):
                return real.now(tz) + dt.timedelta(hours=3)
        main.datetime = Later
        try:
            app.recheck_elapsed()
            for _ in range(8): await pilot.pause()
            check("once its end passes, the row is receded", dimmed(app, "crosses"), True)
            check("and the day was not fetched again",
                  app.client.count("tasks_at"), reads_before)
        finally:
            main.datetime = real

    print("a view holding no events at all")
    async with board([], tasks=[mk("t1", "a task", TODAY)]) as (app, pilot):
        app.recheck_elapsed()
        await pilot.pause()
        check("the check is harmless", app._ended_shown, 0)

# ------------------------------------------------------------------- clock
async def clock():
    print("the clock")
    async with board([]) as (app, pilot):
        c = app.query_one(HeaderClock)
        shown = str(c.render())
        check("it is on screen", bool(shown.strip()), True)
        import re
        check("and reads as hours and minutes, no seconds",
              bool(re.fullmatch(r"\d{2}:\d{2}", shown.strip())), True)
        before = [t.id for t in app.tasks]
        cur = app.query_one(DataTable).cursor_row
        c.refresh()
        for _ in range(4): await pilot.pause()
        check("the clock refreshing leaves the rows alone",
              [t.id for t in app.tasks], before)
        check("and the cursor where it was", app.query_one(DataTable).cursor_row, cur)

# ------------------------------------------------ the header reads in both themes
def _lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c.triplet
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)
def _ratio(fg, bg):
    a, b = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)

async def header_reads():
    print("the header reads in both themes")
    from textual.widgets._header import HeaderTitle
    for theme in (main.TURBO_DARK.name, main.TURBO_BLUE.name):
        async with board([]) as (app, pilot):
            app.theme = theme
            for _ in range(4): await pilot.pause()
            for what, w in (("clock", app.query_one(HeaderClock)),
                            ("title", app.query_one(HeaderTitle))):
                st = w.rich_style
                r = _ratio(st.color, st.bgcolor)
                # 4.5:1 is the ordinary-text bar.  The blue theme's header
                # was 2.18:1 before this was fixed -- the framework draws it
                # on $panel, which that palette makes light grey.
                check(f"{theme.split('-')[-1]}: the {what} is readable (>=4.5:1, got {r:.1f})",
                      r >= 4.5, True)
            check(f"{theme.split('-')[-1]}: the app title is unchanged",
                  app.title, "Singularity tasks")


async def main_():
    await positions()
    await other_days()
    await selected()
    await keeping_up()
    await clock()
    await header_reads()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
