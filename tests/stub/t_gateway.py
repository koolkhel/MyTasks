"""The gateway client: one walk per session, one search per row, one move.

No network and no credentials: the connection is substituted by an account
that records every request (`tests/fakemail.py`), so these checks are about the
requests made, not only the outcome. That matters here more than anywhere else
in the board -- reviewing is the one action it cannot undo by itself, and the
cost of getting the request shape wrong is a row of forty messages costing
forty round trips instead of one.

Invented folder names and `.invalid` identities only.
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
# Imported for what it does on import, not for what it exports: it points
# `journal.PATH` at a throwaway directory, which is what keeps this suite's
# log lines, crash files and traces out of the board's own `logs/`.
# Without it, tracing every gateway request put 708 synthetic lines in there.
# Not `from harness import *`, which shadows `time` with `datetime.time`.
import gateway
#: The reader itself, kept before `harness` replaces it below.  The harness
#: blanks every loader so that a stub suite cannot build a configuration
#: reaching a real account; the checks further down want the reader, and give
#: it an environment of their own and a file holding nothing, so what they
#: build reaches nothing either.  The module's own attribute stays blanked,
#: which is what protects the rest of this suite.
_read_config = gateway.load_config
import harness  # noqa: F401
import fakemail

ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def ident(n):
    return f"<zz{n}@example.invalid>"


def box(folders, **kw):
    return fakemail.FakeMailbox(folders, **kw)


# -- folder names ---------------------------------------------------------
# A folder is named by an identity the account hands out, and the board knows
# only the name a person wrote in their configuration. Resolving one costs a
# walk of the whole tree -- 4.18 s for one folder against 1.36 s for four --
# so the walk happens once and every name it passed is remembered.
print("a folder is found by its name, once a session")
mail = box({"Archive": [], "Alerts": [ident(1)], "Черновики": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    check("the archive is resolved when the session opens",
          "FOLDERS" in mail.commands(), True)
    srv.numbers("Alerts", [ident(1)])
    srv.numbers("Черновики", [ident(1)])
    check("a name that is not ASCII needs no encoding of the board's own",
          srv.numbers("Черновики", []), {})
    check("one walk, however many folders are named",
          mail.commands().count("FOLDERS"), 1)
check("and the walk happens again for the next session",
      fakemail.server(fakemail.CONFIG, mail).__enter__() is not None, True)

print("a folder is named without regard to case")
mail = box({"Archive": [], "ALERTS": [ident(1)]})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    check("the account's spelling and the configuration's need not match",
          sorted(srv.numbers("alerts", [ident(1)])), [ident(1)])

print("a folder that is not there is reported")
mail = box({"Archive": [], "Alerts": [ident(1)]})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    try:
        srv.numbers("Nope", [ident(1)])
        check("an absent folder is refused", "no error raised", "MoveFailed")
    except gateway.MoveFailed as exc:
        check("an absent folder is refused", "Nope" in str(exc))

# -- a row is asked about in one request ----------------------------------
# The old gateway answered a search of eight identities with two of them, so
# the board asked one at a time and a row of eight cost eight searches. The
# account itself answers the set, so the set is the question.
print("a row's messages are asked for in one request")
mail = box({"Alerts": [ident(i) for i in range(40)], "Archive": []})
wanted = [ident(i) for i in range(8)]
with fakemail.server(fakemail.CONFIG, mail) as srv:
    found = srv.numbers("Alerts", wanted)
check("each of the row's identities maps to a message",
      sorted(found), sorted(wanted))
check("and nothing else in the folder was asked about", len(found), 8)
check("the messages are the account's own",
      all(item in mail.held["Alerts"] for item in found.values()), True)
check("one search for the row, not one a message",
      mail.commands().count("SEARCH"), 1)
check("and the search named every identity the row holds",
      [args for name, args in mail.calls if name == "SEARCH"],
      [("Alerts", 8)])
check("the folders were walked once, not once a message",
      mail.commands().count("FOLDERS"), 1)
with fakemail.server(fakemail.CONFIG, mail) as srv:
    check("an identity the folder does not hold is simply absent",
          srv.numbers("Alerts", [ident(999)]), {})
    check("and asking about nothing asks nothing",
          srv.numbers("Alerts", []), {})

print("what a folder still holds is asked the same way")
mail = box({"Alerts": [ident(1), ident(2)], "Archive": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    numbers = srv.numbers("Alerts", [ident(1), ident(2)])
    check("both are there",
          len(srv.present("Alerts", [ident(1), ident(2)])), 2)
    srv.move("Alerts", [numbers[ident(1)]], "Archive")
    check("and one of them is not, once it has moved",
          srv.present("Alerts", [ident(1), ident(2)]), [ident(2)])
    check("asking about nothing asks nothing", srv.present("Alerts", []), [])
check("proving absence took one search, not a search a message",
      mail.commands().count("SEARCH"), 3)

# -- one move covers a row ------------------------------------------------
print("a row of many messages is moved in one request")
mail = box({"Alerts": [ident(i) for i in range(12)], "Archive": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    numbers = srv.numbers("Alerts", [ident(i) for i in range(12)])
    srv.move("Alerts", list(numbers.values()), "Archive")
check("one move, not twelve", mail.commands().count("MOVE"), 1)
check("all twelve arrived", len(mail.ids("Archive")), 12)
check("and none stayed behind", mail.ids("Alerts"), [])
check("the same messages arrived, not copies of one",
      mail.ids("Archive"), sorted(ident(i) for i in range(12)))

print("moving nothing asks nothing")
mail = box({"Alerts": [ident(1)], "Archive": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    srv.move("Alerts", [], "Archive")
check("no request was made but the walk that opened the session",
      mail.commands(), ["FOLDERS"])

print("a refused move is reported, not passed over")


def raising_on(command, exc):
    """A fail hook that raises from one command and lets the rest through."""
    def fail(name, args):
        if name == command:
            raise exc
    return fail


mail = box({"Alerts": [ident(1)], "Archive": []},
           fail=raising_on("MOVE", fakemail.refused("over quota")))
with fakemail.server(fakemail.CONFIG, mail) as srv:
    numbers = srv.numbers("Alerts", [ident(1)])
    try:
        srv.move("Alerts", list(numbers.values()), "Archive")
        check("the refusal is raised", "no error raised", "MoveFailed")
    except gateway.MoveFailed as exc:
        check("the refusal is raised", "over quota" in str(exc))
check("and the message did not move", mail.ids("Alerts"), [ident(1)])

# -- confirming where a message went --------------------------------------
print("asking a folder anything changes nothing in it")
# What the old protocol's read-only open protected: a question must not be a
# change.  There is no mode to ask in now -- a search is a question and
# nothing else -- so this asserts the property directly.
mail = box({"Alerts": [ident(1), ident(2)], "Archive": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    srv.numbers("Alerts", [ident(1), ident(2)])
    srv.present("Alerts", [ident(1)])
    srv.holds("Archive", ident(1))
check("searching moved nothing", mail.ids("Alerts"),
      sorted([ident(1), ident(2)]))
check("and set no flag", (mail.stored_in, mail.unread_in("Alerts")),
      ([], sorted([ident(1), ident(2)])))
check("and asked for nothing but the walk and the searches",
      sorted(set(mail.commands())), ["FOLDERS", "SEARCH"])

print("a folder can be asked whether it holds one message")
mail = box({"Alerts": [ident(1), ident(2)], "Archive": [ident(3)]})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    check("present is present", srv.holds("Archive", ident(3)))
    check("absent is absent", srv.holds("Archive", ident(1)), False)
    check("asking costs one search each",
          mail.commands().count("SEARCH"), 2)

# -- the shape of the question asked --------------------------------------
# Both of these were learnt from the account, and neither could have been
# learnt here: a fake answers any question, however it is shaped, and only a
# server has a limit.  They are checked here so that the shape cannot drift
# back without a suite saying so.
print("the question a row asks does not deepen as the row grows")


def depth(query):
    kids = getattr(query, "children", None) or []
    return 1 + max((depth(k) for k in kids), default=0)


#: An OR of one term per identity nests one level per message, and the
#: service refuses a request deeper than 32 levels -- a row of thirty-nine is
#: an ordinary row on the account this was built for, and it was refused
#: outright with `ErrorSchemaValidation`.
deep = {n: depth(gateway.restriction([ident(i) for i in range(n)]))
        for n in (2, 40, 400)}
check("the same depth for two identities and for four hundred",
      len(set(deep.values())), 1)
check("and that depth is nowhere near the service's limit",
      max(deep.values()) < 8, True)
print(f"      restriction depth by size: {deep}")

print("and it names no more identities at once than the service allows")


class OneFolder:
    """A folder that records how many identities each request named."""

    def __init__(self):
        self.asked = []

    def filter(self, query):
        self.asked.append(len(list(query.children or [])) or 1)
        return self

    def only(self, *fields):
        return []


#: The real `find`, driven against a folder that answers nothing: it reads
#: no state of its own, so it can be called unbound.  What is being checked
#: is how it divides a set, which is the half a substituted account hides.
where = OneFolder()
gateway.Mailbox.find(None, where, [ident(i) for i in range(250)])
check("a set larger than the bound is asked in parts",
      len(where.asked), 3)
check("and no part names more than the bound",
      max(where.asked) <= gateway.BATCH, True)
where = OneFolder()
gateway.Mailbox.find(None, where, [ident(i) for i in range(8)])
check("a row-sized set is one request", len(where.asked), 1)

# -- the credential -------------------------------------------------------
print("the credential is asked for at the moment it is needed")
cfg = gateway.Config(service="https://account.invalid/service", account="me",
                     password_command=("printf", "zzsecret"))
check("the command answers it", gateway.password(cfg), "zzsecret")
try:
    gateway.password(gateway.Config(service="s", account="u"))
    check("a missing command is refused", "no error raised", "GatewayUnreachable")
except gateway.GatewayUnreachable:
    check("a missing command is refused", True)
try:
    gateway.password(gateway.Config(service="s", account="u",
                                    password_command=("false",)))
    check("a failing command is refused", "no error raised", "GatewayUnreachable")
except gateway.GatewayUnreachable:
    check("a failing command is refused", True)

print("the credential command cannot reach the terminal the board owns")
check("its input is closed, so it cannot wait on a person",
      gateway.password(gateway.Config(
          service="s", account="u",
          password_command=("sh", "-c", "test -t 0 && echo tty || echo notty"))),
      "notty")
check("a command that reads its input gets nothing and returns",
      gateway.password(gateway.Config(
          service="s", account="u",
          password_command=("sh", "-c", "cat; echo zzread"))),
      "zzread")

# -- what the configuration reads -----------------------------------------
print("how to reach the account is read from the environment")


def configured(**env):
    keep = {k: os.environ.get(k) for k in
            ("MAIL_EWS_URL", "MAIL_ACCOUNT", "MAIL_PASSWORD_COMMAND",
             "MAIL_IMAP_USER", "MAIL_IMAP_PASSWORD_COMMAND",
             "MAIL_ARCHIVE_FOLDER")}
    try:
        for k in keep:
            os.environ.pop(k, None)
        os.environ.update({k: v for k, v in env.items() if v is not None})
        # A path that holds nothing, so only what is set above is read.
        return _read_config("/dev/null")
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


got = configured(MAIL_EWS_URL="https://a.invalid/s", MAIL_ACCOUNT="me",
                 MAIL_PASSWORD_COMMAND="printf zz")
check("the address, the account and the command make a configuration",
      (got.service, got.account, got.password_command),
      ("https://a.invalid/s", "me", ("printf", "zz")))
check("the archive has a name even when none is configured", got.archive,
      "Archive")
got = configured(MAIL_EWS_URL="https://a.invalid/s", MAIL_IMAP_USER="old",
                 MAIL_IMAP_PASSWORD_COMMAND="printf zz")
check("the names this had when it spoke IMAP are still read",
      (got.account, got.password_command), ("old", ("printf", "zz")))
got = configured(MAIL_EWS_URL="https://a.invalid/s", MAIL_ACCOUNT="new",
                 MAIL_IMAP_USER="old", MAIL_PASSWORD_COMMAND="printf zz")
check("and the new name wins where both are set", got.account, "new")
check("no address means reviewing is not configured",
      configured(MAIL_ACCOUNT="me", MAIL_PASSWORD_COMMAND="printf zz"), None)
check("no account means reviewing is not configured",
      configured(MAIL_EWS_URL="https://a.invalid/s",
                 MAIL_PASSWORD_COMMAND="printf zz"), None)
check("no credential command means reviewing is not configured",
      configured(MAIL_EWS_URL="https://a.invalid/s", MAIL_ACCOUNT="me"), None)

# -- putting a row back --------------------------------------------------
print("an undo costs four requests, whatever the row's size")


def one_undo(size):
    ids = [ident(i) for i in range(size)]
    mail = box({"Alerts": ids[:], "Archive": []})
    gateway.archive(fakemail.CONFIG, {"Alerts": ids}, connect=lambda: mail)
    mark = len(mail.calls)
    out = gateway.restore(fakemail.CONFIG, {"Alerts": ids},
                          connect=lambda: mail)
    return mail, mail.calls[mark:], out


for size in (1, 2, 3, 7):
    mail, undo, out = one_undo(size)
    #: One walk to name the folders, one search to find them, one flag to
    #: mark them unread, one move to put them back.  A message at a time
    #: this was three folder openings each: 3, 6, 9 and 21.
    check(f"a row of {size}: one walk of the folders",
          sum(1 for name, _ in undo if name == "FOLDERS"), 1)
    check(f"a row of {size}: one search, not one a message",
          sum(1 for name, _ in undo if name == "SEARCH"), 1)
    check(f"a row of {size}: one move, not one a message",
          sum(1 for name, _ in undo if name == "MOVE"), 1)
    check(f"a row of {size}: one flag, not one a message",
          sum(1 for name, _ in undo if name == "FLAG"), 1)
    check(f"a row of {size}: all of them came back",
          sorted(out.archived), sorted(ident(i) for i in range(size)))
    check(f"a row of {size}: unread again",
          len(mail.unread_in("Alerts")), size)

check("and the count no longer grows with the row",
      len({len(one_undo(n)[1]) for n in (1, 2, 3, 7)}), 1)

print("one move per folder a row came from, not one per message")
mail = box({"Alerts": [ident(1), ident(2)], "Notes": [ident(3)], "Archive": []})
gateway.archive(fakemail.CONFIG,
                {"Alerts": [ident(1), ident(2)], "Notes": [ident(3)]},
                connect=lambda: mail)
mark = len(mail.calls)
out = gateway.restore(fakemail.CONFIG,
                      {"Alerts": [ident(1), ident(2)], "Notes": [ident(3)]},
                      connect=lambda: mail)
undo = mail.calls[mark:]
check("all three came back", len(out.archived), 3)
check("each to the folder it came from",
      (sorted(mail.ids("Alerts")), mail.ids("Notes")),
      (sorted([ident(1), ident(2)]), [ident(3)]))
check("two moves, one a folder", sum(1 for n, _ in undo if n == "MOVE"), 2)

print("a message not in the archive is still reported, not invented")
mail = box({"Alerts": [], "Archive": []})
out = gateway.restore(fakemail.CONFIG, {"Alerts": [ident(9)]},
                      connect=lambda: mail)
check("it is reported missing", out.missing, (ident(9),))
check("and nothing was moved", mail.commands().count("MOVE"), 0)
check("nor marked", mail.commands().count("FLAG"), 0)

print("a row half in the archive reports both halves")
mail = box({"Alerts": [ident(1)], "Archive": []})
gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]}, connect=lambda: mail)
out = gateway.restore(fakemail.CONFIG, {"Alerts": [ident(1), ident(9)]},
                      connect=lambda: mail)
check("the one there came back", out.archived, (ident(1),))
check("the one that was not is reported missing", out.missing, (ident(9),))

print("an undo is all or nothing")
# The failure window is between one flag and one move, and the move carries
# the whole row -- so either the row comes back or none of it does.  A row
# split between a folder and the archive is the state hardest to reason about.
ids = [ident(i) for i in range(4)]
mail = box({"Alerts": ids[:], "Archive": []})
gateway.archive(fakemail.CONFIG, {"Alerts": ids}, connect=lambda: mail)
mail.fail = raising_on("MOVE", fakemail.refused("refused"))
try:
    gateway.restore(fakemail.CONFIG, {"Alerts": ids}, connect=lambda: mail)
    check("a refused move is reported", "no exception", "MoveFailed")
except gateway.MoveFailed:
    check("a refused move is reported", True)
check("no message reached the folder", mail.ids("Alerts"), [])
check("all four are still in the archive", len(mail.ids("Archive")), 4)
# Marked unread before the move was tried, so a retry finds them as it left
# them rather than having to undo a half-done marking.
check("and all four are unread, ready to be tried again",
      len(mail.unread_in("Archive")), 4)
mail.fail = None


# -- the archive is asked about a fixed number of times -------------------
# Opening the archive was what made this expensive: measured on the real
# account at 6.9 to 16.6 seconds, and it holds everything the account has ever
# kept.  There is no opening now, and a search of it costs 0.96 s whether it
# holds twenty thousand messages or none.
print("confirming a row costs the same requests, whatever its size")


def counts(mail):
    return tuple(mail.commands().count(c)
                 for c in ("FOLDERS", "SEARCH", "MOVE", "FLAG"))


def one_review(size):
    ids = [ident(i) for i in range(size)]
    mail = box({"Alerts": ids[:], "Archive": []})
    gateway.archive(fakemail.CONFIG, {"Alerts": ids}, connect=lambda: mail)
    return mail


for size in (1, 2, 3, 7):
    mail = one_review(size)
    #: One walk, three searches -- the folder, what it let go, the archive --
    #: one move and one flag.  Before this it was a folder opening a message.
    check(f"a row of {size}: one walk, three searches, one move, one flag",
          counts(mail), (1, 3, 1, 1))

#: What it was before, so the change is legible from the suite alone: the
#: archive alone was opened 2, 3, 4 and 8 times for these four sizes.
check("and the count no longer grows with the row",
      len({counts(one_review(n)) for n in (1, 2, 3, 7)}), 1)

print("both groups are asked about in the same request")
# A row can hold messages that moved and messages that had already gone. They
# concern one folder, so they are asked together.
mail = box({"Alerts": [ident(1)], "Archive": [ident(2)]})
out = gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1), ident(2)]},
                      connect=lambda: mail)
check("the moved one is reported archived", out.archived, (ident(1),))
check("the absent one is reported already done", out.already, (ident(2),))
check("and the archive was searched once",
      [args[0] for name, args in mail.calls
       if name == "SEARCH"].count("Archive"), 1)

print("a row that moved nothing is still confirmed, and still marked read")
mail = box({"Alerts": [], "Archive": [ident(3)]})
out = gateway.archive(fakemail.CONFIG, {"Alerts": [ident(3)]},
                      connect=lambda: mail)
check("it is reported already done", out.already, (ident(3),))
check("nothing was moved", mail.commands().count("MOVE"), 0)
# A message found already in the archive is still marked read.  The queue is
# what has not been dealt with, and a reviewed message the account calls new
# is not that -- whether this run moved it or an earlier one did.
check("and it is marked read", mail.commands().count("FLAG"), 1)
check("so an already-archived message ends up read",
      mail.unread_in("Archive"), [])

print("giving up part way is still possible, and sooner")
# The board is required to let an operation give up cleanly when it is forced
# to end.  That check used to sit between messages, each of which cost an
# opening and a search -- about fifteen seconds.  There is one search to be
# before now, so it sits before that.
asked = []


def leaving():
    asked.append(1)
    return True


mail = box({"Alerts": [ident(i) for i in range(5)], "Archive": []})
try:
    gateway.archive(fakemail.CONFIG,
                    {"Alerts": [ident(i) for i in range(5)]},
                    connect=lambda: mail, stop=leaving)
    check("it stops rather than finishing", "no exception", "MoveFailed")
except gateway.MoveFailed as exc:
    check("it stops rather than finishing", "the board is closing" in str(exc))
check("it was asked before the search that confirms", len(asked), 1)
check("what had moved is in the archive", len(mail.ids("Archive")), 5)
check("and nothing was marked read, the confirmation being unfinished",
      mail.commands().count("FLAG"), 0)


print("nothing the account knows is written to the repository")
# This reads git's index, so it sees a file only once it is tracked -- which
# makes it the one check here whose answer changes at the commit.  A suite
# added and run before committing passes it and starts failing after, which is
# how `t_trace.py` shipped tripping it: the tier was green, honestly, and the
# check could not yet see the file.  Run it again after committing.
tracked = subprocess.run(["git", "-C", _REPO, "grep", "-lIE",
                          r"zzsecret|MAIL_IMAP_PASSWORD=|password_command *= *\("],
                         capture_output=True, text=True)
found = [line for line in tracked.stdout.split() if line]
#: The files allowed to name a credential command, each because it must build
#: a configuration to exercise one: this suite, the gateway itself, the account
#: standing in for it, and the trace suite, which constructs one precisely to
#: prove a password cannot reach the trace.
MAY_NAME_ONE = ("t_gateway.py", "gateway.py", "fakemail.py", "t_trace.py")
check("no tracked file holds a password or a literal one to use",
      [f for f in found if not f.endswith(MAY_NAME_ONE)], [])
# The allowance is not a licence to hold a real one.  Whatever these files
# name must be a marker, not a secret.
import re as _re
for f in found:
    body = open(os.path.join(_REPO, f), encoding="utf-8").read()
    for hit in _re.findall(r"password_command *= *\(([^)]*)\)", body):
        check(f"what {f.split('/')[-1]} names is plainly not a real password",
              bool(_re.search(r"printf|echo|false|sh|ZZ|zz|secret", hit)), True)
check("the module holds no password itself",
      subprocess.run(["git", "-C", _REPO, "grep", "-cIE",
                      r"[\"'][A-Za-z0-9+/]{16,}[\"']", "--", "gateway.py"],
                     capture_output=True, text=True).stdout.strip(), "")

# -- filing a row away ----------------------------------------------------
print("archiving confirms both sides")
mail = box({"Alerts": [ident(1), ident(2)], "Notes": [ident(3)], "Archive": []})
out = gateway.archive(fakemail.CONFIG,
                      {"Alerts": [ident(1), ident(2)], "Notes": [ident(3)]},
                      connect=lambda: mail)
check("all three are reported archived", sorted(out.archived),
      sorted(ident(i) for i in (1, 2, 3)))
check("nothing is reported already done", out.already, ())
check("nothing is reported missing", out.missing, ())
check("all three arrived", len(mail.ids("Archive")), 3)
check("both folders were emptied",
      (mail.ids("Alerts"), mail.ids("Notes")), ([], []))
check("one move per folder, not per message", mail.commands().count("MOVE"), 2)
# Two folders: each is searched, each is asked what it let go, and the archive
# is asked once a folder about what landed.
check("six searches for two folders, none of them a message at a time",
      mail.commands().count("SEARCH"), 6)
check("and one flag for the whole row", mail.commands().count("FLAG"), 1)

print("a message left in place is not reported archived")
# The account answers the move and moves nothing: exactly the deviation the
# confirmation exists for.
mail = box({"Alerts": [ident(1)], "Archive": []})
mail.move = lambda items, target: mail.calls.append(("MOVE", (target, 1)))
try:
    gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: mail)
    check("a move that moved nothing is refused", "no error", "MoveFailed")
except gateway.MoveFailed as exc:
    check("a move that moved nothing is refused", "still in Alerts" in str(exc))
check("and the message is where it was", mail.ids("Alerts"), [ident(1)])

print("a message that left and did not arrive is refused")
mail = box({"Alerts": [ident(1)], "Archive": []}, deny=("Archive",))
try:
    gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: mail)
    check("an unconfirmed arrival is refused", "no error", "MoveFailed")
except gateway.MoveFailed as exc:
    check("an unconfirmed arrival is refused", "is not in Archive" in str(exc))

print("a message left unread in the archive is marked read")
mail = box({"Alerts": [], "Archive": [ident(1)]})
out = gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]},
                      connect=lambda: mail)
check("one already there is reported so", out.already, (ident(1),))
check("and marked read all the same", mail.unread_in("Archive"), [])

print("nothing is marked read when the archive cannot be confirmed")
mail = box({"Alerts": [ident(1)], "Archive": []}, deny=("Archive",))
try:
    gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: mail)
except gateway.MoveFailed:
    pass
check("no flag was set", "FLAG" in mail.commands(), False)

print("a message already reviewed is not a failure")
mail = box({"Alerts": [], "Archive": [ident(1)]})
out = gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1)]},
                      connect=lambda: mail)
check("it is reported already done", out.already, (ident(1),))
check("not as archived now", out.archived, ())
check("and it counts as dealt with", out.done, 1)
check("nothing was moved", "MOVE" in mail.commands(), False)

print("a message in neither place is said to be in neither")
mail = box({"Alerts": [], "Archive": []})
out = gateway.archive(fakemail.CONFIG, {"Alerts": [ident(9)]},
                      connect=lambda: mail)
check("it is reported missing", out.missing, (ident(9),))
check("not as archived, and not as already done",
      (out.archived, out.already), ((), ()))
check("and it does not count as dealt with", out.done, 0)

print("a row of many is one move and one confirmation")
mail = box({"Alerts": [ident(i) for i in range(39)], "Archive": []})
out = gateway.archive(fakemail.CONFIG,
                      {"Alerts": [ident(i) for i in range(39)]},
                      connect=lambda: mail)
check("all thirty-nine archived", len(out.archived), 39)
check("in one move", mail.commands().count("MOVE"), 1)
check("found and confirmed in three searches, not seventy-eight",
      mail.commands().count("SEARCH"), 3)
check("and the row of thirty-nine cost what a row of one costs",
      counts(mail), counts(one_review(1)))

print("nothing is deleted, and nothing goes anywhere but the archive")
mail = box({"Alerts": [ident(1), ident(2)], "Archive": [], "Trash": []})
gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1), ident(2)]},
                connect=lambda: mail)
check("no request but the four this module makes",
      sorted(set(mail.commands())), ["FLAG", "FOLDERS", "MOVE", "SEARCH"])
check("every move named the archive",
      {args[0] for name, args in mail.calls if name == "MOVE"}, {"Archive"})
check("and no other folder gained anything", mail.ids("Trash"), [])
# The one flag the board sets anywhere, and only in the archive.
check("the archived messages are marked read", mail.unread_in("Archive"), [])
check("the flag was set in one request for the row",
      mail.commands().count("FLAG"), 1)
check("and only ever in the archive", set(mail.stored_in), {"Archive"})

print("the connection is given a deadline")
check("a bound, so an account that stops answering cannot hang a thread",
      fakemail.CONFIG.timeout > 0, True)

print("undoing a review puts the mail back where it was")
mail = box({"Alerts": [ident(1), ident(2)], "Archive": []})
gateway.archive(fakemail.CONFIG, {"Alerts": [ident(1), ident(2)]},
                connect=lambda: mail)
out = gateway.restore(fakemail.CONFIG, {"Alerts": [ident(1), ident(2)]},
                      connect=lambda: mail)
check("both came back", sorted(mail.ids("Alerts")),
      sorted([ident(1), ident(2)]))
check("the archive is empty again", mail.ids("Archive"), [])
# Unread again, or they would come back to a queue that does not show them.
check("and unread again", sorted(mail.unread_in("Alerts")),
      sorted([ident(1), ident(2)]))
check("both are reported", sorted(out.archived), sorted([ident(1), ident(2)]))
check("a message not in the archive is reported rather than invented",
      gateway.restore(fakemail.CONFIG, {"Alerts": [ident(7)]},
                      connect=lambda: mail).missing, (ident(7),))

# -- the library's exceptions do not leave this module ---------------------
# The board crashed on the real account with `imaplib.IMAP4.abort` from an
# EXAMINE, part way through confirming a seven-message row: neither
# `MoveFailed` nor `GatewayUnreachable`, so the worker's except did not hold
# it and the session ended.  The protocol has changed and the hazard has not:
# whatever happens underneath, a caller of this class sees one of two
# exceptions.
print("a failure underneath leaves as one of the gateway's own exceptions")

from exchangelib.errors import (ErrorAccessDenied, ErrorServerBusy,
                                ErrorTimeoutExpired, TransportError,
                                UnauthorizedError)

#: `ResponseMessageError` is a subclass of `TransportError`, so the order the
#: two are caught in is the whole difference between "the service said no" and
#: "the conversation failed" -- the same trap `abort` and `error` set before.
#: `ErrorTimeoutExpired` is a subclass of `ResponseMessageError`, so a
#: request that never completed reads, by class alone, as the account
#: answering and declining.  A live run against the real account reported a
#: review as refused when nothing had reached anywhere.  It is named here so
#: that reading the hierarchy the easy way fails this suite.
KINDS = (
    ("a timeout", ErrorTimeoutExpired("no answer"), gateway.GatewayUnreachable),
    ("a busy server", ErrorServerBusy("try later"), gateway.GatewayUnreachable),
    ("a refusal", ErrorAccessDenied("access is denied"), gateway.MoveFailed),
    ("a transport failure", TransportError("the line went away"),
     gateway.GatewayUnreachable),
    ("a rejected credential", UnauthorizedError("not authorised"),
     gateway.GatewayUnreachable),
    ("OSError", ConnectionResetError("reset by peer"),
     gateway.GatewayUnreachable),
)


def caught(command, exc, act):
    """What `act` raises when `command` fails underneath it."""
    mail = box({"Alerts": [ident(1), ident(2)], "Archive": []},
               fail=raising_on(command, exc))
    try:
        with fakemail.server(fakemail.CONFIG, mail) as srv:
            act(srv)
    except BaseException as caught_exc:
        return caught_exc
    return None


def an_item(mail, folder=None):
    """One item out of the fake, for the requests that name items."""
    return mail.held[folder or "Alerts"][0]


#: One per request the class makes, with something that exercises it.  A raw
#: library type reaching a caller is the failure being guarded against, so
#: every case asserts the type as well as the message.
VERBS = (
    ("FOLDERS", lambda s: s.numbers("Alerts", [ident(1)])),
    ("SEARCH", lambda s: s.number("Archive", ident(1))),
    ("MOVE", lambda s: s.move("Alerts", [an_item(s.mailbox)], "Archive")),
    ("FLAG", lambda s: s.mark_seen("Alerts", [an_item(s.mailbox)])),
)

for command, act in VERBS:
    for kind, exc, want in KINDS:
        got = caught(command, exc, act)
        check(f"{command} raising {kind} is reported as {want.__name__}",
              type(got), want)
        check(f"{command} raising {kind} names the request",
              command in str(got), True)

# The point of the type check above, stated once on its own: what escaped
# before was the library's, and nothing of the library's may escape now.
from exchangelib.errors import EWSError

for command, act in VERBS:
    for kind, exc, _ in KINDS:
        got = caught(command, exc, act)
        check(f"no library type escapes {command} raising {kind}",
              isinstance(got, (EWSError, OSError)), False)

print("the crash that started this, at the new protocol")
# The shape it actually took: the moves succeed, and the line drops on the
# archive-side confirmation -- the half that used to cost a search a message
# and so held the connection open longest.
seen = []


def drop_on_the_archive_search(name, args):
    if name == "SEARCH" and args and args[0] == "Archive":
        seen.append(name)
        raise TransportError("the connection was closed")


mail = box({"Alerts": [ident(i) for i in range(1, 4)], "Archive": []},
           fail=drop_on_the_archive_search)
try:
    gateway.archive(fakemail.CONFIG,
                    {"Alerts": [ident(1), ident(2), ident(3)]},
                    connect=lambda: mail)
    fell_over = None
except BaseException as exc:
    fell_over = exc
check("the review fails as the account being unreachable",
      type(fell_over), gateway.GatewayUnreachable)
check("and says which request the line dropped on",
      "SEARCH" in str(fell_over), True)
# Half a review is a row to look at again; un-archiving what was confirmed
# to make the report tidy is the one thing that loses mail.
check("what was already moved stays in the archive",
      len(mail.ids("Archive")), 3)
check("and nothing was marked read, the confirmation being unfinished",
      mail.commands().count("FLAG"), 0)

print("an account that is down at the start still says where it tried")
# `__enter__` converts the connection itself, more broadly than the
# per-request helper does, and its message is the one worth reading: a
# review that cannot start is a different fault from one cut off part way.
for kind, exc, _ in KINDS:
    def refuse(exc=exc):
        raise exc
    try:
        with gateway.Server(fakemail.CONFIG, connect=refuse):
            pass
        got = None
    except BaseException as exc_out:
        got = exc_out
    check(f"connecting and raising {kind} is GatewayUnreachable",
          type(got), gateway.GatewayUnreachable)
    check(f"and names where it tried ({kind})",
          fakemail.CONFIG.service in str(got), True)

print("the credential is not asked for until a session opens")
# Building a Server asks nothing of anyone: the command that answers the
# password runs when the session is opened, not when it is described.
asked_for = []
built = gateway.Server(gateway.Config(
    service="https://account.invalid/s", account="me",
    password_command=("sh", "-c", "echo zzpw")))
check("describing a session runs no command", asked_for, [])
check("and the session knows nothing yet", built.mailbox, None)

print("leaving a session asks the account for nothing")
mail = box({"Alerts": [ident(1)], "Archive": []})
with fakemail.server(fakemail.CONFIG, mail) as srv:
    srv.holds("Alerts", ident(1))
    before = len(mail.calls)
check("nothing is sent on the way out", len(mail.calls), before)
check("and the session lets go of what it held",
      (srv.mailbox, srv.archive), (None, None))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
