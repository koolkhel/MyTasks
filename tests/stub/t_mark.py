"""Marking rows: what the key does, how a mark is drawn, and how long it lasts.

Everything here is stubbed -- no account, no network, no mailbox. The calendar
is reached through a replaced `ical.fetch` rather than the real one, because
this shell has no macOS Calendar grant and a suite that asked for it would fail
for a reason that has nothing to do with marking.
"""
import asyncio, datetime as dt, sys
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
import main, ical, mail, tracker
from main import TaskApp
from singularity import Bucket, CHECKED
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
TOMORROW = TODAY + dt.timedelta(days=1)
CFG = ical.Config(work="WorkAcc", personal=("Me",))

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

def ev(title, hh=9, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False)

def issue(key, summary):
    return tracker.Issue(key=key, summary=summary, project="ZZA",
                         state="In progress", assignee="me",
                         base_url="https://track.invalid")

def thread(ident, subject):
    when = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    return mail.Thread((
        mail.Message(sender="someone@example.invalid", subject=subject, when=when,
                     ident=f"<{ident}@example.invalid>", answers=None,
                     body="", text="", folder="Feed", key=ident),))


async def settle(pilot, n=8):
    for _ in range(n):
        await pilot.pause()

def make(position=None, tasks=(), mails=(), events=(), issues=()):
    app = TaskApp(position) if position is not None else TaskApp()
    app.client = StubClient(list(tasks), reference=dt.datetime.now(TZ))
    app.mail_config = None
    app.tracker_config = None
    app.calendar_config = CFG if events else None
    app._pending_mail = list(mails)
    app._pending_events = list(events)
    app._pending_issues = list(issues)
    return app

class run:
    def __init__(self, app, size=(120, 40)):
        self.app, self.size = app, size

    async def __aenter__(self):
        self.saved = ical.fetch
        ical.fetch = lambda cfg, day: list(self.app._pending_events)
        self.ctx = self.app.run_test(size=self.size)
        self.pilot = await self.ctx.__aenter__()
        await settle(self.pilot, 12)
        self.app.mail_threads = list(self.app._pending_mail)
        self.app.tracker_issues = list(self.app._pending_issues)
        if self.app._pending_events:
            self.app.events = list(self.app._pending_events)
            self.app.events_day = self.app.position
        self.app.repaint()
        await settle(self.pilot)
        return self.pilot

    async def __aexit__(self, *exc):
        ical.fetch = self.saved
        return await self.ctx.__aexit__(*exc)


def ordered(tid, title, n):
    """A task whose place in the day is set, so the view's order is known.

    Without a stored order, tasks sharing a day fall back to being ordered by
    title -- which is fine for the board and useless for a check about which
    row comes next.  The first run of the group below asserted against the
    order the fixtures were written in and failed on all of it.
    """
    task = mk(tid, title, TODAY)
    task.raw["scheduleOrder"] = n * 100
    return task


def row(app, title):
    return next(t for t in app.tasks if (t.raw.get("title") or "") == title)

async def cursor_to(app, pilot, title):
    """Put the row cursor on a row by title, and give it back."""
    table = app.query_one(DataTable)
    want = row(app, title)
    at = next(i for i, t in enumerate(app.tasks) if t.id == want.id)
    table.move_cursor(row=at)
    await settle(pilot, 2)
    return want

def cell(app, task):
    """The row-mark cell as drawn."""
    return str(app.row_for(task)[1])

def titles_of(app):
    return [t.raw.get("title") or "" for t in app.marked_tasks()]

def status(app):
    return str(app.query_one("#status").content)

# ---- reading what the table actually drew ---------------------------------

def row_style(app, task):
    """The style the table computes for a row's whole width."""
    from rich.style import Style
    table = app.query_one(DataTable)
    at = next(i for i, t in enumerate(app.tasks) if t.id == task.id)
    return table._get_row_style(at, Style())

def line_of(app, task):
    """The rendered line for a row, as segments.

    Read through the table's own rendering rather than off the cell text, so
    what is checked is what a person would see -- the padding between the
    columns included, which is the difference between a bar and highlighted
    words.
    """
    table = app.query_one(DataTable)
    at = next(i for i, t in enumerate(app.tasks) if t.id == task.id)
    return list(table.render_line(at + (1 if table.show_header else 0)))

