"""A crash leaves a file behind, and the log points at it.

The board died on the real account part way through confirming a
seven-message row: `imaplib.IMAP4.abort` from an EXAMINE, which was neither
of the two exceptions the worker caught. The traceback went to the terminal,
where it survived only because a person pasted it into a file by hand, and
the log beside it said nothing at all -- one `starting` line and no
counterpart, which is all there was to diagnose from.

Two halves here. The writer, driven directly: what it produces, that two
crashes never collide, and that it cannot itself become the reason a session
ends worse than it was already ending. And the hook, driven through a real
board: that the framework's own path to ending a session now goes past it.

The load-bearing check is the last one. A crash file holds the frames and the
values in them, which for a failure mid-review means somebody's mail -- and
that is allowed on one condition, that the directory can never be committed.
So this suite asks git itself, rather than trusting the arrangement.

Self-contained: a stubbed store, a substituted gateway, no network, and the
log pointed at a throwaway directory throughout.
"""
import asyncio, contextlib, io, os, re, subprocess, sys, tempfile, threading

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import fakeimap
import gateway, journal, mail, main
import datetime as dt
from textual.widgets import DataTable

#: Textual's `_handle_exception` is private API, and this suite depends on it.
#: Built against 8.2.8; see `the_hook` for the check that guards the rename.
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
    """Point the log -- and so the crash files -- at a throwaway directory.

    One redirection covers both, the crash file deriving its directory from
    `journal.PATH`.  That is the whole reason the writer lives in `journal`:
    a second path constant would be a second thing to remember here, and a
    second way for a suite to write a crash into a real account's logs.
    """
    journal.PATH = os.path.join(tempfile.mkdtemp(prefix="journal."),
                                "logs", "mytasks.log")
    return os.path.dirname(journal.PATH)


def crashes(room):
    return sorted(f for f in os.listdir(room) if f.startswith("crash-")) \
        if os.path.isdir(room) else []


def lines():
    try:
        with open(journal.PATH, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip()]
    except OSError:
        return []


def raised(make):
    """An exception object, raised for real so it carries a traceback."""
    try:
        make()
    except BaseException as exc:
        return exc
    raise AssertionError("nothing was raised")


