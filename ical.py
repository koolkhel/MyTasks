"""Read-only access to the machine's own calendar.

Only what a day needs: the events on it, from the accounts a person named.
Nothing here writes.  Events are kept in the calendar's own application and
shown here so that a day can be looked at in one place -- the meeting at two
is the reason the task at three will not happen, and a board that cannot say
so is describing a day it does not know.

Read through the system's calendar framework rather than the scriptable
interface, for two measured reasons.  A day costs one to three milliseconds
instead of twenty-one seconds, which is the difference between asking again
whenever the day changes and needing a cache.  And the framework expands a
repeating event onto every day it falls on, where the scriptable interface
reports only the rule: of 106 events in a fortnight on the machine this was
written against, all 106 came from a repetition, so the other route would
have shown almost nothing while appearing to work.

Everything identifying -- which accounts, which of them is work -- comes from
the environment.  None of it is written here.

macOS only, and the only part of the board that is.  Reading the calendar
needs a permission granted outside the board, which may be refused or
withdrawn; every such case arrives here as `CalendarUnreadable`.
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass

from dotenv import load_dotenv

#: How long to wait for a person to answer the permission dialogue.
ACCESS_TIMEOUT_SECONDS = 30
#: What the system calls its answers.  Full access is the only one that can
#: read; "write only" is the trap -- it reports itself as granted and returns
#: nothing, so a day would look free rather than unreadable.
_NOT_DETERMINED, _FULL_ACCESS, _WRITE_ONLY = 0, 3, 4
_ACCESS_TROUBLE = {
    1: "the calendar is restricted on this machine",
    2: "permission to read the calendar was refused"
       " -- grant it in Privacy & Security, then start the terminal afresh",
    _WRITE_ONLY: "permission to read the calendar was granted only in part"
                 " -- change it from adding events to full access, then start"
                 " the terminal afresh",
    None: "the calendar could not be read",
}


class CalendarUnreadable(Exception):
    """The calendar could not be read.

    Its own type so a caller can tell "the calendar is shut to us" from "the
    day could not be loaded": the two must never be reported as each other.
    Covers a refused permission, a withdrawn one, a permission granted only
    in part, and a machine with no such framework at all.
    """


@dataclass(frozen=True)
class Config:
    """Which calendar accounts to read, and which of them is work."""

    #: The account whose events count as work, so that the key hiding work
    #: hides them too.  Empty when none does.
    work: str
    #: The accounts whose events are shown but are not work.
    personal: tuple[str, ...]

    @property
    def accounts(self) -> tuple[str, ...]:
        """Every account to read, work first."""
        return ((self.work,) if self.work else ()) + self.personal

    def is_work(self, account: str) -> bool:
        """Whether events from this account count as work.

        Matched the way the accounts are matched when reading them, so an
        account is not read under one spelling and then missed under another.
        """
        return bool(self.work) and account.casefold() == self.work.casefold()


@dataclass(frozen=True)
class Event:
    """One occurrence of a calendar event, on one day."""

    title: str
    account: str
    calendar: str
    start: _dt.datetime
    end: _dt.datetime
    all_day: bool
    #: Where the event says it happens.  Often the address that joins it
    #: rather than a place, which is why it is carried rather than drawn.
    location: str = ""
    #: What the event says about itself, as written.
    #:
    #: Both of these are kept exactly as the calendar holds them and are not
    #: parsed here.  Which of them holds an address the board is willing to
    #: open is the board's own rule -- the same one it applies to a task's
    #: title -- and copying that rule into this module would be a second
    #: copy of a decision about what may be launched.
    notes: str = ""

    @property
    def label(self) -> str:
        """When it starts, as a row shows it."""
        return "all-day" if self.all_day else self.start.strftime("%H:%M")

    def ended_by(self, moment: _dt.datetime) -> bool:
        """Whether this event is over by then.

        The end, not the start.  An event that has begun and not finished is
        one there is still a chance of joining, and calling it past would say
        there was not.

        An all-day event ends when its day does, which is what the calendar
        stores for it, so a day already behind reads as over and the day
        itself does not.
        """
        return self.end <= moment

    def sort_key(self) -> tuple:
        """Where it falls among a day's rows.

        All-day events lead, because they describe the day rather than a
        moment in it; the rest go by when they start, then by title so that
        two at the same minute never swap about between redraws.
        """
        return (not self.all_day, self.start.timetuple()[3:5], self.title.casefold())


def load_config(env_path: str | os.PathLike[str] | None = None) -> Config | None:
    """The calendar's configuration, or None when there is none.

    Two entries rather than one list, because the work filter has to know
    which account is work and a single list could not say.

    No account configured means no calendar is configured, which is an
    ordinary board rather than a broken one -- so this answers None rather
    than raising.
    """
    load_dotenv(env_path, override=False)
    work = os.getenv("CALENDAR_WORK", "").strip()
    personal = tuple(
        a.strip() for a in os.getenv("CALENDAR_PERSONAL", "").split(",") if a.strip()
    )
    if not (work or personal):
        return None
    return Config(work, personal)


#: The one store this process uses.  Built once: the framework hands out
#: calendars for the first several stores a process creates and then quietly
#: returns none, which reads exactly like an account that has gone missing.
_STORE = None


def _store():
    """The system's event store, with access already established.

    Raises rather than returning something half-usable: a permission granted
    only in part reports itself as granted while returning nothing, and a day
    that wrongly shows no events looks exactly like a free one.
    """
    global _STORE
    if _STORE is not None:
        return _STORE

    try:
        from EventKit import EKEventStore, EKEntityTypeEvent
        from Foundation import NSDate, NSRunLoop
    except ImportError as exc:                       # not macOS, or not installed
        raise CalendarUnreadable(
            "the calendar framework is not available on this machine"
        ) from exc

    status = _status()
    if status == _NOT_DETERMINED:
        store = EKEventStore.alloc().init()
        answered: dict = {}
        _request(store, lambda granted, err: answered.update(granted=bool(granted)))
        deadline = NSDate.dateWithTimeIntervalSinceNow_(ACCESS_TIMEOUT_SECONDS)
        loop = NSRunLoop.currentRunLoop()
        while "granted" not in answered and NSDate.date().compare_(deadline) < 0:
            loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        status = _status()

    if status != _FULL_ACCESS:
        raise CalendarUnreadable(_ACCESS_TROUBLE.get(status, _ACCESS_TROUBLE[None]))
    _STORE = EKEventStore.alloc().init()
    return _STORE


def _status() -> int:
    """What the system says this program may do with the calendar.

    Its own function so the answers can be exercised without the machine
    having to be in each of those states.
    """
    from EventKit import EKEventStore, EKEntityTypeEvent

    return EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent)


def _request(store, callback) -> None:
    """Ask for access, by whichever name this system knows."""
    from EventKit import EKEntityTypeEvent
    ask = getattr(store, "requestFullAccessToEventsWithCompletion_", None)
    if ask is not None:
        ask(callback)
    else:
        store.requestAccessToEntityType_completion_(EKEntityTypeEvent, callback)


def fetch(config: Config, day: _dt.date) -> list[Event]:
    """Every event on `day` from the configured accounts, in the order shown.

    Asked afresh for each day rather than cached: a day costs a couple of
    milliseconds, so there is nothing to keep in step and nothing to go stale.

    An account that names nothing on the machine is reported rather than
    quietly contributing no events, because an empty day and a misconfigured
    one look identical on screen and mean opposite things.
    """
    from Foundation import NSDate

    store = _store()
    from EventKit import EKEntityTypeEvent

    wanted = {a.casefold() for a in config.accounts}
    calendars, seen = [], set()
    for cal in store.calendarsForEntityType_(EKEntityTypeEvent) or []:
        source = cal.source()
        account = str(source.title()) if source is not None else ""
        seen.add(account.casefold())
        if account.casefold() in wanted:
            calendars.append((cal, account))
    if not seen:
        # No accounts at all is the calendar being unreadable, not every
        # configured account having vanished at once.  Blaming the
        # configuration here would send someone to edit a correct setting.
        raise CalendarUnreadable(_ACCESS_TROUBLE[None])
    missing = sorted(a for a in config.accounts if a.casefold() not in seen)
    if missing:
        raise CalendarUnreadable(
            f"no calendar account named {', '.join(missing)} on this machine"
        )
    if not calendars:
        return []

    begin = _dt.datetime.combine(day, _dt.time.min)
    finish = begin + _dt.timedelta(days=1)
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        NSDate.dateWithTimeIntervalSince1970_(begin.timestamp()),
        NSDate.dateWithTimeIntervalSince1970_(finish.timestamp()),
        [cal for cal, _ in calendars],
    )
    account_of = {str(cal.calendarIdentifier()): account for cal, account in calendars}
    return parse(store.eventsMatchingPredicate_(predicate) or [], account_of)


def parse(raw, account_of: dict[str, str]) -> list[Event]:
    """The framework's events as this module's own, in the order shown.

    Kept apart from `fetch` so the ordering and the field handling can be
    exercised without a calendar to read.
    """
    events = []
    for item in raw:
        cal = item.calendar()
        identifier = str(cal.calendarIdentifier()) if cal is not None else ""
        events.append(
            Event(
                title=str(item.title() or ""),
                account=account_of.get(identifier, ""),
                calendar=str(cal.title()) if cal is not None else "",
                start=_stamp(item.startDate()),
                end=_stamp(item.endDate()),
                all_day=bool(item.isAllDay()),
                location=str(item.location() or ""),
                notes=str(item.notes() or ""),
            )
        )
    return sorted(events, key=Event.sort_key)


def _stamp(value) -> _dt.datetime:
    """A framework date as a local one."""
    return _dt.datetime.fromtimestamp(value.timeIntervalSince1970())
