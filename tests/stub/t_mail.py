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
sys.path.insert(0, _TESTS)      # the shared support beside the suites
sys.path.insert(0, _REPO)
from parts import run_parts
import mail
import mailfixture as F

HERE = os.path.dirname(os.path.abspath(__file__))
# A copy, never the committed mailbox: the board can move messages out of a
# mailbox now, so a suite reading the shared one in place could rewrite what
# every other mail suite measures against.  It happened once with a read
# flag, when the board could not yet move anything at all.
SAMPLE = F.copy()
FOLDERS = F.FOLDERS
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

#: The one folder `build` puts its messages in.  The board reads folders it
#: is named, so a mailbox with no folder in it would read as empty.
FEED = "Feed"

def build(messages, root=None):
    """A throwaway mailbox from (subject, extra headers, body) tuples.

    One folder, named, inside a container -- which is the shape the board
    reads.  A bare maildir is not one: it would be read as no folders named
    and answer nothing.
    """
    root = root or tempfile.mkdtemp()
    path = os.path.join(root, "mail_folders")
    if os.path.exists(path): shutil.rmtree(path)
    os.makedirs(path)
    box = mailbox.Maildir(os.path.join(path, FEED), create=True)
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
    return mail.Config(path, (FEED,))

# ------------------------------------------------------------- reading


