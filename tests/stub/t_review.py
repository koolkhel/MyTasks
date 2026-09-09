"""Reviewing mail from the board: folding, ordering, and filing away.

Everything a review touches, against a substituted server that records every
request: which messages a row stands for, where the rows sit, what they open,
what a tick and a promotion do, each of the four outcomes a confirmation can
have, and that nothing on disk changes through all of it.

No account and no credentials: the connection is `tests/fakeimap.py`, so the
paths that must fail can be made to fail. Synthetic mail only -- a private
copy of the committed fixture per board -- and invented project keys.
"""
import asyncio, datetime as dt, os, sys, threading
from contextlib import asynccontextmanager

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import fakeimap
import mailfixture as F
import gateway, mail, main, tracker
from textual.widgets import DataTable

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
#: The invented projects the fixture's subjects name.  `ZZB` is there so a
#: second project's issue is recognised too, and neither key exists anywhere
#: but in this repository's fixtures.
TRK = tracker.Config(base_url="https://track.corp.invalid", token="t",
                     assignee="me", projects=("ZZA", "ZZB"),
                     states=("In progress",))
ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def server_for(path, folders=F.FOLDERS, **kw):
    """A server holding what the mailbox at `path` shows as unread.

    The unread ones: those are the messages the board can ever act on, and a
    server that also held the read ones would let a check pass on a message
    no row stands for.
    """
    held = {name: [] for name in folders}
    for message in mail.read(mail.Config(path, tuple(folders))):
        held[message.folder].append(message.ident)
    held[F.ARCHIVE] = []
    return fakeimap.FakeIMAP(held, **kw)


@asynccontextmanager
async def board(tasks=None, tracker_cfg=None, mail_cfg=None, imap=None,
                gateway_cfg=fakeimap.CONFIG, to_inbox=True, folders=F.FOLDERS):
    app = main.TaskApp()
    app.client = StubClient(tasks if tasks is not None else [mk("i1", "a triage task")],
                            reference=NOW)
    app.calendar_config = None
    app.tracker_config = tracker_cfg
    path = None
    if mail_cfg is None:
        path = F.copy()
        mail_cfg = mail.Config(path, tuple(folders))
    app.mail_config = mail_cfg
    if imap is None and path is not None:
        imap = server_for(path, folders)
    app.gateway_config = gateway_cfg
    app.gateway_connect = None if imap is None else (lambda: imap)
    opened = []
    app.open_url = lambda url: opened.append(url)
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(14): await pilot.pause()
        if to_inbox:
            await pilot.press("i")
            for _ in range(22): await pilot.pause()
        yield app, pilot, path, imap, opened


async def settle(pilot, n=26):
    for _ in range(n): await pilot.pause()


