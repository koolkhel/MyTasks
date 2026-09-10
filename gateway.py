"""Moving a message on the server, and confirming that it landed.

The board reads mail from a directory and writes nothing there: a maildir
whose files are moved by hand stops syncing, with a duplicate-UID failure
that needs the folder rebuilt.  Reviewing a message therefore happens here,
over IMAP, against whatever gateway fronts the account.

Trimmed from `corpmail.py` in the DavMail project next door, which offers
itself to be copied and carries the traps this would otherwise re-learn.
Copied rather than imported: a path dependency on a sibling repository would
stop this one working from a fresh clone.  Its sending, attachment and
index paths are not here -- only what reviewing needs.

What was NOT copied, deliberately: that file names the account it was written
for.  Here the account, the host and the archive's name all come from the
environment, so nothing about one mailbox is committed.

The cost model that shapes this: bulk *flags* are nearly free -- 20,699 of
them in 0.88 s next door, and 291 in 0.14 s here -- while anything
per-message costs about 150 ms, headers included.  Measured on the real
folders, a whole-folder header fetch of 291 messages took 45 s where a
search for one identity took 2.1 s.  So a move takes a set of numbers and is
one round trip whatever the row's size, the numbers are found by a search a
message rather than a fetch a folder, and nothing here ever fetches a body.
"""
from __future__ import annotations

import base64
import imaplib
import os
import re
import subprocess
from dataclasses import dataclass
from time import monotonic

import journal

from dotenv import load_dotenv


class GatewayUnreachable(Exception):
    """The gateway could not be reached, or refused us.

    Its own type because it means the board can still read mail and still
    show the queue -- only reviewing is unavailable, and saying which is
    the difference between a broken board and an unreachable server.
    """


class MoveFailed(Exception):
    """A message could not be moved, or could not be confirmed where it went."""


@dataclass(frozen=True)
class Config:
    """Where the gateway is and how to speak to it."""

    host: str
    port: int
    user: str
    #: The folder a reviewed message is moved to.  Named here because it is
    #: not the board's business what an account calls it.
    archive: str = "Archive"
    #: The command that answers the password on stdout.  A command rather
    #: than a value so no password is ever written to a file: the one this
    #: was built against reads the system keychain.
    password_command: tuple[str, ...] = ()
    #: How long to wait for one request before giving up.  There is a
    #: timeout at all because there was not: a gateway that stopped
    #: answering left a worker thread blocked on a socket forever, and
    #: quitting the board then waited on that thread -- the run hung, with
    #: nothing said, until asyncio gave up after five minutes.
    #:
    #: Generous, because legitimate requests here are slow: a search of the
    #: archive measured 11.5 s and a move of 97 messages 13.7 s.  This is
    #: the bound on a hang, not a target.
    timeout: float = 120.0


def load_config(env_path=None) -> Config | None:
    """How to reach the gateway, or None when it is not configured.

    None is an ordinary board that can read mail and not review it, which
    is a real state: the directory is filled by something else, and that
    something else may be all a person has set up.
    """
    load_dotenv(env_path, override=False)
    host = os.getenv("MAIL_IMAP_HOST", "").strip()
    user = os.getenv("MAIL_IMAP_USER", "").strip()
    command = os.getenv("MAIL_IMAP_PASSWORD_COMMAND", "").strip()
    if not (host and user and command):
        return None
    try:
        port = int(os.getenv("MAIL_IMAP_PORT", "143").strip() or 143)
    except ValueError:
        return None
    return Config(
        host=host, port=port, user=user,
        archive=os.getenv("MAIL_ARCHIVE_FOLDER", "Archive").strip() or "Archive",
        password_command=tuple(command.split()),
    )


