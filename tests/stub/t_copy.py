"""What a row becomes in the text a person pastes elsewhere.

Everything here is stubbed -- no account, no network, no mailbox, no
clipboard. The rows are synthetic and so is every title in them.
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
from singularity import Bucket, CANCELLED, CHECKED, EMPTY
from textual import events
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
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

def thread(ident, subject, count=1):
    when = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    messages = tuple(
        mail.Message(sender="someone@example.invalid", subject=subject, when=when,
                     ident=f"<{ident}-{n}@example.invalid>", answers=None,
                     body="", text="", folder="Feed", key=f"{ident}{n}")
        for n in range(count)
    )
    return mail.Thread(messages)


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
    """Start a board with the sources it was given already in place."""

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


def row(app, title):
    return next(t for t in app.tasks if (t.raw.get("title") or "") == title)

def status(app):
    return str(app.query_one("#status").content)

async def cursor_to(app, pilot, title):
    """Put the row cursor on a row by title, and give it back."""
    table = app.query_one(DataTable)
    want = row(app, title)
    at = next(i for i, t in enumerate(app.tasks) if t.id == want.id)
    table.move_cursor(row=at)
    await settle(pilot, 2)
    return want


# ------------------------------------------------------------------ 2.1

async def group_2_1():
    print("2.1 a row becomes a markdown line")

    print("\n  the three states a task can be in")
    check("an unfinished task carries an empty box",
          main.as_markdown("fix the build", EMPTY), "- [ ] fix the build")
    check("a finished task carries a ticked box",
          main.as_markdown("fix the build", CHECKED), "- [x] fix the build")
    check("a cancelled task is ticked and struck through",
          main.as_markdown("fix the build", CANCELLED), "- [x] ~~fix the build~~")
    # Markdown has two boxes and this board has three states.  Striking the
    # title is the whole of the difference, so if these two ever agreed the
    # distinction would be gone with no other sign of it.
    check("cancelled and finished are not the same line",
          main.as_markdown("x", CANCELLED) != main.as_markdown("x", CHECKED), True)
    check("an unfinished title with no state given",
          main.as_markdown("fix the build"), "- [ ] fix the build")

    print("\n  the title is the row's, not the drawn cell's")
    # Mail is drawn in the inbox and nowhere else, so that is where a board
    # holding a thread has to stand.
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "a short one")],
               mails=[thread("m1", "a subject about something", count=4)])
    async with run(app) as pilot:
        r = row(app, "a subject about something")
        drawn = str(app.row_for(r)[3])
        check("the drawn cell carries the count of messages",
              "(4)" in drawn, True)
        check("the copied line does not",
              app.copy_line(r, markdown=True), "- [ ] a subject about something")

    long_title = "a title far longer than any column this board will ever draw it in"
    app = make(tasks=[mk("t1", long_title, TODAY)], position=TODAY)
    async with run(app, size=(60, 20)) as pilot:
        r = row(app, long_title)
        drawn = str(app.row_for(r)[3])
        check("the column shortened the drawn cell",
              len(drawn) < len(long_title), True)
        check("the copied line carries the whole title",
              app.copy_line(r, markdown=True), f"- [ ] {long_title}")

    print("\n  a row the board does not own is written unfinished")
    # The inbox for the message, which is drawn nowhere else.
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "an own task")],
               mails=[thread("m2", "a message")])
    async with run(app) as pilot:
        check("a mail row", app.copy_line(row(app, "a message"), markdown=True),
              "- [ ] a message")
        check("and it was not refused out loud", app._notice, None)

    # A day for the event and the issue, and for the board's own finished
    # task beside them -- which proves the empty box above is about where a
    # row came from and not about this board never writing a ticked one.
    app = make(position=TODAY,
               tasks=[mk("t1", "an own task", TODAY, checked=CHECKED)],
               events=[ev("an event")], issues=[issue("ZZA-1", "an issue")])
    async with run(app) as pilot:
        check("an event", app.copy_line(row(app, "an event"), markdown=True),
              "- [ ] an event")
        # A tracker row's title is its key and summary together, which is
        # what the board draws and therefore what is copied.
        check("a tracker issue", app.copy_line(row(app, "ZZA-1 — an issue"), markdown=True),
              "- [ ] ZZA-1 — an issue")
        check("the board's own finished task still ticks",
              app.copy_line(row(app, "an own task"), markdown=True), "- [x] an own task")
        check("and none of them was refused out loud", app._notice, None)


class Clipboard:
    """Stands in for the two routes to the system clipboard.

    Nothing here may reach a real one: a suite that ran `pbcopy` would
    replace whatever the person running it had copied, and a suite that
    wrote the escape sequence would send it to the terminal the run is
    happening in.
    """

    def __init__(self, app, program_takes_it=True):
        self.app = app
        self.terminal = []
        self.program = []
        self.takes_it = program_takes_it
        app.copy_to_clipboard = self.terminal.append
        app.clipboard_program = self._program

    def _program(self, text):
        self.program.append(text)
        return self.takes_it

    @property
    def lines(self):
        return self.terminal[-1].splitlines() if self.terminal else []


async def group_2_2():
    print("\n2.2 a row becomes a plain line")

    print("\n  the three states come out the same way")
    app = make(position=TODAY, tasks=[
        mk("t1", "fix the build", TODAY),
        mk("t2", "ship it", TODAY, checked=CHECKED),
        mk("t3", "abandon it", TODAY, checked=CANCELLED)])
    async with run(app) as pilot:
        check("an unfinished task is its title",
              app.copy_line(row(app, "fix the build"), markdown=False),
              "fix the build")
        check("a finished one is its title too",
              app.copy_line(row(app, "ship it"), markdown=False), "ship it")
        check("and a cancelled one loses the striking as well",
              app.copy_line(row(app, "abandon it"), markdown=False),
              "abandon it")
        # The whole of what plain gives up, said once and on purpose: the
        # form carries no state, so two rows in different states are one
        # line apart only in their titles.
        check("nothing in a plain line says a task was done",
              app.copy_line(row(app, "ship it"), markdown=False)
              == app.copy_line(row(app, "ship it"), markdown=True), False)
        check("no bullet, no box, no tildes",
              any(ch in app.copy_line(row(app, "abandon it"), markdown=False)
                  for ch in "-[]~"), False)

    print("\n  and the title is still the row's, not the drawn cell's")
    app = make(position=Bucket.INBOX, tasks=[mk("t1", "a short one")],
               mails=[thread("m1", "a subject about something", count=4)])
    async with run(app) as pilot:
        r = row(app, "a subject about something")
        check("the count of messages is not in the plain line",
              app.copy_line(r, markdown=False), "a subject about something")

    long_title = "a title far longer than any column this board will ever draw it in"
    app = make(tasks=[mk("t1", long_title, TODAY)], position=TODAY)
    async with run(app, size=(60, 20)) as pilot:
        check("nor is the shortening",
              app.copy_line(row(app, long_title), markdown=False), long_title)

    print("\n  a row the board does not own is its title and nothing else")
    app = make(position=TODAY,
               tasks=[mk("t1", "an own task", TODAY, checked=CHECKED)],
               events=[ev("an event")], issues=[issue("ZZA-1", "an issue")])
    async with run(app) as pilot:
        check("an event", app.copy_line(row(app, "an event"), markdown=False),
              "an event")
        check("a tracker issue",
              app.copy_line(row(app, "ZZA-1 — an issue"), markdown=False),
              "ZZA-1 — an issue")
        check("and none of them was refused out loud", app._notice, None)


async def group_4_1():
    print("\n4.1b the plain key puts the marked rows on the clipboard")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY, checked=CHECKED),
                                      mk("t3", "third", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "third")
        await pilot.press("v")
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        await pilot.press("y")
        await settle(pilot)
        check("one bare title per marked row, in the order they were marked",
              board.lines, ["third", "first", "second"])
        check("the terminal route was attempted", len(board.terminal), 1)
        check("and the local program was handed the same text",
              board.program, board.terminal)
        check("the board says what it copied, and in which form",
              "Copied 3 row(s) as plain text" in status(app), True)
        check("and the marks are still there", len(app.marked), 3)

    print("\n  the plain key works in the other keyboard layout")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await pilot.press("н")
        await settle(pilot)
        check("the Russian twin copies plainly too", board.lines, ["first"])

    print("\n  and it reaches a marked row this view is not drawing")
    app = make(position=TODAY, tasks=[mk("t1", "on today", TODAY),
                                      mk("t2", "in the inbox")])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "on today")
        await pilot.press("v")
        await pilot.press("i")
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in the inbox")
        await pilot.press("v")
        await pilot.press("y")
        await settle(pilot)
        check("both rows are in the plain text", board.lines,
              ["on today", "in the inbox"])


async def group_5():
    print("\n5.1 what survives the round trip, and what does not")
    # Markdown out, pasted back in: the tick is in the line, so it arrives.
    app = make(position=TODAY, tasks=[mk("t1", "ship it", TODAY,
                                         checked=CHECKED)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "ship it")
        await pilot.press("v")
        await pilot.press("Y")
        await settle(pilot)
        copied = board.terminal[-1]
        check("the markdown line carries the tick", copied.strip(),
              "- [x] ship it")
        app.post_message(events.Paste(copied))
        await settle(pilot, 25)
        made = [t for t in app.client.store.values()
                if t.raw.get("title") == "ship it" and t.id != "t1"]
        check("pasting it back adds one task", len(made), 1)
        check("and that task is finished", bool(made and made[0].done), True)

    # Plain out, pasted back in: nothing said "done", so nothing arrives done.
    app = make(position=TODAY, tasks=[mk("t1", "ship it", TODAY,
                                         checked=CHECKED)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "ship it")
        await pilot.press("v")
        await pilot.press("y")
        await settle(pilot)
        copied = board.terminal[-1]
        check("the plain line says nothing about the tick", copied.strip(),
              "ship it")
        app.post_message(events.Paste(copied))
        await settle(pilot, 25)
        made = [t for t in app.client.store.values()
                if t.raw.get("title") == "ship it" and t.id != "t1"]
        check("pasting it back adds one task", len(made), 1)
        check("and that task is unfinished, which is what plain means here",
              bool(made and made[0].done), False)


async def group_4():
    print("\n4.1 the markdown key puts the marked rows on the clipboard")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY),
                                      mk("t2", "second", TODAY, checked=CHECKED),
                                      mk("t3", "third", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "third")
        await pilot.press("v")
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await cursor_to(app, pilot, "second")
        await pilot.press("v")
        await pilot.press("Y")
        await settle(pilot)
        check("one line per marked row", board.lines,
              ["- [ ] third", "- [ ] first", "- [x] second"])
        check("in the order the rows were marked", board.lines[0], "- [ ] third")
        check("the terminal route was attempted", len(board.terminal), 1)
        check("and the local program was handed the same text",
              board.program, board.terminal)
        check("the board says what it copied, and in which form",
              "Copied 3 row(s) as markdown" in status(app), True)
        check("and the marks are still there", len(app.marked), 3)

    print("\n  the key works in the other keyboard layout")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await pilot.press("Н")
        await settle(pilot)
        check("the Russian twin copies too", board.lines, ["- [ ] first"])

    print("\n  a machine with no clipboard program still copies")
    app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app, program_takes_it=False)
        await cursor_to(app, pilot, "first")
        await pilot.press("v")
        await pilot.press("Y")
        await settle(pilot)
        check("the terminal route still carried it", board.lines, ["- [ ] first"])
        check("and the board still says it copied", "Copied 1" in status(app), True)

    print("\n4.2 a marked row a filter is hiding is copied too")
    app = make(position=TODAY, tasks=[mk("t1", "keep this", TODAY),
                                      mk("t2", "hide this", TODAY)])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "keep this")
        await pilot.press("v")
        await cursor_to(app, pilot, "hide this")
        await pilot.press("v")
        app.searching = "keep"
        app.repaint()
        await settle(pilot)
        check("the search hid one of the marked rows",
              [t.raw.get("title") for t in app.tasks], ["keep this"])
        check("the count still says two", "2 marked" in status(app), True)
        await pilot.press("Y")
        await settle(pilot)
        check("and both were copied", board.lines,
              ["- [ ] keep this", "- [ ] hide this"])

    print("\n  and one another view is holding")
    app = make(position=TODAY, tasks=[mk("t1", "on today", TODAY),
                                      mk("t2", "in the inbox")])
    async with run(app) as pilot:
        board = Clipboard(app)
        await cursor_to(app, pilot, "on today")
        await pilot.press("v")
        await pilot.press("i")
        await settle(pilot, 6)
        await cursor_to(app, pilot, "in the inbox")
        await pilot.press("v")
        await pilot.press("Y")
        await settle(pilot)
        check("the row marked on the other view is in the text", board.lines,
              ["- [ ] on today", "- [ ] in the inbox"])

    print("\n4.3 copying with nothing marked, either way")
    for key, said in (("y", "plainly"), ("Y", "as markdown")):
        app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
        async with run(app) as pilot:
            board = Clipboard(app)
            await pilot.press(key)
            await settle(pilot)
            check(f"{said}: the board says nothing is marked",
                  "Nothing is marked" in status(app), True)
            check(f"{said}: the terminal route was not used", board.terminal, [])
            check(f"{said}: and neither was the program", board.program, [])


async def group_4_4():
    print("\n4.4 the help and the key bar name the new keys")
    print("\n  the help names them, in English only")
    text = main.Help.TEXT
    check("the marking key is named", "\n  v  " in text, True)
    check("the plain copying key is named", "\n  y  " in text, True)
    check("and the markdown one is too", "\n  Y  " in text, True)
    check("the help says which form each gives",
          ("plain lines" in text, "as markdown" in text), (True, True))
    check("pasting is named", "paste" in text, True)
    # The help is written in the keys the board is written in.  A Cyrillic
    # letter here would name a key the bar does not show and the docs do not
    # use, and the twins suite already guarantees both letters work.
    check("no key is spelled in another alphabet",
          any(ch in text for ch in "\u043c\u043d"), False)
    # The board no longer promises undo never deletes: a paste is one action
    # and one undo, and the undo removes what the paste made.  Leaving the
    # old promise would be the help lying about the one case it is wrong in.
    check("the help no longer says undo never deletes anything",
          "never deletes anything" in text, False)
    check("and it says which case it does delete in",
          "undoing a paste removes" in text, True)

    print("\n  the key bar names both, and still fits at every width")
    for width in (120, 100, 80):
        app = make(position=TODAY, tasks=[mk("t1", "first", TODAY)])
        async with run(app, size=(width, 40)) as pilot:
            bar = str(app.query_one(main.KeyBar).content)
            want = [b.description for b in app.BINDINGS if getattr(b, "show", True)]
            missing = [w for w in want if w and w not in bar]
            check(f"every entry is on the bar at {width} columns", missing, [])
            check(f"marking and both copying keys among them at {width}",
                  ("Mark" in bar, "Copy" in bar, "Copy md" in bar),
                  (True, True, True))


def main_():
    asyncio.run(group_2_1())
    asyncio.run(group_2_2())
    asyncio.run(group_4())
    asyncio.run(group_4_1())
    asyncio.run(group_5())
    asyncio.run(group_4_4())
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main_())
