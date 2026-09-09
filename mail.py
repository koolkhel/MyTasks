"""Reading a mailbox kept on disk, and writing nothing to it.

Only what a queue needs: the unread messages in the folders named, grouped
into the threads they belong to.

Nothing here writes.  Not a flag, not a name, not a folder -- the board once
marked a message read from here, and that path is gone: the directory is a
mirror of an account, moving a file in one by hand is documented to break the
sync that fills it, and a flag says only that one program has looked at a
message rather than that it has been dealt with.  A reviewed message is moved
on the server instead, which is where the record belongs; see `gateway.py`.

The directory is the boundary, deliberately.  Reading a maildir needs no
credential, no network and no knowledge of any server, and it works with
whatever fills the directory: a sync tool, a mail client, an export.  Speaking
a mail protocol from here would tie the board to one account, put a password
in the environment, and have to be redone the day the mail client changed --
which is a live possibility rather than a hypothetical.  A client that keeps
no maildir is therefore not read at all; that is the cost, and it is known.

Named for the format rather than the thing: `mailbox` is a module in Python's
own library, and a file of that name beside the board would shadow the very
thing this uses.  The same reasoning named `ical.py`.

Nothing identifying -- no address, no host, no folder -- appears here.  Where
the mailbox is comes from the environment.
"""

from __future__ import annotations

import email.header
import email.utils
import os
import re as _re
from html.parser import HTMLParser as _HTMLParser
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv

#: How deep a chain of answered messages is followed before giving up.  A
#: thread is a handful of messages, and a limit means a mailbox whose headers
#: point in a circle cannot spin here.
MAX_CHAIN = 100


class MailboxUnreadable(Exception):
    """The mailbox could not be read.

    Its own type so a caller can tell "the mailbox is shut to us" from "the
    day could not be loaded": the two must never be reported as each other.
    Covers a path that is not there, one that is not a maildir, and one the
    system will not open.
    """


@dataclass(frozen=True)
class Config:
    """Where the mail directory is, and which folders in it to read."""

    #: A directory holding one maildir per folder -- not itself a maildir.
    #: Empty when none is configured, which is an ordinary board rather
    #: than a broken one.
    path: str
    #: The folders to read, each a directory of that name inside the path.
    #: Nothing is discovered: what wants processing daily is a few folders
    #: rather than every message an account has ever held, and naming them
    #: is what keeps the queue a queue.  Naming none means no mail.
    folders: tuple[str, ...] = ()


@dataclass(frozen=True)
class Message:
    """One message, in the terms the board needs.

    The text is the subject and the body together, because everything the
    board looks for in a message -- an address, an issue's name -- can be in
    either and a person does not think of them as separate places.
    """

    sender: str
    subject: str
    when: datetime
    ident: str
    #: The message this one answers, where it says so.
    answers: str | None
    #: What the message says, without the subject.  Kept apart from `text`
    #: because the subject is already the row's title, and showing it twice
    #: -- once as the title and again at the head of the body -- reads as a
    #: mistake.
    body: str
    text: str
    #: The folder it was read from, empty for the mailbox's own inbox.  Kept
    #: because nothing else on a message can find the file again: the
    #: identity is a header, and the same header may appear in two folders.
    folder: str = ""
    #: Its key within that folder, which is what the mailbox addresses
    #: messages by.  Searching for the identity instead would be slower and
    #: still ambiguous for the messages that have none.
    key: str = ""


@dataclass(frozen=True)
class Thread:
    """Messages that answer one another, newest last."""

    messages: tuple[Message, ...]

    @property
    def newest(self) -> Message:
        return self.messages[-1]

    @property
    def count(self) -> int:
        return len(self.messages)

    @property
    def text(self) -> str:
        """Every message's text, for finding what the thread points at."""
        return "\n".join(m.text for m in self.messages)

    def sort_key(self) -> tuple:
        """Where the thread falls among the others.

        By its newest message, so what moved most recently reads first; then
        by that message's identity, so two threads that arrived in the same
        second do not swap about between redraws.
        """
        return (-self.newest.when.timestamp(), self.newest.ident)


def load_config(env_path: str | os.PathLike[str] | None = None) -> Config | None:
    """Where the mailbox is, or None when there is none.

    No mailbox configured means no mailbox, which is an ordinary board rather
    than a broken one -- so this answers None rather than raising.
    """
    load_dotenv(env_path, override=False)
    path = os.getenv("MAIL_MAILDIR", "").strip()
    if not path:
        return None
    folders = tuple(
        f.strip() for f in os.getenv("MAIL_FOLDERS", "").split(",") if f.strip()
    )
    return Config(os.path.expanduser(path), folders)


def _decoded(raw: str | None) -> str:
    """A header as text, whatever it was encoded as.

    Subjects and senders arrive encoded whenever they are not plain ASCII,
    and a board that showed the encoding rather than the words would be
    unreadable for exactly the mail that matters most here.
    """
    if not raw:
        return ""
    out = []
    for part, charset in email.header.decode_header(raw):
        if isinstance(part, bytes):
            out.append(part.decode(charset or "utf-8", "replace"))
        else:
            out.append(part)
    return "".join(out).strip()


