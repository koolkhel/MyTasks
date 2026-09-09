"""A server standing in for the gateway, and a record of what was asked of it.

The board's reviewing path is the one place it changes something it cannot
change back on its own, so the suites need to see every request it makes --
not only that the outcome was right. Every call is recorded in order, and a
suite can make any of them fail or answer wrongly.

It speaks the shape `imaplib` hands back, quirks included: folder names arrive
quoted and in the modified UTF-7 the protocol wants, a FETCH answers a list of
alternating tuples and stray `b')'` parts, and a SEARCH that matched nothing
answers one empty string rather than an empty list. Those quirks are the whole
reason for standing a server in rather than stubbing the client's methods: the
parsing is the part that breaks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gateway


class FakeIMAP:
    """Folders holding `{uid: message-id}`, and a log of every call."""

    def __init__(self, folders, fail=None, deny=(), readonly_store=False):
        #: `{folder: [message-id, ...]}` -- numbers are handed out here, as a
        #: server does, so nothing outside may assume what they are.
        self.folders = {}
        self._next = 100
        for name, idents in folders.items():
            self.folders[name] = {}
            for ident in idents:
                self._next += 1
                self.folders[name][str(self._next).encode()] = ident
        #: Called with (command, args) before each request; return a status to
        #: answer with it instead, or raise.
        self.fail = fail
        #: Folders that answer a SEARCH as though empty, however full they are.
        self.deny = set(deny)
        #: Refuse a store, as a server does for a mailbox opened read-only.
        self.readonly_store = readonly_store
        #: Which messages have been marked read, by identity.
        self.seen = set()
        #: Which folder was open each time a flag was set.
        self.stored_in = []
        self.calls = []
        self.selected = None
        self.logged_in = False

    # -- what a suite reads afterwards ------------------------------------
    def ids(self, folder):
        return sorted(self.folders.get(folder, {}).values())

    def unread_in(self, folder):
        """Which of a folder's messages are still unread."""
        return sorted(i for i in self.folders.get(folder, {}).values()
                      if i not in self.seen)

    def commands(self):
        """Just the command names, in order, for counting round trips."""
        return [c[0] for c in self.calls]

    def _record(self, name, *args):
        self.calls.append((name, args))
        if self.fail is not None:
            answer = self.fail(name, args)
            if answer is not None:
                return answer
        return None

    # -- the protocol -----------------------------------------------------
    def login(self, user, secret):
        self._record("LOGIN", user)
        self.logged_in = True
        return ("OK", [b"logged in"])

    def logout(self):
        self._record("LOGOUT")
        self.logged_in = False
        return ("BYE", [b"out"])

    def select(self, mailbox, readonly=False):
        name = gateway.utf7_decode(mailbox.strip('"'))
        early = self._record("SELECT", name, readonly)
        if early is not None:
            return early
        if name not in self.folders:
            self.selected = None
            return ("NO", [b"no such folder"])
        self.selected = name
        return ("OK", [str(len(self.folders[name])).encode()])

    def uid(self, command, *args):
        early = self._record(command.upper(), *args)
        if early is not None:
            return early
        if self.selected is None:
            return ("NO", [b"no folder selected"])
        return getattr(self, f"_uid_{command.lower()}")(*args)

    def _uid_fetch(self, which, what):
        """FLAGS for named numbers, or headers -- whichever was asked for.

        A fetch of numbers the folder no longer has is answered OK with
        nothing, which is how a real server says "they are gone" and is
        what the absence check reads.
        """
        if which == "1:*":
            raise AssertionError(
                "the whole folder was fetched: this gateway answers that by "
                "fetching every message, and it measured 45 s for 291")
        held = self.folders[self.selected]
        out = []
        for uid in which.encode().split(b","):
            if uid not in held:
                continue
            if "FLAGS" in what.upper():
                out.append(b"1 (UID %s FLAGS (\\Seen))" % uid)
                continue
            body = f"Message-ID: {held[uid]}\r\n\r\n".encode()
            out.append((b"1 (UID %s BODY[HEADER.FIELDS (MESSAGE-ID)] {%d}"
                        % (uid, len(body)), body))
            out.append(b")")
        return ("OK", out)

    def _uid_move(self, uids, mailbox):
        target = gateway.utf7_decode(mailbox.strip('"'))
        if target not in self.folders:
            return ("NO", [b"no such folder"])
        for uid in uids.encode().split(b","):
            ident = self.folders[self.selected].pop(uid, None)
            if ident is None:
                return ("NO", [b"no such message"])
            self._next += 1
            self.folders[target][str(self._next).encode()] = ident
        return ("OK", [b"moved"])

    def _uid_store(self, uids, mode, flags):
        if self.readonly_store:
            return ("NO", [b"mailbox is read-only"])
        if r"\Seen" not in flags and "Seen" not in flags:
            raise AssertionError(f"an unexpected flag was set: {flags!r}")
        self.stored_in.append(self.selected)
        held = self.folders[self.selected]
        for uid in uids.encode().split(b","):
            ident = held.get(uid)
            if ident is None:
                return ("NO", [b"no such message"])
            if mode.startswith("+"):
                self.seen.add(ident)
            else:
                self.seen.discard(ident)
        return ("OK", [b"stored"])

    def _uid_search(self, charset, *criteria):
        """A search for one identity.

        One only: an OR of several is what the real gateway answers with 2
        matches out of 8, so a suite that let it work here would pass on a
        request the product must not make.
        """
        if "OR" in criteria:
            raise AssertionError(
                "an OR search was made: this gateway answers those with "
                "some of the matches, not all")
        wanted = criteria[-1].strip('"')
        if self.selected in self.deny:
            return ("OK", [b""])
        found = [uid for uid, ident in sorted(self.folders[self.selected].items())
                 if ident == wanted]
        return ("OK", [b" ".join(found) if found else b""])


def server(config, imap):
    """A `gateway.Server` speaking to `imap`, with no password asked for."""
    return gateway.Server(config, connect=lambda: imap)


#: A configuration that reaches nothing: the connection is substituted, and
#: the password command is one that cannot ask a person anything.
CONFIG = gateway.Config(host="gateway.invalid", port=1143, user="me",
                        archive="Archive",
                        password_command=("printf", "secret"))