# -- the writer ------------------------------------------------------------
def the_writer():
    print("a failure is written down")
    room = elsewhere()

    def deep(marker):
        held = marker
        raise ValueError("something nobody anticipated")

    err = raised(lambda: deep("ZZFRAMEVALUE"))
    where = journal.crash(err)
    check("a file was written", where is not None and os.path.exists(where))
    check("one of them, in the log's own directory", len(crashes(room)), 1)
    body = open(where, encoding="utf-8").read()
    check("it names the exception", "ValueError" in body)
    check("and what the exception said",
          "something nobody anticipated" in body)
    check("it names the frame the failure came from", "deep" in body)
    # The whole point of keeping locals: a review's frame holds the messages
    # being reviewed, and that is what a person needs and cannot re-run.
    check("and holds a value that frame was holding", "ZZFRAMEVALUE" in body)
    check("no colour codes, so it greps and reads in an editor",
          "\x1b[" in body, False)

    print("the traceback is built from the exception, not the current one")
    # It has to be: a worker raises on another thread and the failure arrives
    # as an object, so there is no current exception where this is called.
    # `Traceback()` with no arguments would render nothing at all.
    room = elsewhere()
    carried = []

    def on_a_thread():
        def under(marker):
            held = marker
            raise RuntimeError("raised somewhere else entirely")
        carried.append(raised(lambda: under("ZZOTHERTHREAD")))

    worker = threading.Thread(target=on_a_thread)
    worker.start()
    worker.join()
    check("sys.exc_info() is empty where the writer runs",
          sys.exc_info(), (None, None, None))
    where = journal.crash(carried[0])
    body = open(where, encoding="utf-8").read()
    check("the file still names the exception", "RuntimeError" in body)
    check("and its frames", "under" in body)
    check("and the value that frame held", "ZZOTHERTHREAD" in body)

    print("a wrapper with no traceback of its own still yields the frames")
    # The bug this exists for: Textual hands the hook a `WorkerFailed` it
    # *constructs* rather than raises, so that object has no `__traceback__`.
    # Rendering it produced a 69-byte file naming the wrapper and nothing
    # else, while the terminal showed the whole chain -- because the terminal
    # was rendering the live exception instead.
    room = elsewhere()

    def under(marker):
        held = marker
        raise ValueError("the failure that actually happened")

    real = raised(lambda: under("ZZUNDERNEATH"))

    class Wrapper(Exception):
        pass

    wrapper = Wrapper(real)          # constructed, never raised
    check("the wrapper carries no traceback", wrapper.__traceback__, None)
    check("and nothing is being handled where the writer runs",
          sys.exc_info(), (None, None, None))
    where = journal.crash(wrapper)
    body = open(where, encoding="utf-8").read()
    check("the file names the wrapper", "Wrapper" in body)
    check("and the failure underneath it", "ValueError" in body)
    check("and that failure's frames", "under" in body)
    check("and the value the frame held", "ZZUNDERNEATH" in body)
    check("so the file is a traceback, not a one-line summary",
          len(body) > 400)

    print("one failure never overwrites another")
    room = elsewhere()
    first = journal.crash(raised(lambda: 1 / 0))
    second = journal.crash(raised(lambda: 1 / 0))
    check("two files", len(crashes(room)), 2)
    check("with different names", first != second)
    # Two inside one second is not a real scenario; the rule is not allowed
    # to hold only while the clock cooperates.
    check("and the order they happened in can be read from the names",
          crashes(room), sorted(crashes(room)))
    check("both are files that exist",
          os.path.exists(first) and os.path.exists(second))

    print("the writer cannot make a crash worse")
    room = elsewhere()

    class Unshowable:
        def __repr__(self):
            raise RuntimeError("this repr refuses")

    def with_a_bad_repr():
        held = Unshowable()
        raise KeyError("zz-key")

    err = raised(with_a_bad_repr)
    where = journal.crash(err)
    check("a value that will not render still leaves a file",
          where is not None and os.path.exists(where))
    check("and the file names the exception",
          "KeyError" in open(where, encoding="utf-8").read())

    # Nowhere to write: makedirs cannot make a directory under a file.
    journal.PATH = os.path.join("/dev/null", "logs", "mytasks.log")
    check("nowhere to write writes nothing, and says nothing",
          journal.crash(raised(lambda: 1 / 0)), None)

    print("the log points at the crash file")
    room = elsewhere()
    where = journal.crash(raised(lambda: 1 / 0))
    said = lines()
    check("one line was written", len(said), 1)
    check("marked as a failure", "ERROR" in said[0])
    check("naming the file", os.path.basename(where) in said[0])
    check("and the exception's type", "ZeroDivisionError" in said[0])

    print("but never the exception's message")
    # This log holds no subject and no sender.  An arbitrary exception's
    # message can carry either -- a KeyError on a subject line would put that
    # subject straight into the file that promised not to hold one.
    room = elsewhere()

    def with_a_talkative_message():
        raise KeyError("ZZSUBJECTINMESSAGE")

    where = journal.crash(raised(with_a_talkative_message))
    check("the log does not repeat what the exception said",
          any("ZZSUBJECTINMESSAGE" in l for l in lines()), False)
    check("while the crash file, which may hold it, does",
          "ZZSUBJECTINMESSAGE" in open(where, encoding="utf-8").read())


# -- the hook --------------------------------------------------------------
def the_hook():
    print("the framework's own path to ending a session goes past the writer")
    from textual.app import App
    # Private API, deliberately overridden: this is the only place a worker's
    # failure arrives.  A rename in a future Textual must fail here rather
    # than quietly ending crash files, so the name is asserted, not assumed.
    check("Textual still calls its hook _handle_exception",
          hasattr(App, "_handle_exception"))
    check("and TaskApp overrides it rather than adding a new name",
          "_handle_exception" in vars(main.TaskApp))
    check("the override goes on to the framework's",
          "super()._handle_exception" in
          open(os.path.join(_REPO, "main.py"), encoding="utf-8").read())


