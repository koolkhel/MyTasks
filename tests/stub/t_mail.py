"""Reading a maildir, and grouping into threads.  Synthetic mail only."""
import mailbox, os, shutil, sys, tempfile
from email.message import EmailMessage
from datetime import datetime, timezone, timedelta
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import mail

HERE = os.path.dirname(os.path.abspath(__file__))
# A copy, never the fixture itself.  The board can now write to a mailbox --
# promoting marks a thread read -- so a suite that points it at the shared
# sample can quietly rewrite the thing every other mail suite measures
# against.  It happened once; copying is what makes it impossible.
_FIXTURE = _os.path.join(_TESTS, "fixtures", "sample_mail")
SAMPLE = os.path.join(tempfile.mkdtemp(prefix="fixture."), "sample_mail")
shutil.copytree(_FIXTURE, SAMPLE)
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def build(messages, root=None):
    """A throwaway maildir from (subject, extra headers, body) tuples."""
    root = root or tempfile.mkdtemp()
    path = os.path.join(root, "mail")
    if os.path.exists(path): shutil.rmtree(path)
    box = mailbox.Maildir(path, create=True)
    for i, (subject, headers, body) in enumerate(messages):
        m = EmailMessage()
        m["From"] = headers.pop("From", "someone@example.invalid")
        m["Subject"] = subject
        m["Date"] = headers.pop("Date",
            (datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc)
             + timedelta(minutes=i * 10)).strftime("%a, %d %b %Y %H:%M:%S %z"))
        for k, v in headers.items():
            if v is not None: m[k] = v
        m.set_content(body)
        box.add(mailbox.MaildirMessage(m))
    box.flush()
    return mail.Config(path)

# ------------------------------------------------------------- reading
print("reading the sample maildir")
cfg = mail.Config(SAMPLE)

def snapshot(root):
    """Every file in the maildir with its name, size and mtime."""
    out = {}
    for sub in ("new", "cur", "tmp"):
        d = os.path.join(root, sub)
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            # Dotfiles are not messages: a maildir needs cur/ and tmp/ to
            # exist, git keeps no empty directory, so each holds a marker.
            # The library skips them when reading and so does this, which
            # keeps the count below a count of mail.
            if f.startswith("."):
                continue
            st = os.stat(os.path.join(d, f))
            out[f"{sub}/{f}"] = (st.st_size, st.st_mtime_ns)
    return out

before = snapshot(SAMPLE)
msgs = mail.read(cfg)
after = snapshot(SAMPLE)
# 15 files, one of them built with seen=True and one unparseable: the
# board reads unread mail only, so 14 is the whole of the queue.
check("every unread message is found", len(msgs), 14)
check("each has a sender", all(m.sender for m in msgs), True)
check("each has a subject", all(m.subject for m in msgs), True)
check("each has an identity", all(m.ident for m in msgs), True)
check("each has a date", all(m.when.year == 2026 for m in msgs), True)
check("the text holds subject and body",
      all(m.subject.split(":")[0][:6] in m.text for m in msgs), True)
# Name, size and modification time of every file, before and after.  A
# maildir records "seen" by RENAMING the file, so a comparison of names is
# what catches a library helpfully marking mail read.
check("reading changed no file: no rename, no move, no touch", after, before)
check("and the same number of files", len(after), 15)

print("awkward messages")
c = build([
    ("=?utf-8?B?0J/RgNC40LLQtdGCLCDQvNC40YA=?=",
     {"From": "=?utf-8?B?0J/QtdGC0YDQvtCy?= <p@example.invalid>"}, "body"),
    ("", {}, "no subject at all"),
    ("no date", {"Date": None}, "body"),
    ("no identity", {"Message-ID": None}, "body"),
])
got = mail.read(c)
check("all four are read", len(got), 4)
subs = {m.subject for m in got}
check("an encoded subject is decoded", "Привет, мир" in subs, True)
check("an encoded sender is decoded",
      any("Петров" in m.sender for m in got), True)
check("an empty subject is kept, not dropped", "" in subs, True)
byname = {m.subject: m for m in got}
check("a message with no date sorts oldest",
      byname["no date"].when.year, 1970)
check("a message with no identity still gets one",
      bool(byname["no identity"].ident), True)
check("and it is unique", len({m.ident for m in got}), 4)

print("messages that are HTML")
HTML = ("<html><body><h2>Merge request !47 approved</h2>"
        "<p>Alexey approved <a href='https://git.x.invalid/p/api/-/merge_requests/47'>"
        "p/api!47</a>: <strong>raise the timeout</strong></p>"
        "<ul><li>one.py</li><li>two.py</li></ul>"
        "<script>var x=1;</script><style>p{margin:0}</style></body></html>")
import mailbox as _m
from email.message import EmailMessage as _E
root = tempfile.mkdtemp(); path = os.path.join(root, "mail")
box = _m.Maildir(path, create=True)
def add_html(subject, html, plain=None, mid=None):
    m = _E(); m["From"] = "gitlab@x.invalid"; m["Subject"] = subject
    m["Message-ID"] = mid or f"<{subject}@x.invalid>"
    if plain is None:
        m.set_content(html, subtype="html")
    else:
        m.set_content(plain); m.add_alternative(html, subtype="html")
    box.add(_m.MaildirMessage(m))
