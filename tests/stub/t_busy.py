"""Whether the mailbox is busy, said in one cell -- and a log of what it did.

Reviewing a mail row is the slowest thing the board does and used to show
nothing: ~13 s for a row of one message, ~25 s a message for a folded one,
one review at a time. Ticking ten rows left nine not yet started, and
quitting abandoned them silently.

The load-bearing check here is that the count of operations in flight comes
back down on every path an operation can end by. There are six, and a missed
one would leave the board saying "wait" for the rest of the session -- worse
than saying nothing. Each is driven through the real code against a
substituted server, never by calling the decrement.

Self-contained: a stubbed store, a substituted gateway, no mailbox unless a
check builds one, no network. Every message is generated, and the log is
pointed at a throwaway directory.
"""
import asyncio, datetime as dt, os, re, subprocess, sys, tempfile, threading
from time import monotonic

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import fakeimap
import gateway, journal, mail, main
from textual.widgets import DataTable, Static

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def ident(n):
    return f"<zz{n}@example.invalid>"


def elsewhere():
    """Point the log at a throwaway file, and answer its path."""
    journal.PATH = os.path.join(tempfile.mkdtemp(prefix="journal."),
                                "logs", "mytasks.log")
    return journal.PATH


def lines():
    try:
        with open(journal.PATH, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip()]
    except OSError:
        return []


def server(**kw):
    return fakeimap.FakeIMAP({"Feed": [ident(i) for i in range(4)],
                              "Archive": []}, **kw)


async def board(imap, tasks=None, size=(100, 44), gateway_cfg=fakeimap.CONFIG,
                subject="a notification", body="what it says"):
    """A board whose inbox holds one mail row of three messages."""
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else
                            [mk("i1", "a triage task")], reference=NOW)
    app.calendar_config = app.tracker_config = None
    app.mail_config = None
    base = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    app.mail_threads = [mail.Thread(tuple(
        mail.Message(sender="s@example.invalid", subject=subject,
                     when=base + dt.timedelta(minutes=i), ident=ident(i),
                     answers=None, body=body, text=subject, folder="Feed",
                     key=f"k{i}")
        for i in range(3)))]
    app.gateway_config = gateway_cfg
    app.gateway_connect = None if imap is None else (lambda: imap)
    return app, size


async def settle(pilot, n=14):
    for _ in range(n): await pilot.pause()


def bar(app):
    return str(app.query_one("#daybar", Static).render())


def mark(app):
    return bar(app).rstrip()[-1:]


async def to_mail(app, pilot):
    await pilot.press("i")
    await settle(pilot, 22)
    row = next(t for t in app.tasks if app.is_mail(t))
    table = app.query_one(DataTable)
    at = app.tasks.index(row)
    table.move_cursor(row=at)
    app._selected_id = row.id
    await settle(pilot, 6)
    return row


# -- the log --------------------------------------------------------------
async def the_log():
    print("the log writes one line an entry, where it is told to")
    path = elsewhere()
    journal.ok("a thing happened")
    journal.warn("a thing was odd")
    journal.error("a thing failed")
    got = lines()
    check("three lines", len(got), 3)
    shape = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (OK|WARN|ERROR) +(.+)$")
    parsed = [shape.match(l) for l in got]
    check("each parses into stamp, level and message",
          [bool(m) for m in parsed], [True, True, True])
    check("the levels are the three", [m.group(2) for m in parsed if m],
          ["OK", "WARN", "ERROR"])
    check("and it landed where it was pointed", os.path.exists(path))

    print("its own path is beside the board, not beside the caller")
    import importlib
    fresh = importlib.reload(journal)
    check("the default is the board's own logs directory",
          os.path.relpath(fresh.PATH, _REPO), "logs/mytasks.log")
    check("resolved absolutely, so the working directory cannot move it",
          os.path.isabs(fresh.PATH))
    elsewhere()

    print("a log that cannot be written changes nothing")
    # A path whose parent is a file, so no directory can be made there.
    blocked = tempfile.NamedTemporaryFile(delete=False)
    blocked.close()
    journal.PATH = os.path.join(blocked.name, "logs", "mytasks.log")
    journal.ok("this cannot land anywhere")
    journal.error("nor can this")
    check("nothing was raised", True)
    check("and nothing was written", lines(), [])
    elsewhere()

    print("the log is not committable")
    ignored = subprocess.run(["git", "-C", _REPO, "check-ignore",
                              "logs/mytasks.log"],
                             capture_output=True, text=True)
    check("git ignores it", ignored.stdout.strip(), "logs/mytasks.log")
    listed = subprocess.run(["git", "-C", _REPO, "status", "--porcelain"],
                            capture_output=True, text=True)
    check("and never lists it",
          [l for l in listed.stdout.splitlines() if "logs/" in l], [])


