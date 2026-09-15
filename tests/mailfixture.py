"""Mailboxes for the suites: a copy of the committed one, or one built here.

The board reads a directory that HOLDS maildirs, one per folder, and reads
only the folders it is named. So a suite cannot point it at a single maildir
any more; it needs a container. Both helpers here make one.

Every mailbox a suite reads is its own copy. The committed fixture is never
read in place: the board can move messages out of a mailbox now, and a suite
that wrote to the shared fixture would rewrite the thing every other mail
suite measures against. That happened once with a read flag, before the board
could move anything at all.
"""
import email.utils
import mailbox
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
#: The committed mailbox, shaped from what was measured on the real folders.
FIXTURE = os.path.join(HERE, "fixtures", "mail_folders")
#: The folders in it that hold mail. `Archive` is the move target and is
#: deliberately not among them: the board reads what it is named.
FOLDERS = ("Gitlab", "Jenkins", "YouTrack")
ARCHIVE = "Archive"

BASE = datetime(2026, 9, 8, 8, 0)


def copy():
    """A private copy of the committed mailbox. Returns its path."""
    where = os.path.join(tempfile.mkdtemp(prefix="mailfixture."), "mail_folders")
    shutil.copytree(FIXTURE, where)
    return where


def html_marker(key, done):
    """A tracker notification's markup, as a body suffix a fixture can append.

    Shape only: an `.invalid` host and an invented key.  Two links to the
    issue, as a real notification carries -- the key, struck when the issue is
    finished, and the summary, never struck.
    """
    strike = " text-decoration: line-through;" if done else ""
    host = "https://track.example.invalid"
    return (
        f'\n<html><body>'
        f'<a title="A Project" style="color:#676E75;{strike}"'
        f' href="{host}/issue/{key}">{key}</a>'
        f'<a style="color:#1466c6;" href="{host}/issue/{key}">summary</a>'
        f'</body></html>')


def build(folders, archive=True):
    """A mailbox built here, from `{folder: [(subject, body, headers), ...]}`.

    Minutes apart in the order given, so a suite can rely on which message is
    earliest without stating a date. An `Archive` folder is made unless a
    suite is checking what happens without one.
    """
    root = os.path.join(tempfile.mkdtemp(prefix="mailbuilt."), "mail_folders")
    os.makedirs(root)
    n = 0
    for folder, messages in folders.items():
        box = mailbox.Maildir(os.path.join(root, folder), create=True)
        for subject, body, headers in messages:
            n += 1
            m = EmailMessage()
            m["From"] = headers.get("From", "sender@example.invalid")
            m["To"] = "me@example.invalid"
            m["Subject"] = subject
            m["Date"] = email.utils.format_datetime(
                BASE + timedelta(minutes=headers.get("minutes", n * 5)))
            m["Message-ID"] = headers.get("Message-ID", f"<b{n}@example.invalid>")
            if headers.get("In-Reply-To"):
                m["In-Reply-To"] = headers["In-Reply-To"]
                m["References"] = headers["In-Reply-To"]
            # Anything else named like a header is one.  The keys this helper
            # acts on itself are directions to it rather than headers, and
            # none of them looks like one; a suite that needs a header this
            # does not know about should not have to teach it the name.
            for name, value in headers.items():
                if name in ("From", "Message-ID", "In-Reply-To") or "-" not in name:
                    continue
                if value is not None and name not in m:
                    m[name] = value
            m.set_content(body)
            # An HTML alternative where one is asked for, because the board
            # parses one for every message that has it and a real
            # notification always does.  A fixture of plain parts measures a
            # read that skips that work entirely.
            if headers.get("html"):
                m.add_alternative(headers["html"], subtype="html")
            md = mailbox.MaildirMessage(m)
            if headers.get("seen"):
                md.add_flag("S")
            box.add(md)
        box.flush()
    if archive:
        mailbox.Maildir(os.path.join(root, ARCHIVE), create=True).flush()
    return root


def census(root):
    """Every file in every folder, with a digest, for proving nothing moved."""
    import hashlib
    out = {}
    for base, _dirs, names in os.walk(root):
        for name in names:
            if name.startswith("."):
                continue
            full = os.path.join(base, name)
            with open(full, "rb") as fh:
                out[os.path.relpath(full, root)] = hashlib.sha256(
                    fh.read()).hexdigest()
    return out
