"""The working window: what it says about a moment, and what the board does.

Synthetic tasks and invented hours only.  Every moment here is handed to the
board as an argument rather than waited for, so the suite says the same thing
at three in the morning as it does at noon.
"""
import sys, asyncio
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
# Kept by reference before the harness blanks it: the harness gives every
# stubbed board no window, which is exactly what the other suites need and
# exactly what this one cannot test through.
import singularity
_read_window = singularity.load_working_window
from harness import StubClient, mk, TZ
from datetime import date, datetime, time
import main as M
from main import TaskApp
from textual.widgets import DataTable
from singularity import (WorkingWindow, parse_days, parse_working_window,
                         WORKING_DAYS)

ok = []
def chk(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

def bad(label, hours, days=""):
    """The parser refuses this setting, saying something about it."""
    try:
        parse_working_window(hours, days)
    except ValueError as exc:
        chk(label, str(exc), str(exc))
    else:
        chk(label, False, "no refusal")

# A week of moments, named rather than computed, so a reader can check them.
MON = date(2026, 9, 7)      # a Monday
FRI = date(2026, 9, 11)     # the Friday that week
SAT = date(2026, 9, 12)
SUN = date(2026, 9, 13)
def at(day, h, m=0):
    return datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)


# -- a board with a window -------------------------------------------------
D = date(2099, 9, 1)
WORK = "P-work-0001"


def always():
    """A window holding every minute of every day.  Exact at any instant."""
    return parse_working_window("00:00-24:00", "mon-sun")


def never():
    """A window holding no minute of today, whatever today turns out to be.

    Built from the days rather than the hours because a day outside the
    window is outside it for its whole length: an hour-based fixture would
    have to be built around the present and would be wrong in the minute
    between building it and asserting on it.
    """
    today = datetime.now(TZ).weekday()
    others = ",".join(k for k, v in singularity.WEEKDAYS.items() if v != today)
    return parse_working_window("00:00-24:00", others)


def build(window=None, tasks=None, project=WORK):
    """A board that found this window when it started.

    Substituted around construction rather than assigned afterwards, because
    what the board does at startup is part of what is under test here.
    """
    # Both substituted around construction, not assigned afterwards: the
    # board asks the window at startup and skips it when no work project is
    # configured, so a suite that set the project after building would prove
    # nothing on a machine that happens to have one in `.env` and fail on a
    # machine that does not.
    kept = singularity.load_work_project
    singularity.load_working_window = lambda *a, **k: window
    singularity.load_work_project = lambda *a, **k: project
    try:
        app = TaskApp(D)
    finally:
        singularity.load_working_window = lambda *a, **k: None
        singularity.load_work_project = kept
    app.client = StubClient(tasks if tasks is not None else [])
    app.projects = {WORK: "Work"} if project else {}
    return app


def counting(app):
    """Replace the board's redraw with one that counts, and return the count."""
    drawn = []
    real = app.repaint
    def counted():
        drawn.append(1)
        real()
    app.repaint = counted
    return drawn


def rows(day=D):
    """Two personal tasks and two of the work project's."""
    return [mk("T-p1", "personal one", day),
            mk("T-w1", "work one", day, project=WORK),
            mk("T-p2", "personal two", day),
            mk("T-w2", "work two", day, project=WORK)]


def t_hours():
    print("1.1 the window answers about an hour")
    w = parse_working_window("08:00-18:00")
    chk("inside the range is inside", w.outside(at(FRI, 12)) is None)
    chk("the start hour is inside", w.outside(at(FRI, 8)) is None)
    chk("a minute before the start is outside",
        w.outside(at(FRI, 7, 59)) == "before 08:00", w.outside(at(FRI, 7, 59)))
    chk("a minute before the end is inside", w.outside(at(FRI, 17, 59)) is None)
    chk("the end hour itself is outside",
        w.outside(at(FRI, 18)) == "after 18:00", w.outside(at(FRI, 18)))
    chk("well after the end is outside", w.outside(at(FRI, 23, 30)) == "after 18:00")
    chk("the small hours are outside", w.outside(at(FRI, 3)) == "before 08:00")


