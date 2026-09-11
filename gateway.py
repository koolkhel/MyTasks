"""Moving a message on the server, and confirming that it landed.

The board reads mail from a directory and writes nothing there: a maildir
whose files are moved by hand stops syncing, with a duplicate-UID failure
that needs the folder rebuilt.  Reviewing a message therefore happens here,
against the account itself rather than against the directory.

This talked IMAP to a local gateway that translated to the account's own web
service.  It no longer does, and the reason is measured rather than a matter
of taste: opening a folder made that gateway enumerate it over the service
every time, and a review measured 81.9 seconds of 88.9 doing nothing else --
92%.  Asked directly, the same review has no folder to open.  A search costs
about a second whether the folder holds 33 items or 20,821, a move about a
fifth of a second, and marking read about a tenth.

The cost model that shapes what follows, measured against this account:

  * A search restricted to a set of identities is one request and its cost
    does not grow with the folder.  0.42 s against a folder of 33, 0.96 s
    against one of 20,821.  So a row is one search a folder, not one a
    message -- the opposite of what the old protocol forced, where an OR of
    eight identities came back with two of them and searching one at a time
    was the only honest way to ask.
  * A folder is named by an identity the account hands out, and finding one
    by its name costs a walk of the tree: 1.36 s for four folders at once
    against 4.18 s for one alone.  So the walk happens once a session and
    every name it passes is remembered.
  * Bulk requests are cheap: a move names a set of items and is one request,
    and so is marking a set read.

Nothing here fetches a body.  The board reads what a message says from the
mirrored directory; this half only moves messages and confirms where they
are.

What is deliberately not here: the account, the address of its service and
the archive's name all come from the environment, so nothing about one
mailbox is committed.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from time import monotonic

import journal

from dotenv import load_dotenv


class GatewayUnreachable(Exception):
    """The account could not be reached, or refused us.

    Its own type because it means the board can still read mail and still
    show the queue -- only reviewing is unavailable, and saying which is
    the difference between a broken board and an unreachable server.
    """


class MoveFailed(Exception):
    """A message could not be moved, or could not be confirmed where it went."""


@dataclass(frozen=True)
class Config:
    """Where the account's service is and how to speak to it."""

    #: The address of the service the board talks to.
    service: str
    #: The mailbox to act on, which is also the identity presented.
    account: str
    #: The folder a reviewed message is moved to.  Named here because it is
    #: not the board's business what an account calls it.
    archive: str = "Archive"
    #: The command that answers the password on stdout.  A command rather
    #: than a value so no password is ever written to a file: the one this
    #: was built against reads the system keychain.
    password_command: tuple[str, ...] = ()
    #: How long to wait for one request before giving up.  There is a
    #: timeout at all because there was not: a server that stopped
    #: answering left a worker thread blocked on a socket forever, and
    #: quitting the board then waited on that thread -- the run hung, with
    #: nothing said, until asyncio gave up after five minutes.
    #:
    #: Generous, because this is the bound on a hang rather than a target.
    #: The requests it bounds are measured in a second or two.
    timeout: float = 120.0


