"""One real message, and one real row, moved to the archive and moved back.

The only suite here that touches a real account. It exists because every
other check about reviewing is against a substituted account, and a
substituted account agrees with whatever this code believes: that the service
takes a batched move, that a search finds a message by its identity in one
request, that a folder lets go when messages leave it. Those are beliefs
about a server, and only the server can settle them.

What it does, and no more: takes one unread message from a configured folder,
moves it to the archive, confirms both sides, moves it back and confirms
that. Then the same for one folded row of several messages, timing both and
counting the requests each costs. Nothing is deleted, nothing goes anywhere
but the archive and back, and the restore runs even when a check fails.

It prints counts and durations. No subject, sender, address, identity or
folder name is printed, here or in a failure message: this is a real mailbox.

Note for whoever runs it: a message moved out and back reaches the local
mirror as a removal and then as a new arrival, so it may vanish from the
folder for up to one sync interval and come back. That is the same thing an
ordinary review does, and it is why undoing a review says the row returns
when the mailbox next catches up.
"""
import asyncio
import builtins
import functools
import os
import re
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import gateway
import journal
import mail
import singularity
import tracker

#: The real configuration, captured before the harness is imported: it
#: withholds the mailbox, the account and the log from every board built
#: under it, which is right for every other suite and is exactly what the
#: last check here has to undo.  Captured rather than re-read, so no suite
#: reimplements how the board finds its own settings.
REAL_MAILBOX = mail.load_config
REAL_GATEWAY = gateway.load_config
REAL_LOG = journal.PATH

from harness import StubClient, mk, TZ          # noqa: E402
import main                                     # noqa: E402
from textual.widgets import DataTable, Static   # noqa: E402

#: Every line flushed as it is written.  This suite is minutes long against
#: a real server, and a buffered run looks identical to a hung one -- which
#: it did, the first time it was run.
print = functools.partial(builtins.print, flush=True)

#: An address that refuses, for the half that needs a request to fail for
#: real rather than by a raised exception of the suite's own.
DEAD = "https://127.0.0.1:1/EWS/Exchange.asmx"

ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def fold_for(config):
    """The board's own folding rule, built from the configured projects."""
    if config is None:
        return None

    def fold(message):
        keys = config.keys_in(message.text)
        urls = singularity.urls_in(message.text)
        return (keys[0], urls[0]) if keys and urls else None

    return fold


class Counting:
    """A real account, with every request it is asked for recorded.

    Names only.  An argument would carry a folder name, and this file prints
    what it records.
    """

    def __init__(self, config):
        started = time.monotonic()
        self.real = gateway.Mailbox(config, gateway.password(config))
        self.opened = time.monotonic() - started
        self.seq = []

    def folders(self):
        self.seq.append("FOLDERS")
        return self.real.folders()

    def find(self, folder, idents):
        self.seq.append("SEARCH")
        return self.real.find(folder, idents)

    def move(self, items, target):
        self.seq.append("MOVE")
        return self.real.move(items, target)

    def mark(self, items, seen):
        self.seq.append("FLAG")
        return self.real.mark(items, seen)