def _ch(v):
    v /= 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

def lum(colour):
    """Relative luminance, for comparing two colours without naming either.

    Named values would pass on the theme they were written against and say
    nothing about the other; the two themes have different grounds and the
    same two bars.
    """
    r, g, b = colour.triplet
    return 0.2126 * _ch(r) + 0.7152 * _ch(g) + 0.0722 * _ch(b)

def ratio(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

def cursor_style(app):
    return app.query_one(DataTable).get_component_styles(
        "datatable--cursor").rich_style

def backgrounds(app, task):
    return {seg.style.bgcolor for seg in line_of(app, task) if seg.style}

def title_segments(app, task):
    """The segments carrying a row's title, with their colour and dimness."""
    want = (task.raw.get("title") or "")[:12]
    out = []
    for seg in line_of(app, task):
        if seg.style is not None and want and want[:8] in seg.text:
            out.append(seg)
    return out




# ------------------------------------------------------------------ 3.1

async def group_3_1():
    print("3.1 the key marks a row, and takes the mark off again")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY),
                                      mk("t3", "third", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("the row is marked", titles_of(app), ["first"])
        # The key steps the cursor on, so taking a mark off means going back
        # to the row first.  Pressing twice in place used to toggle; now it
        # marks two rows, which is the point of the change.
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("pressing it again on that row takes the mark off",
              titles_of(app), [])

        print("\n  the order is the order of pressing, not the order drawn")
        await cursor_to(app, pilot, "third")
        await pilot.press("v")
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        check("three rows marked", len(app.marked), 3)
        check("in the order they were pressed", titles_of(app),
              ["third", "first", "second"])
        check("which is not the order the view drew them in",
              titles_of(app) != [t.raw.get("title") for t in app.tasks][:3], True)

        print("\n  and nothing was written")
        check("no write was queued", sum(len(q) for q in app._pending.values()), 0)

    print("\n  the key works in the other keyboard layout")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("м")
        check("the Russian twin marks too", titles_of(app), ["first"])


# ------------------------------------------------------------------ 3.2

async def group_3_2():
    print("\n3.2 a marked row is drawn as one")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY)])
    async with run(app) as pilot:
        first, second = row(app, "first"), row(app, "second")
        plain = cell(app, first)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        marked = cell(app, first)
        check("the marked row's cell differs from its unmarked one",
              marked != plain, True)
        check("it carries the copy mark", main.COPY_MARK in marked, True)
        check("it still carries the row's own mark", plain in marked, True)
        check("and it fits the two cells the column has", len(marked), 2)
        check("an unmarked row beside it carries no copy mark",
              main.COPY_MARK in cell(app, second), False)
        check("and is otherwise unchanged", cell(app, second), plain)

        print("\n  the mark survives being the selected row")
        # The cursor replaces a colour outright while leaving a glyph alone,
        # which is why this is a character.  If it were a colour the mark
        # would vanish on exactly the row a person is looking at.
        table = app.query_one(DataTable)
        at = next(i for i, t in enumerate(app.tasks) if t.id == first.id)
        # Marking steps the cursor on, so it has to be brought back to read
        # the row as the selected one.
        await cursor_to(app, pilot, "first")
        check("the marked row is the selected one", table.cursor_row, at)
        # Compared against the unmarked cell rather than against what this
        # row drew a moment ago.  Comparing a cell with itself passes
        # whatever the drawing does, which a vacuity run caught: with the
        # mark removed altogether this check went on passing.
        check("and it still carries the copy mark while selected",
              main.COPY_MARK in cell(app, first), True)
        check("which is more than the unmarked row draws",
              cell(app, first) != plain, True)

        print("\n  the cursor and the mark are different things")
        await cursor_to(app, pilot, "second")
        check("the cursor moved", app.tasks[table.cursor_row].id, second.id)
        check("the first row is still marked", titles_of(app), ["first"])
        check("and still drawn marked, with the cursor elsewhere",
              main.COPY_MARK in cell(app, first), True)
        check("while the row under the cursor is not marked",
              main.COPY_MARK in cell(app, second), False)


