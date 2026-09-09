"""Promoting a mail thread to a task on today.

Synthetic mail only: a fresh copy of the sample maildir per board, so a run
that marks messages read cannot reach the next one or the sample itself.
No subject, sender or body is printed -- names of checks and counts only.
"""
import asyncio, datetime as dt, hashlib, mailbox, os, shutil, sys, tempfile, threading
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
SAMPLE = _os.path.join(_TESTS, "fixtures", "sample_mail")
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
TRK = tracker.Config(base_url="https://track.corp.invalid", token="t", assignee="me",
                     projects=("ABC",), states=("In progress",))
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")

def copy_sample():
    path = os.path.join(tempfile.mkdtemp(prefix="promote."), "mail")
    shutil.copytree(SAMPLE, path)
    return path

def build(messages, folder=None):
    """A throwaway maildir of invented messages."""
    path = os.path.join(tempfile.mkdtemp(prefix="promote."), "mail")
    box = mailbox.Maildir(path, create=True)
    target = box.add_folder(folder) if folder else box
    for i, (subject, body, headers) in enumerate(messages):
        m = EmailMessage()
        m["From"] = headers.get("From", "sender@example.invalid")
        m["Subject"] = subject
        m["Date"] = (NOW - dt.timedelta(minutes=(len(messages) - i) * 5)).strftime(
            "%a, %d %b %Y %H:%M:%S %z")
        m["Message-ID"] = headers.get("Message-ID", f"<b{i}@example.invalid>")
        if headers.get("In-Reply-To"): m["In-Reply-To"] = headers["In-Reply-To"]
        m.set_content(body)
        target.add(mailbox.MaildirMessage(m))
    target.flush()
    return path

def census(root):
    out = {}
    for base, _dirs, names in os.walk(root):
        for name in names:
            full = os.path.join(base, name)
            with open(full, "rb") as fh:
                out[os.path.relpath(full, root)] = hashlib.sha256(fh.read()).hexdigest()
    return out

UNSET = object()

@asynccontextmanager
async def board(mail_path=UNSET, tasks=None, tracker_cfg=None, folders=(),
                to_inbox=True):
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [mk("t1", "a task", TODAY)],
                            reference=NOW)
    app.calendar_config = None
    app.tracker_config = tracker_cfg
    path = copy_sample() if mail_path is UNSET else mail_path
    app.mail_config = None if path is None else mail.Config(path, tuple(folders))
    opened = []
    app.open_url = lambda url: opened.append(url)
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        if to_inbox:
            await pilot.press("i")
            for _ in range(20): await pilot.pause()
        yield app, pilot, path, opened

async def select(app, pilot, pred):
    row = next(i for i, t in enumerate(app.tasks) if pred(t))
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()
    return app.tasks[row]

async def settle(pilot, n=24):
    for _ in range(n): await pilot.pause()

async def to_today(app, pilot):
    """Go to today, which is where a promoted task lands.

    Mail is shown in the inbox and the task is dated today, so the inbox
    filters the new task straight back out -- it has a date.  Anything that
    looks at the created task on screen has to go and look at today.
    """
    await pilot.press("t")
    await settle(pilot, 26)

def status(app): return str(app.query_one("#status").render())
def mail_row(app): return next(t for t in app.tasks if app.is_mail(t))
def made(app):
    return [t for t in app.client.store.values() if t.id.startswith("T-new-")]