def password(config: Config) -> str:
    """The password, asked for at the moment it is needed.

    Asked for then rather than at startup because the prompt does not reach
    the terminal the board owns: on this system an unauthorised keychain
    item is answered by SecurityAgent, a windowed process of its own, and a
    missing one comes back as an error in fourteen milliseconds with nothing
    written to the terminal at all.  So there is nothing for a full-screen
    view to be interrupted by, and fetching it early would hold a password
    in memory for a session that may never review anything.

    The command is configurable, though, so it is run with its input closed
    and its output captured: it cannot read from or write to the terminal
    the board has repainted.  A command that opens the terminal device
    itself could still reach it, and that is the choice of whoever
    configured the command.
    """
    if not config.password_command:
        raise GatewayUnreachable("no password command is configured")
    try:
        done = subprocess.run(list(config.password_command),
                              stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GatewayUnreachable(
            f"the password command did not answer: {type(exc).__name__}") from exc
    if done.returncode != 0 or not done.stdout.strip():
        raise GatewayUnreachable(
            "the password command answered nothing"
            + (f": {done.stderr.strip()[:80]}" if done.stderr.strip() else ""))
    return done.stdout.strip()


# -- folder names -------------------------------------------------------
# IMAP names folders in a modified UTF-7 that Python ships no codec for, and
# the library hands back the encoded form: selecting a non-ASCII folder by
# its real name raises before it reaches the server.  Both directions are
# therefore done here.

def utf7_encode(name: str) -> str:
    """A folder's name as IMAP wants it.  ASCII names pass through."""
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            b = "".join(buf).encode("utf-16-be")
            out.append("&" + base64.b64encode(b).decode()
                       .rstrip("=").replace("/", ",") + "-")
            buf.clear()

    for ch in name:
        if ch == "&":
            flush(); out.append("&-")
        elif 0x20 <= ord(ch) <= 0x7e:
            flush(); out.append(ch)
        else:
            buf.append(ch)
    flush()
    return "".join(out)


def utf7_decode(name: str) -> str:
    """The inverse: what IMAP returns, as a name a person would recognise."""
    out: list[str] = []
    i = 0
    while i < len(name):
        if name[i] == "&":
            j = name.index("-", i)
            chunk = name[i + 1:j]
            if chunk == "":
                out.append("&")
            else:
                b = chunk.replace(",", "/")
                b += "=" * (-len(b) % 4)
                out.append(base64.b64decode(b).decode("utf-16-be"))
            i = j + 1
        else:
            out.append(name[i]); i += 1
    return "".join(out)


_ID = re.compile(rb"message-id:\s*(<[^>\s]+>)", re.I)


class Server:
    """A connection to the gateway, for the length of one review."""

    def __init__(self, config: Config, connect=None):
        self.config = config
        #: Substitutable so a suite can drive every path here without a
        #: server: the connection is the only thing that reaches outside.
        self._connect = connect or self._open
        self.imap = None

    def _open(self):
        # Plain IMAP4, not IMAP4_SSL: the gateway this was built against
        # binds the loopback only and advertises no TLS.
        opened = imaplib.IMAP4(self.config.host, self.config.port,
                               timeout=self.config.timeout)
        return opened

    def __enter__(self):
        try:
            self.imap = self._connect()
            self.imap.login(self.config.user, password(self.config))
        except GatewayUnreachable:
            raise
        except Exception as exc:
            raise GatewayUnreachable(
                f"the gateway at {self.config.host}:{self.config.port} "
                f"could not be reached: {type(exc).__name__}") from exc
        return self

    def __exit__(self, *exc):
        try:
            if self.imap is not None:
                self.imap.logout()
        except Exception:
            pass
        return False

    def _talk(self, command: str, call, about: str = ""):
        """Run one request, and answer for it in this module's own terms.

        The one place `imaplib`'s exceptions are allowed to end.  Whatever
        happens underneath -- the gateway closing the line mid-command, a
        socket error, a protocol refusal -- leaves here as one of this
        module's two exceptions, so that nothing calling this class has to
        know a protocol is involved.

        Only `__enter__` used to do this, for connect and login, which
        covers a review that cannot start.  Nothing covered the connection
        dying part way through, and against this gateway that is the likeliest
        of the three: an operation stays open for tens of seconds, and the
        longer it is open the better its chance of being cut.

        `abort` is caught before `error` because it is a subclass of it.
        imaplib raises `abort` when the connection is gone and `error` when
        the server answered and would not do it; read the other way round,
        every dropped line would be reported as a refusal.

        One call, never a method body.  An `OSError` raised by something
        else in the same method is a bug in this file, and reporting it as
        an unreachable mailbox would hide it.
        """
        started = monotonic()
        try:
            answer = call()
        except imaplib.IMAP4.abort as exc:
            journal.trace(command, about, monotonic() - started,
                          f"ABORT {exc}")
            raise GatewayUnreachable(
                f"the gateway closed the line during {command}: {exc}") from exc
        except imaplib.IMAP4.error as exc:
            journal.trace(command, about, monotonic() - started,
                          f"REFUSED {exc}")
            raise MoveFailed(f"the gateway refused {command}: {exc}") from exc
        except OSError as exc:
            journal.trace(command, about, monotonic() - started,
                          f"FAILED {type(exc).__name__}")
            raise GatewayUnreachable(
                f"the line to the gateway failed during {command}: "
                f"{type(exc).__name__}") from exc
        # Written on every path, so the last line before a session ends is the
        # request that ended it.  `answer` is not looked at: what a search
        # found is already in the operation's own line in the log, and
        # teaching this function each command's response shape would put
        # parsing in the one place that has none.
        journal.trace(command, about, monotonic() - started, "ok")
        return answer

    def _select(self, folder: str, readonly=False):
        typ, _ = self._talk(
            "EXAMINE" if readonly else "SELECT",
            lambda: self.imap.select(f'"{utf7_encode(folder)}"',
                                     readonly=readonly),
            about=folder)
        if typ != "OK":
            raise MoveFailed(f"the folder {folder} could not be opened")

    def numbers(self, folder: str, idents, stop=None) -> dict[str, bytes]:
        """The server's number for each of these messages in one folder.

        One search a message, bounded by the row rather than by the folder.

        The plan was one bulk header fetch for the whole folder, on the
        measurement that bulk metadata is nearly free.  It is not free for
        headers: this gateway answers a header fetch by fetching each
        message from Exchange, so asking a 291-message folder for its
        identities measured 45 s where the same folder's flags came back in
        0.14 s.  A search for one identity measured 2.1 s, so a row of eight
        costs 17 s against 45 s -- and it does not grow when the folder does.

        An OR of the row's identities in a single search would have been one
        round trip for the lot.  This gateway answers it with 2 matches out
        of 8 identities that are all found when searched for one at a time,
        so that is out: the same class of deviation the confirmation below
        exists for.
        """
        self._select(folder, readonly=True)
        out: dict[str, bytes] = {}
        for ident in idents:
            # Asked between searches, so a board being forced to end waits out
            # one search rather than a folder opening and a search.  The
            # confirmation used to ask this between messages, where each
            # message cost an opening as well -- about fifteen seconds against
            # about one now.
            if stop is not None and stop():
                raise MoveFailed("gave up part way: the board is closing")
            found = self._number_here(folder, ident)
            if found is not None:
                out[ident] = found
        return out

    def present(self, folder: str, uids) -> list[bytes]:
        """Which of these numbers the folder still holds.

        A flags fetch of the numbers already known, which is the cheap half
        of the cost model: 0.14 s for a folder of 291.  It is what proves a
        move actually removed something, and it needs no identity -- a
        number that is gone from the folder is the message that left it.
        """
        wanted = [u.decode() if isinstance(u, bytes) else str(u) for u in uids]
        if not wanted:
            return []
        self._select(folder, readonly=True)
        typ, data = self._talk(
            "FETCH", lambda: self.imap.uid("FETCH", ",".join(wanted),
                                           "(FLAGS)"),
            about=f"{folder} n={len(wanted)}")
        if typ != "OK":
            # A fetch of numbers that have all gone is answered OK with
            # nothing; a refusal is something else, and is not "absent".
            raise MoveFailed(f"the folder {folder} could not be checked")
        still = []
        for part in data or ():
            line = part[0] if isinstance(part, tuple) else part
            found = re.search(rb"UID (\d+)", line or b"")
            if found and found.group(1) in [w.encode() for w in wanted]:
                still.append(found.group(1))
        return still

    def move(self, folder: str, uids, target: str) -> None:
        """Move these numbered messages to another folder, in one request."""
        wanted = [u.decode() if isinstance(u, bytes) else str(u) for u in uids]
        if not wanted:
            return
        self._select(folder)
        typ, resp = self._talk(
            "MOVE", lambda: self.imap.uid("MOVE", ",".join(wanted),
                                          f'"{utf7_encode(target)}"'),
            about=f"{folder} n={len(wanted)} -> {target}")
        if typ != "OK":
            raise MoveFailed(f"the move was refused: {resp}")

    def number(self, folder: str, message_id: str) -> bytes | None:
        """One message's number in a folder, or None if it is not there.

        A search rather than a fetch: the folder in question may be the
        archive, which holds everything the account has ever kept, and a
        search is answered in about two seconds whatever its size.
        """
        self._select(folder, readonly=True)
        return self._number_here(folder, message_id)

    def _number_here(self, folder: str, message_id: str) -> bytes | None:
        """The same, for a folder already open.  Saves re-selecting it."""
        typ, data = self._talk(
            "SEARCH",
            lambda: self.imap.uid("SEARCH", None, "HEADER", "Message-ID",
                                  f'"{message_id}"'),
            about=f"{folder} {message_id}")
        if typ != "OK":
            raise MoveFailed(f"the folder {folder} could not be searched")
        found = (data[0].split() if data and data[0] else [])
        return found[0] if found else None

    def holds(self, folder: str, message_id: str) -> bool:
        """Whether a folder holds this message."""
        return self.number(folder, message_id) is not None

    def mark_seen(self, folder: str, uids, seen: bool = True) -> None:
        """Mark these numbered messages read, or unread again.

        One request for the row, and it costs no search: the numbers come
        from the confirmation, which had to look each message up in the
        archive anyway and used to throw the answer away.

        Read matters because the board's queue is what has not been dealt
        with, and it reads that from the flag.  A reviewed message left
        unread in the archive is a message the account still calls new.
        Undoing a review clears it again, or the row would come back to a
        queue that no longer counts it.
        """
        wanted = [u.decode() if isinstance(u, bytes) else str(u) for u in uids]
        if not wanted:
            return
        # Writable: a read-only mailbox refuses a store, and this is the one
        # flag the board sets anywhere.
        self._select(folder)
        typ, resp = self._talk(
            "STORE",
            lambda: self.imap.uid("STORE", ",".join(wanted),
                                  "+FLAGS" if seen else "-FLAGS",
                                  r"(\Seen)"),
            about=f"{folder} n={len(wanted)} "
                  f"{'+' if seen else '-'}Seen")
        if typ != "OK":
            raise MoveFailed(
                f"the messages could not be marked "
                f"{'read' if seen else 'unread'}: {resp}")


@dataclass(frozen=True)
class Outcome:
    """What became of each message a review was asked to file away.

    Three outcomes rather than a pair, because "not where we left it" is
    ambiguous and the ambiguity matters: found in the archive it means the
    review has already happened, found nowhere it means something else moved
    the message and the board should say so rather than claim either.
    """

    archived: tuple[str, ...] = ()
    already: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()

    @property
    def done(self) -> int:
        """How many messages are now in the archive, however they got there."""
        return len(self.archived) + len(self.already)


def archive(config: Config, by_folder: dict, connect=None,
            stop=None) -> Outcome:
    """Move these messages to the archive, and confirm both sides.

    Takes `{folder: [identity, ...]}` -- a row can hold messages from more
    than one folder, since what folds them is the issue they are about.

    A confirmed message is then marked read, which is the one flag the board
    sets anywhere: the queue is what has not been dealt with, and a reviewed
    message the account still calls new is not that.  Last of all, so
    nothing is marked read on the strength of a move that could not be
    confirmed.

    Confirmation is both halves: gone from the folder it was in, and present
    in the archive.  A move that answered OK is not evidence; the gateway
    this speaks to has been caught elsewhere answering a request with
    something the protocol does not allow, and a row retired on an
    unconfirmed move is a message a person believes they have dealt with.

    Absence is proved by asking the folder for the numbers just moved: a
    flags fetch of numbers already known, which is the cheap half of the
    cost model.  Presence in the archive is a search per message, which is
    what it costs to know.

    `stop` is asked, between messages, whether to give up -- the board wires
    it to its own shutdown.  Confirming a large row takes minutes, and a
    person quitting should not wait for it: the messages that were moved are
    in the archive either way, and the next run finds them there and reports
    them already reviewed.

    Raises `MoveFailed` when a move cannot be confirmed, so the caller can
    put the row back.  The messages that were confirmed stay archived: they
    are dealt with, and un-archiving them to make the report tidy would be
    the one thing that loses mail.
    """
    archived: list[str] = []
    already: list[str] = []
    missing: list[str] = []
    #: Where each one landed in the archive, for marking it read.
    arrived: list[bytes] = []
    with Server(config, connect=connect) as srv:
        for folder, idents in by_folder.items():
            wanted = [i for i in idents if i]
            if not wanted:
                continue
            numbers = srv.numbers(folder, wanted)
            here = [i for i in wanted if i in numbers]
            elsewhere = [i for i in wanted if i not in numbers]
            if here:
                moved = [numbers[i] for i in here]
                srv.move(folder, moved, config.archive)
                stayed = srv.present(folder, moved)
                if stayed:
                    raise MoveFailed(
                        f"{len(stayed)} of {len(here)} are still in {folder} "
                        f"after the move")
            # One opening of the archive for the whole confirmation, and for
            # both groups: those just moved, and those that turned out to be
            # elsewhere already.  They concern one folder, and opening it was
            # measured on this account at about fourteen seconds against about
            # one to search it -- so opening it per message made a folded row
            # cost minutes where it costs seconds.  A row of seven spent two
            # minutes here; it spends half of one.
            #
            # The numbers are kept, not just the yes-or-no: they are what
            # marks the messages read below, and finding them again would cost
            # another search of the archive.
            #
            # Searches are still one a message.  An OR of the row would be one
            # round trip and this gateway answers an OR of eight identities
            # with two of them -- see `numbers`.
            landed = srv.numbers(config.archive, here + elsewhere, stop=stop)
            for ident in here:
                if ident not in landed:
                    raise MoveFailed(
                        f"a message left {folder} and is not in "
                        f"{config.archive}")
                archived.append(ident)
                arrived.append(landed[ident])
            for ident in elsewhere:
                if ident not in landed:
                    missing.append(ident)
                else:
                    already.append(ident)
                    arrived.append(landed[ident])
        # Read, now that they are where they belong: one request for the
        # whole row, on numbers the confirmation already found.  Last, so a
        # message is never marked read on the strength of a move that could
        # not be confirmed.
        srv.mark_seen(config.archive, arrived)
    return Outcome(tuple(archived), tuple(already), tuple(missing))


def restore(config: Config, by_folder: dict, connect=None) -> Outcome:
    """Move these messages out of the archive, back where they came from.

    The reverse of `archive`, for undoing a review.  Whether the row comes
    back on screen is not this function's business and not the board's: the
    folder is a mirror, and the row returns when whatever fills it next
    catches up.
    """
    back: list[str] = []
    missing: list[str] = []
    with Server(config, connect=connect) as srv:
        for folder, idents in by_folder.items():
            wanted = [i for i in idents if i]
            if not wanted:
                continue
            # Three openings of the archive for the row, not three a message.
            # Written a message at a time this cost 3n openings at about
            # fourteen seconds each -- a row of seven spent nearly five
            # minutes of an undo doing nothing but opening one folder.
            found = srv.numbers(config.archive, wanted)
            missing += [i for i in wanted if i not in found]
            here = [i for i in wanted if i in found]
            if not here:
                continue
            moving = [found[i] for i in here]
            # Unread again before they go back, and in that order: after a
            # move a message is in another folder with another number, so
            # marking it afterwards would mean finding it again.
            #
            # The queue is what has not been dealt with, and a message that
            # returned read would return to a queue that does not show it.
            srv.mark_seen(config.archive, moving, seen=False)
            # One move for the row, which is what makes the undo all or
            # nothing: either the row comes back or none of it does.  A row
            # split between a folder and the archive is the state hardest to
            # reason about and the one a person can do least about.
            srv.move(config.archive, moving, folder)
            back += here
    return Outcome(tuple(back), (), tuple(missing))
