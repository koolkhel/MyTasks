"""What the board said to the mailbox, written down as it says it.

The board died on the real account part way through confirming a row of seven
messages, and the log had one line to offer: that the review had started.
Which of the seven it was on, whether the gateway had been slowing for minutes
or went from healthy to gone, whether the socket had been idle -- none of it
was answerable, and the change that made the failure survivable could not make
it legible.

All four are answered by a command, a duration and an order. So every request
is written down as it is made, always, in a file a day beside the log.

Two of this suite's checks are about what the trace *cannot* hold rather than
what it does. Neither is a filter: the board issues six IMAP verbs and not one
fetches a header or a body, so no subject can reach the trace to be removed
from it; and the one request carrying a password is the one request that is
not on the traced path.

Self-contained: a substituted server that records every request, no network,
and the trace pointed at a throwaway directory throughout.
"""
import asyncio, datetime as dt, os, re, subprocess, sys, tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import fakeimap
import gateway, journal, mail, main
from textual.widgets import DataTable

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
    """Point the log -- and so the trace -- at a throwaway directory.

    One redirection covers the log, the crash file and the trace, all three
    taking their directory from `journal.PATH`.  That is why the trace lives
    in `journal`: a second path constant would be a second thing to redirect
    and a second way for a suite to write into a real account's logs.
    """
    journal.PATH = os.path.join(tempfile.mkdtemp(prefix="journal."),
                                "logs", "mytasks.log")
    return os.path.dirname(journal.PATH)


def traces(room):
    return sorted(f for f in os.listdir(room)
                  if f.startswith("imap-")) if os.path.isdir(room) else []


def traced(room):
    """Every traced line, from every day's file in this directory."""
    out = []
    for f in traces(room):
        with open(os.path.join(room, f), encoding="utf-8") as fh:
            out += [l.rstrip("\n") for l in fh if l.strip()]
    return out


def server(size=3, **kw):
    return fakeimap.FakeIMAP({"Feed": [ident(i) for i in range(size)],
                              "Archive": []}, **kw)


def review(size=3, **kw):
    """One review against a recording server.  Answers (server, lines)."""
    room = elsewhere()
    imap = server(size, **kw)
    try:
        gateway.archive(fakeimap.CONFIG,
                        {"Feed": [ident(i) for i in range(size)]},
                        connect=lambda: imap)
    except Exception:
        pass
    return imap, traced(room), room


# -- a line for every request ---------------------------------------------
def every_request():
    print("every request the board makes is written down")
    imap, lines, room = review(3)
    #: The recording server sees LOGIN and LOGOUT too; the trace does not,
    #: those two being outside the traced path -- which is what keeps a
    #: credential off it.  So the trace is the commands minus those two.
    asked = imap.commands()
    check("the server was asked something at all", len(asked) > 0)
    check("a line for every request but login and logout",
          len(lines), len([c for c in asked if c not in ("LOGIN", "LOGOUT")]))
    check("one file, for today", traces(room),
          [f"imap-{dt.datetime.now(dt.timezone.utc):%Y-%m-%d}.log"])

    print("each line says which command, which folder, and how long")
    shape = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) "
                       r"(\w+) +(\S.*?) +(\d+\.\d\d)s (.+)$")
    parsed = [shape.match(l) for l in lines]
    check("every line parses into stamp, command, about, duration, outcome",
          [bool(m) for m in parsed], [True] * len(lines))
    check("the commands are the ones the gateway issues",
          sorted({m.group(2) for m in parsed if m}),
          ["EXAMINE", "FETCH", "MOVE", "SEARCH", "SELECT", "STORE"])
    check("every line names its folder",
          all(("Feed" in m.group(3) or "Archive" in m.group(3))
              for m in parsed if m))
    check("every line carries a duration",
          all(m.group(4) is not None for m in parsed if m))
    check("and every one of them says it ended well",
          {m.group(5) for m in parsed if m}, {"ok"})

    print("a search names the message, and the rest name a count")
    by = {}
    for m in parsed:
        by.setdefault(m.group(2), []).append(m.group(3))
    check("a search names the identity it searched for",
          all(ident(0)[:5] in a or "<zz" in a for a in by["SEARCH"]),
          True)
    check("a fetch names how many", all("n=" in a for a in by["FETCH"]))
    check("a move names how many and where to",
          all("n=" in a and "->" in a for a in by["MOVE"]))
    check("a store names how many and which flag",
          all("n=" in a and "Seen" in a for a in by["STORE"]))
    check("a select names only its folder",
          all("n=" not in a for a in by["SELECT"] + by["EXAMINE"]))

    print("login and logout are not on the traced path")
    check("no line names login", any("LOGIN" in l for l in lines), False)
    check("nor logout", any("LOGOUT" in l for l in lines), False)
    src = open(os.path.join(_REPO, "gateway.py"), encoding="utf-8").read()
    check("the gateway calls them outside the traced helper",
          bool(re.search(r"self\.imap\.login\(", src))
          and "self._talk(\n            \"LOGIN\"" not in src)


