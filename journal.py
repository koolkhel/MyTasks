"""A log of what the board did to the mail account, for reading afterwards.

The mailbox is the one place the board changes something it cannot change
back on its own, and a failure there is announced in a notice that the next
notice replaces -- so a person clearing a queue of two hundred rows can miss
the one that went wrong.  This is where it can be found afterwards.

Written and never read.  Nothing on the board is drawn from this file, no
behaviour depends on it, and deleting it changes nothing -- which is what
makes it safe to keep at all, given that the board otherwise holds no state
it reads back.

One line per entry, in the shape the machine's other mail service already
logs in:

    2026-09-09T14:53:16Z OK    review 3 message(s) from Feed: moved
    2026-09-09T14:53:54Z ERROR review of 2 message(s) from Feed: ...

Identities, folder names, counts and durations.  No subject, no sender, no
part of a body: this is a durable file outside the mail store, and an
identity is both what the gateway addresses a message by and what a person
would search on to find it again.  The board's own notices name the row on
screen, where it is already visible.

Every write is best-effort.  A missing directory, a full disk or a
permission must not fail a review or say anything to the person about
itself: losing a line is a smaller harm than losing the review, and a person
told mid-queue that a log could not be written learns nothing they can act
on.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))

#: Where the log is written.  Beside the board's own files, not beside
#: whatever directory a person happened to start it from: the launcher
#: changes into the repository but `main.py` can be run from anywhere, and a
#: log that lands somewhere different each time is a log nobody finds twice.
#:
#: A module-level name so a suite can point it elsewhere; nothing in the
#: product reassigns it.
PATH = os.path.join(_HERE, "logs", "mytasks.log")

#: The three levels, matching the neighbouring mail service's.  Padded so
#: the messages line up when the file is read by eye.
OK = "OK   "
WARN = "WARN "
ERROR = "ERROR"


def write(level: str, message: str) -> None:
    """Append one line.  Never raises, never reports itself."""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        with open(PATH, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {level} {message}\n")
    except Exception:
        # Deliberately everything: a log is not worth an exception reaching
        # a worker thread that is part way through moving somebody's mail.
        pass


def ok(message: str) -> None:
    write(OK, message)


def warn(message: str) -> None:
    write(WARN, message)


def error(message: str) -> None:
    write(ERROR, message)
