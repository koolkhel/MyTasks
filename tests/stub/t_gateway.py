"""The gateway client: folder names, one fetch per folder, one move per row.

No network and no credentials: the connection is substituted by a server that
records every request (`tests/fakeimap.py`), so these checks are about the
requests made, not only the outcome. That matters here more than anywhere else
in the board -- reviewing is the one action it cannot undo by itself, and the
cost of getting the request shape wrong is a folder of forty messages costing
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
import fakeimap
import gateway

ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def ident(n):
    return f"<zz{n}@example.invalid>"


# -- folder names ---------------------------------------------------------
# The library hands back the encoded form and has no codec for it, so a folder
# whose name is not ASCII cannot be selected by the name a person sees.
print("a folder's name survives the round trip")
for name in ("Archive", "Gitlab", "Черновики", "Zwei&Drei", "Å Å", "日本"):
    check(f"{name!r} round-trips",
          gateway.utf7_decode(gateway.utf7_encode(name)), name)
check("a non-ASCII name is actually encoded, not passed through",
      gateway.utf7_encode("Черновики"), "&BCcENQRABD0EPgQyBDgEOgQ4-")
check("an ASCII name is passed through untouched",
      gateway.utf7_encode("Archive"), "Archive")
check("an ampersand is escaped", gateway.utf7_encode("A&B"), "A&-B")
check("and comes back", gateway.utf7_decode("A&-B"), "A&B")

# -- numbers are asked for by the row, not by the folder -------------------
# The gateway answers a whole-folder header fetch by fetching every message
# from Exchange: 45 s for a folder of 291, against 0.14 s for the same
# folder's flags. So a row asks about its own messages and nothing else.
print("a row's numbers are asked for one identity at a time")
imap = fakeimap.FakeIMAP({"Alerts": [ident(i) for i in range(40)],
                          "Archive": []})
wanted = [ident(i) for i in range(8)]
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    found = srv.numbers("Alerts", wanted)
check("each of the row's identities maps to a number",
      sorted(found), sorted(wanted))
check("and nothing else in the folder was asked about", len(found), 8)
check("the numbers are the server's own",
      set(found.values()) <= set(imap.folders["Alerts"]), True)
check("one search a message", imap.commands().count("SEARCH"), 8)
check("the folder was opened once, not once a message",
      imap.commands().count("SELECT"), 1)
check("and nothing was fetched", "FETCH" in imap.commands(), False)
check("the folder was opened read-only",
      [args[1] for name, args in imap.calls if name == "SELECT"], [True])
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    check("an identity the folder does not hold is simply absent",
          srv.numbers("Alerts", [ident(999)]), {})
    check("and asking about nothing asks nothing",
          srv.numbers("Alerts", []), {})

print("a folder that is not there is reported")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)]})
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    try:
        srv.numbers("Nope", [ident(1)])
        check("an absent folder is refused", "no error raised", "MoveFailed")
    except gateway.MoveFailed as exc:
        check("an absent folder is refused", "Nope" in str(exc))

print("what a folder still holds is asked by number")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1), ident(2)], "Archive": []})
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    numbers = srv.numbers("Alerts", [ident(1), ident(2)])
    check("both are there", len(srv.present("Alerts", numbers.values())), 2)
    srv.move("Alerts", [numbers[ident(1)]], "Archive")
    check("and one of them is not, once it has moved",
          srv.present("Alerts", numbers.values()), [numbers[ident(2)]])
    check("asking about no numbers asks nothing",
          srv.present("Alerts", []), [])
check("proving absence took one fetch, not a search a message",
      imap.commands().count("FETCH"), 2)

# -- one move covers a row ------------------------------------------------
print("a row of many messages is moved in one request")
imap = fakeimap.FakeIMAP({"Alerts": [ident(i) for i in range(12)],
                          "Archive": []})
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    numbers = srv.numbers("Alerts", [ident(i) for i in range(12)])
    srv.move("Alerts", list(numbers.values()), "Archive")
check("one move, not twelve", imap.commands().count("MOVE"), 1)
check("all twelve arrived", len(imap.ids("Archive")), 12)
check("and none stayed behind", imap.ids("Alerts"), [])
check("the same messages arrived, not copies of one",
      imap.ids("Archive"), sorted(ident(i) for i in range(12)))

print("moving nothing asks nothing")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)], "Archive": []})
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    srv.move("Alerts", [], "Archive")
check("no request was made at all", imap.commands(), ["LOGIN", "LOGOUT"])

print("a refused move is reported, not passed over")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)], "Archive": []},
                         fail=lambda name, args:
                             ("NO", [b"over quota"]) if name == "MOVE" else None)
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    numbers = srv.numbers("Alerts", [ident(1)])
    try:
        srv.move("Alerts", list(numbers.values()), "Archive")
        check("the refusal is raised", "no error raised", "MoveFailed")
    except gateway.MoveFailed as exc:
        check("the refusal is raised", "over quota" in str(exc))
check("and the message did not move", imap.ids("Alerts"), [ident(1)])

# -- confirming where a message went --------------------------------------
print("a folder can be asked whether it holds one message")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1), ident(2)], "Archive": [ident(3)]})
with fakeimap.server(fakeimap.CONFIG, imap) as srv:
    check("present is present", srv.holds("Archive", ident(3)))
    check("absent is absent", srv.holds("Archive", ident(1)), False)
    check("asking does not fetch anything", "FETCH" in imap.commands(), False)

# -- the credential -------------------------------------------------------
print("the credential is asked for at the moment it is needed")
cfg = gateway.Config(host="gateway.invalid", port=1143, user="me",
                     password_command=("printf", "zzsecret"))
check("the command answers it", gateway.password(cfg), "zzsecret")
try:
    gateway.password(gateway.Config(host="h", port=1, user="u"))
    check("a missing command is refused", "no error raised", "GatewayUnreachable")
except gateway.GatewayUnreachable:
    check("a missing command is refused", True)
try:
    gateway.password(gateway.Config(host="h", port=1, user="u",
                                    password_command=("false",)))
    check("a failing command is refused", "no error raised", "GatewayUnreachable")
except gateway.GatewayUnreachable:
    check("a failing command is refused", True)

print("the credential command cannot reach the terminal the board owns")
check("its input is closed, so it cannot wait on a person",
      gateway.password(gateway.Config(
          host="h", port=1, user="u",
          password_command=("sh", "-c", "test -t 0 && echo tty || echo notty"))),
      "notty")
check("a command that reads its input gets nothing and returns",
      gateway.password(gateway.Config(
          host="h", port=1, user="u",
          password_command=("sh", "-c", "cat; echo zzread"))),
      "zzread")

print("nothing the gateway knows is written to the repository")
tracked = subprocess.run(["git", "-C", _REPO, "grep", "-lIE",
                          r"zzsecret|MAIL_IMAP_PASSWORD=|password_command *= *\("],
                         capture_output=True, text=True)
found = [line for line in tracked.stdout.split() if line]
check("no tracked file holds a password or a literal one to use",
      [f for f in found if not f.endswith(("t_gateway.py", "gateway.py",
                                           "fakeimap.py"))], [])
check("the module holds no password itself",
      subprocess.run(["git", "-C", _REPO, "grep", "-cIE",
                      r"[\"'][A-Za-z0-9+/]{16,}[\"']", "--", "gateway.py"],
                     capture_output=True, text=True).stdout.strip(), "")

# -- filing a row away ----------------------------------------------------
print("archiving confirms both sides")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1), ident(2)],
                          "Notes": [ident(3)], "Archive": []})
out = gateway.archive(fakeimap.CONFIG,
                      {"Alerts": [ident(1), ident(2)], "Notes": [ident(3)]},
                      connect=lambda: imap)
check("all three are reported archived", sorted(out.archived),
      sorted(ident(i) for i in (1, 2, 3)))
check("nothing is reported already done", out.already, ())
check("nothing is reported missing", out.missing, ())
check("all three arrived", len(imap.ids("Archive")), 3)
check("both folders were emptied",
      (imap.ids("Alerts"), imap.ids("Notes")), ([], []))
check("one move per folder, not per message", imap.commands().count("MOVE"), 2)
check("absence was proved with one fetch a folder",
      imap.commands().count("FETCH"), 2)
# Three to find them, three to confirm they arrived. The finding half is
# bounded by the row; the confirming half is what it costs to know.
check("and identities were searched for, never fetched wholesale",
      imap.commands().count("SEARCH"), 6)

print("a message left in place is not reported archived")
# The gateway answers OK and moves nothing: exactly the deviation the
# confirmation exists for.
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)], "Archive": []})
imap._uid_move = lambda uids, mailbox: ("OK", [b"moved"])
try:
    gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: imap)
    check("a move that moved nothing is refused", "no error", "MoveFailed")
except gateway.MoveFailed as exc:
    check("a move that moved nothing is refused", "still in Alerts" in str(exc))
check("and the message is where it was", imap.ids("Alerts"), [ident(1)])

print("a message that left and did not arrive is refused")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)], "Archive": []},
                         deny=("Archive",))
try:
    gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: imap)
    check("an unconfirmed arrival is refused", "no error", "MoveFailed")
except gateway.MoveFailed as exc:
    check("an unconfirmed arrival is refused", "is not in Archive" in str(exc))

print("a message left unread in the archive is marked read")
imap = fakeimap.FakeIMAP({"Alerts": [], "Archive": [ident(1)]})
out = gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1)]},
                      connect=lambda: imap)
check("one already there is reported so", out.already, (ident(1),))
check("and marked read all the same", imap.unread_in("Archive"), [])

print("nothing is marked read when the archive cannot be confirmed")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1)], "Archive": []},
                         deny=("Archive",))
try:
    gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1)]},
                    connect=lambda: imap)
except gateway.MoveFailed:
    pass
check("no flag was set", "STORE" in imap.commands(), False)

print("a message already reviewed is not a failure")
imap = fakeimap.FakeIMAP({"Alerts": [], "Archive": [ident(1)]})
out = gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1)]},
                      connect=lambda: imap)
check("it is reported already done", out.already, (ident(1),))
check("not as archived now", out.archived, ())
check("and it counts as dealt with", out.done, 1)
check("nothing was moved", "MOVE" in imap.commands(), False)

print("a message in neither place is said to be in neither")
imap = fakeimap.FakeIMAP({"Alerts": [], "Archive": []})
out = gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(9)]},
                      connect=lambda: imap)
check("it is reported missing", out.missing, (ident(9),))
check("not as archived, and not as already done",
      (out.archived, out.already), ((), ()))
check("and it does not count as dealt with", out.done, 0)

print("a row of many is one move and a confirmation each")
imap = fakeimap.FakeIMAP({"Alerts": [ident(i) for i in range(39)],
                          "Archive": []})
out = gateway.archive(fakeimap.CONFIG,
                      {"Alerts": [ident(i) for i in range(39)]},
                      connect=lambda: imap)
check("all thirty-nine archived", len(out.archived), 39)
check("in one move", imap.commands().count("MOVE"), 1)
check("found by a search each and confirmed by a search each",
      imap.commands().count("SEARCH"), 78)
check("and the folder was never fetched wholesale",
      imap.commands().count("FETCH"), 1)

print("nothing is deleted, and nothing goes anywhere but the archive")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1), ident(2)], "Archive": [],
                          "Trash": []})
gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1), ident(2)]},
                connect=lambda: imap)
check("nothing was deleted or expunged",
      [c for c in imap.commands() if c in ("EXPUNGE", "DELETE")], [])
check("every move named the archive",
      {args[1].strip('"') for name, args in imap.calls if name == "MOVE"},
      {"Archive"})
check("and no other folder gained anything", imap.ids("Trash"), [])
# The one flag the board sets anywhere, and only in the archive.
check("the archived messages are marked read",
      imap.unread_in("Archive"), [])
check("the flag was set in one request for the row",
      imap.commands().count("STORE"), 1)
check("and only ever in the archive", imap.stored_in, ["Archive"])

print("a confirmation can be given up part way")
imap = fakeimap.FakeIMAP({"Alerts": [ident(i) for i in range(4)],
                          "Archive": []})
asked = []
try:
    gateway.archive(fakeimap.CONFIG,
                    {"Alerts": [ident(i) for i in range(4)]},
                    connect=lambda: imap,
                    stop=lambda: bool(asked.append(1)) or len(asked) > 2)
    check("it stops rather than finishing", "no error raised", "MoveFailed")
except gateway.MoveFailed as exc:
    check("it stops rather than finishing", "the board is closing" in str(exc))
check("it was asked between messages, not once", len(asked) >= 3, True)
check("what had already moved is in the archive", len(imap.ids("Archive")), 4)
check("and nothing was marked read, the confirmation being unfinished",
      imap.commands().count("STORE"), 0)

print("the connection is given a deadline")
check("a bound, so a gateway that stops answering cannot hang a thread",
      fakeimap.CONFIG.timeout > 0, True)

print("undoing a review puts the mail back where it was")
imap = fakeimap.FakeIMAP({"Alerts": [ident(1), ident(2)], "Archive": []})
gateway.archive(fakeimap.CONFIG, {"Alerts": [ident(1), ident(2)]},
                connect=lambda: imap)
out = gateway.restore(fakeimap.CONFIG, {"Alerts": [ident(1), ident(2)]},
                      connect=lambda: imap)
check("both came back", sorted(imap.ids("Alerts")),
      sorted([ident(1), ident(2)]))
check("the archive is empty again", imap.ids("Archive"), [])
# Unread again, or they would come back to a queue that does not show them.
check("and unread again", sorted(imap.unread_in("Alerts")),
      sorted([ident(1), ident(2)]))
check("both are reported", sorted(out.archived), sorted([ident(1), ident(2)]))
check("a message not in the archive is reported rather than invented",
      gateway.restore(fakeimap.CONFIG, {"Alerts": [ident(7)]},
                      connect=lambda: imap).missing, (ident(7),))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