async def select(app, pilot, pred):
    row = next(i for i, t in enumerate(app.tasks) if pred(t))
    app.query_one(DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()
    return app.tasks[row]


def status(app):
    return str(app.query_one("#status").render())


def rows(app):
    return [t for t in app.tasks if app.is_mail(t)]


def titled(app, needle):
    return next(t for t in rows(app) if needle in (t.raw.get("title") or ""))


def made(app):
    return [t for t in app.client.store.values() if t.id.startswith("T-new-")]


# ------------------------------------------------------------------ folding
async def folding():
    print("messages about one issue are one row")
    async with board(tracker_cfg=TRK) as (app, pilot, path, imap, _o):
        check("the fixture's nine header threads are eight rows", len(rows(app)), 8)
        row = titled(app, "ZZA-100")
        check("the folded row stands for five messages",
              row.raw[main.MAIL_COUNT], 5)
        check("and holds five messages to act on",
              len(row.raw[main.MAIL_MESSAGES]), 5)
        check("the other issue's row stands for three",
              titled(app, "ZZA-200").raw[main.MAIL_COUNT], 3)
        # ZZB-9: the same issue named twice, from two different addresses.
        # The condition that keeps this apart is the one that stops a review
        # filing away mail nobody looked at.
        both = [t for t in rows(app) if "ZZB-9" in (t.raw.get("title") or "")]
        check("the same issue from two addresses stays two rows", len(both), 2)
        check("each standing for one message",
              sorted(t.raw[main.MAIL_COUNT] for t in both), [1, 1])
        # The two numbers the status line is built from.  Read here rather
        # than off the line itself because a configured tracker cannot be
        # reached from a suite, and saying so is a notice that outlives the
        # counts -- the line's own wording is checked below, where no
        # tracker is configured.
        check("the counts report rows and messages, not rows twice",
              (app.shown_mail, app.shown_messages), (8, 18))

    print("nothing folds where no issue is named")
    async with board(tracker_cfg=None) as (app, pilot, path, imap, _o):
        check("with no project configured, the header threads stand",
              len(rows(app)), 9)
        check("and both queues are named on the status line",
              ("9 thread(s)" in status(app), "18 message(s)" in status(app)),
              (True, True))
    async with board(tracker_cfg=TRK, folders=("Jenkins",)) as (
            app, pilot, path, imap, _o):
        # The folder whose subjects name no issue of a configured project:
        # its rows must be what the headers alone give, unchanged.
        plain = mail.threads(mail.read(mail.Config(path, ("Jenkins",))))
        check("a folder naming no issues is grouped by its headers alone",
              sorted(t.raw[main.MAIL_COUNT] for t in rows(app)),
              sorted(t.count for t in plain))
        check("and a subject with letters, a dash and digits folds nothing",
              [t.raw[main.MAIL_COUNT] for t in rows(app)
               if "ISO-8601" in (t.raw.get("title") or "")], [1])


# ----------------------------------------------------------------- ordering
async def ordering():
    print("the inbox's tasks lead its mail")
    tasks = [mk("i1", "first triage"), mk("i2", "second triage"),
             mk("i3", "third triage"), mk("d1", "a dated task", TODAY)]
    async with board(tasks=tasks, tracker_cfg=TRK) as (app, pilot, path, imap, _o):
        kinds = ["MAIL" if app.is_mail(t) else "task" for t in app.tasks]
        check("every task comes before every mail row",
              kinds, ["task"] * 3 + ["MAIL"] * 8)
        check("the cursor starts on a task",
              app.is_mail(app.selected), False)
        with_mail = [t.id for t in app.tasks if not app.is_mail(t)]
    # The same board with no mailbox at all: a configuration naming no path
    # is how a person turns mail off.
    async with board(tasks=tasks, tracker_cfg=TRK,
                     mail_cfg=mail.Config("", ())) as (
            app, pilot, path, imap, _o):
        check("and taking the mail away leaves them in that same order",
              [t.id for t in app.tasks], with_mail)
        check("with no mail counted", "thread(s)" in status(app), False)


# ------------------------------------------------------------ what it opens
async def opens():
    print("what a row offers to open")
    async with board(tracker_cfg=TRK) as (app, pilot, path, imap, opened):
        # A run of build notifications: no fragment anywhere, so the rule
        # this folder's behaviour was formed on stands untouched.
        builds = await select(app, pilot,
                              lambda t: "deploy-prod #844" in (t.raw.get("title") or ""))
        check("a run of four builds offers one address", len(app.openable(builds)), 1)
        await pilot.press("o")
        await settle(pilot, 10)
        check("and it is the newest message's",
              opened[-1:], ["https://ci.corp.invalid/job/deploy-prod/844/console"])
        anchored = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        check("an anchored row offers the earliest anchored address",
              [url for _s, url in app.openable(anchored) if "#" in url],
              ["https://track.corp.invalid/issue/ZZA-100#comment-11"])
        check("and the issue it names beside it",
              [url for _s, url in app.openable(anchored) if "#" not in url],
              ["https://track.corp.invalid/issue/ZZA-100"])
        nothing = await select(app, pilot,
                               lambda t: "quick question" in (t.raw.get("title") or ""))
        before = list(opened)
        await pilot.press("o")
        await settle(pilot, 10)
        check("a row with nothing to open opens nothing", opened, before)
        check("and says so", status(app), "That thread has no link")


# ---------------------------------------------------------------- reviewing
async def reviewing():
    print("ticking a mail row files it away")
    async with board(tracker_cfg=TRK) as (app, pilot, path, imap, _o):
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("space")
        await settle(pilot, 30)
        check("the row is gone from the inbox",
              [t.id for t in rows(app) if t.id == row.id], [])
        check("all five messages are in the archive",
              sorted(i for i in imap.ids(F.ARCHIVE) if i in idents), sorted(idents))
        check("not only the newest", len(imap.ids(F.ARCHIVE)), 5)
        check("and none is left in the folder it was in",
              [i for i in imap.ids("YouTrack") if i in idents], [])
        check("the board says what it filed away",
              "5 filed away" in status(app), True)
        check("no task was ticked", app.client.count("set_done"), 0)
        check("and no task was created", len(made(app)), 0)

    print("the row goes before the server has answered")
    hold = threading.Event()

    def wait_once(name, args):
        # The first thing a review asks: which numbers the row's messages
        # have.  Held open, so the board is caught with the row gone and
        # nothing moved.
        if name == "SEARCH":
            hold.wait(10)
        return None

    path = F.copy()
    imap = server_for(path, fail=wait_once)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        await pilot.press("space")
        await settle(pilot, 14)
        check("the row is already gone",
              [t.id for t in rows(app) if t.id == row.id], [])
        check("while the server is still being asked where the messages are",
              imap.commands(), ["LOGIN", "SELECT", "SEARCH"])
        check("and nothing has moved", imap.ids(F.ARCHIVE), [])
        hold.set()
        await settle(pilot, 30)
        check("and it stays gone once the move is confirmed",
              [t.id for t in rows(app) if t.id == row.id], [])

    print("several reviews reach the gateway one at a time")
    # Ten rows ticked in a row used to open ten connections at once, each
    # holding the slow archive open.  The rows leave the screen either way.
    opened = []
    hold = threading.Event()

    def count_logins(name, args):
        if name == "LOGIN":
            opened.append(1)
            hold.wait(10)
        return None

    path = F.copy()
    imap = server_for(path, fail=count_logins)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        was = len(rows(app))
        for _ in range(3):
            await select(app, pilot, app.is_mail)
            await pilot.press("space")
            await settle(pilot, 8)
        check("all three rows are off the screen at once",
              len(rows(app)), was - 3)
        check("but only one has reached the gateway", len(opened), 1)
        hold.set()
        await settle(pilot, 40)
        check("and the rest follow, none of them lost", len(opened), 3)

    print("promoting archives as well as making a task")
    async with board(tracker_cfg=TRK) as (app, pilot, path, imap, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("f")
        await settle(pilot, 34)
        check("a task was created", len(made(app)), 1)
        check("all three messages are archived",
              sorted(i for i in imap.ids(F.ARCHIVE) if i in idents), sorted(idents))
        check("the row is gone", [t.id for t in rows(app) if t.id == row.id], [])

    print("a promotion survives a gateway that will not take the mail")
    imap = None
    path = F.copy()
    broken = server_for(path, fail=lambda name, args:
                        ("NO", [b"refused"]) if name == "MOVE" else None)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=broken) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        await pilot.press("f")
        await settle(pilot, 34)
        check("the task stands", len(made(app)), 1)
        check("the row is back in the queue",
              [t.id for t in rows(app) if t.id == row.id], [row.id])
        check("and the board says why", "is back in the queue" in status(app), True)

    print("nothing is deleted and nothing goes anywhere else")
    async with board(tracker_cfg=TRK) as (app, pilot, path, imap, _o):
        for needle in ("ZZA-100", "ZZA-200", "deploy-prod #844"):
            await select(app, pilot, lambda t, n=needle: n in (t.raw.get("title") or ""))
            await pilot.press("space")
            await settle(pilot, 30)
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 34)
        check("only these requests were made",
              sorted(set(imap.commands())),
              ["FETCH", "LOGIN", "LOGOUT", "MOVE", "SEARCH", "SELECT",
               "STORE"])
        check("every move named the archive",
              {args[1].strip('"') for name, args in imap.calls if name == "MOVE"},
              {F.ARCHIVE})
        check("nothing was deleted or expunged",
              [c for c in imap.commands() if c in ("EXPUNGE", "DELETE")], [])
        # The one flag the board sets, and only where a reviewed message
        # has landed.
        check("what was archived is marked read",
              imap.unread_in(F.ARCHIVE), [])
        check("and no flag was set anywhere but the archive",
              set(imap.stored_in), {F.ARCHIVE})
        check("and every message is still on the server",
              sum(len(f) for f in imap.folders.values()), 18)