# ------------------------------------------------------------------ 3.3

async def group_3_3():
    print("\n3.3 every row the board draws can be marked")
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "an own task")],
               mails=[thread("m1", "a message")])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "a message")
        await pilot.press("v")
        check("a mail row is marked", titles_of(app), ["a message"])
        check("and it was not refused out loud", app._notice, None)
        check("nothing was written", sum(len(q) for q in app._pending.values()), 0)

    app = make(position=TODAY, tasks=[mk("t1", "an own task", TODAY)],
               events=[ev("an event")], issues=[issue("ZZA-1", "an issue")])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "an event")
        await pilot.press("v")
        await cursor_to(app, pilot, "ZZA-1 — an issue")
        await pilot.press("v")
        check("an event and a tracker issue are marked",
              titles_of(app), ["an event", "ZZA-1 — an issue"])
        check("and neither was refused out loud", app._notice, None)
        check("nothing was written", sum(len(q) for q in app._pending.values()), 0)


# ------------------------------------------------------------------ 3.4

async def group_3_4():
    print("\n3.4 how long a mark lasts")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        print("\n  a write landing rebuilds the table")
        await cursor_to(app, pilot, "second")
        await pilot.press("space")            # tick the other row
        await settle(pilot, 10)
        check("the mark is still on the row it was put on",
              titles_of(app), ["first"])
        check("and the row that was ticked is not marked",
              row(app, "second").checked, CHECKED)

    print("\n  marks gathered from several views")
    app = make(position=TODAY,
               tasks=[mk("t1", "on today", TODAY), mk("t2", "in the inbox"),
                      mk("t3", "in someday", deferred=True),
                      mk("t4", "on tomorrow", TOMORROW)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "on today")
        await pilot.press("v")
        await pilot.press("i")                # the inbox
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in the inbox")
        await pilot.press("v")
        await pilot.press("s")                # someday
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in someday")
        await pilot.press("v")
        check("three rows from three views are marked", len(app.marked), 3)
        check("and the copy can still reach every one of them",
              sorted(titles_of(app)), ["in someday", "in the inbox", "on today"])
        await pilot.press("t")                # back to today
        await settle(pilot, 6)
        check("they are still marked from a fourth view", len(app.marked), 3)

    print("\n  a mark on a row the board no longer holds")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "doomed", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        doomed = await cursor_to(app, pilot, "doomed")
        await pilot.press("v")
        check("both are marked", len(app.marked), 2)
        # The row leaves the board the way a deletion leaves it: gone from
        # what was fetched, with the next repaint noticing.
        app._base = [t for t in app._base if t.id != doomed.id]
        app.repaint()
        await settle(pilot)
        check("the mark on the row that went is forgotten", titles_of(app), ["first"])
        check("and the count no longer counts it", len(app.marked), 1)

    print("\n  escape clears every mark")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("marked", len(app.marked), 1)
        await pilot.press("escape")
        await settle(pilot)
        check("escape cleared it", app.marked, [])
        check("and forgot the row with it", app._marked_rows, {})


# ------------------------------------------------------------------ 3.5

async def group_3_5():
    print("\n3.5 the board says how many rows are marked")


    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY),
                                      mk("t3", "elsewhere")])
    async with run(app) as pilot:
        check("nothing is said with no row marked",
              "marked" in status(app), False)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        check("one marked is reported", "1 marked" in status(app), True)
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        check("two marked is reported", "2 marked" in status(app), True)

        print("\n  a mark this view cannot draw is still counted")
        await pilot.press("i")                # the inbox, which holds neither
        await settle(pilot, 6)
        check("the rows marked on today are not drawn here",
              [t.raw.get("title") for t in app.tasks], ["elsewhere"])
        check("but the count still says two", "2 marked" in status(app), True)

        print("\n  and one a search is hiding is counted too")
        await cursor_to(app, pilot, "elsewhere")
        await pilot.press("v")
        app.searching = "nothing matches this"
        app.repaint()
        await settle(pilot)
        check("the view is empty", app.tasks, [])
        check("the count still says three", "3 marked" in status(app), True)

        await pilot.press("escape")
        await settle(pilot)
        check("escape clears the search and the marks together",
              (app.searching, app.marked), (None, []))
        check("and the count says nothing again",
              "marked" in status(app), False)