# -- the count comes down, six ways ---------------------------------------
async def every_way_it_ends():
    print("the count rises on a tick and falls when it is confirmed")
    elsewhere()
    imap = server()
    app, size = await board(imap)
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        row = next(t for t in app.tasks if app.is_mail(t))
        check("nothing in flight to start", app.mail_busy, 0)
        # Called rather than pressed, and read with nothing awaited between:
        # the count rises on the UI thread before the worker is scheduled,
        # and the substituted server is fast enough to finish inside a
        # keypress.  Key dispatch is what every other case here presses for.
        app.review(row)
        check("one in flight the moment a review starts", app.mail_busy, 1)
        await settle(pilot, 34)
        check("and none when it is confirmed", app.mail_busy, 0)
        check("nothing is marked as failed", app.mail_broken, False)

    ways = []

    print("unconfirmed: the archive denies it arrived")
    elsewhere()
    ways.append(("unconfirmed", server(deny=("Archive",)), True))

    print("in neither place: it is in no folder at all")
    elsewhere()
    empty = fakeimap.FakeIMAP({"Feed": [], "Archive": []})
    ways.append(("in neither place", empty, True))

    print("already archived: somebody else moved it")
    elsewhere()
    done = fakeimap.FakeIMAP({"Feed": [],
                              "Archive": [ident(i) for i in range(3)]})
    ways.append(("already archived", done, False))

    print("unreachable: the gateway refuses us")
    elsewhere()

    class Refuses(fakeimap.FakeIMAP):
        def login(self, user, secret):
            raise OSError("no route to host")

    ways.append(("gateway unreachable",
                 Refuses({"Feed": [ident(i) for i in range(3)],
                          "Archive": []}), True))

    for label, imap, expect_failed in ways:
        elsewhere()
        app, size = await board(imap)
        async with app.run_test(size=size) as pilot:
            await settle(pilot)
            await to_mail(app, pilot)
            await pilot.press("space")
            await settle(pilot, 40)
            check(f"{label}: the count is back to zero", app.mail_busy, 0)
            check(f"{label}: and the mark says "
                  f"{'failed' if expect_failed else 'idle'}",
                  app.mail_broken, expect_failed)
            check(f"{label}: something was logged", len(lines()) >= 2, True)

    print("the flag that says the board is leaving is the board's own")
    # It was `_closing` until this change, which is Textual's own: its
    # message loop reads `while not (self._closed or self._closing)`, so
    # setting it told the framework the app was shutting down and the board
    # stopped accepting messages while still running.  Nothing after this
    # point in the suite could run at all.
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        check("the board does not name the pump's flag",
              hasattr(app, "_leaving") and app._leaving is False, True)
        app._leaving = True
        # The board must still be a working application: this is the pause
        # that never returned.
        await settle(pilot, 8)
        check("and setting it leaves the board able to draw",
              str(app.query_one("#daybar", Static).render()) != "", True)
        await pilot.press("t")
        await settle(pilot, 20)
        check("and able to answer a key", app.position, TODAY)

    print("given up: the board is leaving")
    # Given up at the door rather than part way through: the board is
    # already closing when the tick lands, so `file_away` returns from
    # inside the lock and its `finally` is what must still bring the count
    # down.  The mid-operation give-up -- the stop callback firing between
    # messages -- is driven in t_gateway, where it can be held open without
    # a live app waiting on the worker at teardown.
    elsewhere()
    imap = server()
    app, size = await board(imap)
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        app._leaving = True
        await pilot.press("space")
        await settle(pilot, 24)
        check("given up: the count is back to zero", app.mail_busy, 0)
        check("given up: nothing was asked of the server", imap.commands(), [])
        check("given up: and the board is still drawing", mark(app),
              main.MAIL_IDLE_MARK)
        check("given up: and it says so in the log",
              any("given up" in l for l in lines()), True)

    print("undoing settles too")
    for label, imap in (("put back", server()),
                        ("not in the archive",
                         fakeimap.FakeIMAP({"Feed": [], "Archive": []}))):
        elsewhere()
        app, size = await board(imap)
        async with app.run_test(size=size) as pilot:
            await settle(pilot)
            await to_mail(app, pilot)
            await pilot.press("space")
            await settle(pilot, 34)
            await pilot.press("u")
            await settle(pilot, 34)
            check(f"undo, {label}: the count is back to zero",
                  app.mail_busy, 0)
            check(f"undo, {label}: it was logged",
                  any("undo" in l for l in lines()), True)

    print("a board that has done nothing, and one with no gateway")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        check("nothing in flight", app.mail_busy, 0)
    elsewhere()
    imap = server()
    app, size = await board(imap, gateway_cfg=None)
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        await pilot.press("space")
        await settle(pilot, 20)
        check("a tick refused for want of a gateway counts nothing",
              app.mail_busy, 0)
        check("and asked the server nothing", imap.commands(), [])