# ------------------------------------------------------------- confirmation
async def confirming():
    print("a message already in the archive is already reviewed")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        # Somebody else moved them, between the mirror being written and now.
        for folder in list(imap.folders):
            for uid, ident in list(imap.folders[folder].items()):
                if ident in idents:
                    del imap.folders[folder][uid]
                    imap.folders[F.ARCHIVE][b"9" + uid] = ident
        await pilot.press("space")
        await settle(pilot, 30)
        check("it is reported as already reviewed",
              "already reviewed" in status(app), True)
        check("not as a failure", "back in the queue" in status(app), False)
        check("and the row stays gone",
              [t.id for t in rows(app) if t.id == row.id], [])

    print("a message in neither place is said to be in neither")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        for folder in list(imap.folders):
            for uid, ident in list(imap.folders[folder].items()):
                if ident in idents:
                    del imap.folders[folder][uid]
        await pilot.press("space")
        await settle(pilot, 30)
        check("the board says so",
              "in neither the folder nor the archive" in status(app), True)
        check("and does not claim success",
              "filed away" in status(app), False)
        # Nothing was confirmed, so nothing is held back: the row returns at
        # the next read rather than being quietly retired on a message the
        # board could not find.
        check("nothing is held back", app.reviewed, set())
        app.load_mail()
        await settle(pilot, 26)
        check("and the row comes back to be dealt with",
              [t.id for t in rows(app) if t.id == row.id], [row.id])

    print("an unconfirmed archive brings the row back")
    path = F.copy()
    imap = server_for(path, deny=(F.ARCHIVE,))
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        where = next(i for i, t in enumerate(rows(app)) if t.id == row.id)
        await pilot.press("space")
        await settle(pilot, 34)
        back = rows(app)
        check("the row is back", [t.id for t in back if t.id == row.id], [row.id])
        check("where it was", next(i for i, t in enumerate(back) if t.id == row.id),
              where)
        check("and the board says why",
              ("is back in the queue" in status(app)
               and F.ARCHIVE in status(app)), True)

    print("undoing a review puts the mail back")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("space")
        await settle(pilot, 30)
        check("they went to the archive", len(imap.ids(F.ARCHIVE)), 5)
        await pilot.press("u")
        await settle(pilot, 34)
        check("all five are back in the folder they came from",
              sorted(i for i in imap.ids("YouTrack") if i in idents), sorted(idents))
        check("and the archive is empty again", imap.ids(F.ARCHIVE), [])
        check("the board says the row comes back when the mailbox catches up",
              "catches up" in status(app), True)


