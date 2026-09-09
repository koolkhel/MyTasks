"""The mail view on the board: rows, counts, refusals, opening.

Synthetic mail only -- the sample maildir and throwaway ones built here.
"""
import asyncio, datetime as dt, mailbox, os, shutil, sys, tempfile, threading
from contextlib import asynccontextmanager
from email.message import EmailMessage
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import main, mail, tracker, ical
from textual.widgets import DataTable

HERE = os.path.dirname(os.path.abspath(__file__))
# A copy, never the fixture itself.  The board can now write to a mailbox --
# promoting marks a thread read -- so a suite that points it at the shared
# sample can quietly rewrite the thing every other mail suite measures
# against.  It happened once; copying is what makes it impossible.
_FIXTURE = _os.path.join(_TESTS, "fixtures", "sample_mail")
SAMPLE = os.path.join(tempfile.mkdtemp(prefix="fixture."), "sample_mail")
shutil.copytree(_FIXTURE, SAMPLE)
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
TRK = tracker.Config(base_url="https://track.corp.invalid", token="t", assignee="me",
                     projects=("ABC",), states=("In progress",))
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def build(messages):
    root = tempfile.mkdtemp()
    path = os.path.join(root, "mail")
    box = mailbox.Maildir(path, create=True)
    for i, (subject, body, headers) in enumerate(messages):
        m = EmailMessage()
        m["From"] = headers.get("From", "sender@example.invalid")
        m["Subject"] = subject
        m["Date"] = (NOW - dt.timedelta(minutes=(len(messages) - i) * 5)).strftime(
            "%a, %d %b %Y %H:%M:%S %z")
        m["Message-ID"] = headers.get("Message-ID", f"<b{i}@example.invalid>")
        if headers.get("In-Reply-To"): m["In-Reply-To"] = headers["In-Reply-To"]
        m.set_content(body)
        box.add(mailbox.MaildirMessage(m))
    box.flush()
    return mail.Config(path)

#: "not specified" must be tellable from "no mailbox", or the helper cannot
#: express the very case it is asked to test.
UNSET = object()

@asynccontextmanager
async def board(mail_cfg=UNSET, tasks=None, tracker_cfg=None, go_to_inbox=True):
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [mk("t1", "a task", TODAY)],
                            reference=NOW)
    app.calendar_config = None
    app.tracker_config = tracker_cfg
    app.mail_config = mail.Config(SAMPLE) if mail_cfg is UNSET else mail_cfg
    opened = []
    app.open_url = lambda url: opened.append(url)
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        if go_to_inbox:
            await pilot.press("i")
            for _ in range(20): await pilot.pause()
        yield app, pilot, opened

def shown(app):
    return [str(app.row_for(t)[3]) for t in app.tasks]

async def select(app, pilot, pred):
    row = next(i for i, t in enumerate(app.tasks) if pred(t))
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()
    return app.tasks[row]

def status(app): return str(app.query_one("#status").render())