def t_days():
    print("1.1 the window answers about a day")
    w = parse_working_window("08:00-18:00")
    chk("a weekday at noon is inside", w.outside(at(MON, 12)) is None)
    chk("Saturday at noon is outside",
        w.outside(at(SAT, 12)) == "outside the working week", w.outside(at(SAT, 12)))
    chk("Sunday at noon is outside", w.outside(at(SUN, 12)) == "outside the working week")
    chk("and a day outside is outside for its whole length",
        all(w.outside(at(SAT, h)) == "outside the working week"
            for h in range(24)))
    chk("the day is what it names, not the hour",
        w.outside(at(SAT, 3)) == "outside the working week", w.outside(at(SAT, 3)))
    weekend = parse_working_window("10:00-14:00", "sat,sun")
    chk("configured days replace the default",
        weekend.outside(at(SAT, 12)) is None
        and weekend.outside(at(MON, 12)) == "outside the working week")


def t_default_days():
    print("1.1 absent days mean Monday to Friday")
    chk("the default is the five weekdays", parse_days("") == WORKING_DAYS)
    chk("which is Monday to Friday", sorted(WORKING_DAYS) == [0, 1, 2, 3, 4])
    w = parse_working_window("08:00-18:00")
    chk("a window built without days uses it", w.days == WORKING_DAYS)
    chk("so Saturday is outside without anyone saying so",
        w.outside(at(SAT, 12)) == "outside the working week")


def t_day_words():
    print("1.1 the day words, as a person writes them")
    chk("a range", parse_days("mon-fri") == frozenset({0, 1, 2, 3, 4}))
    chk("a list", parse_days("mon,wed,fri") == frozenset({0, 2, 4}))
    chk("one day", parse_days("wed") == frozenset({2}))
    chk("a range and a day", parse_days("mon-wed,sun") == frozenset({0, 1, 2, 6}))
    chk("case is ignored", parse_days("MON-Fri") == frozenset({0, 1, 2, 3, 4}))
    chk("spacing is ignored", parse_days(" mon - fri , sun ") ==
        frozenset({0, 1, 2, 3, 4, 6}))
    chk("a range may run round the end of the week",
        parse_days("sun-thu") == frozenset({6, 0, 1, 2, 3}))


def t_unreadable():
    print("1.1 what cannot be read is refused, and says why")
    bad("an end no later than the start", "18:00-08:00")
    bad("an end equal to the start", "09:00-09:00")
    bad("no range at all", "evenings")
    bad("one time only", "08:00")
    bad("an hour that does not exist", "08:00-25:00")
    bad("a minute that does not exist", "08:70-18:00")
    bad("a start at the end of the day", "24:00-24:00")
    bad("a day that is not a day", "08:00-18:00", "mon-funday")
    bad("a range of three", "08:00-18:00", "mon-wed-fri")


def t_midnight():
    print("1.1 the end of the day is a thing a window may name")
    evening = parse_working_window("18:00-24:00")
    chk("an evening window holds the last minute of the day",
        evening.outside(at(FRI, 23, 59)) is None)
    chk("and not the afternoon",
        evening.outside(at(FRI, 17, 59)) == "before 18:00")
    whole = parse_working_window("00:00-24:00", "mon-sun")
    chk("a whole-day window holds every minute of every day",
        not any(whole.outside(at(day, h, m))
                for day in (MON, FRI, SAT, SUN)
                for h in range(24) for m in (0, 30, 59)))
    chk("the window can say how it was written", whole.label() == "00:00-24:00",
        whole.label())
    chk("and so can an ordinary one",
        parse_working_window("08:00-18:00").label() == "08:00-18:00")


def t_reader():
    print("1.2 the reader, on the absent case only")
    # Only the absent case is asserted here.  python-dotenv finds the real
    # `.env` by walking up from singularity.py, so emptying the environment
    # does not hide a configured window -- a check that asserted on one would
    # pass or fail by whose machine ran it.  What the parser does with a
    # configured window is covered above, on strings.
    import os, tempfile
    kept = os.environ.pop("WORK_HOURS", None)
    empty = _os.path.join(tempfile.mkdtemp(prefix="window."), ".env")
    try:
        open(empty, "w").close()
        window = _read_window(empty)
        chk("no WORK_HOURS means no window", window is None, repr(window))
    finally:
        if kept is not None:
            os.environ["WORK_HOURS"] = kept
    chk("the reader is the one the board uses",
        _read_window is not None and callable(_read_window))