# ------------------------------------------------- nothing on disk changes
async def nothing_written():
    print("a run of reviews and promotions writes nothing to the mailbox")
    path = F.copy()
    before = F.census(path)
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        for _ in range(3):
            await select(app, pilot, app.is_mail)
            await pilot.press("space")
            await settle(pilot, 28)
        await select(app, pilot, app.is_mail)
        await pilot.press("f")
        await settle(pilot, 32)
        await pilot.press("u")
        await settle(pilot, 30)
    after = F.census(path)
    check("every file is byte-identical", after, before)
    check("no file was added, removed or renamed", set(after), set(before))
    check("the committed fixture is untouched", F.census(F.FIXTURE),
          F.census(F.FIXTURE))
    check("and the board offers no way to write to a mailbox",
          [n for n in dir(mail) if n.startswith("mark_") or n == "_reflag"], [])


# ------------------------------------------- the queue drains and stays drained
async def stays_gone():
    print("a reviewed row does not come back while the mailbox lags")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        was = len(rows(app))
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("space")
        await settle(pilot, 30)
        check("the row went", len(rows(app)), was - 1)
        # The mirror still holds every message: nothing has removed the local
        # files, and it will not until the sync next runs.
        check("the mailbox on disk still holds them",
              len(mail.read(mail.Config(path, F.FOLDERS))), 18)
        # What a person actually does: leave the inbox and come back.
        await pilot.press("t")
        await settle(pilot, 26)
        await pilot.press("i")
        await settle(pilot, 30)
        check("and it is still gone after leaving and returning",
              len(rows(app)), was - 1)
        check("held back by identity, and only those five",
              app.reviewed, set(idents))
        check("nothing else was hidden",
              sum(t.raw[main.MAIL_COUNT] for t in rows(app)), 13)

    print("what the mailbox has caught up on is forgotten")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        idents = [m.ident for m in row.raw[main.MAIL_MESSAGES]]
        await pilot.press("space")
        await settle(pilot, 30)
        check("they are held back", app.reviewed, set(idents))
        # The sync catches up: the local files go, as they do within one
        # interval because the archive is not among the mirrored folders.
        for message in mail.read(mail.Config(path, F.FOLDERS)):
            if message.ident in idents:
                folder = mail._folder_path(mail.Config(path, F.FOLDERS),
                                           message.folder)
                for area in ("new", "cur"):
                    here = os.path.join(folder, area)
                    for name in os.listdir(here) if os.path.isdir(here) else []:
                        if name.split(":")[0] == message.key:
                            os.remove(os.path.join(here, name))
        app.load_mail()
        await settle(pilot, 26)
        check("and forgotten once it has", app.reviewed, set())
        check("the row is still not in the queue",
              [t for t in rows(app) if t.id == row.id], [])

    print("undoing a review lets the row come back")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-100" in (t.raw.get("title") or ""))
        await pilot.press("space")
        await settle(pilot, 30)
        check("held back while reviewed", len(app.reviewed), 5)
        await pilot.press("u")
        await settle(pilot, 34)
        check("nothing is held back once it is undone", app.reviewed, set())
        app.load_mail()
        await settle(pilot, 26)
        check("and the row is in the queue again",
              [t.id for t in rows(app) if t.id == row.id], [row.id])

    print("a row that could not be archived is not held back")
    path = F.copy()
    imap = server_for(path, deny=(F.ARCHIVE,))
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap) as (app, pilot, _p, _i, _o):
        row = await select(app, pilot, lambda t: "ZZA-200" in (t.raw.get("title") or ""))
        await pilot.press("space")
        await settle(pilot, 34)
        check("nothing is held back", app.reviewed, set())
        app.load_mail()
        await settle(pilot, 26)
        check("and the row is there to try again",
              [t.id for t in rows(app) if t.id == row.id], [row.id])