# ------------------------------------------------------ the bar (group 1)

async def group_bar():
    print("\n1.2/1.3 a marked row is drawn as a bar across its whole width")
    app = make(position=TODAY, tasks=[ordered("t1", "marked one", 1),
                                      ordered("t2", "plain one", 2),
                                      ordered("t3", "the cursor sits here", 3)])
    async with run(app) as pilot:
        marked = await cursor_to(app, pilot, "marked one")
        await pilot.press("v")
        # The key moves the cursor on, so park it well away from the row
        # being read -- the cursor's own bar would otherwise be what is
        # measured, and every check below would pass for the wrong reason.
        await cursor_to(app, pilot, "the cursor sits here")
        plain = row(app, "plain one")
        cursor = row(app, "the cursor sits here")

        m_style, p_style = row_style(app, marked), row_style(app, plain)
        check("the marked row's computed style differs from a plain one's",
              m_style != p_style, True)
        check("and differs in its background", m_style.bgcolor != p_style.bgcolor,
              True)
        # Its own colour, and deliberately not the selected row's.  Reading
        # the bar off the cursor's style is what kept the two identical, and
        # that failure is invisible: nothing errors, the bars simply match.
        cur = cursor_style(app)
        check("which is not the one the selected row uses",
              m_style.bgcolor != cur.bgcolor, True)
        check("and the selected row's is the brighter of the two",
              lum(cur.bgcolor) > lum(m_style.bgcolor), True)
        apart = ratio(cur.bgcolor, m_style.bgcolor)
        check(f"far enough apart to tell at a glance (>=2:1, got {apart:.2f}:1)",
              apart >= 2.0, True)
        check("nothing else about the style changed",
              (m_style.color, m_style.bold), (p_style.color, p_style.bold))

        print("\n  and it covers the padding, not only the characters")
        # One background across the whole rendered line is the difference
        # between a bar and highlighted words: a bar built out of cell
        # styles would leave the gaps between columns unpainted, and this
        # is the check that would catch it.
        check("the marked row's line carries exactly one background",
              len(backgrounds(app, marked)), 1)
        check("and it is the bar's",
              backgrounds(app, marked).pop(), m_style.bgcolor)
        # The padding itself, named rather than inferred.  A line with one
        # background passes that check whether the background is the bar or
        # the ground, so on its own it says nothing; this asks for the bar
        # under a run of spaces, which is exactly what a bar built out of
        # cell styles would fail to paint.
        gaps = [seg for seg in line_of(app, marked)
                if seg.text and not seg.text.strip()]
        check("there is padding on the line to check",
              bool(gaps), True)
        check("and the bar is painted under it",
              {seg.style.bgcolor for seg in gaps if seg.style}, {m_style.bgcolor})
        check("a plain row's line is not painted with it",
              m_style.bgcolor in backgrounds(app, plain), False)

    print("\n1.4 the bar shows against either theme's ground")
    for theme in ("turbo-cpp-dark", "turbo-cpp-blue"):
        app = make(position=TODAY, tasks=[ordered("t1", "marked one", 1),
                                          ordered("t2", "plain one", 2),
                                          ordered("t3", "park here", 3)])
        async with run(app) as pilot:
            app.theme = theme
            await settle(pilot, 6)
            marked = await cursor_to(app, pilot, "marked one")
            await pilot.press("v")
            # Marking steps the cursor onto the next row, which would then
            # be wearing the cursor's own bar -- the very colour this is
            # about to look for on a row that should not have it.
            await cursor_to(app, pilot, "park here")
            await settle(pilot, 4)
            bar = row_style(app, marked).bgcolor
            ground = backgrounds(app, row(app, "plain one"))
            # A difference in both themes, rather than a colour named here:
            # the two have different grounds, and a check naming one would
            # pass by luck on the other.
            check(f"the bar differs from the ground in {theme}",
                  bar not in ground, True)


