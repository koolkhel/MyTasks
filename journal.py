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

import io
import os
import sys
import traceback
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


def crash(error: BaseException) -> str | None:
    """Write one failure down, and answer with the file it went in.

    A traceback printed to the terminal survives only as long as the
    scrollback and only if somebody thought to save it.  Today's crash
    reached a file because a person pasted it there by hand; the durable log
    beside this said nothing at all about why the review never finished.

    Deliberately more than `write` records.  That log holds identities,
    folders, counts and durations and must hold nothing else; this holds the
    frames and the values in them, which for a failure part way through a
    review means the messages being reviewed -- subjects, senders, bodies.
    The two answer different questions.  The log says what the board did and
    is read routinely.  This says why the board stopped, and is read once, by
    somebody who has already lost the session and should not also have to
    reproduce it to find out why.

    That content is allowed here on one condition, and the condition is not
    a courtesy: the directory is excluded from commits, so a file holding
    somebody's mail cannot reach a repository that gets shared.  Anything
    that would put these files somewhere committable has to answer for that
    first.

    Best-effort on the same terms as the log, and for a stronger reason: this
    runs while a session is already ending, and a writer that raised would
    make a crash worse than the crash.
    """
    try:
        where = _crash_file(error)
    except Exception:
        # Deliberately everything.  There is no one left to tell: the board
        # is going, and a failure to record a failure is not worth a second
        # traceback on top of the first.
        return None
    # A line in the log too, so the file that is read routinely points at the
    # one that is read once.  Today it fell silent instead: a review that
    # started and no entry of any kind afterwards.
    #
    # The exception's type, never its message.  This log holds no subject and
    # no sender, and an arbitrary message can carry either -- a KeyError on a
    # subject line would put that subject straight into the file that
    # promised not to hold one.  The message is in the crash file, which is
    # allowed to hold it.
    error_line = (f"the board stopped on an unhandled "
                  f"{type(error).__name__}; written to "
                  f"{os.path.basename(where)}")
    write(ERROR, error_line)
    return where


def _crash_file(error: BaseException) -> str | None:
    """The part that is allowed to fail, so `crash` can be the part that isn't."""
    where = _free_name()
    os.makedirs(os.path.dirname(where), exist_ok=True)
    with open(where, "w", encoding="utf-8") as fh:
        fh.write(_rendered(error))
    return where


def _free_name() -> str:
    """`crash-<stamp>.txt` beside the log, and never a name already taken.

    Two crashes inside one second is not a real scenario.  The rule is that
    one crash never overwrites another, though, and a rule that holds only
    while the clock cooperates is not the rule.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    room = os.path.dirname(PATH)
    for suffix in ("",) + tuple(f"-{n}" for n in range(2, 100)):
        where = os.path.join(room, f"crash-{stamp}{suffix}.txt")
        if not os.path.exists(where):
            return where
    # Ninety-nine in one second is a crash loop, and the last name is a
    # better answer than no file at all.
    return where


def _frames(error: BaseException):
    """The exception that actually carries frames, given the one handed over.

    The failure a framework hands to a hook is not always the failure that
    happened.  Textual wraps a worker's exception in a `WorkerFailed` it
    *constructs* rather than raises, so that object has no `__traceback__` at
    all: rendering it produced a 69-byte file naming the wrapper and nothing
    else, while the terminal showed the whole chain.  The terminal was
    rendering the live exception instead, which is the one with the frames.

    So: the argument if it has a traceback, then whatever is currently being
    handled, then anything the argument was constructed around -- a wrapper
    holds the original in its `args`.  The last of those covers being called
    from outside an `except` block, which is how a suite calls it.
    """
    if error.__traceback__ is not None:
        return type(error), error, error.__traceback__
    current = sys.exc_info()
    if current[1] is not None and current[1].__traceback__ is not None:
        return current
    for held in getattr(error, "args", ()):
        if isinstance(held, BaseException) and held.__traceback__ is not None:
            return type(held), held, held.__traceback__
    return type(error), error, None


def _rendered(error: BaseException) -> str:
    """The traceback as text, with the frame values, falling back twice.

    Rendering values can itself fail -- a `__repr__` that raises, a
    structure that recurses -- so a plain traceback is the fallback, and it
    is the exception's name and nothing else if even that will not render.
    Something in the file always beats an empty one.
    """
    kind, value, tb = _frames(error)
    # Say so when the failure that was handed over is not the one being
    # rendered, or the file would silently be about a different exception
    # from the one the log line names.
    preface = ("" if value is error else
               f"{type(error).__name__}: {error}\n\n")
    try:
        from rich.console import Console
        from rich.traceback import Traceback
        import rich

        drawn = Traceback.from_exception(
            kind, value, tb,
            # The same settings Textual would have used for the terminal, so
            # this file and a hand-saved one can be read against each other.
            show_locals=True, width=None, locals_max_length=5,
            suppress=[rich])
        into = io.StringIO()
        # No colour: this is read in an editor and grepped, not replayed.
        Console(file=into, width=150, no_color=True,
                force_terminal=False).print(drawn)
        return preface + into.getvalue()
    except Exception:
        pass
    try:
        return preface + "".join(traceback.format_exception(kind, value, tb))
    except Exception:
        return f"{type(error).__name__}: {error!r}\n"