# --------------------------------------------------------- a thread becomes a task
async def becomes_a_task():
    print("a thread becomes a task on today")
    async with board(tasks=[mk("i1", "an inbox task"),
                            mk("d1", "a task", TODAY)]) as (app, pilot, path, _o):
        row = mail_row(app)
        subject, count = row.title, row.raw[main.MAIL_COUNT]
        await pilot.press("f")
        await settle(pilot, 30)
        new = made(app)
        check("one task was created", len(new), 1)
        check("titled from what the thread is about", new[0].title, subject)
        check("dated today", new[0].local_start(TZ).date(), TODAY)
        check("all day, not at a time", new[0].raw.get("useTime"), False)
        check("not deferred", bool(new[0].raw.get("deferred")), False)
        check("the store was asked to create exactly once",
              app.client.count("create_task"), 1)

    print("its order is past everything the day holds")
    async with board(tasks=[mk("i1", "an inbox task"),
                            mk("d1", "a task", TODAY),
                            mk("d2", "another", TODAY)]) as (app, pilot, path, _o):
        for i, t in enumerate(app.client.store.values()):
            t.raw["scheduleOrder"] = 5000 + i * 10
        held = max(t.schedule_order for t in app.client.store.values()
                   if t.local_start(TZ) and t.local_start(TZ).date() == TODAY)
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        new = made(app)
        check("the day was asked what it holds",
              app.client.count("tasks_for_day"), 1)
        check("and the order is past all of it",
              bool(new) and new[0].schedule_order > held,
              True)

    print("promoting from a day view works the same")
    async with board(tasks=[mk("i1", "an inbox task")], to_inbox=True) as (
            app, pilot, path, _o):
        row = await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        check("one task on today", len(made(app)), 1)
        check("even though the promotion was made from the inbox",
              made(app)[0].local_start(TZ).date(), TODAY)

# ------------------------------------------------------------ shown before the store
async def shown_at_once():
    print("the row is on screen before the store has answered")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        app.client.gate = threading.Event()
        row = await select(app, pilot, app.is_mail)
        subject = row.title
        await pilot.press("f")
        await settle(pilot, 12)
        placeholders = [t for t in app._base if t.id.startswith("tmp:")]
        check("a placeholder is in the base", len(placeholders), 1)
        check("carrying the title", placeholders[0].title, subject)
        check("and the store has not answered yet",
              app.client.store.get("T-new-1"), None)
        app.client.gate.set()
        await settle(pilot, 30)
        check("once it has, the placeholder is gone",
              [t for t in app._base if t.id.startswith("tmp:")], [])
        check("and the real task is there", len(made(app)), 1)

    print("a refusal from the store is reported")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        app.client.fail["create_task"] = SingularityError("the store said no")
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        check("nothing was created", made(app), [])
        check("no orphan row is left on screen",
              [t for t in app._base if t.id.startswith("tmp:")], [])
        check("and the board says so",
              "failed" in status(app).lower() and "said no" in status(app), True)

# -------------------------------------------------------------- what it carries
async def what_it_carries():
    print("the note carries the message and its identity")
    path = build([("Build #4812 failed",
                   "the job failed\nsee https://ci.corp.invalid/job/4812/console\n",
                   {"Message-ID": "<build-4812@ci.corp.invalid>"})])
    async with board(mail_path=path, tasks=[mk("i1", "an inbox task")]) as (
            app, pilot, _p, opened):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        note = made(app)[0].note_text
        check("the body is in the note", "the job failed" in note, True)
        check("the address the message carried is in the note",
              "https://ci.corp.invalid/job/4812/console" in note, True)
        check("and the identity of the message it came from",
              "<build-4812@ci.corp.invalid>" in note, True)
        check("written as a note the store will take",
              made(app)[0].raw["note"].startswith('[{"insert"'), True)

        # and o reaches the thing through the note
        await to_today(app, pilot)
        await select(app, pilot, lambda t: t.id.startswith("T-new-"))
        await pilot.press("o")
        await settle(pilot, 20)
        check("o opens what the message pointed at, found in the note",
              opened, ["https://ci.corp.invalid/job/4812/console"])

    print("a message that said nothing")
    path = build([("a subject and no more", "", {"Message-ID": "<empty@x.invalid>"})])
    async with board(mail_path=path, tasks=[mk("i1", "an inbox task")]) as (
            app, pilot, _p, _o):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        check("the task is still created", len(made(app)), 1)
        note = made(app)[0].note_text
        check("with the identity alone", note.strip(), "Message-ID: <empty@x.invalid>")

    print("the newest message is the one carried")
    path = build([
        ("Build #1 failed", "first https://ci.corp.invalid/1", {"Message-ID": "<m1@x.invalid>"}),
        ("Re: Build #1 failed", "third https://ci.corp.invalid/3",
         {"Message-ID": "<m3@x.invalid>", "In-Reply-To": "<m1@x.invalid>"}),
    ])
    async with board(mail_path=path, tasks=[mk("i1", "an inbox task")]) as (
            app, pilot, _p, opened):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        note = made(app)[0].note_text
        check("the newest message's body", ("third" in note, "first" in note), (True, False))
        check("and the newest message's identity",
              "<m3@x.invalid>" in note and "<m1@x.invalid>" not in note, True)

    print("a body written to look like markup")
    path = build([("[b]not bold[/b]", "a [dim]body[/dim] with [markup] in it",
                   {"Message-ID": "<markup@x.invalid>"})])
    async with board(mail_path=path, tasks=[mk("i1", "an inbox task")]) as (
            app, pilot, _p, _o):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        note = made(app)[0].note_text
        check("every character is in the note as sent",
              ("[dim]body[/dim]" in note, "[markup]" in note), (True, True))
        await to_today(app, pilot)
        await select(app, pilot, lambda t: t.id.startswith("T-new-"))
        await settle(pilot, 8)
        drawn = str(app.query_one("#detail").render())
        check("and is drawn as its own characters", "[dim]body[/dim]" in drawn, True)
        check("the rest of the board is as it was", app.mail_error, None)

    print("the note can be edited afterwards")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 30)
        await to_today(app, pilot)
        await select(app, pilot, lambda t: t.id.startswith("T-new-"))
        await pilot.press("n")
        await settle(pilot, 14)
        screen = app.screen
        check("the editor opened", type(screen).__name__, "NoteInput")
        holding = screen.query_one(main.NoteArea).text
        check("holding what was written",
              holding == made(app)[0].note_text and "Message-ID:" in holding, True)
        await pilot.press("escape")
        await settle(pilot, 14)

