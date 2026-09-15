"""Reading a directory of maildirs: which folders, which messages, and that
nothing on disk is touched.

Replaces `t_promail`, which tested the read flag the board used to write when
promoting. The board writes nothing to a mail store now -- reviewing moves the
message on the server -- so eighteen of that suite's thirty checks were about
behaviour that no longer exists. The twelve that remain are here, and the
census that proved "only the promoted messages were renamed" now proves the
stronger thing: that no file changed at all.

Synthetic mail only: a copy of the committed mailbox, and throwaway ones built
here.
"""
import mailbox
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import mail
import mailfixture as F

ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


def where_is(folder_path, key):
    """The file a maildir key names, relative to its folder."""
    for area in ("new", "cur"):
        here = os.path.join(folder_path, area)
        if not os.path.isdir(here):
            continue
        for name in os.listdir(here):
            if name.split(":")[0] == key:
                return os.path.join(area, name)
    return None


# -- which folder a message came from, and its key ------------------------
print("a message knows where it was read from")
box = F.build({"Alerts": [("one", "body", {}), ("two", "body", {})],
               "Reviews": [("three", "body", {})]})
cfg = mail.Config(box, ("Alerts", "Reviews"))
found = mail.read(cfg)
check("the folder is recorded", sorted({m.folder for m in found}),
      ["Alerts", "Reviews"])
check("no message claims an empty folder", any(m.folder == "" for m in found),
      False)
check("each folder's own messages are attributed to it",
      sum(1 for m in found if m.folder == "Alerts"), 2)
check("every message carries a key", all(m.key for m in found))
check("the key addresses the message on disk",
      all(where_is(mail._folder_path(cfg, m.folder), m.key) for m in found))

# -- a message with no identity of its own --------------------------------
print("a message with no Message-ID")
box = F.build({"Alerts": [("one", "body", {}), ("two", "body", {})]})
here = os.path.join(box, "Alerts", "new")
target = sorted(os.listdir(here))[0]
full = os.path.join(here, target)
raw = open(full, "rb").read()
open(full, "wb").write(b"\n".join(
    l for l in raw.split(b"\n") if not l.lower().startswith(b"message-id:")))
found = mail.read(mail.Config(box, ("Alerts",)))
nameless = [m for m in found if m.ident.startswith("<key:")]
check("it falls back to its maildir key", len(nameless), 1)
check("and is still addressable by that key",
      bool(nameless) and nameless[0].key == target)

# -- the folder is the queue ---------------------------------------------
print("the queue is what has not been dealt with")
box = F.copy()
whole = len(mail.read(mail.Config(box, F.FOLDERS)))
check("the committed mailbox has unread messages", whole > 1, True)
was_read = sum(1 for m in mail.read(mail.Config(box, F.FOLDERS)) if m.seen)
one = mail.read(mail.Config(box, F.FOLDERS))[0]
folder = mail._folder_path(mail.Config(box, F.FOLDERS), one.folder)
was_at = where_is(folder, one.key)
os.rename(os.path.join(folder, was_at),
          os.path.join(folder, "cur", f"{one.key}:2,S"))
# Read elsewhere, and still outstanding.  This asserted the opposite while
# the queue was the unread messages: the message vanished from the board and
# stayed in the account's inbox, dealt with by nobody.  Filing is what takes
# a message out of the queue, and a mail client marking it read is not that.
after = mail.read(mail.Config(box, F.FOLDERS))
check("a message flagged read by another program is still there",
      len(after), whole)
check("and says it was read",
      sum(1 for m in after if m.seen), was_read + 1)

box = F.copy()
folder = os.path.join(box, "Jenkins")
first = sorted(f for f in os.listdir(os.path.join(folder, "new"))
               if not f.startswith("."))[0]
shutil.move(os.path.join(folder, "new", first),
            os.path.join(folder, "cur", first))
check("an unflagged message in cur/ counts as unread",
      len(mail.read(mail.Config(box, F.FOLDERS))), whole)