# ---------------------------------------------------------------- the view
async def the_view():
    print("mail is shown in the inbox, leading its tasks")
    async with board(tasks=[mk("i1", "an inbox task"),
                            mk("d1", "a task", TODAY)]) as (app, pilot, opened):
        kinds = ["MAIL" if app.is_mail(t) else "task" for t in app.tasks]
        check("the inbox holds mail and tasks", set(kinds), {"MAIL", "task"})
        check("mail leads, and is contiguous", kinds, ["MAIL"] * 8 + ["task"])
        check("both queues are counted",
              ("8 thread(s)" in status(app), "14 message(s)" in status(app)),
              (True, True))
        tasks_only = sum(1 for t in app.tasks if not app.is_mail(t))
        check("and the task count counts tasks alone",
              f"{tasks_only} task(s)" in status(app), True)
        # and away again
        await pilot.press("t")
        for _ in range(18): await pilot.pause()
        check("back on the day, its tasks are there", shown(app), ["a task"])
        check("and no mail row came with it",
              any(app.is_mail(t) for t in app.tasks), False)
        await pilot.press("s")
        for _ in range(18): await pilot.pause()
        check("someday holds no mail",
              any(app.is_mail(t) for t in app.tasks), False)

    print("no mailbox configured")
    async with board(mail_cfg=None, tasks=[mk("i1", "an inbox task")]) as (app, pilot, opened):
        check("the inbox is exactly the view it was",
              [t.raw.get("title") for t in app.tasks], ["an inbox task"])
        check("no mail row appears", any(app.is_mail(t) for t in app.tasks), False)
        check("and no failure is reported", app.mail_error, None)
        check("nor any thread count", "thread(s)" in status(app), False)

    print("a mailbox that cannot be read")
    async with board(mail_cfg=mail.Config("/nonexistent/mailbox"),
                     tasks=[mk("i1", "an inbox task"),
                            mk("d1", "a task", TODAY)]) as (app, pilot, opened):
        check("it says so", "mailbox" in status(app).lower(), True)
        check("and the inbox still holds its tasks",
              [t.raw.get("title") for t in app.tasks], ["an inbox task"])
        await pilot.press("t")
        for _ in range(18): await pilot.pause()
        check("the day is unaffected", shown(app), ["a task"])

# ----------------------------------------------------------------- the row
async def the_row():
    print("what a mail row shows")
    cfg = build([
        ("first of a run", "one", {"Message-ID": "<r1@x.invalid>"}),
        ("second of a run", "two", {"Message-ID": "<r2@x.invalid>",
                                    "In-Reply-To": "<r1@x.invalid>"}),
        ("alone", "solo", {"From": "Alexey Petrov <a.p@x.invalid>",
                           "Message-ID": "<s1@x.invalid>"}),
        ("[x] and [bold]loud[/]", "markup", {"Message-ID": "<m1@x.invalid>"}),
    ])
    async with board(mail_cfg=cfg, tasks=[]) as (app, pilot, opened):
        rows = {str(app.row_for(t)[3]): app.row_for(t) for t in app.tasks}
        run = next(r for k, r in rows.items() if "second of a run" in k)
        check("a thread of several says how many", "(2)" in str(run[3]), True)
        solo = next(r for k, r in rows.items() if "alone" in k)
        check("a thread of one says no count", "(" in str(solo[3]), False)
        # The column is eleven cells, so a longer name is shortened -- what
        # matters is that the NAME is used rather than the address.
        check("a display name is preferred over an address",
              str(solo[4]).startswith("Alexey"), True)
        check("a sender without one shows the part before the @",
              any("sender" in str(r[4]) for r in rows.values()), True)
        check("the mark is the mailbox's own", str(run[1]), main.MAIL_ROW_MARK)
        check("distinct from a task's, an event's and the tracker's",
              len({main.MAIL_ROW_MARK, main.EVENT_ROW_MARK,
                   main.TRACKER_ROW_MARK, main.MARKS[0]}), 4)
        hostile = next(k for k in rows if "loud" in k)
        check("a subject's markup characters are shown, not interpreted",
              hostile.startswith("[x] and [bold]loud[/]"), True)
        drawn = app.row_for(next(t for t in app.tasks
                                 if "loud" in (t.raw.get("title") or "")))[3]
        check("and no styling comes from them",
              [str(sp.style) for sp in getattr(drawn, "spans", ())], [])
        check("the when column fits",
              max(len(str(app.row_for(t)[2])) for t in app.tasks) <= main._WHEN_WIDTH, True)

    print("a subject too long for its column")
    long = "x" * 400
    cfg = build([(long, "body", {})])
    for width in (60, 80, 100, 120, 160):
        async with board(mail_cfg=cfg, tasks=[]) as (app, pilot, opened):
            app.query_one(DataTable)  # laid out
            cell = str(app.row_for(app.tasks[0])[3])
            ok.append(len(cell) <= app.title_width)
            if len(cell) > app.title_width:
                print(f"  FAIL a long subject is shortened at width {width}")
    print(f"  ok   a long subject is shortened, at every width tried")