# --------------------------------------- the row stays readable (group 2)

async def group_readable():
    print("\n2.1 a marked row keeps neither its past-due colour nor its dimming")
    late = mk("t1", "overdue one", TODAY - dt.timedelta(days=3))
    app = make(position=TODAY, tasks=[late, mk("t2", "ordinary one", TODAY),
                                      mk("t3", "park here", TODAY)])
    async with run(app) as pilot:
        overdue = await cursor_to(app, pilot, "overdue one")
        await pilot.press("v")
        await cursor_to(app, pilot, "park here")
        ordinary = row(app, "ordinary one")
        marked_fg = {s.style.color for s in title_segments(app, overdue)}
        plain_fg = {s.style.color for s in title_segments(app, ordinary)}
        check("the marked past-due title carries no colour of its own",
              marked_fg, plain_fg)
        check("and the row still says how overdue it is",
              "ago" in str(app.row_for(overdue)[2]), True)

    print("\n  the same row unmarked still carries it")
    app = make(position=TODAY, tasks=[mk("t1", "overdue one",
                                         TODAY - dt.timedelta(days=3)),
                                      mk("t2", "ordinary one", TODAY)])
    async with run(app) as pilot:
        overdue, ordinary = row(app, "overdue one"), row(app, "ordinary one")
        await cursor_to(app, pilot, "ordinary one")
        unmarked_fg = {s.style.color for s in title_segments(app, overdue)}
        plain_fg = {s.style.color for s in title_segments(app, ordinary)}
        check("an unmarked past-due row is drawn in its own colour",
              unmarked_fg != plain_fg, True)

    print("\n2.2 a strike survives being marked, a dim does not")
    app = make(position=TODAY, tasks=[mk("t1", "finished one", TODAY, checked=CHECKED),
                                      mk("t2", "park here", TODAY)])
    async with run(app) as pilot:
        done = await cursor_to(app, pilot, "finished one")
        await pilot.press("v")
        await cursor_to(app, pilot, "park here")
        segs = title_segments(app, done)
        check("the finished title is still struck through",
              any(s.style.strike for s in segs), True)
        check("and is no longer dimmed", any(s.style.dim for s in segs), False)

    app = make(position=TODAY, tasks=[mk("t1", "finished one", TODAY, checked=CHECKED),
                                      mk("t2", "park here", TODAY)])
    async with run(app) as pilot:
        done = row(app, "finished one")
        await cursor_to(app, pilot, "park here")
        segs = title_segments(app, done)
        check("an unmarked finished row is still dimmed",
              any(s.style.dim for s in segs), True)
        check("and still struck through",
              any(s.style.strike for s in segs), True)


# ------------------------------------- cursor against mark (group 3)

async def group_cursor():
    print("\n3.1/3.3 the cursor is still tellable from a mark")
    app = make(position=TODAY, tasks=[ordered("t1", "first", 1),
                                      ordered("t2", "second", 2),
                                      ordered("t3", "third", 3)])
    async with run(app) as pilot:
        first = await cursor_to(app, pilot, "first")
        await pilot.press("v")
        second = await cursor_to(app, pilot, "second")
        await pilot.press("v")
        # Cursor now on "third"; "first" and "second" are marked.
        await cursor_to(app, pilot, "second")
        on_cursor = {(s.style.color, s.style.bold)
                     for s in title_segments(app, second)}
        off_cursor = {(s.style.color, s.style.bold)
                      for s in title_segments(app, first)}
        check("a marked row under the cursor is drawn as the selected row",
              on_cursor != off_cursor, True)
        # They must NOT share it.  A cursor sitting in a run of marked rows
        # was one bar among several, and finding it meant reading the weight
        # of every row's text in turn -- which is the thing a glance is for.
        check("they do not share the bar",
              backgrounds(app, first) == backgrounds(app, second), False)
        check("and the row under the cursor wears the brighter one",
              lum(cursor_style(app).bgcolor)
              > lum(row_style(app, first).bgcolor), True)
        # A named difference, not mere inequality: two styles differing in
        # something invisible would pass an inequality check and fail a
        # person looking at the screen.
        colours = {c for c, _ in on_cursor} | {c for c, _ in off_cursor}
        check("and differ in text colour", len(colours), 2)
        check("the cursor's text is the bold one",
              (all(b for _, b in on_cursor), any(b for _, b in off_cursor)),
              (True, False))

    print("\n3.2 the mark's own character stays on the row under the cursor")
    app = make(position=TODAY, tasks=[mk("t1", "only row", TODAY)])
    async with run(app) as pilot:
        only = await cursor_to(app, pilot, "only row")
        await pilot.press("v")
        await settle(pilot, 4)
        check("marking the last row leaves the cursor on it",
              app.tasks[app.query_one(DataTable).cursor_row].id, only.id)
        check("and the mark character is there to say it is marked",
              main.COPY_MARK in cell(app, only), True)
        await pilot.press("v")
        await settle(pilot, 4)
        check("pressing again takes it off, visibly",
              main.COPY_MARK in cell(app, only), False)