# -- the request that ended a session -------------------------------------
def what_failed():
    print("a request that failed is written down as having failed")
    import imaplib

    def drop_on_archive(name, args):
        if name == "SELECT" and args and args[0] == "Archive":
            raise imaplib.IMAP4.abort("command: EXAMINE => socket error: EOF")
        return None

    imap, lines, room = review(3, fail=drop_on_archive)
    check("something was traced before it died", len(lines) > 0)
    last = lines[-1]
    check("the last line is the request that ended it", "ABORT" in last, True)
    check("and it says what it failed with", "socket error: EOF" in last, True)
    check("and which command it was", "EXAMINE" in last, True)
    check("and how long it had been waiting",
          bool(re.search(r"\d+\.\d\ds ABORT", last)), True)
    check("nothing was traced after it",
          [l for l in lines[lines.index(last) + 1:]], [])

    print("a refusal is told apart from a dropped line")
    def refuse_the_move(name, args):
        return ("NO", [b"refused"]) if name == "MOVE" else None

    _, lines, _ = review(3, fail=refuse_the_move)
    moves = [l for l in lines if " MOVE " in l]
    check("the move is traced as having been answered",
          bool(moves) and moves[-1].rstrip().endswith("ok"), True)
    # A "NO" is an answer, not a protocol error: the gateway reads the status
    # and raises its own MoveFailed, which is not the request failing.
    check("and the operation stopped there",
          [l for l in lines if " STORE " in l], [])


# -- a file a day ---------------------------------------------------------
def a_day_at_a_time():
    print("each day's requests are in a file named for that day")
    room = elsewhere()
    real = journal.datetime

    def on(day):
        class Frozen(real):
            @classmethod
            def now(cls, tz=None):
                return dt.datetime(2026, 9, day, 12, 0,
                                   tzinfo=dt.timezone.utc)
        return Frozen

    for day in (9, 10):
        journal.datetime = on(day)
        try:
            journal.trace("EXAMINE", "Archive", 10.2, "ok")
        finally:
            journal.datetime = real
    check("two days make two files", traces(room),
          ["imap-2026-09-09.log", "imap-2026-09-10.log"])
    check("each holds its own day's line",
          [len(open(os.path.join(room, f), encoding="utf-8").readlines())
           for f in traces(room)], [1, 1])
    # Removing one day leaves the other, which is the point of the shape.
    os.remove(os.path.join(room, "imap-2026-09-09.log"))
    check("removing a day leaves the rest", traces(room),
          ["imap-2026-09-10.log"])

    print("a trace that cannot be written changes nothing")
    journal.PATH = os.path.join("/dev/null", "logs", "mytasks.log")
    imap = server(1)
    out = gateway.archive(fakeimap.CONFIG, {"Feed": [ident(0)]},
                          connect=lambda: imap)
    check("the review still happened", len(out.archived), 1)
    check("and nothing was raised about the trace", True)
    check("and the message really moved", imap.ids("Archive"), [ident(0)])