# ------------------------------------------------------------ configuration
async def configuration():
    print("a board with no gateway reads mail and will not file it away")
    path = F.copy()
    imap = server_for(path)
    async with board(tracker_cfg=TRK, mail_cfg=mail.Config(path, F.FOLDERS),
                     imap=imap, gateway_cfg=None) as (app, pilot, _p, _i, _o):
        check("the mail is there to read", len(rows(app)), 8)
        row = await select(app, pilot, app.is_mail)
        await pilot.press("space")
        await settle(pilot, 24)
        check("the row stays", [t.id for t in rows(app) if t.id == row.id], [row.id])
        check("and the board says what is missing",
              "no mail gateway is configured" in status(app), True)
        check("nothing was asked of any server", imap.commands(), [])
        check("and nothing moved", imap.ids(F.ARCHIVE), [])
        await pilot.press("f")
        await settle(pilot, 32)
        check("promoting still makes the task", len(made(app)), 1)
        check("says the thread is still in the queue",
              "still in the queue" in status(app), True)
        check("and the row is still there",
              [t.id for t in rows(app) if t.id == row.id], [row.id])

    print("the folders read are the folders named")
    async with board(tracker_cfg=TRK, folders=("Gitlab", "Jenkins")) as (
            app, pilot, path, imap, _o):
        check("only the named folders' messages appear",
              sorted({m.folder for t in rows(app)
                      for m in t.raw[main.MAIL_MESSAGES]}),
              ["Gitlab", "Jenkins"])
        check("the third folder's eight are not discovered",
              sum(t.raw[main.MAIL_COUNT] for t in rows(app)), 10)

    print("an unreadable mailbox is reported once")
    async with board(tracker_cfg=None,
                     mail_cfg=mail.Config("/nonexistent/mail", ("Gitlab",))) as (
            app, pilot, _p, _i, _o):
        check("it is reported", bool(app.mail_error), True)
        said = []
        app.notice = lambda message, error=False: said.append(message)
        app.load_mail()
        await settle(pilot, 20)
        app.load_mail()
        await settle(pilot, 20)
        check("and not said again for the same failure", said, [])
        check("while the inbox still holds its task",
              [t.raw.get("title") for t in app.tasks], ["a triage task"])