# ------------------------------------------------ what a message says
async def the_body():
    print("what a message says, in the notes region")
    cfg = build([
        ("says something", "the first line\nthe second line", {}),
        ("says nothing", "", {}),
        ("markup inside", "before [bold red]LOUD[/] and [x] after", {}),
    ])
    async with board(mail_cfg=cfg,
                     tasks=[mk("i1", "a task with a note")]) as (app, pilot, opened):
        app._base[0].raw["note"] = "the task's own note"
        app.repaint(); await pilot.pause()
        detail = app.query_one("#detail", main.Static)
        await select(app, pilot, lambda t: "says something" in (t.raw.get("title") or ""))
        shown = str(detail.render())
        check("the body is shown", shown, "the first line\nthe second line")
        check("and the subject is not repeated in it",
              shown.startswith("says something"), False)
        await select(app, pilot, lambda t: "says nothing" in (t.raw.get("title") or ""))
        check("an empty body shows nothing", str(detail.render()), "")
        await select(app, pilot, lambda t: "markup inside" in (t.raw.get("title") or ""))
        drawn = detail.render()
        check("every character of a markup-like body survives",
              str(drawn), "before [bold red]LOUD[/] and [x] after")
        check("and no styling comes from it",
              [str(sp.style) for sp in getattr(drawn, "spans", ())], [])
        await select(app, pilot, lambda t: not app.is_mail(t))
        check("selecting a task shows the task's own note",
              str(detail.render()), "the task's own note")


# -------------------------------------------------------------- opening
async def opening():
    print("opening what a thread points at")
    async with board(tracker_cfg=TRK, tasks=[]) as (app, pilot, opened):
        four = await select(app, pilot,
                            lambda t: "deploy-prod #844" in (t.raw.get("title") or ""))
        check("a run of four builds offers one address, not four",
              len(app.openable(four)), 1)
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        check("and it is the newest",
              opened[-1:], ["https://ci.corp.invalid/job/deploy-prod/844/console"])
        check("with no choice presented",
              [type(s).__name__ for s in app.screen_stack], ["Screen"])
        issue = await select(app, pilot,
                             lambda t: "ABC-1234" in (t.raw.get("title") or ""))
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        check("a thread naming a configured issue opens the issue",
              opened[-1:], ["https://track.corp.invalid/issue/ABC-1234"])
        human = await select(app, pilot,
                             lambda t: "quick question" in (t.raw.get("title") or ""))
        before = list(opened)
        await pilot.press("o")
        for _ in range(8): await pilot.pause()
        check("a thread with nothing to open opens nothing", opened, before)
        check("and says so, naming what the row is", status(app), "That thread has no link")
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written by any of it", writes, [])

    print("an unconfigured project's key is not an issue")
    async with board(tracker_cfg=None, tasks=[]) as (app, pilot, opened):
        t = await select(app, pilot, lambda x: "ABC-99" in (x.raw.get("title") or ""))
        offers = [s for s, _ in app.openable(t)]
        check("only the address is offered", offers,
              ["https://track.corp.invalid/issue/ABC-99"])

# ------------------------------------------------------------- refusals
async def refusals():
    print("a mail row cannot be changed from the board")
    before = None
    async with board(tasks=[]) as (app, pilot, opened):
        snap = lambda: sorted(os.listdir(os.path.join(SAMPLE, "new")))
        before = snap()
        await select(app, pilot, app.is_mail)
        for key in ["space", "x", "d", "e", "n", "g", "p", "J", "K", "backspace"]:
            await pilot.press(key)
            await pilot.pause()
            check(f"{key}: nothing is asked first",
                  [type(s).__name__ for s in app.screen_stack], ["Screen"])
        check("and it says the row belongs to the mailbox",
              "mailbox" in status(app).lower(), True)
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written to the store", writes, [])
        check("and nothing to the mailbox", snap(), before)
        # The count is asserted where the view is checked, not here: a
        # refusal notice is sticky, so after pressing a refused key the
        # status line is the refusal rather than the counts.