def load_config(env_path=None) -> Config | None:
    """How to reach the account, or None when it is not configured.

    None is an ordinary board that can read mail and not review it, which
    is a real state: the directory is filled by something else, and that
    something else may be all a person has set up.

    The address decides.  Reading is configured separately -- a directory of
    maildirs -- and either half may be set up alone, so what makes reviewing
    possible is knowing where to send a request.

    The identity and the credential command are read under their own names
    and, failing that, under the names they had when this spoke IMAP.  A key
    called `MAIL_IMAP_USER` naming an account reached without IMAP would be
    a lie, and renaming it without a fallback would stop an unedited
    configuration reviewing anything with nothing said about why.
    """
    load_dotenv(env_path, override=False)

    def named(new: str, old: str) -> str:
        return (os.getenv(new, "").strip() or os.getenv(old, "").strip())

    service = os.getenv("MAIL_EWS_URL", "").strip()
    account = named("MAIL_ACCOUNT", "MAIL_IMAP_USER")
    command = named("MAIL_PASSWORD_COMMAND", "MAIL_IMAP_PASSWORD_COMMAND")
    if not (service and account and command):
        return None
    return Config(
        service=service, account=account,
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


#: The library's exception types, fetched once and kept.  Not imported at the
#: top of the module for the reason `Mailbox` is not: a board that never
#: reviews anything should not pay for an XML parser and a cryptography stack
#: on the way up.  Not imported per request either, which is what this was at
#: first -- the one place every request passes through is the last place to
#: put work that can be done once.
_KINDS = None


def _error_kinds():
    """(never happened, a refusal, a rejected credential, a line, anything).

    The order these are caught in is the whole of the difference between
    telling a person the account refused their review and telling them it
    could not be reached, and the library's hierarchy does not draw that
    line for us: `ErrorTimeoutExpired` -- a request that never completed --
    is a subclass of `ResponseMessageError`, which otherwise means the
    service answered and would not do it.  Read in class order a timeout
    reads as a refusal, and the board says the move was refused when nothing
    was ever asked.  A live run against the account caught exactly that.

    So the ones that mean "this never reached anywhere, or it did and the
    account asked for later" are named first, and everything else in
    `ResponseMessageError` keeps its meaning.  This is the same trap
    `imaplib` set with `abort` being a subclass of `error`, in a different
    library.
    """
    global _KINDS
    if _KINDS is None:
        from exchangelib.errors import (EWSError, ErrorServerBusy,
                                        ErrorTimeoutExpired, RateLimitError,
                                        ResponseMessageError, TransportError,
                                        UnauthorizedError)
        never_happened = (ErrorTimeoutExpired, ErrorServerBusy, RateLimitError)
        _KINDS = (never_happened, ResponseMessageError, UnauthorizedError,
                  TransportError, EWSError)
    return _KINDS


#: How many identities one restriction may name.  The service refuses a
#: restriction with "too many elements" somewhere above this -- a folder's
#: worth of them is refused, 120 was answered -- and a row on this account
#: holds at most a few dozen, so this bounds a question nothing real asks
#: rather than dividing one that is.
BATCH = 100


def restriction(idents):
    """One restriction naming every identity, in a shape that does not nest.

    Written this way because the other way failed against the account.  An
    OR of one term per identity nests one level per message, and the service
    refuses a request more than 32 levels deep -- `ErrorSchemaValidation`,
    "the maximum read depth (32) has been exceeded".  A row of thirty-nine
    messages is an ordinary row on this account, and it would have been
    refused outright.  The stubs could not have caught it: nesting is legal
    and cheap in a fake, and only a server has a depth limit.

    A membership test is flat however many identities it names -- 120 of them
    in one request, answered with 120 matches -- so the shape stops depending
    on how big a row is.
    """
    from exchangelib import Q
    return Q(message_id__in=list(idents))


class Mailbox:
    """The account, in the four requests this module makes of it.

    A class of its own, and small on purpose.  It is the only thing here
    that knows a library, and it is what a suite substitutes: the board's
    reviewing path is the one place it changes something it cannot change
    back, so a suite has to be able to drive every path without an account.

    The old protocol was faked at the wire, because the parsing of its
    answers was the part that broke -- folder names in a modified UTF-7, a
    fetch answering alternating tuples, a search that matched nothing
    answering one empty string.  There is no parsing here: the library
    answers with objects.  What can be got wrong instead is *which request
    is made*, so that is what these four methods make visible and what a
    suite counts.
    """

    def __init__(self, config: Config, secret: str):
        # Imported here rather than at the top of the module: the board
        # starts, draws and reads mail without ever touching this, and a
        # library that pulls in an XML parser and a cryptography stack
        # should not be on the path of a board that never reviews anything.
        from exchangelib import Account, Configuration, Credentials, DELEGATE
        from exchangelib.protocol import BaseProtocol

        # The library holds its timeout on the class rather than per
        # connection, so this is set rather than passed.
        BaseProtocol.TIMEOUT = config.timeout
        settings = Configuration(
            service_endpoint=config.service,
            credentials=Credentials(config.account, secret),
            # Named rather than negotiated: this account answers it, and
            # letting the library try each in turn would make a wrong
            # password cost several round trips before it said so.
            auth_type="NTLM",
        )
        self.account = Account(primary_smtp_address=config.account,
                               config=settings, autodiscover=False,
                               access_type=DELEGATE)
        self._known: dict[str, object] | None = None

    def folders(self) -> dict[str, object]:
        """Every folder the account holds, by name folded for comparison.

        One walk, remembered.  Finding one folder by name costs the same
        walk as finding all of them -- 4.18 s for one against 1.36 s for
        four, the difference being where the walk happened to stop -- so
        asking once and keeping the answer is the whole of the difference
        between a session and a request.
        """
        if self._known is None:
            found: dict[str, object] = {}
            for folder in self.account.root.walk():
                found.setdefault(str(folder.name).casefold(), folder)
            self._known = found
        return self._known

    def find(self, folder, idents) -> list:
        """Every message in this folder whose identity is one of these.

        One request for the whole set.  The identities are what the mirror
        knows a message by, and they are what the board asks about, so this
        is the one question a review needs answered.
        """
        wanted = [i for i in idents if i]
        if not wanted:
            return []
        # Only what is needed to name a message again: its identity, and the
        # pair the service uses to say *this* item.  Asking for more would
        # fetch bodies the board reads from the mirror instead.
        #
        # In parts where a set is larger than the service will name at once,
        # which no row is: a row of thirty-nine is the largest this account
        # has, and the bound is a hundred.  A caller asking about a folder's
        # worth of identities -- putting mail back after something went wrong,
        # say -- gets an answer rather than a refusal.
        found = []
        for at in range(0, len(wanted), BATCH):
            found += list(folder.filter(restriction(wanted[at:at + BATCH]))
                          .only("message_id", "id", "changekey"))
        return found

    def move(self, items, target) -> None:
        """Move these items to that folder, in one request."""
        self.account.bulk_move(ids=items, to_folder=target)

    def mark(self, items, seen: bool) -> None:
        """Mark these items read, or unread again, in one request."""
        for item in items:
            item.is_read = seen
        self.account.bulk_update([(item, ("is_read",)) for item in items])


class Server:
    """A connection to the account, for the length of one review."""

    def __init__(self, config: Config, connect=None):
        self.config = config
        #: Substitutable so a suite can drive every path here without an
        #: account: the connection is the only thing that reaches outside.
        self._connect = connect or self._open
        self.mailbox = None
        #: The archive, resolved once when the session opens.
        self.archive = None
        #: Every folder the account holds, asked for once a session.  The
        #: walk that answers costs about as much for all of them as for one,
        #: and a review names two or three, so it is asked once and kept.
        self._known: dict[str, object] | None = None

    def _open(self):
        return Mailbox(self.config, password(self.config))

    def __enter__(self):
        try:
            self.mailbox = self._connect()
        except GatewayUnreachable:
            raise
        except Exception as exc:
            raise GatewayUnreachable(
                f"the account at {self.config.service} "
                f"could not be reached: {type(exc).__name__}") from exc
        # Resolved here beside the connection, not in each method that needs
        # it: the walk that finds a folder costs about as much as the walk
        # that finds every folder, and a review asks about the archive three
        # times.  One session, one walk.
        self.archive = self._folder(self.config.archive)
        return self

    def __exit__(self, *exc):
        self.mailbox = None
        self.archive = None
        self._known = None
        return False

    def _talk(self, command: str, call, about: str = ""):
        """Run one request, and answer for it in this module's own terms.

        The one place the library's exceptions are allowed to end.  Whatever
        happens underneath -- the line failing mid-request, the service
        refusing, the credential being wrong -- leaves here as one of this
        module's two exceptions, so that nothing calling this class has to
        know a protocol is involved.

        The order of the clauses is load bearing, as it was when this spoke
        IMAP and `abort` had to be caught before `error` because it was a
        subclass of it.  Here `ResponseMessageError` is a subclass of
        `TransportError`: the first means the service answered and would not
        do what was asked, the second that the conversation itself failed.
        Read the other way round, every refusal would be reported as an
        unreachable account and the board would say the wrong thing about
        every one of them.

        One call, never a method body.  An `OSError` raised by something
        else in the same method is a bug in this file, and reporting it as
        an unreachable mailbox would hide it.
        """
        never_happened, refused, unauthorised, transport, any_error = \
            _error_kinds()
        started = monotonic()
        try:
            answer = call()
        except never_happened as exc:
            journal.trace(command, about, monotonic() - started,
                          f"ABORT {exc}")
            raise GatewayUnreachable(
                f"the line to the account went down during {command}: "
                f"{exc}") from exc
        except refused as exc:
            journal.trace(command, about, monotonic() - started,
                          f"REFUSED {exc}")
            raise MoveFailed(f"the account refused {command}: {exc}") from exc
        except unauthorised as exc:
            journal.trace(command, about, monotonic() - started,
                          f"REFUSED {exc}")
            raise GatewayUnreachable(
                f"the account refused us during {command}: {exc}") from exc
        except transport as exc:
            journal.trace(command, about, monotonic() - started,
                          f"ABORT {exc}")
            raise GatewayUnreachable(
                f"the line to the account went down during {command}: "
                f"{exc}") from exc
        except any_error as exc:
            journal.trace(command, about, monotonic() - started,
                          f"REFUSED {exc}")
            raise MoveFailed(f"the account refused {command}: {exc}") from exc
        except OSError as exc:
            journal.trace(command, about, monotonic() - started,
                          f"FAILED {type(exc).__name__}")
            raise GatewayUnreachable(
                f"the line to the account went down during {command}: "
                f"{type(exc).__name__}") from exc
        # Written on every path, so the last line before a session ends is the
        # request that ended it.  `answer` is not looked at: what a search
        # found is already in the operation's own line in the log, and
        # teaching this function each command's response shape would put
        # parsing in the one place that has none.
        journal.trace(command, about, monotonic() - started, "ok")
        return answer

    def _folder(self, name: str):
        """The folder of that name, or a refusal naming it.

        Asked of the account once a session.  The walk that answers costs
        about as much for every folder as for one, and a review names the
        archive three times, so the answer is kept for as long as the
        session that needed it.

        Matched without regard to case, because what the board is given is
        what a person wrote in their configuration and what the account
        holds is however that account spells it.
        """
        if self._known is None:
            self._known = self._talk("FOLDERS",
                                     lambda: self.mailbox.folders(),
                                     about="every folder")
        found = self._known.get(name.casefold())
        if found is None:
            raise MoveFailed(f"the folder {name} could not be found")
        return found

    def numbers(self, folder: str, idents, stop=None) -> dict:
        """Each of these messages in one folder, by identity.

        One request for the whole row, which is what the account's own
        service allows and the old gateway did not: asked for eight
        identities at once it answered with two of them, so the board asked
        one at a time and a row of eight cost eight searches.  Here the set
        is the question.

        `stop` is asked before the request rather than between messages,
        there being one request to be between.  A board being forced to end
        waits out at most one search.
        """
        wanted = [i for i in idents if i]
        if not wanted:
            return {}
        if stop is not None and stop():
            raise MoveFailed("gave up part way: the board is closing")
        where = folder if not isinstance(folder, str) else self._folder(folder)
        name = folder if isinstance(folder, str) else str(folder.name)
        items = self._talk("SEARCH",
                           lambda: self.mailbox.find(where, wanted),
                           about=f"{name} n={len(wanted)}")
        out = {}
        for item in items:
            ident = getattr(item, "message_id", None)
            if ident in wanted and ident not in out:
                out[ident] = item
        return out

    def present(self, folder, idents) -> list:
        """Which of these messages the folder still holds.

        What proves a move actually removed something.  The same question as
        `numbers` and deliberately so: after a move the item is elsewhere
        with an identity of the service's own, so asking the folder about the
        message identities is the only question that still means anything.
        """
        wanted = [i for i in idents if i]
        if not wanted:
            return []
        return sorted(self.numbers(folder, wanted))

    def move(self, folder, items, target) -> None:
        """Move these items to another folder, in one request."""
        held = list(items)
        if not held:
            return
        where = target if not isinstance(target, str) else self._folder(target)
        name = target if isinstance(target, str) else str(target.name)
        # The source is named only so the trace reads as a sentence: the
        # items carry where they are, and the request names them, not a
        # folder to take them from.
        source = folder if isinstance(folder, str) else str(folder.name)
        self._talk("MOVE", lambda: self.mailbox.move(held, where),
                   about=f"{source} n={len(held)} -> {name}")

    def number(self, folder: str, message_id: str):
        """One message in a folder, or None if it is not there."""
        return self.numbers(folder, [message_id]).get(message_id)

    def holds(self, folder: str, message_id: str) -> bool:
        """Whether a folder holds this message."""
        return self.number(folder, message_id) is not None

    def mark_seen(self, folder, items, seen: bool = True) -> None:
        """Mark these items read, or unread again.

        One request for the row, and it costs no search: the items come
        from the confirmation, which had to look each message up in the
        archive anyway and used to throw the answer away.

        Read matters because the board's queue is what has not been dealt
        with, and it reads that from the flag.  A reviewed message left
        unread in the archive is a message the account still calls new.
        Undoing a review clears it again, or the row would come back to a
        queue that no longer counts it.
        """
        held = list(items)
        if not held:
            return
        name = folder if isinstance(folder, str) else str(folder.name)
        self._talk("FLAG", lambda: self.mailbox.mark(held, seen),
                   about=f"{name} n={len(held)} "
                         f"{'+' if seen else '-'}Seen")


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
    in the archive.  A move that was accepted is not evidence; a row retired
    on an unconfirmed move is a message a person believes they have dealt
    with.

    What a row costs, in requests, whatever it holds: one search of the
    folder, one move, one search that proves the folder let go, one search of
    the archive, and one flag for the whole row.  None of them grows with the
    number of messages in the row, which is the property the specification
    states and the reason the searches take a set rather than a message.

    `stop` is asked before each search whether to give up -- the board wires
    it to its own shutdown.  The messages that were moved are in the archive
    either way, and the next run finds them there and reports them already
    reviewed.

    Raises `MoveFailed` when a move cannot be confirmed, so the caller can
    put the row back.  The messages that were confirmed stay archived: they
    are dealt with, and un-archiving them to make the report tidy would be
    the one thing that loses mail.
    """
    archived: list[str] = []
    already: list[str] = []
    missing: list[str] = []
    #: Where each one landed in the archive, for marking it read.
    arrived: list = []
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
                srv.move(folder, moved, srv.archive)
                stayed = srv.present(folder, here)
                if stayed:
                    raise MoveFailed(
                        f"{len(stayed)} of {len(here)} are still in {folder} "
                        f"after the move")
            # One search of the archive for the whole confirmation, and for
            # both groups: those just moved, and those that turned out to be
            # elsewhere already.  The items are kept, not just the yes-or-no:
            # they are what marks the messages read below, and finding them
            # again would cost another search.
            landed = srv.numbers(srv.archive, here + elsewhere, stop=stop)
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
        # whole row, on items the confirmation already found.  Last, so a
        # message is never marked read on the strength of a move that could
        # not be confirmed.
        srv.mark_seen(srv.archive, arrived)
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
            # Three requests for the row, not three a message.
            found = srv.numbers(srv.archive, wanted)
            missing += [i for i in wanted if i not in found]
            here = [i for i in wanted if i in found]
            if not here:
                continue
            moving = [found[i] for i in here]
            # Unread again before they go back, and in that order: after a
            # move a message is in another folder under another identity of
            # the service's own, so marking it afterwards would mean finding
            # it again.
            #
            # The queue is what has not been dealt with, and a message that
            # returned read would return to a queue that does not show it.
            srv.mark_seen(srv.archive, moving, seen=False)
            # One move for the row, which is what makes the undo all or
            # nothing: either the row comes back or none of it does.  A row
            # split between a folder and the archive is the state hardest to
            # reason about and the one a person can do least about.
            srv.move(srv.archive, moving, folder)
            back += here
    return Outcome(tuple(back), (), tuple(missing))