class _Reader(_HTMLParser):
    """Turns a message's HTML into the text a person would read from it.

    Notification mail is very often HTML and nothing else -- a merge request,
    an issue update -- so a board that only read the plain part would show
    nothing for exactly the mail most worth peeking at.

    An external renderer was measured against this and not taken.  `w3m`
    formats tables and quotations more prettily, at 7.7 ms a message against
    0.06 ms here, being a subprocess each time; on a queue of two thousand
    that is fifteen seconds against a tenth of one.  The difference in output
    is cosmetic for a notification, and this needs no program to be
    installed, which the rest of this module does not either.

    Addresses are collected as they are met and appended at the end.  Both
    renderers otherwise lose them -- the markup carries the address and the
    words carry only the link's text -- and the board reads this text to find
    what a row can open, so losing them would break opening for precisely the
    mail most likely to have something to open.
    """

    #: Tags whose contents are not words a person reads.
    SILENT = {"script", "style", "head", "title"}
    #: Tags that end a line.
    BREAKS = {"p", "div", "br", "tr", "li", "ul", "ol", "table",
              "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._silent = 0
        self._links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SILENT:
            self._silent += 1
            return
        if tag in self.BREAKS:
            self._parts.append("\n")
        if tag == "li":
            self._parts.append("- ")
        if tag == "a":
            for name, value in attrs:
                if (name == "href" and value
                        and value.startswith(("http://", "https://"))
                        and value not in self._links):
                    self._links.append(value)

    def handle_endtag(self, tag):
        if tag in self.SILENT:
            self._silent = max(0, self._silent - 1)
        elif tag in self.BREAKS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._silent:
            self._parts.append(data)

    @property
    def text(self) -> str:
        joined = _re.sub(r"[ \t\xa0]+", " ", "".join(self._parts))
        joined = _re.sub(r"\n[ \t]*", "\n", joined)
        joined = _re.sub(r"\n{3,}", "\n\n", joined).strip()
        if self._links:
            joined = f"{joined}\n\n" + "\n".join(self._links) if joined \
                else "\n".join(self._links)
        return joined


def _from_html(source: str) -> str:
    """A message's HTML as readable text, or nothing if it will not parse."""
    reader = _Reader()
    try:
        reader.feed(source)
        reader.close()
    except Exception:
        return ""
    return reader.text


def _body(message) -> str:
    """The message's plain text, as much as there is of it.

    The first plain part of a multipart message, or the payload of a simple
    one.  Nothing is rendered: this is read to be searched and shown as text.

    Stripped, the way a task's note is stripped when it is read.  A mail
    body all but always ends in a newline, and an empty one is then a single
    newline rather than nothing -- which draws as a blank line where the
    board means to draw nothing at all.
    """
    try:
        if message.is_multipart():
            html_part = None
            for part in message.walk():
                kind = part.get_content_type()
                if kind == "text/plain":
                    raw = part.get_payload(decode=True) or b""
                    return raw.decode(
                        part.get_content_charset() or "utf-8", "replace").strip()
                if kind == "text/html" and html_part is None:
                    html_part = part
            if html_part is not None:
                raw = html_part.get_payload(decode=True) or b""
                return _from_html(raw.decode(
                    html_part.get_content_charset() or "utf-8", "replace"))
            return ""
        if message.get_content_type() == "text/html":
            raw = message.get_payload(decode=True) or b""
            return _from_html(raw.decode(
                message.get_content_charset() or "utf-8", "replace"))
        raw = message.get_payload(decode=True)
        if raw is None:
            return str(message.get_payload() or "").strip()
        return raw.decode(
            message.get_content_charset() or "utf-8", "replace").strip()
    except Exception:
        # A message the library cannot decode still has a subject worth
        # showing, so this is not allowed to lose the whole row.
        return ""


def _when(raw: str | None) -> datetime:
    """The message's date, or the beginning of time if it has none.

    A message with no readable date sorts oldest rather than being dropped:
    the board would rather show it at the bottom than not at all.
    """
    try:
        when = email.utils.parsedate_to_datetime(raw) if raw else None
    except (TypeError, ValueError):
        when = None
    if when is None:
        return datetime.fromtimestamp(0, timezone.utc)
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def read(config: Config) -> list[Message]:
    """Every unread message in the folders named.

    Unread, because a queue is what has not been dealt with.  A message
    already marked read has been dealt with -- here, or in whatever program
    the person reads mail with -- and showing it again would make the queue a
    list of everything instead.

    The named folders and no others.  Nothing is discovered: what wants
    processing daily is a few folders rather than every message an account
    has ever held, and naming them is what keeps the queue a queue.  Naming
    none is how a person turns mail off, and answers nothing rather than
    failing.

    A message that cannot be parsed is passed over rather than taking the
    others with it: one malformed mail in a corporate inbox is ordinary, and
    an empty view would be a worse answer than an incomplete one.
    """
    import mailbox as _mailbox

    if not config.path or not config.folders:
        return []
    if not os.path.isdir(config.path):
        raise MailboxUnreadable("no mail directory at the configured path")

    found = []
    for name in config.folders:
        where = _folder_path(config, name)
        # A folder that is not there is reported rather than passed over: an
        # empty queue and a misspelt folder name look identical on screen
        # and mean the opposite.
        if not os.path.isdir(os.path.join(where, "cur")):
            raise MailboxUnreadable(f"no folder named {name} in the mail directory")
        try:
            folder = _mailbox.Maildir(where, create=False)
        except OSError as exc:
            raise MailboxUnreadable(f"the folder {name} could not be read") from exc
        found.extend(_messages(folder, name))
    return found


def _folder_path(config: Config, folder: str) -> str:
    """Where a folder's own maildir sits on disk.

    A directory of that name beside the others.  The configured path holds
    one maildir per folder and is not itself a maildir -- there is no cur/
    at its root -- which is the layout the tool that fills it writes.

    Not the dot-prefixed form, where a folder hangs off a mailbox as a
    subdirectory.  The board read that shape while it was pointed at a
    sample; no real mail directory here has it.
    """
    return os.path.join(config.path, folder)


def _messages(box, folder: str = "") -> list[Message]:
    """Every unread message in one folder, skipping any that cannot be parsed.

    Read messages are skipped here rather than filtered afterwards: parsing
    a body is the expensive part of reading a mailbox, and a folder holding
    a year of dealt-with mail would pay it for every message to throw them
    all away.
    """
    found = []
    try:
        keys = list(box.keys())
    except OSError:
        return found
    for key in keys:
        try:
            raw = box[key]
        except Exception:
            continue
        try:
            # Maildir keeps a message's flags in its filename, and `S` is
            # the one meaning seen.  A message still in `new/` has no flags
            # at all, which is what unread looks like there.
            if "S" in raw.get_flags():
                continue
        except Exception:
            # A message whose flags cannot be read is shown rather than
            # hidden: an unreadable flag is not evidence of having dealt
            # with anything.
            pass
        try:
            subject = _decoded(raw.get("Subject"))
            body = _body(raw)
            found.append(Message(
                sender=_decoded(raw.get("From")),
                subject=subject,
                when=_when(raw.get("Date")),
                # A message with no identity of its own is given the mailbox
                # key, which is unique within the mailbox -- enough for it to
                # be a thread of its own and to be told from its neighbours.
                ident=(raw.get("Message-ID") or f"<key:{key}>").strip(),
                answers=(raw.get("In-Reply-To") or "").strip() or None,
                body=body,
                text=f"{subject}\n{body}",
                folder=folder,
                key=key,
            ))
        except Exception:
            continue
    return found


def threads(messages: list[Message],
            fold: "Callable[[Message], object] | None" = None) -> list[Thread]:
    """The messages grouped into rows, newest first.

    Two ways of grouping, in that order of preference.

    `fold` answers what a message is *about*, or None where it cannot tell.
    Messages sharing an answer are one row however their headers relate --
    which is what turns a tracker's notifications about one issue into one
    row.  Measured on real folders, the headers alone gave 385 rows for 199
    issues, so grouping by them was asking the same question twice over.

    It is passed in rather than worked out here because deciding what a
    message is about needs to know which tracker projects are configured and
    how to find an address in text, and neither belongs in a module whose
    whole job is reading a maildir.  This module stays free of both.

    Everything `fold` cannot place is grouped by the headers that say which
    message answers which, exactly as before.

    Grouping follows the header that says which message answers which, each
    chain walked to its start.  Subjects are deliberately not consulted:
    unrelated messages share a subject constantly -- a weekly digest, a
    nightly report -- and merging those would hide mail rather than tidy it,
    which is worse than listing it.

    A message whose parent is not in the mailbox is the start of its own
    thread; so is one that answers nothing.  A chain that points in a circle
    stops at `MAX_CHAIN` rather than spinning.
    """
    by_ident = {m.ident: m for m in messages}

    def root(message: Message) -> str:
        seen = {message.ident}
        for _ in range(MAX_CHAIN):
            parent = by_ident.get(message.answers) if message.answers else None
            if parent is None or parent.ident in seen:
                break
            seen.add(parent.ident)
            message = parent
        return message.ident

    grouped: dict[object, list[Message]] = {}
    for message in messages:
        mark = fold(message) if fold is not None else None
        # Keyed apart so a fold's answer can never collide with an identity:
        # a message whose subject named an issue would otherwise be able to
        # land in a chain belonging to a message of that name.
        grouped.setdefault(
            ("fold", mark) if mark is not None else ("chain", root(message)),
            []).append(message)
    made = [
        Thread(tuple(sorted(group, key=lambda m: (m.when, m.ident))))
        for group in grouped.values()
    ]
    return sorted(made, key=Thread.sort_key)