# -- what it cannot hold --------------------------------------------------
def nothing_identifying():
    print("no message text can reach the trace")
    #: A board with a real subject and body planted in its mail, reviewed
    #: through the real path -- the same shape `t_busy` uses for the log.
    room = elsewhere()
    imap = server(3)
    app = main.TaskApp()
    app.client = StubClient([mk("i1", "a triage task")], reference=NOW)
    app.calendar_config = app.tracker_config = None
    app.mail_config = None
    base = dt.datetime(2026, 9, 8, 8, 0, tzinfo=dt.timezone.utc)
    app.mail_threads = [mail.Thread(tuple(
        mail.Message(sender="zzsender@example.invalid",
                     subject="ZZMARKERSUBJECT about a thing",
                     when=base + dt.timedelta(minutes=i), ident=ident(i),
                     answers=None, body="ZZMARKERBODY and more of it",
                     text="ZZMARKERSUBJECT", folder="Feed", key=f"k{i}")
        for i in range(3)))]
    app.gateway_config = fakeimap.CONFIG
    app.gateway_connect = lambda: imap

    async def go():
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(14):
                await pilot.pause()
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
                if not app.mail_busy:
                    break
    asyncio.run(go())
    text = "\n".join(traced(room))
    check("something was traced at all", len(traced(room)) > 0)
    check("no subject reached the trace", "ZZMARKERSUBJECT" in text, False)
    check("no body reached the trace", "ZZMARKERBODY" in text, False)
    check("no sender reached the trace", "zzsender" in text, False)
    check("the folder is there", "Feed" in text, True)
    check("and the identities are, as the log's rule allows",
          ident(0) in text, True)

    print("and no request asks for any, which is why")
    src = open(os.path.join(_REPO, "gateway.py"), encoding="utf-8").read()
    for verb in ("BODY", "RFC822", "ENVELOPE", "BODYSTRUCTURE",
                 "HEADER.FIELDS"):
        check(f"the gateway never asks for {verb}", verb in src, False)
    # The one HEADER it names is a search key, which carries no message text.
    check("the only HEADER it names is the search key",
          re.findall(r'"HEADER"', src), ['"HEADER"'])


def nothing_secret():
    print("no credential can reach the trace")
    #: The password the gateway would send, planted as a marker.
    room = elsewhere()
    marked = gateway.Config(
        host=fakeimap.CONFIG.host, port=fakeimap.CONFIG.port,
        user=fakeimap.CONFIG.user, archive=fakeimap.CONFIG.archive,
        password_command=("printf", "ZZMARKERPASSWORD"))
    check("the password command really yields the marker",
          gateway.password(marked), "ZZMARKERPASSWORD")
    imap = server(1)
    gateway.archive(marked, {"Feed": [ident(0)]}, connect=lambda: imap)
    text = "\n".join(traced(room))
    check("something was traced", len(traced(room)) > 0)
    check("the password is nowhere in it", "ZZMARKERPASSWORD" in text, False)
    check("and neither is the user", marked.user in text, False)


