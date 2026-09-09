"""One real message, and one real row, moved to the archive and moved back.

The only suite here that touches a real account. It exists because every
other check about reviewing is against a substituted server, and a
substituted server agrees with whatever this code believes: that the gateway
takes a batched move, that a search finds a message by its identity, that a
folder empties when messages leave it. Those are beliefs about a server, and
only the server can settle them.

What it does, and no more: takes one unread message from a configured folder,
moves it to the archive, confirms both sides, moves it back and confirms
that. Then the same for one folded row of several messages, timing the
confirmation. Nothing is deleted, nothing goes anywhere but the archive and
back, and the restore runs even when a check fails.

It prints counts, folder names and durations. No subject, sender, address or
identity is printed, here or in a failure message: this is a real mailbox.

Note for whoever runs it: a message moved out and back reaches the local
mirror as a removal and then as a new arrival, so it may vanish from the
folder for up to one sync interval and come back with a new number. That is
the same thing an ordinary review does, and it is why undoing a review says
the row returns when the mailbox next catches up.
"""
import asyncio
import builtins
import functools
import os
import re
import sys
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
#: withholds the mailbox, the gateway and the log from every board built
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


def summarise(threads):
    return {"rows": len(threads), "messages": sum(t.count for t in threads)}


async def main_():
    mailbox = REAL_MAILBOX()
    gw = REAL_GATEWAY()
    if mailbox is None or not mailbox.folders or gw is None:
        print("no mailbox or no gateway configured; nothing was run")
        return 2

    found = mail.read(mailbox)
    rows = mail.threads(found, fold=fold_for(tracker.load_config()))
    print(f"the mailbox holds {len(found)} unread in "
          f"{len(mailbox.folders)} folder(s), as {len(rows)} row(s)")
    if not rows:
        print("nothing unread to move; nothing was run")
        return 2

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
        started = time.monotonic()
        # Inside the try, not before it: the move happens in here, so an
        # interrupt or a failure part way through must still reach the
        # restore below.  It was written the other way round first, and an
        # interrupted run would have left somebody's mail in the archive.
        try:
            outcome = gateway.archive(gw, where)
            took = time.monotonic() - started
            check("it is reported archived", len(outcome.archived), 1)
            check("not as already done, and not as missing",
                  (len(outcome.already), len(outcome.missing)), (0, 0))
            with gateway.Server(gw) as srv:
                check("the archive holds it", srv.holds(gw.archive, message.ident))
                check("and the folder it was in does not",
                      srv.holds(message.folder, message.ident), False)
            print(f"  archived and confirmed in {took:.2f}s "
                  f"from folder {message.folder}")
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
        started = time.monotonic()
        try:
            outcome = gateway.archive(gw, by_folder)
            took = time.monotonic() - started
            check("every message in the row is archived",
                  len(outcome.archived), many.count)
            check("none is reported missing", len(outcome.missing), 0)
            print(f"  {many.count} archived and confirmed in {took:.2f}s "
                  f"({took / many.count:.2f}s a message)")
            with gateway.Server(gw) as srv:
                held = sum(1 for idents in by_folder.values()
                           for ident in idents if srv.holds(gw.archive, ident))
            check("the archive holds all of them", held, many.count)
        finally:
            back = gateway.restore(gw, by_folder)
            check("all of them are moved back", len(back.archived), many.count)
            check("and none was lost on the way", len(back.missing), 0)

    # -- the board's own path, against the real gateway -------------------
    # Everything above drives `gateway.archive` directly, which is not the
    # path a keypress takes: the counting, the indicator and the log all
    # live in the board's review worker.  So this builds a board with a
    # STUBBED task store and the REAL gateway -- nothing live about the
    # half that does not need to be -- and ticks one row.
    print("a board with a stubbed store and the real gateway")
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

    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1


def _lines_in_log():
    try:
        with open(journal.PATH, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip()]
    except OSError:
        return []


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
        check("the row the gateway half used is on the board", at is not None)
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