# --------------------------------------------------------------- out of the queue
async def out_of_the_queue():
    print("the thread leaves the queue")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        before = sum(1 for t in app.tasks if app.is_mail(t))
        row = await select(app, pilot, app.is_mail)
        gone, count = row.id, row.raw[main.MAIL_COUNT]
        await pilot.press("f")
        await settle(pilot, 40)
        check("its messages are marked read",
              len(mail.read(mail.Config(path))), 14 - count)
        after = sum(1 for t in app.tasks if app.is_mail(t))
        check("the row is gone from the inbox", (before - after, after), (1, before - 1))
        check("and it is that row that went",
              gone not in {t.id for t in app.tasks}, True)
        # It has a date, so the inbox is exactly where it does not belong.
        check("the task is not left in the inbox it was made from",
              any(t.id.startswith("T-new-") for t in app.tasks), False)
        await to_today(app, pilot)
        check("it is on today", [t.id for t in app.tasks
                                 if t.id.startswith("T-new-")], ["T-new-1"])

    print("a thread in a named folder is marked in that folder")
    path = build([("a report", "body https://reports.corp.invalid/1",
                   {"Message-ID": "<r1@x.invalid>"})], folder="Reports")
    async with board(mail_path=path, folders=("Reports",),
                     tasks=[mk("i1", "an inbox task")]) as (app, pilot, _p, _o):
        check("the thread was read from the folder",
              [t.raw[main.MAIL_MESSAGES][0].folder
               for t in app.tasks if app.is_mail(t)], ["Reports"])
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 40)
        check("and it is out of the queue",
              mail.read(mail.Config(path, ("Reports",))), [])

    print("a mailbox that cannot be written")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        row = await select(app, pilot, app.is_mail)
        for area in ("new", "cur"):
            os.chmod(os.path.join(path, area), 0o500)
        try:
            await pilot.press("f")
            await settle(pilot, 40)
            check("the task is still created", len(made(app)), 1)
            said = status(app)
            check("and the board says the message could not be marked",
                  "could not be marked" in said, True)
        finally:
            for area in ("new", "cur"):
                os.chmod(os.path.join(path, area), 0o700)
        check("nothing in the mailbox was marked",
              len(mail.read(mail.Config(path))), 14)

    print("nothing else about the mailbox changed")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        was = census(path)
        row = await select(app, pilot, app.is_mail)
        keys = {m.key for m in row.raw[main.MAIL_MESSAGES]}
        await pilot.press("f")
        await settle(pilot, 40)
        now = census(path)
        uniq = lambda rel: os.path.basename(rel).split(":")[0]
        was_by = {uniq(k): (k, v) for k, v in was.items()}
        now_by = {uniq(k): (k, v) for k, v in now.items()}
        check("no message was added or removed", set(was_by), set(now_by))
        check("no message's content differs",
              all(was_by[k][1] == now_by[k][1] for k in was_by), True)
        check("no message changed folder",
              all(os.path.dirname(os.path.dirname(was_by[k][0]))
                  == os.path.dirname(os.path.dirname(now_by[k][0])) for k in was_by),
              True)
        check("only the promoted thread's files were renamed",
              {k for k in was_by if was_by[k][0] != now_by[k][0]}, keys)

    print("nothing is remembered anywhere but the mailbox")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        home = os.path.expanduser("~")
        watched = [_REPO, os.getcwd()]
        before = {w: sorted(os.listdir(w)) for w in watched}
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 40)
        check("no file appeared beside the board",
              {w: sorted(os.listdir(w)) for w in watched}, before)