# ------------------------------------------- the cursor moves on (group 4)

async def group_advance():
    print("\n4.1/4.2 marking moves the cursor on, so a run needs one key")
    names = ["one", "two", "three", "four", "five", "six"]
    app = make(position=TODAY,
               tasks=[ordered(f"t{n}", name, n) for n, name in enumerate(names)])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        await cursor_to(app, pilot, "one")
        await pilot.press("v")
        check("one press marks the row and steps down",
              (titles_of(app), app.tasks[table.cursor_row].raw.get("title")),
              (["one"], "two"))
        for _ in range(3):
            await pilot.press("v")
            await settle(pilot, 3)
        check("four presses mark the first four, in order",
              titles_of(app), ["one", "two", "three", "four"])
        check("and leave the cursor on the fifth",
              app.tasks[table.cursor_row].raw.get("title"), "five")
        check("no row was marked twice", len(app.marked), len(set(app.marked)))

    print("\n4.3 taking a mark off moves on as well")
    app = make(position=TODAY, tasks=[ordered("t1", "one", 1),
                                      ordered("t2", "two", 2),
                                      ordered("t3", "three", 3)])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        await cursor_to(app, pilot, "one")
        await pilot.press("v")
        await cursor_to(app, pilot, "one")
        await pilot.press("v")
        check("the mark came off", titles_of(app), [])
        check("and the cursor moved on just the same",
              app.tasks[table.cursor_row].raw.get("title"), "two")

    print("\n4.4 the last row keeps the cursor")
    app = make(position=TODAY, tasks=[ordered("t1", "one", 1),
                                      ordered("t2", "last", 2)])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        await cursor_to(app, pilot, "last")
        await pilot.press("v")
        check("the last row is marked", titles_of(app), ["last"])
        check("and the cursor stayed on it",
              app.tasks[table.cursor_row].raw.get("title"), "last")
        await pilot.press("v")
        check("pressing again unmarks it", titles_of(app), [])
        check("and the cursor is still there",
              app.tasks[table.cursor_row].raw.get("title"), "last")

    print("\n4.5 the step follows what is drawn, not what is held")
    app = make(position=TODAY, tasks=[ordered("t1", "keep alpha", 1),
                                      ordered("t2", "hide beta", 2),
                                      ordered("t3", "keep gamma", 3)])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        app.searching = "keep"
        app.repaint()
        await settle(pilot, 6)
        check("the search removed the middle row",
              [t.raw.get("title") for t in app.tasks],
              ["keep alpha", "keep gamma"])
        await cursor_to(app, pilot, "keep alpha")
        await pilot.press("v")
        check("the cursor stepped over the row the search removed",
              app.tasks[table.cursor_row].raw.get("title"), "keep gamma")