# -- a thread does not care which of it was read --------------------------
print("read and unread fold together")
box = F.build({"Alerts": [
    ("a thread", "body", {"Message-ID": "<t1@x.invalid>", "seen": True,
                          "minutes": 1}),
    ("Re: a thread", "body", {"Message-ID": "<t2@x.invalid>",
                              "In-Reply-To": "<t1@x.invalid>", "seen": True,
                              "minutes": 2}),
    ("Re: a thread", "body", {"Message-ID": "<t3@x.invalid>",
                              "In-Reply-To": "<t2@x.invalid>", "minutes": 3}),
]})
found = mail.read(mail.Config(box, ("Alerts",)))
check("all three are read off the folder", len(found), 3)
check("two of them were already read", sum(1 for m in found if m.seen), 2)
ths = mail.threads(found)
check("they are one thread", len(ths), 1)
check("standing for all three, not for the unread one",
      ths[0].count, 3)
check("and the newest is what the row would show",
      ths[0].newest.ident, "<t3@x.invalid>")

# -- the newest message decides what the thread says about its issue ------
print("a thread reports its newest message's issue state")
HOST = "https://track.example.invalid"
def note(key, struck, mid, answers=None, minute=0):
    style = "color:#676E75;" + (" text-decoration: line-through;" if struck else "")
    html = (f'<html><body><a style="{style}" href="{HOST}/issue/{key}">{key}</a>'
            f'<a style="color:#1466c6;" href="{HOST}/issue/{key}">the summary</a>'
            f'</body></html>')
    h = {"Message-ID": mid, mail.ISSUE_HEADER: key, "minutes": minute}
    if answers: h["In-Reply-To"] = answers
    return ("an issue moves", html, h)

def issue_box(entries):
    root = tempfile.mkdtemp()
    path = os.path.join(root, "mail_folders")
    os.makedirs(path)
    box = mailbox.Maildir(os.path.join(path, "Alerts"), create=True)
    from email.message import EmailMessage
    for subject, html, headers in entries:
        m = EmailMessage()
        m["From"] = "tracker@example.invalid"
        m["Subject"] = subject
        m["Date"] = f"Tue, 08 Sep 2026 08:{headers.get('minutes', 0):02d}:00 +0000"
        m["Message-ID"] = headers["Message-ID"]
        m[mail.ISSUE_HEADER] = headers[mail.ISSUE_HEADER]
        if headers.get("In-Reply-To"):
            m["In-Reply-To"] = headers["In-Reply-To"]
            m["References"] = headers["In-Reply-To"]
        m.set_content("the plain part")
        m.add_alternative(html, subtype="html")
        box.add(mailbox.MaildirMessage(m))
    box.flush()
    return mail.Config(path, ("Alerts",))

# Older messages say unfinished, the newest says finished.
cfg2 = issue_box([
    note("ZZA-1", False, "<a1@x.invalid>", minute=1),
    note("ZZA-1", False, "<a2@x.invalid>", answers="<a1@x.invalid>", minute=2),
    note("ZZA-1", True, "<a3@x.invalid>", answers="<a2@x.invalid>", minute=3),
])
ths = mail.threads(mail.read(cfg2))
check("the three are one thread", len(ths), 1)
check("its newest says the issue is finished", ths[0].newest.issue_done, True)
check("even though its older messages do not",
      [m.issue_done for m in ths[0].messages], [False, False, True])

# And the reverse: reopened, so the newest says unfinished.
cfg2 = issue_box([
    note("ZZA-2", True, "<b1@x.invalid>", minute=1),
    note("ZZA-2", False, "<b2@x.invalid>", answers="<b1@x.invalid>", minute=2),
])
ths = mail.threads(mail.read(cfg2))
check("a thread whose newest says unfinished reports unfinished",
      ths[0].newest.issue_done, False)

# -- and nothing at all is written ----------------------------------------
print("reading writes nothing")
box = F.copy()
before = F.census(box)
found = mail.read(mail.Config(box, F.FOLDERS))
mail.threads(found)
for m in found:                       # touch every body, as a view would
    _ = m.text
check("every file is byte-identical afterwards", F.census(box), before)
check("no file was added or removed", set(F.census(box)), set(before))
check("the module offers no way to write to a mailbox",
      [n for n in dir(mail)
       if n in ("mark_read", "mark_unread", "_reflag", "MailboxUnwritable")],
      [])
check("and holds no rename of its own",
      "os.rename" in open(mail.__file__).read(), False)

# -- the committed mailbox is never the one read --------------------------
print("the committed mailbox is left alone")
fixture_before = F.census(F.FIXTURE)
mail.read(mail.Config(F.copy(), F.FOLDERS))
check("it is unchanged by anything here", F.census(F.FIXTURE), fixture_before)

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