# -- nothing identifying reaches the file ---------------------------------
async def nothing_identifying():
    print("the log holds identities, not subjects or senders")
    elsewhere()
    app, size = await board(server(), subject="ZZMARKERSUBJECT about a thing",
                            body="ZZMARKERBODY and more of it")
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        await pilot.press("space")
        await settle(pilot, 34)
    text = "\n".join(lines())
    check("something was logged at all", len(lines()) >= 2, True)
    check("no subject reached the file", "ZZMARKERSUBJECT" in text, False)
    check("no body reached the file", "ZZMARKERBODY" in text, False)
    check("no sender reached the file", "s@example.invalid" in text, False)
    check("the folder is there", "Feed" in text, True)
    check("the count is there", "3 message(s)" in text, True)
    check("and a duration", bool(re.search(r"in \d+\.\ds", text)), True)


# -- the cell -------------------------------------------------------------
async def the_cell():
    print("one cell at the right of the bar, in every view")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        for key, label in (("t", "a day"), ("i", "the inbox"),
                           ("s", "someday")):
            await pilot.press(key)
            await settle(pilot, 20)
            check(f"{label}: the bar ends with the idle mark",
                  mark(app), main.MAIL_IDLE_MARK)
            check(f"{label}: and still says what it said",
                  len(bar(app).strip()) > 3, True)

    print("every mark it can show is one cell wide")
    import unicodedata
    every = (main.MAIL_IDLE_MARK, main.MAIL_FAILED_MARK) + main.MAIL_BUSY_MARKS
    check("each is a single character", [len(m) for m in every],
          [1] * len(every))
    check("and none is double-width",
          [m for m in every
           if unicodedata.east_asian_width(m) in ("W", "F")], [])
    check("the busy frames share one width class, so the edge cannot jitter",
          len({unicodedata.east_asian_width(m)
               for m in main.MAIL_BUSY_MARKS}), 1)

    print("a terminal too narrow for both keeps the text")

    async def bar_at(width):
        elsewhere()
        app, size = await board(server(), size=(width, 24))
        async with app.run_test(size=size) as pilot:
            await settle(pilot)
            return str(app.query_one("#daybar", Static).render())

    # Measured, not assumed.  This bar is a date, and a day name and a month
    # name are of different lengths on different days: the mark goes only once
    # the line reaches 37 characters, and in September only a Wednesday's name
    # is long enough.  Written on a Wednesday, this case asked whether today
    # was called something long rather than whether the mark is dropped when it
    # will not fit, and it failed on the other six days.
    wide = (await bar_at(200)).rstrip()
    if wide.endswith(main.MAIL_IDLE_MARK):
        wide = wide[:-1].rstrip()
    room = len(wide)
    check("the bar says something to measure", room > 8, True)
    # The board pads the mark on and drops it when `len(text) + 2 > room`,
    # with `room` two columns narrower than the terminal -- so it fits from
    # four columns above the text's own length.  Both sides of that boundary
    # are asserted, so a change to the padding fails one of them rather than
    # passing quietly.
    for width, expect in ((room + 4, True), (room + 3, False)):
        shown = await bar_at(width)
        check(f"{width - room:+d} columns from the text: the mark is "
              f"{'shown' if expect else 'dropped'}",
              shown.rstrip().endswith(main.MAIL_IDLE_MARK), expect)
        check(f"{width - room:+d}: and the bar still says what it said",
              wide[:12] in shown, True)

    # And well away from the boundary, where the ordinary answers live.
    for width, expect in ((200, True), (max(room - 10, 12), False)):
        shown = await bar_at(width)
        check(f"{width} cols: the mark is {'shown' if expect else 'dropped'}",
              shown.rstrip().endswith(main.MAIL_IDLE_MARK), expect)
        check(f"{width} cols: and the bar still says what it said",
              len(shown.strip()) > 3, True)

    print("and the boundary sits at the same place whatever the bar says")
    # The bracket above measures today's bar, so it holds today by
    # construction.  What has to hold on any day is that the offset is the
    # same for a text of any length -- a Wednesday's name is two characters
    # longer than a Friday's, and that difference is what broke this case.
    # So: the rule, asked about two supplied texts rather than about today.
    SAID = ("Friday 11 September 2026  ·  tomorrow",
            "Wednesday 09 September 2026  ·  yesterday")
    check("the two texts really are of different lengths",
          len(SAID[0]) != len(SAID[1]), True)
    for said in SAID:
        for width, expect in ((len(said) + 4, True), (len(said) + 3, False)):
            elsewhere()
            app, size = await board(server(), size=(width, 24))
            async with app.run_test(size=size) as pilot:
                await settle(pilot)
                # Not `bar`: this suite has a module-level `bar(app)` helper,
                # and a local of that name shadows it for the whole function.
                widget = app.query_one("#daybar", Static)
                got = app.with_mark(said, widget).rstrip()
                check(f"{len(said)} chars at {width} cols: the mark is "
                      f"{'shown' if expect else 'dropped'}",
                      got.endswith(main.MAIL_IDLE_MARK), expect)
                check(f"{len(said)} chars at {width} cols: the text is kept",
                      got.startswith(said), True)

    print("in flight while a review runs, and at rest after")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        row = await to_mail(app, pilot)
        app.review(row)
        check("the mark is one of the busy frames",
              mark(app) in main.MAIL_BUSY_MARKS, True)
        check("and a timer is turning it", app._spinner is not None, True)
        await settle(pilot, 34)
        check("at rest once it is confirmed", mark(app), main.MAIL_IDLE_MARK)
        check("and the timer has stopped", app._spinner is None, True)

    print("the frames advance while it is in flight")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        app.mail_started()          # held busy, with no worker to wait for
        seen = {mark(app)}
        for _ in range(6):
            app.spin()
            seen.add(mark(app))
        check("more than one frame was shown", len(seen) > 1, True)
        check("and every one is a named frame",
              seen - set(main.MAIL_BUSY_MARKS), set())
        app.mail_settled()
        check("back to rest", mark(app), main.MAIL_IDLE_MARK)

    print("turning it redraws no row")
    elsewhere()
    app, size = await board(server(), tasks=[mk(f"i{i:02d}", f"triage {i}")
                                             for i in range(12)])
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        table = app.query_one(DataTable)
        app.mail_started()
        rows, chosen, offset = (len(app.tasks), app._selected_id,
                                int(table.scroll_y))
        for _ in range(8):
            app.spin()
            await pilot.pause()
        check("the same rows are shown", len(app.tasks), rows)
        check("the same row is selected", app._selected_id, chosen)
        check("and the view has not moved", int(table.scroll_y), offset)
        app.mail_settled()

    print("a failure shows, survives a success, and clears on a reload")
    elsewhere()
    app, size = await board(server(deny=("Archive",)))
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        await pilot.press("space")
        await settle(pilot, 40)
        check("the mark says something failed", mark(app),
              main.MAIL_FAILED_MARK)
        fresh = server()
        app.gateway_connect = lambda: fresh
        row = next((t for t in app.tasks if app.is_mail(t)), None)
        check("the row came back to try again", row is not None, True)
        if row is not None:
            app.review(row)
            await settle(pilot, 34)
        check("a later success does not clear it", mark(app),
              main.MAIL_FAILED_MARK)
        await pilot.press("r")
        await settle(pilot, 24)
        check("asking for a reload clears it", mark(app),
              main.MAIL_IDLE_MARK)