add_html("html only", HTML)
add_html("both parts", HTML, plain="the plain one")
add_html("broken html", "<p>unclosed <b>bits <a href='https://x.invalid/a'>link")
box.flush()
got = {m.subject: m for m in mail.read(mail.Config(path))}
check("an HTML-only message is readable, not empty",
      "Merge request !47 approved" in got["html only"].body, True)
check("its script and style are not shown",
      ("var x=1" in got["html only"].body,
       "margin" in got["html only"].body), (False, False))
check("a list reads as a list", "- one.py" in got["html only"].body, True)
check("where there is a plain part, that is preferred",
      got["both parts"].body, "the plain one")
check("the address in the markup survives",
      "https://git.x.invalid/p/api/-/merge_requests/47" in got["html only"].text, True)
check("even though the words never contained it",
      "https://git.x.invalid" in "Alexey approved p/api!47", False)
check("malformed HTML still yields a row",
      "unclosed" in got["broken html"].body, True)
check("and its address too",
      "https://x.invalid/a" in got["broken html"].text, True)

print("failures become the one type")
for name, path in [("a path that is not there", "/nonexistent/mailbox"),
                   ("a path that is not a maildir", tempfile.mkdtemp())]:
    try:
        mail.read(mail.Config(path))
        check(name, False, True)
    except mail.MailboxUnreadable:
        check(name, True, True)
    except Exception as exc:
        check(f"{name} raises only MailboxUnreadable", type(exc).__name__, "MailboxUnreadable")
check("no mailbox configured reads nothing", mail.read(mail.Config("")), [])

print("configuration")
import os as _os
_os.environ.pop("MAIL_MAILDIR", None)
check("no path set -> no mailbox", mail.load_config("/nonexistent"), None)
_os.environ["MAIL_MAILDIR"] = "~/somewhere"
c2 = mail.load_config("/nonexistent")
check("a path is expanded", c2.path.startswith(_os.path.expanduser("~")), True)
_os.environ.pop("MAIL_MAILDIR", None)

# ------------------------------------------------------------- threading
print("folders")
import mailbox as _mb
root = tempfile.mkdtemp(); path = os.path.join(root, "mail")
box = _mb.Maildir(path, create=True)
def put(target, subject):
    m = EmailMessage(); m["From"] = "s@x.invalid"; m["Subject"] = subject
    m["Message-ID"] = f"<{subject}@x.invalid>"; m.set_content("body")
    target.add(_mb.MaildirMessage(m))
put(box, "in the inbox")
for name in ("Alerts", "Reviews", "Ignored"):
    put(box.add_folder(name), f"in {name}")
box.flush()
subs = lambda cfg: sorted(m.subject for m in mail.read(cfg))
check("with no folders named, the mailbox's own inbox alone",
      subs(mail.Config(path)), ["in the inbox"])
check("named folders are read, and only those",
      subs(mail.Config(path, ("Alerts", "Reviews"))),
      ["in Alerts", "in Reviews", "in the inbox"])
check("a folder not named is not read",
      "in Ignored" in subs(mail.Config(path, ("Alerts",))), False)
try:
    mail.read(mail.Config(path, ("Nope",)))
    check("a folder that does not exist is reported", False, True)
except mail.MailboxUnreadable as exc:
    check("a folder that does not exist is reported, by name", "Nope" in str(exc), True)

print("threads")
ths = mail.threads(mail.read(cfg))
check("the sample's eight unread threads", len(ths), 8)
check("the three runs are found",
      sorted(t.count for t in ths if t.count > 1), [2, 3, 4])
check("newest thread first",
      [t.newest.when for t in ths] == sorted((t.newest.when for t in ths), reverse=True), True)
check("each thread's messages are oldest first",
      all(list(t.messages) == sorted(t.messages, key=lambda m: m.when) for t in ths), True)
check("newest is the last", all(t.newest is t.messages[-1] for t in ths), True)

print("what must NOT be merged")
c = build([("[weekly] digest", {"Message-ID": "<a@x.invalid>"}, "one"),
           ("[weekly] digest", {"Message-ID": "<b@x.invalid>"}, "two")])
check("two messages sharing a subject but answering nothing stay apart",
      len(mail.threads(mail.read(c))), 2)

print("chains")
c = build([("orphan", {"Message-ID": "<o@x.invalid>",
                       "In-Reply-To": "<absent@x.invalid>"}, "body")])
check("a message whose parent is absent is its own thread",
      len(mail.threads(mail.read(c))), 1)
c = build([("loop a", {"Message-ID": "<la@x.invalid>", "In-Reply-To": "<lb@x.invalid>"}, "a"),
           ("loop b", {"Message-ID": "<lb@x.invalid>", "In-Reply-To": "<la@x.invalid>"}, "b")])
t = mail.threads(mail.read(c))
check("a circular chain does not spin, and yields rows", len(t) >= 1, True)
check("and holds both messages", sum(x.count for x in t), 2)
c = build([("root", {"Message-ID": "<r@x.invalid>"}, "r"),
           ("mid", {"Message-ID": "<m@x.invalid>", "In-Reply-To": "<r@x.invalid>"}, "m"),
           ("leaf", {"Message-ID": "<l@x.invalid>", "In-Reply-To": "<m@x.invalid>"}, "l")])
check("a chain of three is walked to its start", len(mail.threads(mail.read(c))), 1)
check("and the thread holds all three", mail.threads(mail.read(c))[0].count, 3)

print()
print(f"{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
