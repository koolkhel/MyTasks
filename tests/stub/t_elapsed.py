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
from contextlib import asynccontextmanager, contextmanager
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

# -- the three positions in time, built to be true at any hour --------------
# These used to be written inline as arithmetic on the hour with the end
# clamped to 23, and the clamp inverted them: at hour 23 an event meant to span
# the present became 22:00-23:00, which is already over, and the check then
# asserted the opposite of what it set out to.  Five fixtures across four
# blocks did it, and the suite was red for the last two hours of every day.
#
# `ev` rolls an end hour of 24 to the next day's midnight, so there was never
# anything to clamp around.

def hour():
    """The hour to build a fixture for, read now rather than at import.

    Read once at import, a suite could build a fixture for hour 10 and assert
    against it at 11:00:01.  Reading it where the fixture is built narrows that
    window from the suite's whole runtime to the moment between building and
    asserting.
    """
    return dt.datetime.now(TZ).hour


def spans_now(title, h, day=None):
    """An event containing the present.  Exists at every hour."""
    return ev(title, h, h + 1, day=day)


def after_now(title, h, day=None):
    """An event that has not started.  None exists in the last hour.

    The assertion is the guard, not a comment: `ev` takes the start hour
    modulo 24, so asking for hour 24 would silently give **midnight today** --
    in the past -- and a check for "still to come" would pass for the opposite
    of its reason.  Better to raise here than to be quietly wrong there.
    """
    assert h <= 22, f"no hour is still to come at {h}; the caller must skip"
    return ev(title, h + 1, h + 2, day=day)


def before_now(title, h, day=None):
    """An event already over.  None exists at midnight.

    From the start of the day to the top of the current hour, so it has ended
    for any hour from one.  Written as `h-2 .. h-1` it needed two.
    """
    assert h >= 1, "nothing has ended today at midnight; the caller must skip"
    return ev(title, 0, h, day=day)


#: When each position has an example at all.  Named so a guard reads as the
#: reason it is there rather than as a bound on a number.
def has_ended(h):   return h >= 1
def has_future(h):  return h <= 22


@contextmanager
def clock_at(h):
    """Make the board believe it is half past `h` today.

    The suite already moves the clock this way -- `keeping_up` rebinds
    `main.datetime` to a subclass whose `now` runs three hours ahead, so that
    an event's end can pass without waiting for it.  This is the same seam
    aimed at a chosen hour instead of an offset, which is what lets a fixture
    built for any hour be checked in a run that happens at one.

    Only the board's clock moves.  The fixtures are built from the hour passed
    in, so the pair under test is the fixture and the present it was built
    for.
    """
    real = main.datetime
    at = dt.datetime.combine(TODAY, dt.time(h, 30))

    class Frozen(real):
        @classmethod
        def now(cls, tz=None):
            return at.astimezone(tz) if tz is not None else at

    main.datetime = Frozen
    try:
        yield
    finally:
        main.datetime = real


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
    h = hour()
    events = []
    if has_ended(h): events.append(before_now("over", h))
    events.append(spans_now("under way", h))
    if has_future(h): events.append(after_now("to come", h))
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
    h = hour()
    events = ([before_now("over", h)] if has_ended(h) else []) + \
             ([after_now("to come", h)] if has_future(h) else [])
    async with board(events) as (app, pilot):
        app.reference = None          # what the store returns for any other day
        app.repaint()
        await pilot.pause()
        if has_ended(h):
            check("an ended event is still receded", dimmed(app, "over"), True)
        else:
            print("      (skipped: nothing has ended today at midnight)")
        if has_future(h):
            check("and one to come is still not", dimmed(app, "to come"), False)
        else:
            print("      (skipped: nothing is still to come in the last hour)")

    n = TODAY + dt.timedelta(days=1)
    async with board([ev("tomorrow 09", 9, 10, day=n),
                      ev("tomorrow all", 0, 24, day=n, all_day=True)],
                     tasks=[], day=n) as (app, pilot):
        check("no event on a later day is past",
              [dimmed(app, t) for t in ("tomorrow 09", "tomorrow all")], [False, False])

# ------------------------------------------------------------ selected row
async def selected():
    print("still legible while selected")
    h = hour()
    # This one compares the two against each other, so it needs an hour that
    # has both: not midnight, when nothing has ended, and not the last hour,
    # when nothing is still to come.
    if not (has_ended(h) and has_future(h)):
        print("      (skipped: this hour has no ended event and one still to "
              "come at the same time)")
        return
    async with board([before_now("over", h), after_now("to come", h)]) as (app, pilot):
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

# ------------------------------------------ the positions, at every hour
async def every_hour():
    """The three positions, built for each hour and checked against it.

    The point of the suite is that an event over, under way or still to come
    is drawn according to which it is.  For most of a day any arithmetic on
    the hour gets that right, which is why fixtures clamped to hour 23 went
    unnoticed until a run happened to fall in the last two hours of the day.

    So rather than trust the hour this run falls in, each hour is built for and
    then presented to the board as the present.  What is under test is the pair
    -- the fixture and the moment it was built for -- and the board's own
    dimming is the judge, reading the clock through the seam `keeping_up`
    already uses.
    """
    print("the three positions hold at every hour of the day")

    def really(position, event, at):
        """Whether the event is, in fact, the position it is named for.

        Asked of the fixture's own span, not of how the board drew it.  The
        board's dimming answers only "has this ended", so it cannot tell an
        event under way from one still to come -- and a clamped `to come`
        fixture at hour 22 became 22:00-23:00, which is under way.  The check
        passed anyway, for the wrong reason.  This is what notices.
        """
        if position == "over":
            return event.end <= at
        if position == "under way":
            return event.start <= at < event.end
        return at < event.start          # still to come

    lying = []
    wrong = []
    skipped = []
    for h in range(24):
        at = dt.datetime.combine(TODAY, dt.time(h, 30))
        want = [("under way", spans_now("under way", h), False)]
        if has_ended(h):
            want.append(("over", before_now("over", h), True))
        else:
            skipped.append(f"over@{h}")
        if has_future(h):
            want.append(("to come", after_now("to come", h), False))
        else:
            skipped.append(f"to come@{h}")
        for title, event, _ in want:
            if not really(title, event, at):
                lying.append(f"{title}@{h:02d}")
        with clock_at(h):
            async with board([e for _, e, _ in want]) as (app, pilot):
                for title, _, receded in want:
                    if dimmed(app, title) != receded:
                        wrong.append(f"{title}@{h:02d}")
    check("every fixture really is the position it is named for", lying, [])
    check("and the board draws each accordingly at every hour", wrong, [])
    # Skipped because no example exists, not because it was awkward: at
    # midnight nothing has ended today, and in the last hour nothing is still
    # to come.
    check("and the only cases skipped are the two that cannot exist",
          skipped, ["over@0", "to come@23"])
    print(f"      24 hours checked, {len(skipped)} case(s) skipped: "
          f"{', '.join(skipped)}")


# ----------------------------------------------------------------- the timer
async def keeping_up():
    print("keeping up as the hour passes")
    h = hour()
    events = [spans_now("crosses", h)] + \
             ([after_now("to come", h)] if has_future(h) else [])
    async with board(events) as (app, pilot):
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
    await every_hour()
    await other_days()
    await selected()
    await keeping_up()
    await clock()
    await header_reads()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