# -- quitting -------------------------------------------------------------
async def quitting():
    print("quitting asks while the mailbox is busy")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        app.mail_started()          # busy, with no worker to wait for
        await pilot.press("q")
        await settle(pilot, 16)
        top = [type(sc).__name__ for sc in app.screen_stack][-1:]
        check("the board asks first", top, ["Confirm"])
        asked = str(app.screen.query_one("#dialog-title").render())
        check("and says how much is outstanding", "1 mailbox operation" in asked,
              True)
        check("the board is still running", app.is_running, True)
        await pilot.press("escape")
        await settle(pilot, 12)
        check("declining leaves it running", app.is_running, True)
        check("on the same view", app.position, main.Bucket.INBOX)
        check("with the work still counted", app.mail_busy, 1)
        check("and no dialogue left open",
              [type(sc).__name__ for sc in app.screen_stack], ["Screen"])
        app.mail_settled()

    print("confirming ends it")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        app.mail_started()
        await pilot.press("q")
        await settle(pilot, 16)
        check("it asked", [type(sc).__name__ for sc in app.screen_stack][-1:],
              ["Confirm"])
        await pilot.press("y")
        await settle(pilot, 20)
        check("the board is ending", app.is_running, False)
        check("and it said so in the log",
              any("quit with" in l for l in lines()), True)

    print("with nothing in flight it asks nothing")
    elsewhere()
    app, size = await board(server())
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        await to_mail(app, pilot)
        check("nothing outstanding", app.mail_busy, 0)
        await pilot.press("q")
        await settle(pilot, 20)
        check("no dialogue appeared",
              [type(sc).__name__ for sc in app.screen_stack], ["Screen"])
        check("and the board is ending", app.is_running, False)