async def a_board(imap):
    """A board with one mail row of three messages, and a stubbed store."""
    app = main.TaskApp()
    app.client = StubClient([mk("i1", "a triage task")], reference=NOW)
    app.calendar_config = app.tracker_config = None
    app.mail_config = None
    base = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    app.mail_threads = [mail.Thread(tuple(
        mail.Message(sender="s@example.invalid", subject="a notification",
                     when=base + dt.timedelta(minutes=i), ident=ident(i),
                     answers=None, body="what it says", text="a notification",
                     folder="Feed", key=f"k{i}")
        for i in range(3)))]
    app.gateway_config = fakeimap.CONFIG
    app.gateway_connect = lambda: imap
    return app


async def a_crashing_review():
    """Tick a mail row against a gateway that fails in a way nothing catches.

    Not `abort` -- that is now converted and handled, and the point of this
    suite's other half.  Something nothing anticipated, which is what a crash
    file is for: a defect, reaching the framework's own hook.
    """
    print("a review that fails in a way nothing anticipated")
    room = elsewhere()

    def a_bug(name, args):
        if name == "MOVE":
            raise ZeroDivisionError("a defect, not a mailbox failure")
        return None

    imap = fakeimap.FakeIMAP({"Feed": [ident(i) for i in range(4)],
                              "Archive": []}, fail=a_bug)
    app = await a_board(imap)
    ended = None
    # The framework still prints the traceback to the terminal on its way
    # out.  Caught rather than let through, both to keep this suite's output
    # readable and so that it can be asserted: the file is in addition to
    # what a person saw, not instead of it.
    shouted = io.StringIO()
    try:
        with contextlib.redirect_stderr(shouted):
          async with app.run_test(size=(100, 44)) as pilot:
            # To the inbox  , and onto the mail row itself, the same way the
              # other mail suites get there.
              await pilot.press("i")
              for _ in range(22):
                  await pilot.pause()
              row = next(t for t in app.tasks if app.is_mail(t))
              table = app.query_one(DataTable)
              table.move_cursor(row=app.tasks.index(row))
              app._selected_id = row.id
              for _ in range(6):
                  await pilot.pause()
              await pilot.press("space")
              for _ in range(60):
                  await pilot.pause()
                  if crashes(room):
                      break
    except BaseException as exc:
        ended = exc
    check("the framework still told the terminal",
          "ZeroDivisionError" in shouted.getvalue())
    made = crashes(room)
    check("a crash file was written", len(made), 1)
    body = open(os.path.join(room, made[0]), encoding="utf-8").read() if made else ""
    check("naming the exception nothing caught", "ZeroDivisionError" in body)
    check("and the worker it came out of", "file_away" in body)
    # The session still ends.  A failure nothing anticipated is evidence of a
    # defect, not a state to keep working in.
    check("the session ended rather than carrying on", ended is not None)
    check("and the log points at the file",
          bool(made) and any(made[0] in l and "ERROR" in l for l in lines()))


# -- the directory the files land in ---------------------------------------
def not_committable():
    print("the crash file's directory can never be committed")
    # Asked of git rather than assumed: the file holds whatever the frames
    # held, which mid-review is somebody's mail.  That content is allowed
    # here on this condition and no other.
    real = os.path.join(os.path.dirname(os.path.abspath(journal.__file__)),
                        "logs")
    candidate = os.path.join(real, "crash-20260909T173924Z.txt")
    done = subprocess.run(["git", "check-ignore", "-v", candidate],
                          cwd=_REPO, capture_output=True, text=True)
    check("git reports it ignored", done.returncode, 0)
    check("and names the rule that does it", ".gitignore" in done.stdout)
    check("the log beside it too",
          subprocess.run(["git", "check-ignore", os.path.join(real, "mytasks.log")],
                         cwd=_REPO, capture_output=True).returncode, 0)
    # A hand-saved traceback goes where a person is standing, which is the
    # working directory -- that is how today's arrived.
    check("and a traceback saved by hand at the top of the repository",
          subprocess.run(["git", "check-ignore",
                          os.path.join(_REPO, "crash.txt")],
                         cwd=_REPO, capture_output=True).returncode, 0)


the_writer()
the_hook()
asyncio.run(a_crashing_review())
not_committable()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