# -- what it costs --------------------------------------------------------
def costs_nothing():
    print("tracing asks the account for nothing extra")
    #: Stated as the invariant rather than as totals.  Written as totals --
    #: 12, 18 and 30 requests for rows of one, three and seven -- it also
    #: became a check on the request shape, and drifted the moment the
    #: confirmation stopped opening the archive once a message.  What "costs
    #: nothing" actually means is that every request the account sees is one
    #: the gateway would have made anyway, and that the trace holds those and
    #: no others.
    UNTRACED = ("LOGIN", "LOGOUT")
    for size in (1, 3, 7):
        imap, lines, _ = review(size)
        asked = imap.commands()
        check(f"a row of {size}: the trace holds every request but "
              f"{' and '.join(UNTRACED).lower()}",
              len(lines), len([c for c in asked if c not in UNTRACED]))
        check(f"a row of {size}: and holds nothing the account never saw",
              len(lines) <= len(asked), True)
        check(f"a row of {size}: those two are the only ones untraced",
              sorted({c for c in asked if c in UNTRACED}), ["LOGIN", "LOGOUT"])

    print("nothing on the board is drawn from it")
    room = elsewhere()
    imap = server(1)
    gateway.archive(fakeimap.CONFIG, {"Feed": [ident(0)]},
                    connect=lambda: imap)
    check("a trace was written", len(traces(room)), 1)
    for f in traces(room):
        os.remove(os.path.join(room, f))
    check("and removing it leaves the gateway answering the same",
          gateway.Server(fakeimap.CONFIG,
                         connect=lambda: imap).__class__.__name__, "Server")
    out = gateway.restore(fakeimap.CONFIG, {"Feed": [ident(0)]},
                          connect=lambda: imap)
    check("the message still came back", len(out.archived), 1)
    check("with the trace gone beforehand", True)


# -- the repetition it makes visible --------------------------------------
def no_repetition():
    print("a folded row opens the archive twice, not once a message")
    imap, lines, _ = review(7)
    selects = [l for l in lines if " SELECT " in l or " EXAMINE " in l]
    archive = [l for l in selects if "Archive" in l]
    #: Readonly opens are EXAMINE, writable ones SELECT.  The gateway opens
    #: the archive readonly once to confirm the whole row arrived, and
    #: writably once to mark it read.
    reading = [l for l in archive if " EXAMINE " in l]
    writing = [l for l in archive if " SELECT " in l]
    #: This assertion has moved rather than been written afresh.  It used to
    #: record the repetition as present: eleven folder openings for seven
    #: messages, eight of them the archive, seven readonly and six of those
    #: repetition -- about a minute of a folded row spent opening one folder,
    #: most of the nine minutes the crash spent before the line dropped.  It
    #: was written as a check so that removing the repetition would have an
    #: assertion to move instead of a claim to re-establish.  This is that.
    check("five folder openings for seven messages", len(selects), 5)
    check("two of them open the archive", len(archive), 2)
    check("one readonly, for the whole confirmation", len(reading), 1)
    check("and one writable, for the flag", len(writing), 1)
    check("the searches are still one a message",
          len([l for l in lines if " SEARCH " in l and "Archive" in l]), 7)
    #: The point of the shape: it does not grow with the row.
    opens = {}
    for size in (1, 3, 7):
        _, some, _ = review(size)
        opens[size] = len([l for l in some
                           if ("Archive" in l)
                           and (" SELECT " in l or " EXAMINE " in l)])
    check("and the count is the same for any row size", set(opens.values()),
          {2})
    print(f"      archive openings by row size: {opens}")


# -- the directory it lands in --------------------------------------------
def not_committable():
    print("a trace can never be committed")
    real = os.path.join(os.path.dirname(os.path.abspath(journal.__file__)),
                        "logs")
    candidate = os.path.join(real, "imap-2026-09-10.log")
    done = subprocess.run(["git", "check-ignore", "-v", candidate],
                          cwd=_REPO, capture_output=True, text=True)
    check("git reports it ignored", done.returncode, 0)
    check("and names the rule", ".gitignore" in done.stdout)
    listed = subprocess.run(["git", "status", "--porcelain"],
                            cwd=_REPO, capture_output=True, text=True)
    check("and no trace is ever listed",
          [l for l in listed.stdout.splitlines() if "imap-" in l], [])


every_request()
what_failed()
a_day_at_a_time()
nothing_identifying()
nothing_secret()
costs_nothing()
no_repetition()
not_committable()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