# ----------------------------------------------------------------------- undo
async def undoing():
    print("undoing a promotion returns the thread")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        before = sum(1 for t in app.tasks if app.is_mail(t))
        row = await select(app, pilot, app.is_mail)
        gone, count = row.id, row.raw[main.MAIL_COUNT]
        await pilot.press("f")
        await settle(pilot, 40)
        check("promoted", (len(made(app)), len(mail.read(mail.Config(path)))),
              (1, 14 - count))
        await pilot.press("u")
        await settle(pilot, 40)
        check("the task is gone", made(app), [])
        check("the store was asked to delete it", app.client.count("delete_task"), 1)
        check("the messages are unread again",
              len(mail.read(mail.Config(path))), 14)
        check("the row is back in the inbox",
              (sum(1 for t in app.tasks if app.is_mail(t)),
               gone in {t.id for t in app.tasks}),
              (before, True))
        check("and the board says what it reversed",
              "undid" in status(app).lower() and "promoting" in status(app).lower(),
              True)

    print("a message put back stays in the current area")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        row = await select(app, pilot, app.is_mail)
        keys = [m.key for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("f")
        await settle(pilot, 40)
        await pilot.press("u")
        await settle(pilot, 40)
        where = []
        for key in keys:
            for area in ("new", "cur"):
                for name in os.listdir(os.path.join(path, area)):
                    if name.split(":")[0] == key:
                        where.append((area, ":2,S" in name))
        check("each is in cur, unflagged", set(where), {("cur", False)})

    print("undo after the creation confirms reaches the real task")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 40)
        real = made(app)[0].id
        check("the task has its real id", real.startswith("T-new-"), True)
        await pilot.press("u")
        await settle(pilot, 40)
        check("and that is the id deleted",
              [a for c, a in app.client.calls if c == "delete_task"], [(real,)])

    print("undoing before the creation has confirmed")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        app.client.gate = threading.Event()
        row = await select(app, pilot, app.is_mail)
        count = row.raw[main.MAIL_COUNT]
        await pilot.press("f")
        await settle(pilot, 12)
        check("the creation is still in flight",
              [t.id for t in app._base if t.id.startswith("tmp:")] != [], True)
        await pilot.press("u")
        await settle(pilot, 12)
        check("the messages are already unread again",
              len(mail.read(mail.Config(path))), 14)
        app.client.gate.set()
        await settle(pilot, 60)
        check("the task the store made was deleted, by its real id",
              [a for c, a in app.client.calls if c == "delete_task"],
              [("T-new-1",)])
        check("and nothing is left on the account", made(app), [])

    print("undoing twice reaches further back, not round again")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 40)
        await pilot.press("u")
        await settle(pilot, 40)
        await pilot.press("u")
        await settle(pilot, 30)
        check("the deletion is not itself undone",
              app.client.count("delete_task"), 1)
        check("and nothing was created again", made(app), [])