async def group_themes():
    print("\n4.1 the selected row stands out among marked ones, in either theme")
    for theme in ("turbo-cpp-dark", "turbo-cpp-blue"):
        app = make(position=TODAY, tasks=[ordered("t1", "above", 1),
                                          ordered("t2", "the cursor", 2),
                                          ordered("t3", "below", 3)])
        async with run(app) as pilot:
            app.theme = theme
            await settle(pilot, 6)
            above = await cursor_to(app, pilot, "above")
            await pilot.press("v")          # steps onto "the cursor"
            await cursor_to(app, pilot, "below")
            await pilot.press("v")          # steps past the end, stays on "below"
            await cursor_to(app, pilot, "the cursor")
            await settle(pilot, 4)
            check(f"{theme}: the rows either side are the marked ones",
                  sorted(titles_of(app)), ["above", "below"])
            cur = cursor_style(app).bgcolor
            neighbours = {row_style(app, above).bgcolor,
                          row_style(app, row(app, "below")).bgcolor}
            check(f"{theme}: the selected row's bar differs from theirs",
                  cur in neighbours, False)
            # And from the ground as well, so it is findable with nothing
            # marked at all -- which it was not before this change.
            ground = app.query_one(DataTable).background_colors[1]
            from rich.color import Color as _RC
            g = _RC.parse(ground.hex)
            check(f"{theme}: and from the ground (>=3:1, got {ratio(cur, g):.2f}:1)",
                  ratio(cur, g) >= 3.0, True)

    print("\n4.2 the text on each bar is legible against it")
    for theme in ("turbo-cpp-dark", "turbo-cpp-blue"):
        app = make(position=TODAY, tasks=[ordered("t1", "marked one", 1),
                                          ordered("t2", "park here", 2)])
        async with run(app) as pilot:
            app.theme = theme
            await settle(pilot, 6)
            marked = await cursor_to(app, pilot, "marked one")
            await pilot.press("v")      # marks it, and steps onto "park here"
            await settle(pilot, 4)
            cur = cursor_style(app)
            bar = row_style(app, marked).bgcolor
            # The board's own rule: dark text on a light bar and the reverse
            # on a dark one.  Asked as a comparison of luminance rather than
            # by naming a colour, so one form covers both themes.
            check(f"{theme}: the selected row's bar is light, its text dark",
                  lum(cur.bgcolor) > lum(cur.color), True)
            r = ratio(cur.color, cur.bgcolor)
            check(f"{theme}: and legible on it (>=4.5:1, got {r:.2f}:1)",
                  r >= 4.5, True)
            # The marked row carries an ordinary title, whose colour the row
            # style leaves alone -- so what is checked is that the bar did
            # not take the text down with it.
            title = {sg.style.color for sg in title_segments(app, marked)}
            worst = min(ratio(c, bar) for c in title if c is not None)
            check(f"{theme}: a marked row's title still reads on its bar "
                  f"(>=2.4:1, got {worst:.2f}:1)", worst >= 2.4, True)


def group_hook():
    print("\n5.1 the framework hook the bar depends on")
    import inspect
    from textual.widgets import DataTable as _DataTable
    # Private API, deliberately overridden: it is the only place a row that
    # is not the cursor can be given a background across its whole width.  A
    # rename in a future Textual would leave marks silently undrawn -- no
    # error, no failed import, just no bar -- so the name is asserted rather
    # than assumed.  The same guard `t_crash` puts on its own hook.
    check("Textual still calls its hook _get_row_style",
          hasattr(_DataTable, "_get_row_style"), True)
    check("and the board overrides it rather than adding a new name",
          "_get_row_style" in vars(main.TaskTable), True)
    check("the override goes on to the framework's",
          "super()._get_row_style" in
          open(_os.path.join(_REPO, "main.py"), encoding="utf-8").read(), True)
    # The arguments too: a hook that kept its name and changed its shape
    # would fail at the first redraw rather than here, which is worse.
    check("it still takes the row and a base style",
          list(inspect.signature(_DataTable._get_row_style).parameters)[1:],
          ["row_index", "base_style"])


def main_():
    asyncio.run(group_3_1())
    asyncio.run(group_3_2())
    asyncio.run(group_3_3())
    asyncio.run(group_3_4())
    asyncio.run(group_3_5())
    asyncio.run(group_bar())
    asyncio.run(group_readable())
    asyncio.run(group_cursor())
    asyncio.run(group_advance())
    asyncio.run(group_themes())
    group_hook()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main_())