class Dying(Counting):
    """A real account whose next request goes nowhere, on cue.

    The board crashed on this account when the line dropped between the move
    and the confirmation that followed it.  That was a stateful conversation:
    one connection carried a whole review, and losing it lost the review.
    This one is not -- every request stands alone over HTTP, and a connection
    closed between two of them costs nothing but a reconnection.  So the
    failure worth reproducing is no longer a cut line but a request that
    cannot be made, and the way to produce one honestly is to send it
    somewhere that refuses rather than to raise something here and call it a
    network.
    """

    def __init__(self, config, cut_when):
        super().__init__(config)
        self.cut_when = cut_when
        self.cut = False

    def _cutting(self, name):
        """Whether this request is the one that should go nowhere."""
        if self.cut or not self.cut_when(name, self.seq):
            return False
        self.cut = True
        return True

    def _through_nowhere(self, call):
        """Make one request, with the address pointed somewhere that refuses.

        Put back in a `finally`, and that is the whole of why this method
        exists.  The library keeps one protocol object per address and
        credential and hands it to every account built afterwards, so an
        address left pointing at nothing outlives this object: the first
        version of this redirected and never put it back, and the restore
        that exists to return somebody's mail to its folder failed with it.
        A real message sat in the archive until it was found by hand.

        Through the configuration, too, rather than the protocol: the
        property on the protocol has no setter, and assigning to it raised
        an AttributeError inside the request -- which `_talk` rightly does
        not catch, so the board wrote a crash file and this suite reported a
        fault of its own making as a fault of the board's.
        """
        protocol = self.real.account.protocol
        was = protocol.config.service_endpoint
        protocol.config.service_endpoint = DEAD
        try:
            return call()
        finally:
            protocol.config.service_endpoint = was

    def folders(self):
        self.seq.append("FOLDERS")
        if self._cutting("FOLDERS"):
            return self._through_nowhere(lambda: self.real.folders())
        return self.real.folders()

    def find(self, folder, idents):
        self.seq.append("SEARCH")
        if self._cutting("SEARCH"):
            return self._through_nowhere(
                lambda: self.real.find(folder, idents))
        return self.real.find(folder, idents)

    def move(self, items, target):
        self.seq.append("MOVE")
        if self._cutting("MOVE"):
            return self._through_nowhere(
                lambda: self.real.move(items, target))
        return self.real.move(items, target)

    def mark(self, items, seen):
        self.seq.append("FLAG")
        if self._cutting("FLAG"):
            return self._through_nowhere(lambda: self.real.mark(items, seen))
        return self.real.mark(items, seen)


