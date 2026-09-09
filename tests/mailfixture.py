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
            m.set_content(body)
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