# -- saying so ------------------------------------------------------------
async def saying_so():
    print("the overlay says what the cell means and where the log is")
    text = main.Help.TEXT
    check("all three states are named",
          [m in text for m in (main.MAIL_IDLE_MARK, main.MAIL_BUSY_MARKS[0],
                               main.MAIL_FAILED_MARK)],
          [True, True, True])
    check("it says filing takes ten seconds or more",
          "ten seconds or more" in text, True)
    check("that they go one at a time", "one at a time" in text, True)
    check("that quitting asks", "asks before quitting" in text, True)
    check("that r takes the mark down",
          f"r takes the {main.MAIL_FAILED_MARK} down" in text, True)
    check("the log's path is named", "logs/mytasks.log" in text, True)
    check("and that it holds no subject or sender",
          ("no subject" in text, "no sender" in text), (True, True))
    check("the overlay names no Cyrillic key",
          [ch for ch in text if "\u0400" <= ch <= "\u04ff"], [])

    print("and nothing shipped claims the board writes nothing to disk")
    board_src = open(_REPO + "/main.py").read()
    for claim in ("writes nothing to disk", "no state of its own on disk",
                  "nothing is written to disk"):
        check(f"the board does not claim {claim!r}",
              claim in board_src or claim in text, False)


async def main_():
    for part in (the_log, every_way_it_ends, nothing_identifying, the_cell,
                 quitting, saying_so):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


sys.exit(asyncio.run(main_()))