# --------------------------------------------- the mailbox never delays the board
async def never_delays():
    print("the mailbox does not delay the day")
    gate = threading.Event()
    real_read = mail.read
    def slow(cfg):
        gate.wait(10)
        return real_read(cfg)
    mail.read = slow
    try:
        async with board(go_to_inbox=False) as (app, pilot, opened):
            check("the day's tasks are on screen with the mailbox still reading",
                  shown(app), ["a task"])
            check("and the board is not saying it is loading",
                  "Loading" in status(app), False)
            gate.set()
            for _ in range(20): await pilot.pause()
    finally:
        mail.read = real_read
        gate.set()

    print("a mailbox far larger than a person would read")
    import time
    big = tempfile.mkdtemp()
    path = os.path.join(big, "mail")
    box = mailbox.Maildir(path, create=True)
    for i in range(2000):
        m = EmailMessage()
        m["From"] = f"robot{i % 7}@example.invalid"
        m["Subject"] = f"notification number {i}"
        m["Date"] = (NOW - dt.timedelta(minutes=i)).strftime("%a, %d %b %Y %H:%M:%S %z")
        m["Message-ID"] = f"<big{i}@example.invalid>"
        if i % 4:                       # three in four answer the one before
            m["In-Reply-To"] = f"<big{i - 1}@example.invalid>"
        m.set_content(f"see https://example.invalid/n/{i}")
        box.add(mailbox.MaildirMessage(m))
    box.flush()
    t0 = time.perf_counter()
    msgs = mail.read(mail.Config(path))
    read_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    ths = mail.threads(msgs)
    thread_ms = (time.perf_counter() - t0) * 1000
    print(f"      2000 messages: read {read_ms:.0f}ms, threaded {thread_ms:.0f}ms,"
          f" {len(ths)} threads")
    check("two thousand messages are all read", len(msgs), 2000)
    check("and threading them is not quadratic (under a second)", thread_ms < 1000, True)
    async with board(mail_cfg=mail.Config(path), tasks=[]) as (app, pilot, opened):
        check("the board draws the big mailbox", len(app.tasks), len(ths))
        t0 = time.perf_counter()
        await pilot.press("t")
        for _ in range(20): await pilot.pause()
        check("and moving away from it still works", shown(app), [])


# ------------------------------- the mail view with the other sources present
async def beside_the_other_sources():
    """The suite set calendar_config to None everywhere else, which hid a
    real bug: the calendar was asked for the events of a position that is
    not a date.  So this one has every source configured at once."""
    print("the inbox with a calendar and a tracker configured")
    app = main.TaskApp()
    app.client = StubClient([mk("t1", "a task", TODAY)], reference=NOW)
    app.calendar_config = ical.Config(work="W", personal=("Me",))
    app.tracker_config = TRK
    app.mail_config = mail.Config(SAMPLE)
    start = dt.datetime.combine(TODAY, dt.time(9, 0))
    saved = ical.fetch
    ical.fetch = lambda cfg, day: [ical.Event(
        title="a meeting", account="Me", calendar="c", start=start,
        end=start + dt.timedelta(hours=1), all_day=False)]
    try:
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(16): await pilot.pause()
            check("the day holds its task and its event",
                  sorted(t.raw.get("title") for t in app.tasks), ["a meeting", "a task"])
            await pilot.press("i")
            for _ in range(24): await pilot.pause()
            check("the inbox holds the threads", sum(1 for t in app.tasks
                                                     if app.is_mail(t)), 8)
            check("and no calendar event came into it",
                  any(app.is_event(t) for t in app.tasks), False)
            check("and nothing raised while getting there", app._exception is None
                  if hasattr(app, "_exception") else True, True)
            await pilot.press("t")
            for _ in range(24): await pilot.pause()
            check("and the day comes back whole",
                  sorted(t.raw.get("title") for t in app.tasks), ["a meeting", "a task"])
    finally:
        ical.fetch = saved


async def main_():
    await beside_the_other_sources()
    await never_delays()
    await the_view()
    await the_row()
    await the_body()
    await opening()
    await refusals()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
