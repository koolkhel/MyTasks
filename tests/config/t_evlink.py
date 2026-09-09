"""Opening an event's link, and showing its description.

Every event here is invented.  No real calendar is read by this suite.
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

TODAY = dt.datetime.now(TZ).date()
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

CFG = ical.Config(work="WorkAcc", personal=("Me",))

def ev(title, hh=9, location="", notes="", account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False,
                      location=location, notes=notes)

async def board(events, tasks=None):
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [mk("t1", "a task", TODAY)],
                            reference=dt.datetime.now(TZ))
    app.work_project = "P-work"
    app.calendar_config = CFG
    app.tracker_config = None
    opened = []
    app.open_url = lambda url: opened.append(url)
    saved = ical.fetch
    ical.fetch = lambda cfg, day: list(events)
    return app, opened, saved

async def select(app, pilot, predicate):
    row = next(i for i, t in enumerate(app.tasks) if predicate(t))
    app.query_one(main.DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()
    return app.tasks[row]

# ------------------------------------------------ where the address is found
async def sources():
    print("the address is found wherever the calendar put it")
    JOIN, OTHER = "https://meet.example/room-1", "https://elsewhere.example/x"
    cases = [
        ("in the location alone",     ev("a", location=JOIN),                          JOIN),
        ("in the description alone",  ev("b", notes=f"Some words\n\nJoin: {JOIN}"),     JOIN),
        ("the location wins",         ev("c", location=JOIN, notes=f"see {OTHER}"),     JOIN),
        ("a location that is a place", ev("d", location="Room 4B", notes=f"x {JOIN}"),  JOIN),
        ("neither field",             ev("e"),                                          None),
        ("text holding no address",   ev("f", location="Room 4B", notes="just words"), None),
        ("an anchor in the notes",    ev("g", notes=f"<a href='{JOIN}'>join</a>"),      JOIN),
    ]
    app, opened, saved = await board([e for _, e, _ in cases])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            by_title = {t.raw["title"]: t for t in app.tasks if app.is_event(t)}
            for (name, event, want) in cases:
                check(name, by_title[event.title].raw.get(main.EVENT_URL), want)
    finally:
        ical.fetch = saved

# ------------------------------------------------------- schemes are refused
async def schemes():
    print("only web addresses are opened")
    cases = [
        ("a mail address in the location", ev("a", location="mailto:x@example.com"), None),
        ("a file address in the notes",    ev("b", notes="file:///etc/passwd"),      None),
        ("a shell-ish scheme",             ev("c", location="ssh://host/x"),         None),
        ("a refused one beside a good one",
         ev("d", location="mailto:x@example.com", notes="https://ok.example/j"),
         "https://ok.example/j"),
    ]
    app, opened, saved = await board([e for _, e, _ in cases])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            by_title = {t.raw["title"]: t for t in app.tasks if app.is_event(t)}
            for (name, event, want) in cases:
                check(name, by_title[event.title].raw.get(main.EVENT_URL), want)
    finally:
        ical.fetch = saved

# --------------------------------------------------------------- opening it
async def opening():
    print("opening the selected event")
    JOIN = "https://meet.example/room-9"
    app, opened, saved = await board([ev("with a link", location=JOIN),
                                      ev("without one", hh=10)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            await select(app, pilot, lambda t: t.raw.get("title") == "with a link")
            await pilot.press("o")
            await pilot.pause()
            check("the event's own address is handed over", opened, [JOIN])
            check("and the board says so", "Opening" in str(app.query_one("#status").render()), True)
            writes = [c for c, _ in app.client.calls
                      if c not in StubClient.READS | {"tag_title"}]
            check("nothing was written", writes, [])

            await select(app, pilot, lambda t: t.raw.get("title") == "without one")
            await pilot.press("o")
            await pilot.pause()
            check("an event with no address opens nothing", opened, [JOIN])
            check("and is called an event, not a task",
                  str(app.query_one("#status").render()), "That event has no link")

            # a task in the same view still says "task"
            await select(app, pilot, lambda t: not app.is_event(t))
            await pilot.press("o")
            await pilot.pause()
            check("a task with no link still says task",
                  str(app.query_one("#status").render()), "That task has no link")
    finally:
        ical.fetch = saved

# -------------------------------------------------- opening is the one key
async def only_opening():
    print("opening is the one key that acts on an event")
    JOIN = "https://meet.example/room-3"
    app, opened, saved = await board([ev("a meeting", location=JOIN)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            await select(app, pilot, app.is_event)
            for key in ["space", "x", "d", "g", "p", "e", "J", "K", "backspace"]:
                await pilot.press(key)
                await pilot.pause()
                check(f"{key} asks nothing, it just refuses",
                      [type(s).__name__ for s in app.screen_stack], ["Screen"])
                said = str(app.query_one("#status").render()).lower()
                check(f"{key} says the row is not the board's",
                      "calendar" in said, True)
            writes = [c for c, _ in app.client.calls
                      if c not in StubClient.READS | {"tag_title"}]
            check("every writing key still writes nothing", writes, [])
            check("and nothing was opened by them", opened, [])
            await select(app, pilot, app.is_event)
            await pilot.press("o")
            await pilot.pause()
            check("while opening still works", opened, [JOIN])
    finally:
        ical.fetch = saved

# ------------------------------------------------------- the description
async def description():
    print("the description of a selected event")
    # Invented, but shaped like the real thing: prose, a rule, a labelled
    # address, non-ASCII throughout.  No real description is used here.
    TEXT = "Привет всем.\n\n____\n\nАдрес:\nhttps://meet.example/room-7"
    app, opened, saved = await board([
        ev("with words", location="https://meet.example/room-7", notes=TEXT),
        ev("silent", hh=10),
        ev("words but no link", hh=11, notes="just what it is about"),
    ], tasks=[mk("t1", "a task", TODAY)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            detail = app.query_one("#detail", main.Static)
            await select(app, pilot, lambda t: t.raw.get("title") == "with words")
            shown = str(detail.render())
            check("the description is shown", shown, TEXT)

            await select(app, pilot, lambda t: t.raw.get("title") == "silent")
            check("an event with none shows nothing", str(detail.render()), "")

            await select(app, pilot, lambda t: t.raw.get("title") == "words but no link")
            check("shown even with no address", str(detail.render()), "just what it is about")

            await select(app, pilot, lambda t: not app.is_event(t))
            check("selecting a task afterwards leaves nothing of it",
                  str(detail.render()), "")
    finally:
        ical.fetch = saved

# ----------------------------------------------------------- escaping it
async def escaping():
    print("a description is shown as its own characters")
    HOSTILE = "before [bold red]LOUD[/] and [x] after"
    app, opened, saved = await board([ev("hostile", notes=HOSTILE)])
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            for _ in range(12):
                await pilot.pause()
            detail = app.query_one("#detail", main.Static)
            await select(app, pilot, app.is_event)
            drawn = detail.render()
            check("every character survives", str(drawn), HOSTILE)
            check("and no style was applied", list(getattr(drawn, "spans", [])), [])
    finally:
        ical.fetch = saved

async def main_():
    await sources()
    await schemes()
    await opening()
    await only_opening()
    await description()
    await escaping()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