def the_mailbox():
    """Everything this suite checks, as the one part it is made of.

    It ran at import before, which meant that reading the file ran
    it -- and in a process that had already read another suite, ran
    it against loaders that suite had blanked.
    """
    print("reading the sample maildir")
    cfg = mail.Config(SAMPLE, FOLDERS)

    def snapshot(root):
        """Every message file in every folder, with its name, size and mtime.

        Walks the folders, because the mailbox is a directory holding one
        maildir each rather than a maildir itself -- looking for new/ and cur/
        at the root found nothing and reported no files at all.
        """
        out = {}
        for folder in sorted(os.listdir(root)):
          for sub in ("new", "cur", "tmp"):
            d = os.path.join(root, folder, sub)
            if not os.path.isdir(d): continue
            for f in os.listdir(d):
                # Dotfiles are not messages: a maildir needs cur/ and tmp/ to
                # exist, git keeps no empty directory, so each holds a marker.
                # The library skips them when reading and so does this, which
                # keeps the count below a count of mail.
                if f.startswith("."):
                    continue
                st = os.stat(os.path.join(d, f))
                out[f"{folder}/{sub}/{f}"] = (st.st_size, st.st_mtime_ns)
        return out

    before = snapshot(SAMPLE)
    msgs = mail.read(cfg)
    after = snapshot(SAMPLE)
    # 19 messages across three folders, one of them built with seen=True. All 19
    # are the queue: filing is what takes a message out of it, and being read is
    # not filing.  This read 18 while the read one was skipped.
    check("every message the folders hold is found", len(msgs), 19)
    check("including the one already marked read",
          sum(1 for m in msgs if m.seen), 1)
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
    check("and the same number of files", len(after), 19)

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
    root = tempfile.mkdtemp(); path = os.path.join(root, "mail_folders")
    os.makedirs(path)
    box = _m.Maildir(os.path.join(path, FEED), create=True)
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
    got = {m.subject: m for m in mail.read(mail.Config(path, (FEED,)))}
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
            mail.read(mail.Config(path, (FEED,)))
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
    # A container of maildirs, not a maildir: the board reads the folders it is
    # named and never the directory holding them.
    root = tempfile.mkdtemp(); path = os.path.join(root, "mail_folders")
    os.makedirs(path)
    def put(target, subject):
        m = EmailMessage(); m["From"] = "s@x.invalid"; m["Subject"] = subject
        m["Message-ID"] = f"<{subject}@x.invalid>"; m.set_content("body")
        target.add(_mb.MaildirMessage(m))
    for name in ("Alerts", "Reviews", "Ignored"):
        put(mailbox.Maildir(os.path.join(path, name), create=True), f"in {name}")
    subs = lambda cfg: sorted(m.subject for m in mail.read(cfg))
    check("with no folder named, nothing is read",
          subs(mail.Config(path)), [])
    check("named folders are read, and only those",
          subs(mail.Config(path, ("Alerts", "Reviews"))),
          ["in Alerts", "in Reviews"])
    check("a folder not named is not read",
          "in Ignored" in subs(mail.Config(path, ("Alerts",))), False)
    try:
        mail.read(mail.Config(path, ("Nope",)))
        check("a folder that does not exist is reported", False, True)
    except mail.MailboxUnreadable as exc:
        check("a folder that does not exist is reported, by name", "Nope" in str(exc), True)

    print("what is in the queue, and what takes a message out of it")
    # Built here rather than read from the sample, so that the read and unread
    # messages sit side by side in one folder and the only difference between
    # them is the flag.
    def built_with_seen(root=None):
        root = root or tempfile.mkdtemp()
        path = os.path.join(root, "mail_folders")
        if os.path.exists(path): shutil.rmtree(path)
        os.makedirs(path)
        box = mailbox.Maildir(os.path.join(path, FEED), create=True)
        for subject, seen in (("already read", True), ("never opened", False)):
            m = EmailMessage()
            m["From"] = "someone@example.invalid"
            m["Subject"] = subject
            m["Date"] = "Tue, 08 Sep 2026 08:00:00 +0000"
            m["Message-ID"] = f"<{subject.split()[0]}@example.invalid>"
            m.set_content("body")
            md = mailbox.MaildirMessage(m)
            if seen: md.add_flag("S")
            box.add(md)
        box.flush()
        return mail.Config(path, (FEED,)), os.path.join(path, FEED)

    mixed, feed = built_with_seen()
    got = mail.read(mixed)
    check("a read message and an unread one are both in the queue",
          sorted(m.subject for m in got), ["already read", "never opened"])
    check("and each says which it was",
          {m.subject: m.seen for m in got},
          {"already read": True, "never opened": False})

    # Filing is a move, so the queue empties by the folder emptying.  Done here
    # with the filesystem rather than the gateway: what is being checked is that
    # `read` answers for the folder as it finds it, not how a message got out.
    # Through the mailbox rather than by filename: a maildir names its files by
    # key and flags, never by subject, so picking the file to remove by reading
    # the name is picking at random.
    _box = mailbox.Maildir(feed, create=False)
    for _k in list(_box.keys()):
        if "S" not in _box[_k].get_flags():
            _box.remove(_k)
    _box.flush()
    left = mail.read(mixed)
    check("a message moved out of the folder is no longer in the queue",
          [m.subject for m in left], ["already read"])

    # A folder the board was not named holds nothing it will read, whatever is
    # in it.
    elsewhere = mail.Config(mixed.path, ("Nothing",))
    try:
        mail.read(elsewhere)
        check("an unnamed folder is not read", False, True)
    except mail.MailboxUnreadable:
        check("a folder that is not there is reported rather than read as empty",
              True, True)

    # A flag that cannot be read at all.  The message stays in the queue and
    # reports unread: an unreadable flag is evidence of nothing, and unread is
    # the answer that claims least.
    class _NoFlags:
        def __init__(self, inner): self._inner = inner
        def __getattr__(self, name): return getattr(self._inner, name)
        def get_flags(self): raise OSError("flags unreadable")

    class _Box:
        def __init__(self, inner): self._inner = inner
        def keys(self): return self._inner.keys()
        def __getitem__(self, k): return _NoFlags(self._inner[k])

    blind = mail._messages(_Box(mailbox.Maildir(feed, create=False)), FEED)
    check("a message whose flags cannot be read is still in the queue",
          [m.subject for m in blind], ["already read"])
    check("and reports unread", [m.seen for m in blind], [False])

    print("a notification that says its issue is finished")
    # The markup shape a tracker's notification has, copied in shape and nothing
    # else: invented project keys, an .invalid host, generated subjects.  A
    # notification carries TWO links to its own issue -- the key, struck when the
    # issue is finished, and the summary, never struck.
    def issue_mail(root, messages):
        """messages: (subject, header_key, html) -> a mailbox holding them."""
        path = os.path.join(root, "mail_folders")
        if os.path.exists(path): shutil.rmtree(path)
        os.makedirs(path)
        box = mailbox.Maildir(os.path.join(path, FEED), create=True)
        for i, (subject, key, html) in enumerate(messages):
            m = EmailMessage()
            m["From"] = "tracker@example.invalid"
            m["Subject"] = subject
            m["Date"] = "Tue, 08 Sep 2026 08:00:00 +0000"
            m["Message-ID"] = f"<n{i}@example.invalid>"
            if key: m[mail.ISSUE_HEADER] = key
            m.set_content("the plain part, which is what _body reads")
            m.add_alternative(html, subtype="html")
            box.add(mailbox.MaildirMessage(m))
        box.flush()
        return mail.Config(path, (FEED,))

    HOST = "https://track.example.invalid"
    def key_link(key, struck):
        style = "font-size: 15px; color: #676E75;"
        if struck: style += " text-decoration: line-through; "
        return f'<a title="A Project" style="{style}" href="{HOST}/issue/{key}">{key}</a>'
    def summary_link(key):
        # The second link every notification carries, and never struck.
        return (f'<a title="created by somebody" style="font-size: 15px; color: #1466c6;"'
                f' href="{HOST}/issue/{key}">a summary of the issue</a>')
    def page(*bits):
        return "<html><body><table><tr><td>" + "".join(bits) + "</td></tr></table></body></html>"

    room = tempfile.mkdtemp()
    cfg2 = issue_mail(room, [
        ("finished", "ZZA-1", page(key_link("ZZA-1", True), summary_link("ZZA-1"))),
        ("unfinished", "ZZA-2", page(key_link("ZZA-2", False), summary_link("ZZA-2"))),
    ])
    got = {m.subject: m for m in mail.read(cfg2)}
    check("a struck key marks the message done", got["finished"].issue_done, True)
    check("an unstruck one does not", got["unfinished"].issue_done, False)
    check("and the plain part is still what is read",
          "the plain part" in got["finished"].body, True)

    # The header decides which issue is looked at, not the links.  A notification
    # about ZZA-3 that also links a finished ZZA-9 is not about ZZA-9.
    cfg2 = issue_mail(room, [
        ("mentions another", "ZZA-3",
         page(key_link("ZZA-3", False), summary_link("ZZA-3"),
              "<p>see also ", key_link("ZZA-9", True), "</p>")),
    ])
    got = mail.read(cfg2)
    check("another issue's struck key does not mark this message",
          [m.issue_done for m in got], [False])

    # Any self-link struck is enough: the summary link is never struck, so
    # requiring all of them would never fire.
    cfg2 = issue_mail(room, [
        ("key struck, summary not", "ZZA-4",
         page(summary_link("ZZA-4"), key_link("ZZA-4", True))),
    ])
    check("any self-link struck is enough, whatever its order",
          [m.issue_done for m in mail.read(cfg2)], [True])

    # Nothing that is not a tracker notification is marked, and none of it raises.
    cfg2 = issue_mail(room, [
        ("no header at all", None, page(key_link("ZZA-5", True))),
        ("header, no link", "ZZA-6", page("<p>nothing linked here</p>")),
        ("header, broken html", "ZZA-7", "<p>unclosed <a href='" + HOST + "/issue/ZZA-7'"),
    ])
    got = {m.subject: m for m in mail.read(cfg2)}
    check("a message with no issue header is not marked",
          got["no header at all"].issue_done, False)
    check("a message whose HTML links no issue is not marked",
          got["header, no link"].issue_done, False)
    check("a message whose HTML will not parse is not marked, and does not raise",
          got["header, broken html"].issue_done, False)

    # A message with no HTML part at all: every message from the folders that are
    # not tracker mail.
    plain = build([("just text", {mail.ISSUE_HEADER: "ZZA-8"}, "no html here")])
    check("a message with no HTML part is not marked",
          [m.issue_done for m in mail.read(plain)], [False])

    # The canary.  This is the only warning the board will get if the tracker
    # changes its template: nothing would be marked, and nothing would say so.
    # It checks the shape this repository believes a notification has -- it
    # cannot check the shape the real server sends tomorrow.
    check("the canary: the shape the detector looks for is the shape checked here",
          mail._issue_done(
              __import__("email").message_from_string(
                  f"{mail.ISSUE_HEADER}: ZZA-1\n\n"),
              page(key_link("ZZA-1", True))),
          True)

    print("reading reaches nothing")
    # Shown rather than asserted: every way of opening a socket is replaced with
    # one that raises, and the mailbox is read anyway.  A read that touched the
    # network would fail here instead of answering.
    import socket as _socket
    _saved = (_socket.socket, _socket.create_connection, _socket.getaddrinfo)
    def _refuse(*a, **k):
        raise AssertionError("reading the mailbox tried to reach the network")
    _socket.socket = _refuse
    _socket.create_connection = _refuse
    _socket.getaddrinfo = _refuse
    # Its own mailbox, not whatever `cfg2` was last set to: a check that reads a
    # variable left over from an earlier block measures whatever ran before it.
    offline = issue_mail(tempfile.mkdtemp(),
                         [("finished", "ZZA-1",
                           page(key_link("ZZA-1", True), summary_link("ZZA-1")))])
    try:
        reached = mail.read(offline)
        check("a mailbox of notifications reads with the network taken away",
              len(reached), 1)
        check("and still decides about the issue",
              [m.issue_done for m in reached], [True])
    finally:
        _socket.socket, _socket.create_connection, _socket.getaddrinfo = _saved

    print("threads")
    ths = mail.threads(mail.read(cfg))
    check("the mailbox's ten threads", len(ths), 10)
    # Two chains for one issue, one for another, a merge-request pair and a run
    # of builds.  Most real notifications about an issue do carry the header, but
    # not all to the same message -- which is why folding beats threading here.
    check("the runs the headers give", 
          sorted(t.count for t in ths if t.count > 1), [2, 2, 3, 3, 4])
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


#: The parts this suite is made of, in the order they run.  One list,
#: read by the runner to report and select them one at a time, and by
#: the file itself when it is run directly.
PARTS = (the_mailbox,)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