async def main_():
    mailbox = REAL_MAILBOX()
    gw = REAL_GATEWAY()
    if mailbox is None or not mailbox.folders or gw is None:
        print("no mailbox or no account configured; nothing was run")
        return 2

    found = mail.read(mailbox)
    rows = mail.threads(found, fold=fold_for(tracker.load_config()))
    print(f"the mailbox holds {len(found)} unread in "
          f"{len(mailbox.folders)} folder(s), as {len(rows)} row(s)")
    if not rows:
        print("nothing unread to move; nothing was run")
        return 2

    # -- what a session costs before it does anything ---------------------
    print("reaching the account")
    counted = Counting(gw)
    print(f"  building a session took {counted.opened:.2f}s")
    check("a session can be built at all", counted.real is not None)
    started = time.monotonic()
    walk = counted.folders()
    print(f"  and naming every folder took {time.monotonic() - started:.2f}s")
    check("the configured archive is among the folders it names",
          gw.archive.casefold() in walk, True)

    #: What each half cost, in requests, for the comparison at the end.
    cost = {}

    # -- one message ------------------------------------------------------
    print("one message, archived and confirmed on both sides")
    smallest = min(mailbox.folders,
                   key=lambda f: sum(1 for m in found if m.folder == f))
    single = next((t for t in rows
                   if t.count == 1 and t.newest.folder == smallest),
                  next((t for t in rows if t.count == 1), None))
    if single is None:
        print("  no row stands for a single message; skipping this half")
    else:
        message = single.newest
        where = {message.folder: [message.ident]}
        one = Counting(gw)
        started = time.monotonic()
        # Inside the try, not before it: the move happens in here, so an
        # interrupt or a failure part way through must still reach the
        # restore below.  It was written the other way round first, and an
        # interrupted run would have left somebody's mail in the archive.
        try:
            outcome = gateway.archive(gw, where, connect=lambda: one)
            took = time.monotonic() - started
            cost["a row of one"] = list(one.seq)
            check("it is reported archived", len(outcome.archived), 1)
            check("not as already done, and not as missing",
                  (len(outcome.already), len(outcome.missing)), (0, 0))
            with gateway.Server(gw) as srv:
                check("the archive holds it", srv.holds(gw.archive, message.ident))
                check("and the folder it was in does not",
                      srv.holds(message.folder, message.ident), False)
            print(f"  archived and confirmed in {took:.2f}s, "
                  f"{len(one.seq)} requests: {' '.join(one.seq)}")
        finally:
            back = gateway.restore(gw, where)
            check("it is moved back", len(back.archived), 1)
            with gateway.Server(gw) as srv:
                check("the folder holds it again",
                      srv.holds(message.folder, message.ident))
                check("and the archive does not",
                      srv.holds(gw.archive, message.ident), False)

    # -- one folded row ---------------------------------------------------
    print("a folded row, archived in one move")
    # The smallest row that stands for more than one message.  "Several" is
    # what needs proving, and every message this moves is somebody's real
    # mail -- taking the largest row would move thirty-nine of them to make
    # the same point.
    folded = [t for t in rows if t.count > 1]
    many = min(folded, key=lambda t: t.count) if folded else rows[0]
    if many.count < 2:
        print("  no row stands for more than one message; skipping this half")
    else:
        by_folder = {}
        for message in many.messages:
            by_folder.setdefault(message.folder, []).append(message.ident)
        print(f"  the row stands for {many.count} message(s) in "
              f"{len(by_folder)} folder(s)")
        several = Counting(gw)
        started = time.monotonic()
        try:
            outcome = gateway.archive(gw, by_folder, connect=lambda: several)
            took = time.monotonic() - started
            cost["a folded row"] = list(several.seq)
            check("every message in the row is archived",
                  len(outcome.archived), many.count)
            check("none is reported missing", len(outcome.missing), 0)
            print(f"  {many.count} archived and confirmed in {took:.2f}s "
                  f"({took / many.count:.2f}s a message), "
                  f"{len(several.seq)} requests: {' '.join(several.seq)}")
            with gateway.Server(gw) as srv:
                held = sum(1 for idents in by_folder.values()
                           for ident in idents if srv.holds(gw.archive, ident))
            check("the archive holds all of them", held, many.count)
        finally:
            back = gateway.restore(gw, by_folder)
            check("all of them are moved back", len(back.archived), many.count)
            check("and none was lost on the way", len(back.missing), 0)

    # -- what the spec says a row costs -----------------------------------
    # The property the specification states, measured here rather than
    # assumed: what a row costs does not grow with the number of messages it
    # holds.  Both halves must have run in one folder for the comparison to
    # mean anything, which is why it is guarded rather than skipped silently.
    print("what a row costs, against the account")
    if len(cost) == 2 and len(by_folder) == 1:
        one_row, folded_row = cost["a row of one"], cost["a folded row"]
        print(f"  a row of one:  {len(one_row)} requests")
        print(f"  a folded row:  {len(folded_row)} requests "
              f"for {many.count} messages")
        check("a folded row costs no more requests than a single one",
              len(folded_row) <= len(one_row), True)
        check("and they are the same requests in the same order",
              folded_row, one_row)
    else:
        print("  one of the halves did not run, or the row spanned folders; "
              "not compared")

    # -- the board's own path, against the real account -------------------
    # Everything above drives `gateway.archive` directly, which is not the
    # path a keypress takes: the counting, the indicator and the log all
    # live in the board's review worker.  So this builds a board with a
    # STUBBED task store and the REAL account -- nothing live about the
    # half that does not need to be -- and ticks one row.
    print("a board with a stubbed store and the real account")
    single = next((t for t in rows if t.count == 1), None)
    if single is None:
        print("  no row stands for a single message; skipping this half")
    else:
        journal.PATH = REAL_LOG
        before = _lines_in_log()
        where = {single.newest.folder: [single.newest.ident]}
        await _board_review(single, mailbox, gw)
        after = _lines_in_log()
        fresh = after[len(before):]
        check("the board logged what it did", len(fresh) >= 2, True)
        check("an entry says the review started",
              any("review of 1 message(s)" in l and "starting" in l
                  for l in fresh), True)
        check("an entry says it was confirmed",
              any("confirmed in" in l and "1 archived" in l for l in fresh),
              True)
        check("with a duration", any(re.search(r"in \d+\.\ds", l)
                                     for l in fresh), True)
        check("and the folder it came from",
              any(single.newest.folder in l for l in fresh), True)
        check("no subject or sender reached the log",
              any(single.newest.subject[:18] in l for l in fresh), False)
        for line in fresh:
            print(f"  logged: {line.split(' ', 1)[1][:76]}")
        # And put it back, whatever the checks said.
        back = gateway.restore(gw, where)
        check("the message is back in its folder", len(back.archived), 1)

    # -- a request that cannot be made, against the real account ----------
    # The crash this was written for, in the shape it can still take: the
    # move goes out and is answered, and the request that would confirm it
    # never reaches anywhere.  See `Dying` for why this is no longer a cut
    # line.
    #
    # The log goes to a throwaway directory for this half, unlike the one
    # above.  Two reasons: proving that no crash file was written needs a
    # directory that did not already have one, and a synthetic failure has no
    # business in the log a person reads to find real ones.
    print("a request that cannot be made, part way through a real review")
    # The mirror is read again here rather than the row being taken from the
    # reading at the top.  By this point three halves have run, each moving a
    # real message and putting it back, and the mailbox mirror is refreshed on
    # a timer: over the minutes that takes, it re-syncs underneath a row
    # chosen at the start.  Taken from the top's reading, this case looked for
    # a row the board no longer drew and returned before ticking anything --
    # twice in a row, and reported as "the message is back in its folder: 0",
    # which reads like stranded mail and was nothing of the kind.
    fresh = mail.threads(mail.read(mailbox), fold=fold_for(tracker.load_config()))
    single = next((t for t in fresh if t.count == 1), None)
    if single is None:
        print("  no row stands for a single message; skipping this half")
    else:
        room = tempfile.mkdtemp(prefix="gwlive.")
        journal.PATH = os.path.join(room, "logs", "mytasks.log")
        where = {single.newest.folder: [single.newest.ident]}
        moved = []
        try:
            await _board_review_cut(single, mailbox, gw, moved)
        finally:
            # The move succeeded before the cut, so the message is in the
            # archive whatever the checks said.  In a finally, and reported:
            # an interrupt here must still put somebody's mail back.
            #
            # Reported as "nothing to put back" when the review never got as
            # far as moving anything, rather than as a failure: a restore
            # finding nothing is only alarming when something was moved.
            back = gateway.restore(gw, where)
            if moved:
                check("the message is back in its folder after the cut",
                      len(back.archived), 1)
            else:
                check("nothing was moved, so nothing needed putting back",
                      len(back.archived), 0)
        journal.PATH = REAL_LOG

    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