async def t_opens():
    print("2.4 the board opens in the state the clock says")
    app = build(never(), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("outside the window, the work is already hidden with no key pressed",
            app.hiding_work is True, repr(app.hiding_work))
        chk("and the board knows the window is what says so",
            app._work_override is None and app._window_hides is True,
            f"{app._work_override!r} {app._window_hides!r}")
    app = build(always(), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("inside the window, nothing is hidden",
            app.hiding_work is False, repr(app.hiding_work))
    app = build(None, rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("with no window configured, nothing is hidden",
            app.hiding_work is False, repr(app.hiding_work))
        chk("and the window was never asked",
            app._window_hides is None, repr(app._window_hides))


async def t_moment():
    print("2.3 the board takes the mode from a moment it is handed")
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        drawn = counting(app)
        app.apply_window(at(FRI, 17, 59))
        chk("a minute before the end, the work is shown",
            app.hiding_work is False, repr(app.hiding_work))
        app.apply_window(at(FRI, 18, 1))
        chk("a minute after it, the work is hidden", app.hiding_work is True)
        chk("and the crossing redrew once", len(drawn) >= 1, str(len(drawn)))
        drawn.clear()
        app.apply_window(at(FRI, 19, 0))
        chk("a later moment on the same side changes nothing",
            app.hiding_work is True and not drawn, str(len(drawn)))
        app.apply_window(at(SAT, 12))
        chk("Saturday noon is still hidden", app.hiding_work is True)
        chk("but the reason changed, so the board redrew to say the new one",
            app._window_reason == "outside the working week" and drawn,
            f"{app._window_reason!r} {len(drawn)}")
        drawn.clear()
        app.apply_window(at(SUN, 12))
        chk("and the rest of the weekend changes nothing again",
            app.hiding_work is True and not drawn, str(len(drawn)))
        app.apply_window(at(MON, 9))
        chk("Monday morning crosses back", app.hiding_work is False)
        chk("and that redrew", len(drawn) >= 1, str(len(drawn)))


async def t_key_still_flips():
    print("2.5 the key still has two states, whatever set the mode")
    app = build(never(), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("the clock hid the work", app.hiding_work is True)
        await pilot.press("w")
        await pilot.pause()
        chk("the key brings it back", app.hiding_work is False)
        chk("and the board records whose decision that is",
            app._work_override is False, repr(app._work_override))
        await pilot.press("w")
        await pilot.pause()
        chk("pressing it again hides it", app.hiding_work is True)
        chk("still as the person's decision", app._work_override is True,
            repr(app._work_override))


async def t_tick():
    print("3.1 one timer, looking at two things")
    src = open(_os.path.join(_REPO, "main.py")).read()
    chk("the slow tick is set up once", src.count("set_interval(ELAPSED_CHECK_SECONDS") == 1)
    chk("and it runs the pair, not the elapsed check alone",
        "set_interval(ELAPSED_CHECK_SECONDS, self.each_minute)" in src)
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        called = []
        app.recheck_elapsed = lambda: called.append("elapsed")
        app.apply_window = lambda *a: called.append("window")
        app.each_minute()
        chk("a tick looks at what has ended and at the window",
            called == ["elapsed", "window"], str(called))


async def t_lapse():
    print("3.2 a press lasts until the window is next crossed")
    # Pressed outside the window to bring the work back: when the window
    # opens, the press lapses into the same answer and nothing moves.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(FRI, 19))
        await pilot.pause()
        chk("the evening hid the work", app.hiding_work is True)
        await pilot.press("w")
        await pilot.pause()
        before = [t.id for t in app.tasks]
        chk("the press brought it back", app.hiding_work is False)
        app.apply_window(at(MON, 9))
        await pilot.pause()
        chk("the window opening leaves the work shown", app.hiding_work is False)
        chk("and nothing on screen moved", [t.id for t in app.tasks] == before,
            str(before))
        chk("the press is spent, the window in charge again",
            app._work_override is None, repr(app._work_override))

    # Pressed inside the window to hide it: the window closing lapses it the
    # same way.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 9))
        await pilot.pause()
        chk("the morning shows the work", app.hiding_work is False)
        await pilot.press("w")
        await pilot.pause()
        before = [t.id for t in app.tasks]
        chk("the press hid it", app.hiding_work is True)
        app.apply_window(at(MON, 19))
        await pilot.pause()
        chk("the window closing leaves it hidden", app.hiding_work is True)
        chk("and nothing on screen moved", [t.id for t in app.tasks] == before,
            str(before))

    # Pressed twice, ending where the window already had it: the next
    # crossing acts as though no key had been pressed at all.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(FRI, 19))
        await pilot.pause()
        await pilot.press("w")
        await pilot.press("w")
        await pilot.pause()
        chk("two presses leave the work hidden, as the window had it",
            app.hiding_work is True)
        app.apply_window(at(MON, 9))
        await pilot.pause()
        chk("and the morning brings it back, as if neither press happened",
            app.hiding_work is False)

    # And with no crossing, a press lasts however long it is left.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 9))
        await pilot.press("w")
        await pilot.pause()
        for hour in (10, 12, 14, 16, 17):
            app.apply_window(at(MON, hour))
        await pilot.pause()
        chk("a press with no crossing under it stays where it was put",
            app.hiding_work is True and app._work_override is True)


def many(count=60):
    """A list long enough to scroll, half of it the work project's."""
    out = []
    for i in range(count):
        work = i % 2
        out.append(mk(f"T-{i:03d}", f"task {i}", D,
                      project=WORK if work else None))
    return out


async def settled(app, moment, press, at_row):
    """Where the board ends up after hiding the work one way or the other.

    Run twice over identical boards -- once crossing the window, once
    pressing the key -- so the two can be compared rather than each being
    asserted against a number written down by hand.
    """
    async with app.run_test(size=(100, 20)) as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 9))
        await pilot.pause()
        table = app.query_one(DataTable)
        # A work row, found in the drawn order rather than the built one:
        # the board sorts for display, so the thirtieth row is not the
        # thirtieth task made.  The selected row has to be one the hiding
        # removes or the comparison proves nothing.
        at_row = next(i for i, task in enumerate(app.tasks)
                      if task.project_id == WORK and i >= at_row)
        table.move_cursor(row=at_row)
        await pilot.pause()
        table.scroll_to(y=at_row - 4, animate=False)
        await pilot.pause()
        was = (table.scroll_offset, app._selected_id)
        writes = [c for c, _ in app.client.calls if c not in StubClient.READS]
        if press:
            await pilot.press("w")
        else:
            app.apply_window(moment)
        await pilot.pause()
        after = [c for c, _ in app.client.calls if c not in StubClient.READS]
        return {"rows": [t.id for t in app.tasks],
                "scroll": table.scroll_offset,
                "selected": app._selected_id,
                "was": was,
                "writes": after == writes,
                "store": sorted(app.client.store)}


async def t_crossing_is_the_key():
    print("3.3 a crossing removes rows exactly as the key does")
    crossed = await settled(build(parse_working_window("08:00-18:00"), many()),
                            at(MON, 19), press=False, at_row=30)
    pressed = await settled(build(parse_working_window("08:00-18:00"), many()),
                            at(MON, 19), press=True, at_row=30)
    chk("the crossing removed the work rows, and only those",
        len(crossed["rows"]) == 30
        and all(int(r.split("-")[1]) % 2 == 0 for r in crossed["rows"]),
        str(len(crossed["rows"])))
    chk("the same rows the key leaves", crossed["rows"] == pressed["rows"])
    chk("the same scroll position the key leaves",
        crossed["scroll"] == pressed["scroll"],
        f'{crossed["scroll"]} vs {pressed["scroll"]}')
    chk("the same selected row the key leaves",
        crossed["selected"] == pressed["selected"],
        f'{crossed["selected"]} vs {pressed["selected"]}')
    chk("the view really was scrolled, so the comparison means something",
        crossed["was"][0].y > 0, str(crossed["was"][0]))
    chk("the selected row really was one of the removed ones",
        crossed["was"][1] not in crossed["rows"], repr(crossed["was"][1]))
    chk("and the selection landed on a surviving row",
        crossed["selected"] in crossed["rows"], repr(crossed["selected"]))
    chk("the crossing sent no write", crossed["writes"])
    chk("and left every task in the store", len(crossed["store"]) == 60,
        str(len(crossed["store"])))


def drawn(app, what="#status"):
    """What a chrome widget is actually showing, as characters."""
    return app.query_one(what).visual.plain


async def t_says_why():
    print("4.1 the board says which boundary is hiding the work")
    # The hour.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 19))
        await pilot.pause()
        line = drawn(app)
        chk("it reports the count", "2 work hidden" in line, line)
        chk("and names the hour the window ends", "after 18:00" in line, line)
        chk("the daybar says it too", app.work_note() ==
            ["work hidden (2), after 18:00"], str(app.work_note()))
    # Before the window opens is the other side of the same boundary.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 6))
        await pilot.pause()
        chk("the early morning names the hour it starts",
            "before 08:00" in drawn(app), drawn(app))
    # The day.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(SAT, 12))
        await pilot.pause()
        line = drawn(app)
        chk("a weekend says the week, not an hour",
            "outside the working week" in line and "after" not in line, line)
    # A press.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 9))
        await pilot.press("w")
        await pilot.pause()
        line = drawn(app)
        chk("a press reports the count as it always has",
            "2 work hidden" in line, line)
        chk("and names no boundary, because none is doing it",
            "after" not in line and "working week" not in line, line)
        chk("nor does the daybar", app.work_note() == ["work hidden (2)"],
            str(app.work_note()))
    # Not hiding at all.
    app = build(parse_working_window("08:00-18:00"), rows())
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_window(at(MON, 9))
        await pilot.pause()
        line = drawn(app)
        chk("with the work shown the board says nothing about it",
            "hidden" not in line and "window" not in line, line)
        chk("and the daybar says nothing either", app.work_note() == [])


async def t_unreadable_window():
    print("4.2 an unreadable window is said once and then behaves as absent")
    kept = singularity.load_working_window
    def refuse(*a, **k):
        raise ValueError("'evenings' is not a range of hours like 08:00-18:00")
    singularity.load_working_window = refuse
    try:
        app = TaskApp(D)
    finally:
        singularity.load_working_window = kept
    app.client = StubClient(rows())
    app.work_project = WORK
    app.projects = {WORK: "Work"}
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("the board opened", app.is_running)
        chk("it says the setting could not be read",
            "WORK_HOURS could not be read" in drawn(app), drawn(app))
        chk("nothing is hidden", app.hiding_work is False)
        chk("and it kept no window", app.working_window is None)
        said = drawn(app)
        app.each_minute()
        app.each_minute()
        await pilot.pause()
        chk("two ticks later it has not said it again",
            drawn(app) == said and app._window_hides is None, drawn(app))


async def t_window_without_a_project():
    print("4.3 a window with no work project acts on nothing")
    app = build(always(), rows(), project=None)
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("nothing is hidden", app.hiding_work is False)
        chk("the window was never consulted", app._window_hides is None,
            repr(app._window_hides))
        chk("and the board says nothing of its own accord",
            "hidden" not in drawn(app) and app.work_note() == [], drawn(app))
    app = build(never(), rows(), project=None)
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("outside the window it is still silent and still hides nothing",
            app.hiding_work is False and app.work_note() == [])
        await pilot.press("w")
        await pilot.pause()
        chk("and the key's own refusal is the only thing that mentions it",
            "No work project is set" in drawn(app), drawn(app))


for fn in (t_hours, t_days, t_default_days, t_day_words, t_unreadable,
           t_midnight, t_reader):
    fn()
for fn in (t_opens, t_moment, t_key_still_flips, t_tick, t_lapse,
           t_crossing_is_the_key, t_says_why, t_unreadable_window,
           t_window_without_a_project):
    asyncio.run(fn())

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