# ------------------------------------------------------------------ refusals
async def refusals():
    print("the key acts on a mail thread alone")
    async with board(tasks=[mk("i1", "an inbox task")], tracker_cfg=None) as (
            app, pilot, path, _o):
        await select(app, pilot, lambda t: not app.is_mail(t))
        await pilot.press("f")
        await settle(pilot, 24)
        check("nothing was created on a task", made(app), [])
        check("and the board says what the key is for",
              "turns a mail thread into a task" in status(app), True)
        check("the mailbox is untouched", len(mail.read(mail.Config(path))), 14)

    print("on a calendar event")
    ev = ical.Event(title="a meeting", account="work", calendar="c",
                    start=dt.datetime.combine(TODAY, dt.time(14, 0), tzinfo=TZ),
                    end=dt.datetime.combine(TODAY, dt.time(15, 0), tzinfo=TZ),
                    all_day=False, location="", notes="")
    was_fetch = ical.fetch
    ical.fetch = lambda cfg, day: [ev]
    async with board(tasks=[mk("d1", "a task", TODAY)], to_inbox=False) as (
            app, pilot, path, _o):
        app.calendar_config = ical.Config(work="work", personal=())
        app.load_calendar()
        await settle(pilot, 20)
        await select(app, pilot, app.is_event)
        await pilot.press("f")
        await settle(pilot, 24)
        check("nothing was created on an event", made(app), [])
        check("and the board says what the key is for",
              "turns a mail thread into a task" in status(app), True)
    ical.fetch = was_fetch

    print("on a tracker issue")
    async with board(tasks=[mk("d1", "a task", TODAY)], tracker_cfg=TRK,
                     to_inbox=False) as (app, pilot, path, _o):
        app.tracker_issues = [tracker.Issue("ABC-1", "summary", "ABC",
                                            "In progress", "me",
                                            "https://track.corp.invalid")]
        app.tracker_error = None
        app.repaint()
        await settle(pilot, 16)
        await select(app, pilot, app.is_tracker)
        await pilot.press("f")
        await settle(pilot, 24)
        check("nothing was created on a tracker issue", made(app), [])
        check("and the board says what the key is for",
              "turns a mail thread into a task" in status(app), True)

    print("with no mailbox configured at all")
    async with board(mail_path=None, tasks=[mk("i1", "an inbox task")]) as (
            app, pilot, _p, _o):
        await select(app, pilot, lambda t: True)
        await pilot.press("f")
        await settle(pilot, 24)
        check("nothing was created", made(app), [])
        check("and the board says what the key is for",
              "turns a mail thread into a task" in status(app), True)

# ---------------------------------------------------------------- saying so
async def saying_so():
    print("the key is named where keys are named")
    async with board(tasks=[mk("i1", "an inbox task")]) as (app, pilot, path, _o):
        await pilot.press("question_mark")
        await settle(pilot, 14)
        text = main.Help.TEXT
        check("the help overlay names f", "\n  f  " in text, True)
        check("and says what it does",
              "turn the selected mail thread into a" in text, True)
        check("and that the row leaves the inbox", "leaves the inbox" in text, True)
        check("the overlay names no Cyrillic key",
              [c for c in text if "Ѐ" <= c <= "ӿ" and c not in "Зеленая"],
              [])
        await pilot.press("escape")
        await settle(pilot, 10)
        # By the binding's own first key, not by prefix: `full_stop` starts
        # with an f as well, and a check that catches it proves nothing.
        bound = [b for b in app.BINDINGS
                 if getattr(b, "key", "").split(",")[0] == "f"]
        check("the key bar carries it",
              [(b.description, b.show) for b in bound], [("To task", True)])

    print("the shipped wording no longer claims nothing is written")
    board_src = open(_REPO + "/main.py").read()
    mail_src = open(_REPO + "/mail.py").read()
    check("main.py does not say mail is read-only in the inbox",
          "Mail is read-only here" in board_src, False)
    check("mail.py does not say nothing here writes",
          "Nothing here writes" in mail_src, False)
    check("and it says what the one write is",
          "marking a message read" in mail_src, True)

async def main_():
    for part in (becomes_a_task, shown_at_once, what_it_carries,
                 out_of_the_queue, undoing, refusals, saying_so):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    sys.exit(0 if all(ok) else 1)

asyncio.run(main_())
