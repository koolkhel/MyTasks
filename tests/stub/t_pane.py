"""The note pane: one height whatever the note, and scrollable.

The pane was `height: auto`, so the list was as tall as whatever the selected
row happened to carry -- and the rows moved under a cursor stepping through
them. Everything here is about the pane's height not depending on its content,
and about reading a note that does not fit.

Self-contained: a stubbed store, no mailbox unless a check builds one from a
copy of the committed fixture, no calendar, no tracker, no network.
"""
import asyncio, datetime as dt, os, sys
from time import monotonic

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import ical, mail, main, tracker
import mailfixture as F
from textual.widgets import DataTable, Static

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
#: A note far longer than the pane can ever show.
LONG = "\n".join(f"line {i}" for i in range(40))
ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def noted(tid, title, note, start=TODAY):
    """A task carrying a note, in the shape the store hands one back."""
    task = mk(tid, title, start)
    task.raw["note"] = note
    return task


def triage(tid, title, note):
    """The same with no date, so the inbox shows it beside the mail."""
    return noted(tid, title, note, start=None)


async def board(tasks=None, size=(80, 44)):
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [], reference=NOW)
    app.calendar_config = None
    app.tracker_config = None
    app.mail_config = None
    return app, size


async def settle(pilot, n=12):
    for _ in range(n): await pilot.pause()


def pane(app):
    return app.query_one("#notes")


def text(app):
    return str(app.query_one("#detail", Static).render())


async def select(app, pilot, tid):
    row = next(i for i, t in enumerate(app.tasks) if t.id == tid)
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await settle(pilot, 6)
    return app.tasks[row]


# -- the note still arrives where it always did ---------------------------
async def the_text_still_lands():
    print("the note is still written to the widget four suites read")
    app, size = await board([noted("t1", "a task", "what it says")])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        check("the pane holds a Static with that id",
              isinstance(app.query_one("#detail"), Static))
        check("and it answers the note", text(app), "what it says")
        check("the pane is the scrollable thing, not the text",
              type(pane(app)).__name__, "VerticalScroll")
        check("the text widget is inside it",
              app.query_one("#detail").parent is pane(app))


# -- the list keeps the focus ---------------------------------------------
async def focus_stays_on_the_list():
    print("the pane never takes the keys away from the list")
    app, size = await board([noted("t1", "first", ""),
                             noted("t2", "second", LONG),
                             noted("t3", "third", "one line")])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        check("the table holds focus", app.focused.id, "tasks")
        check("the pane cannot be focused", pane(app).can_focus, False)
        table = app.query_one(DataTable)
        was = table.cursor_row
        await pilot.press("down")
        await settle(pilot, 6)
        check("down moves the cursor", table.cursor_row, was + 1)
        await pilot.press("j")
        await settle(pilot, 6)
        check("and so does j", table.cursor_row, was + 2)
        await pilot.press("tab")
        await settle(pilot, 6)
        check("tab does not land on the pane",
              app.focused is None or app.focused.id != "notes")


# -- the height does not depend on the note -------------------------------
async def one_height():
    print("the list is the same height whatever the note")
    for size in ((80, 44), (80, 20)):
        heights, panes = [], []
        for note in ("", "one line", LONG):
            app, _ = await board([noted("t1", "a task", note)])
            async with app.run_test(size=size) as pilot:
                await settle(pilot, 14)
                heights.append(app.query_one(DataTable).size.height)
                panes.append(pane(app).size.height)
        check(f"{size[1]} rows: the table is one height for all three notes",
              len(set(heights)), 1)
        check(f"{size[1]} rows: and so is the pane", len(set(panes)), 1)
        print(f"        table {heights[0]} rows, pane {panes[0]} rows of text")

    print("eight rows of text where there is room, a share where there is not")
    app, _ = await board([noted("t1", "a task", LONG)])
    async with app.run_test(size=(80, 44)) as pilot:
        await settle(pilot, 14)
        check("a tall window gives the pane its eight",
              pane(app).size.height, 8)
    app, _ = await board([noted("t1", "a task", LONG)])
    async with app.run_test(size=(80, 12)) as pilot:
        await settle(pilot, 14)
        short = pane(app).size.height
        check("a short one gives it less rather than eating the list",
              0 < short < 8, True)
        check("and leaves a list to read",
              app.query_one(DataTable).size.height > 0, True)
        print(f"        12-row window: pane {short}, "
              f"table {app.query_one(DataTable).size.height}")

    print("and it holds its height with nothing selected at all")
    app, _ = await board([])
    async with app.run_test(size=(80, 44)) as pilot:
        await settle(pilot, 14)
        check("no rows are shown", len(app.tasks), 0)
        check("the pane is its full height regardless",
              pane(app).size.height, 8)
        check("showing nothing", text(app), "")