def _lines_in_log():
    try:
        with open(journal.PATH, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip()]
    except OSError:
        return []


async def _board_review_cut(row, mailbox, gw, moved=None):
    """Tick one real row, and make the confirmation unable to go out.

    `moved` is appended to once the move has actually gone out, so the caller
    can tell "the restore found nothing because nothing moved" from "the
    restore lost something".
    """
    made = []

    def cut_after_the_move(name, seq):
        """Cut on the second search after the move.

        Counting rather than matching a folder name.  The sequence after a
        move is fixed: a search of the folder just emptied, which proves the
        messages left, and then a search of the archive, which proves they
        arrived and is the half the line went down in on the account.  So the
        second search after the move is the archive-side confirmation,
        whatever the account happens to call its archive.
        """
        if name == "MOVE" and moved is not None:
            moved.append(name)
        if name != "SEARCH" or "MOVE" not in seq:
            return False
        after = seq[seq.index("MOVE"):]
        return after.count("SEARCH") == 2

    app = main.TaskApp()
    app.client = StubClient([mk("zz-stub-cut", "a stubbed task")],
                            reference=__import__("datetime").datetime.now(TZ))
    app.calendar_config = app.tracker_config = None
    app.mail_config = mailbox
    app.gateway_config = gw

    def connect():
        one = Dying(gw, cut_after_the_move)
        made.append(one)
        return one

    app.gateway_connect = connect
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(20):
            await pilot.pause()
        await pilot.press("i")
        for _ in range(40):
            await pilot.pause()
        wanted = f"{main.MAIL_PREFIX}{row.newest.ident}"
        at = next((i for i, t in enumerate(app.tasks) if t.id == wanted), None)
        check("the row is on the board", at is not None)
        if at is None:
            return
        was = len([t for t in app.tasks if main.TaskApp.is_mail(t)])
        table = app.query_one(DataTable)
        table.move_cursor(row=at)
        app._selected_id = wanted
        for _ in range(6):
            await pilot.pause()
        app.review(app.tasks[at])
        started = time.monotonic()
        for _ in range(1800):
            await asyncio.sleep(0.1)
            if app.mail_busy == 0:
                break
        took = time.monotonic() - started
        print(f"  the request failed after {took:.1f}s")
        check("the confirmation was actually sent nowhere",
              any(one.cut for one in made))
        if not any(one.cut for one in made):
            print(f"  requests in order: "
                  f"{' '.join(one.seq for one in made for one in [one])[:80]}")
        check("nothing is left in flight", app.mail_busy, 0)
        check("the board is still running", app.is_running)
        # The whole point.  This failure used to end the session.
        check("no crash file was written",
              [f for f in os.listdir(os.path.dirname(journal.PATH))
               if f.startswith("crash-")]
              if os.path.isdir(os.path.dirname(journal.PATH)) else [], [])
        check("the mailbox is marked as having failed", app.mail_broken)
        check("and the cell says so", app.mail_mark(), main.MAIL_FAILED_MARK)
        check("the row came back to the queue",
              len([t for t in app.tasks if main.TaskApp.is_mail(t)]), was)
        said = _lines_in_log()
        failed = [l for l in said if "ERROR" in l]
        check("one line says it failed", len(failed), 1)
        check("naming how many messages",
              bool(failed) and "1 message(s)" in failed[0])
        check("and that the line went down rather than a move being refused",
              bool(failed) and "went down" in failed[0])
        check("no subject or sender reached the log",
              any(row.newest.subject[:18] in l for l in said), False)
        for line in failed:
            print(f"  logged: {line.split(' ', 1)[1][:76]}")