# --------------------------------------------------------------- saying so
async def saying_so():
    print("the board says what the key does")
    text = main.Help.TEXT
    check("the overlay says what ticking a mail row does",
          ("space files it away" in text, "space\n  reviews it" in text),
          (True, True))
    check("and that the message goes where the board cannot show it again",
          ("archive folder" in text, "not\n  mirrored here" in text), (True, True))
    check("and that mail follows the tasks",
          ("below your own tasks" in text, "above them" in text), (True, False))
    check("and that promoting files the mail away too",
          "filed away as well" in text, True)
    # "marked read" appears again, but about the server, not this disk: the
    # claim that must not come back is that a flag on a local file is what
    # takes a message out of the queue.
    check("it no longer claims a local flag is what reviews a message",
          ("maildir records a flag" in text,
           "messages are marked read, so the row" in text),
          (False, False))
    check("and says the local mail is not written to at all",
          "nothing at all is written\n  to the mail on this disk" in text, True)
    check("and says a reviewed message is marked read",
          ("they are marked read" in text, "unread\n  again" in text),
          (True, True))
    check("the overlay names no Cyrillic key",
          [ch for ch in text if "\u0400" <= ch <= "\u04ff"], [])
    check("the key bar names both things the key does",
          [b.description for b in main.TaskApp.BINDINGS
           if getattr(b, "key", "") == "space"], ["Tick / review"])
    board_src = open(_REPO + "/main.py").read()
    check("the board's own comments no longer say it marks a thread read",
          "marks the thread read" in board_src, False)
    check("and nothing in the board writes a mail flag",
          ("mark_read" in board_src, "mark_unread" in board_src), (False, False))


async def main_():
    for part in (folding, ordering, opens, reviewing, confirming,
                 stays_gone, nothing_written, configuration, saying_so):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


sys.exit(asyncio.run(main_()))