# -- reading a note that does not fit ------------------------------------
async def scrolling():
    print("the keys scroll the pane, a page less one line at a time")
    app, size = await board([noted("t1", "a task", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        step = pane(app).size.height - 1
        check("the pane holds more than it shows", pane(app).max_scroll_y > 0)
        check("and starts at the top", pane(app).scroll_offset.y, 0)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("one press moves a page less one line",
              pane(app).scroll_offset.y, step)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("a second press moves it again",
              pane(app).scroll_offset.y, step * 2)
        await pilot.press("left_square_bracket")
        await settle(pilot, 8)
        check("and back", pane(app).scroll_offset.y, step)
        await pilot.press("left_square_bracket")
        await settle(pilot, 8)
        check("to the top", pane(app).scroll_offset.y, 0)
        print(f"        pane {pane(app).size.height} rows, step {step}")

    print("the Cyrillic twins do the same")
    app, size = await board([noted("t1", "a task", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("ъ")
        await settle(pilot, 8)
        check("ъ scrolls down", pane(app).scroll_offset.y > 0)
        await pilot.press("х")
        await settle(pilot, 8)
        check("х scrolls back up", pane(app).scroll_offset.y, 0)

    print("scrolling moves no selection and writes nothing")
    app, size = await board([noted("t1", "first", LONG),
                             noted("t2", "second", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        table = app.query_one(DataTable)
        was_row, was_id = table.cursor_row, app._selected_id
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("the cursor has not moved", table.cursor_row, was_row)
        check("nor the selection", app._selected_id, was_id)
        writes = [c for c, _a in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("and nothing was written", writes, [])
        await pilot.press("down")
        await settle(pilot, 8)
        check("the cursor still moves afterwards", table.cursor_row, was_row + 1)

    print("a note that fits, and the top of one that does not")
    app, size = await board([noted("t1", "a task", "one line")])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        check("nothing to scroll", pane(app).max_scroll_y, 0)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("] leaves it where it was", pane(app).scroll_offset.y, 0)
        await pilot.press("left_square_bracket")
        await settle(pilot, 8)
        check("and so does [", pane(app).scroll_offset.y, 0)
        check("with nothing said", "note" in str(
            app.query_one("#status").render()).lower(), False)
        writes = [c for c, _a in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("and nothing written", writes, [])

    print("the pane says when it holds more than it shows")
    for size in ((80, 44), (80, 20)):
        app, _ = await board([noted("t1", "a task", LONG)])
        async with app.run_test(size=size) as pilot:
            await settle(pilot, 14)
            check(f"{size[1]} rows: a long note shows a scrollbar",
                  pane(app).show_vertical_scrollbar)
        app, _ = await board([noted("t1", "a task", "one line")])
        async with app.run_test(size=size) as pilot:
            await settle(pilot, 14)
            check(f"{size[1]} rows: a short one shows none",
                  pane(app).show_vertical_scrollbar, False)


# -- a new selection starts at the beginning -----------------------------
async def rewinding():
    print("moving to another row shows that row's note from its first line")
    app, size = await board([noted("t1", "first", LONG),
                             noted("t2", "second", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await select(app, pilot, "t1")
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("part way down the first note", pane(app).scroll_offset.y > 0)
        await select(app, pilot, "t2")
        check("the second opens at its beginning", pane(app).scroll_offset.y, 0)
        check("and shows that note", text(app).startswith("line 0"))

    print("a repaint of the same row leaves the offset alone")
    app, size = await board([noted("t1", "first", LONG),
                             noted("t2", "second", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await select(app, pilot, "t1")
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        was = pane(app).scroll_offset.y
        check("part way down", was > 0)
        # What a background load does when it returns: rebuild every row
        # while the selection has not changed.
        for _ in range(3):
            app.repaint()
            await settle(pilot, 6)
        check("three repaints later it is still there",
              pane(app).scroll_offset.y, was)

    print("away and back again starts at the top")
    app, size = await board([noted("t1", "first", LONG),
                             noted("t2", "second", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await select(app, pilot, "t1")
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("part way down the first note", pane(app).scroll_offset.y > 0)
        await select(app, pilot, "t2")
        await select(app, pilot, "t1")
        check("coming back shows it from the top",
              pane(app).scroll_offset.y, 0)

    print("and a view with nothing in it rewinds too")
    app, size = await board([noted("t1", "only", LONG)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("part way down", pane(app).scroll_offset.y > 0)
        app.client.store.clear()
        app._base = []
        app.repaint()
        await settle(pilot, 8)
        check("an empty view shows the top of nothing",
              pane(app).scroll_offset.y, 0)


# -- rows the board does not own -----------------------------------------
async def rows_from_elsewhere():
    print("a mail row's note scrolls like any other")
    # Built here rather than read from the committed fixture, because a
    # notification long enough to scroll is the point and the fixture's are
    # short.  Synthetic throughout: invented subjects, .invalid addresses.
    box = F.build({"Feed": [("a long notification",
                             "\n".join(f"line {i}" for i in range(40)), {})]})
    app, size = await board([])
    app.mail_config = mail.Config(box, ("Feed",))
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        row = next((t for t in app.tasks if app.is_mail(t)), None)
        check("the mail row is there", row is not None)
        await select(app, pilot, row.id)
        check("its note is longer than the pane", pane(app).max_scroll_y > 0)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("and it scrolls", pane(app).scroll_offset.y > 0)
        # By the refusal's own wording, not by the word "mailbox": the
        # board says plenty about a mailbox that has nothing to do with
        # refusing a row.
        check("the row was not refused as unownable",
              "not editable here" in str(app.query_one("#status").render()),
              False)

    print("and so does a copy of the committed mailbox")
    # Copied per run: the board can move messages out of a mailbox now, and
    # a suite reading the shipped one in place would rewrite what every
    # other mail suite measures against.
    app, size = await board([])
    app.mail_config = mail.Config(F.copy(), F.FOLDERS)
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 22)
        row = next((t for t in app.tasks if app.is_mail(t)), None)
        check("its rows are shown", row is not None)
        await select(app, pilot, row.id)
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("the key is accepted rather than refused",
              "not editable here" in str(app.query_one("#status").render()),
              False)

    print("a calendar row's description scrolls")
    app, size = await board([mk("t1", "a task", TODAY)])
    app.calendar_config = ical.Config(work="W", personal=("Me",))
    start = dt.datetime.combine(TODAY, dt.time(9, 0))
    saved = ical.fetch
    ical.fetch = lambda cfg, day: [ical.Event(
        title="a meeting", account="Me", calendar="c", start=start,
        end=start + dt.timedelta(hours=1), all_day=False,
        notes="\n".join(f"line {i}" for i in range(40)))]
    try:
        async with app.run_test(size=size) as pilot:
            await settle(pilot, 18)
            row = next((t for t in app.tasks if app.is_event(t)), None)
            check("the event row is there", row is not None)
            await select(app, pilot, row.id)
            check("its description is longer than the pane",
                  pane(app).max_scroll_y > 0)
            await pilot.press("right_square_bracket")
            await settle(pilot, 8)
            check("and it scrolls", pane(app).scroll_offset.y > 0)
            check("the row was not refused as unownable",
                  "not editable here" in str(app.query_one("#status").render()),
                  False)
    finally:
        ical.fetch = saved

    print("a tracker row is not refused either")
    # A tracker row carries no note, so there is nothing for the key to
    # scroll -- which is the honest outcome and the whole of what can be
    # checked here: the key is accepted, and the row is not called
    # unownable.
    app, size = await board([mk("t1", "a task", TODAY)])
    app.tracker_config = tracker.Config(
        base_url="https://track.invalid", token="t", assignee="me",
        projects=("ZZA",), states=("In progress",))
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        app.tracker_issues = [tracker.Issue(
            key="ZZA-1", summary="an issue", project="ZZA",
            state="In progress", assignee="me",
            base_url="https://track.invalid")]
        app.repaint()
        await settle(pilot, 8)
        row = next((t for t in app.tasks if app.is_tracker(t)), None)
        check("the tracker row is there", row is not None)
        await select(app, pilot, row.id)
        was = pane(app).scroll_offset.y
        await pilot.press("right_square_bracket")
        await settle(pilot, 8)
        check("the key is accepted", pane(app).scroll_offset.y, was)
        check("and the row is not called unownable",
              "not editable here" in str(app.query_one("#status").render()),
              False)
        writes = [c for c, _a in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written by any of it", writes, [])


# -- the focus card agrees with the pane ---------------------------------
async def the_card():
    print("the card shows a note as the characters it contains")
    loud = "before [bold red]LOUD[/] and [x] after"
    app, size = await board([noted("t1", "a task", loud)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        check("the pane shows every character", text(app), loud)
        # Opened by its own action rather than by pressing enter: the table
        # turns enter into a row selection, and what is being checked here
        # is the card, not that dispatch.
        app.action_focus_task()
        await settle(pilot, 10)
        drawn = app.screen.query_one("#focus-note", Static).render()
        check("and so does the card", str(drawn), loud)
        check("with no styling from it",
              [str(sp.style) for sp in getattr(drawn, "spans", ())], [])
        await pilot.press("escape")
        await settle(pilot, 8)

    print("and leaves an ordinary note alone")
    app, size = await board([noted("t1", "a task", "just what it says")])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        app.action_focus_task()
        await settle(pilot, 10)
        check("shown unchanged",
              str(app.screen.query_one("#focus-note", Static).render()),
              "just what it says")
        await pilot.press("escape")
        await settle(pilot, 8)

    print("a task with no note renders no note line")
    app, size = await board([noted("t1", "a task", "")])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        app.action_focus_task()
        await settle(pilot, 10)
        check("there is no note widget at all",
              len(app.screen.query("#focus-note")), 0)
        check("and the card is open all the same",
              [type(sc).__name__ for sc in app.screen_stack][-1:], ["TaskFocus"])


# -- saying so ------------------------------------------------------------
async def saying_so():
    print("the board says what the keys do")
    text_ = main.Help.TEXT
    check("the overlay names both keys", "[ / ]" in text_)
    check("and says the area keeps one height",
          "keeps one\n                     height whatever the note is" in text_)
    check("and that a taller note scrolls rather than being cut",
          ("scrolls\n                     rather than being cut" in text_,
           "A scrollbar" in text_), (True, True))
    check("and that reading a note changes nothing",
          "Reading a note changes nothing" in text_)
    check("the mail section says where a long notification is read",
          "[ and ] scroll it" in text_)
    check("the overlay names no Cyrillic key",
          [ch for ch in text_ if "\u0400" <= ch <= "\u04ff"], [])

    bar = {b.description: b.key for b in main.TaskApp.BINDINGS}
    check("the key bar carries the two keys",
          (bar.get("Note up"), bar.get("Note down")),
          ("left_square_bracket,х", "right_square_bracket,ъ"))
    check("and shows them", [b.show for b in main.TaskApp.BINDINGS
                             if b.description in ("Note up", "Note down")],
          [True, True])

    print("and no longer describes the area as sized to its note")
    src = open(_REPO + "/main.py").read()
    check("the stylesheet no longer sizes the pane to its content",
          "#detail {\n        height: auto;\n        max-height: 40%;" in src,
          False)
    check("and the pane is declared with a height of its own",
          "#notes {" in src and "height: 9;" in src)
    check("the overlay does not say the note area grows",
          ("as tall as" in text_, "grows to fit" in text_), (False, False))


# -- and it costs nothing to draw ----------------------------------------
async def drawing():
    print("a repaint with the pane full, beside the real volume of mail")
    # 460 mail rows is what the real folders fold to; the note is forty
    # lines, so the pane is full and scrollable throughout.  Threads are
    # handed to the board directly rather than built as a mailbox: what is
    # being timed is drawing, and reading is timed by t_mailperf.
    rows = []
    base = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    for i in range(460):
        message = mail.Message(
            sender="sender@example.invalid", subject=f"notification {i}",
            when=base + dt.timedelta(minutes=i),
            ident=f"<zz{i}@example.invalid>", answers=None,
            body="\n".join(f"line {n}" for n in range(40)),
            text=f"notification {i}", folder="Feed", key=f"k{i}")
        rows.append(mail.Thread((message,)))
    app, size = await board([triage(f"i{i}", f"a triage task {i}", LONG)
                             for i in range(35)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot, 14)
        await pilot.press("i")
        await settle(pilot, 20)
        app.mail_threads = rows
        started = monotonic()
        app.repaint()
        drew = monotonic() - started
        await settle(pilot, 8)
        shown = sum(1 for t in app.tasks if app.is_mail(t))
        check("every mail row is on the board", shown, 460)
        check("beside the tasks", sum(1 for t in app.tasks
                                     if not app.is_mail(t)), 35)
        await select(app, pilot, app.tasks[0].id)
        check("the pane is full and has more to show",
              pane(app).max_scroll_y > 0)
        started = monotonic()
        for _ in range(3):
            app.repaint()
        again = (monotonic() - started) / 3
        print(f"        first repaint {drew:.2f}s, then {again:.2f}s each, "
              f"for {shown} mail rows + 35 tasks")
        # Generous, and the same bound t_mailperf uses: this happens on a
        # keypress, so a person notices anything above a moment.
        check("drawing stays under a second", drew < 1.0, True)
        started = monotonic()
        await pilot.press("right_square_bracket")
        await settle(pilot, 6)
        scrolled = monotonic() - started
        print(f"        and one scroll of the pane took {scrolled:.2f}s")
        check("scrolling the pane does not redraw the list",
              pane(app).scroll_offset.y > 0)


async def main_():
    for part in (the_text_still_lands, focus_stays_on_the_list, one_height,
                 scrolling, rewinding, rows_from_elsewhere, the_card,
                 saying_so, drawing):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


sys.exit(asyncio.run(main_()))