async def _board_review(row, mailbox, gw):
    """Tick one real row on a board whose store is stubbed.  Reports only."""
    app = main.TaskApp()
    app.client = StubClient([mk("zz-stub", "a stubbed task")],
                            reference=__import__("datetime").datetime.now(TZ))
    app.calendar_config = app.tracker_config = None
    app.mail_config = mailbox
    app.gateway_config = gw
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(20):
            await pilot.pause()
        await pilot.press("i")
        for _ in range(40):
            await pilot.pause()
        wanted = f"{main.MAIL_PREFIX}{row.newest.ident}"
        at = next((i for i, t in enumerate(app.tasks) if t.id == wanted), None)
        check("the row the account half used is on the board", at is not None)
        if at is None:
            return
        table = app.query_one(DataTable)
        table.move_cursor(row=at)
        app._selected_id = wanted
        for _ in range(6):
            await pilot.pause()
        bar = app.query_one("#daybar", Static)
        check("the mark is at rest before the tick",
              str(bar.render()).rstrip()[-1:], main.MAIL_IDLE_MARK)
        app.review(app.tasks[at])
        check("one operation in flight the moment it starts", app.mail_busy, 1)
        check("and the mark says so",
              str(bar.render()).rstrip()[-1:] in main.MAIL_BUSY_MARKS, True)
        started = time.monotonic()
        for _ in range(1200):
            await asyncio.sleep(0.1)
            if app.mail_busy == 0:
                break
        took = time.monotonic() - started
        check("the count comes back to zero", app.mail_busy, 0)
        check("the mark returns to rest",
              str(bar.render()).rstrip()[-1:], main.MAIL_IDLE_MARK)
        check("and nothing is marked as having failed", app.mail_broken, False)
        print(f"  the board's own review took {took:.1f}s")


sys.exit(asyncio.run(main_()))
