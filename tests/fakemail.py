"""An account standing in for the real one, and a record of what was asked.

The board's reviewing path is the one place it changes something it cannot
change back on its own, so the suites need to see every request it makes --
not only that the outcome was right. Every call is recorded in order, and a
suite can make any of them fail.

This stands in for `gateway.Mailbox`, which is the only part of the gateway
that knows a library. The old protocol was faked at the wire, because parsing
its answers was the part that broke: folder names in a modified UTF-7, a fetch
answering alternating tuples, a search that matched nothing answering one
empty string. There is no parsing now -- the library answers with objects --
so what can be got wrong instead is *which request is made*, and that is what
this makes countable.

Invented folder names and `.invalid` identities only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gateway


def refused(why):
    """What the account raises when it answers and will not do what was asked.

    The library's own type, not a stand-in: the gateway sorts its exceptions
    by the library's hierarchy, and a fake that raised something else would
    prove nothing about the sorting.
    """
    from exchangelib.errors import ErrorAccessDenied
    return ErrorAccessDenied(why)


class Item:
    """One message, as the account hands it back.

    It carries where it is, which is what lets a suite prove that the one
    flag the board sets is set only in the archive: a flag request names
    items rather than a folder, so the folder has to be readable from the
    item.
    """

    def __init__(self, message_id, folder):
        self.message_id = message_id
        self.folder = folder
        self.is_read = False

    def __repr__(self):
        return f"<Item {self.message_id} in {self.folder}>"


class Folder:
    """A folder, named the way the account names it."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Folder {self.name}>"


class FakeMailbox:
    """Folders holding messages, and a log of every request."""

    def __init__(self, folders, fail=None, deny=(), readonly_flag=False):
        #: `{folder name: [Item, ...]}` -- the account's own contents.
        self.held = {name: [Item(i, name) for i in idents]
                     for name, idents in folders.items()}
        #: Called with (command, args) before each request; raise from it to
        #: make that request fail, as the account would.
        self.fail = fail
        #: Folders that answer a search as though empty, however full they are.
        self.deny = set(deny)
        #: Refuse to set a flag, as an account does when it will not.
        self.readonly_flag = readonly_flag
        #: Which folder each flagged message was in, so a suite can prove the
        #: one flag the board sets is set nowhere but the archive.
        self.stored_in = []
        self.calls = []

    # -- what a suite reads afterwards ------------------------------------
    def ids(self, folder):
        return sorted(item.message_id for item in self.held.get(folder, ()))

    def unread_in(self, folder):
        """Which of a folder's messages are still unread."""
        return sorted(item.message_id for item in self.held.get(folder, ())
                      if not item.is_read)

    def commands(self):
        """Just the command names, in order, for counting round trips."""
        return [c[0] for c in self.calls]

    def _record(self, name, *args):
        self.calls.append((name, args))
        if self.fail is not None:
            self.fail(name, args)

    @staticmethod
    def _named(folder):
        """The folder's name, whether it was given as one or as a folder."""
        return folder if isinstance(folder, str) else folder.name

    # -- the four requests the gateway makes -------------------------------
    def folders(self):
        """Every folder, by name folded for comparison.  One walk."""
        self._record("FOLDERS")
        return {name.casefold(): Folder(name) for name in self.held}

    def find(self, folder, idents):
        """Every message in this folder whose identity is one of these."""
        name = self._named(folder)
        wanted = list(idents)
        self._record("SEARCH", name, len(wanted))
        if name in self.deny:
            return []
        return [item for item in self.held.get(name, ())
                if item.message_id in set(wanted)]

    def move(self, items, target):
        """Move these items to that folder, in one request."""
        name = self._named(target)
        self._record("MOVE", name, len(items))
        if name not in self.held:
            raise refused(f"no folder called {name}")
        for item in items:
            here = self.held.get(item.folder, [])
            if item not in here:
                raise refused("no such message")
            here.remove(item)
            item.folder = name
            self.held[name].append(item)

    def mark(self, items, seen):
        """Mark these items read, or unread again, in one request."""
        where = items[0].folder if items else ""
        self._record("FLAG", where, len(items), seen)
        if self.readonly_flag:
            raise refused("the folder will not take a flag")
        for item in items:
            self.stored_in.append(item.folder)
            item.is_read = seen


def server(config, mailbox):
    """A `gateway.Server` speaking to `mailbox`, with no password asked for."""
    return gateway.Server(config, connect=lambda: mailbox)


#: A configuration that reaches nothing: the connection is substituted, and
#: the password command is one that cannot ask a person anything.
CONFIG = gateway.Config(service="https://account.invalid/service",
                        account="me@example.invalid",
                        archive="Archive",
                        password_command=("printf", "secret"))
