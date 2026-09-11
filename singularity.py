"""Client for the SingularityApp REST API v2.

Docs: https://singularity-app.ru/wiki/api/
Swagger: https://api.singularity-app.com/v2/api  (JSON at /v2/api-json)

Quirks worth knowing, discovered against the live API:

* The date filters reject date-only values ("2026-09-03") and reject numeric
  UTC offsets ("...+03:00"), despite what the docs show.  Only full ISO
  datetimes ending in "Z" are accepted, so every datetime is normalised to
  UTC-Z before it goes out.  See `iso_z`.
* `startDateFrom` / `startDateTo` are deprecated aliases for `start.gte` /
  `start.lte`; this client uses the modern spelling.
* All timestamps come back in UTC, so "today" is a window between two UTC
  instants derived from local midnight, not a date string.  See `day_bounds`.
* With `includeAllRecurrenceInstances=false` (the default) the server
  post-filters after paging, so `count` can be under `maxCount` and offset
  paging can skip rows.  `iter_tasks` therefore forces the flag on when it
  pages.
"""

from __future__ import annotations

import enum
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from itertools import chain
from typing import Any, Iterable, Iterator, Sequence

import requests
from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.singularity-app.com/v2"
MAX_PAGE = 1000
# How far apart a fresh run of hand-set orders is spaced, and how far past a
# neighbour a task goes when nothing bounds it on that side.  Wide enough
# that many later moves fit between two rows without respacing them.
ORDER_STEP = 1000

# `checked` values (per TaskCreateDto in the spec).
EMPTY, CHECKED, CANCELLED = 0, 1, 2
# `priority` values.
HIGH, NORMAL, LOW = 0, 1, 2
# `state` values.
PINNED, UNPINNED = 0, 1

PRIORITY_NAMES = {HIGH: "high", NORMAL: "normal", LOW: "low"}


class Bucket(enum.Enum):
    """The two places a task can sit when it has no date.

    A board position is either a `datetime.date` or one of these, so callers
    pass a single value instead of a date plus a pair of flags that could
    contradict each other.  Both buckets are `start.isSet=false` upstream;
    `deferred` is what separates them.

    SOMEDAY is named after what SingularityApp itself calls this state: a
    task set to Someday there comes back as `start=None, deferred=true`,
    which is exactly this bucket.  `deferred` is the only dateless flag the
    API has, so there is no separate "never".
    """

    INBOX = "inbox"
    SOMEDAY = "someday"

    @property
    def deferred(self) -> bool:
        """Whether tasks in this bucket carry the API's `deferred` flag."""
        return self is Bucket.SOMEDAY

    @property
    def label(self) -> str:
        return "Inbox" if self is Bucket.INBOX else "Someday"


#: A position the board can show: one calendar day, or one of the buckets.
Position = "date | Bucket"


class SingularityError(Exception):
    """Any failure talking to the API."""


class ApiError(SingularityError):
    """The API answered with a non-2xx status."""

    def __init__(self, status: int, message: str, payload: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message
        self.payload = payload


# --------------------------------------------------------------------------
# time helpers
# --------------------------------------------------------------------------

def local_tz() -> tzinfo:
    """The machine's local timezone, as a fixed-offset tzinfo."""
    return datetime.now().astimezone().tzinfo or timezone.utc


def iso_z(moment: datetime) -> str:
    """Format a datetime the one way the API's date filters accept.

    Naive datetimes are read as local time.  The result always ends in "Z"
    because numeric offsets are rejected by the server.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=local_tz())
    return (
        moment.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def parse_dt(value: str | None) -> datetime | None:
    """Parse an API timestamp into an aware datetime (None passes through)."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def day_bounds(day: date, tz: tzinfo | None = None) -> tuple[str, str]:
    """The half-open local day [00:00, 24:00) as two ISO-Z instants.

    The upper bound is the last millisecond of the day rather than the next
    midnight, because the API's `start.lte` filter is inclusive: using
    midnight itself would pull in the following day's first task.
    """
    tz = tz or local_tz()
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = datetime.combine(day, time.max, tzinfo=tz)
    return iso_z(start), iso_z(end)


# --------------------------------------------------------------------------
# task model
# --------------------------------------------------------------------------

@dataclass
class Task:
    """A task, wrapping the raw API dict with the bits the UI cares about."""

    raw: dict[str, Any] = field(repr=False)

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def title(self) -> str:
        return self.raw.get("title") or "(untitled)"

    @property
    def checked(self) -> int:
        return self.raw.get("checked") or 0

    @property
    def done(self) -> bool:
        return self.checked == CHECKED

    @property
    def cancelled(self) -> bool:
        return self.checked == CANCELLED

    @property
    def priority(self) -> int:
        p = self.raw.get("priority")
        return NORMAL if p is None else p

    @property
    def pinned(self) -> bool:
        return self.raw.get("state") == PINNED

    @property
    def project_id(self) -> str | None:
        return self.raw.get("projectId") or None

    @property
    def tags(self) -> tuple[str, ...]:
        """The tag ids this task carries, in the order the API gave them.

        A row the board made up rather than fetched -- a tracker issue --
        has no tags at all, and neither does a task the API answered without
        the field, so the absent case is a tuple rather than an error.
        """
        return tuple(self.raw.get("tags") or ())

    def has_tag(self, tag_id: str | None) -> bool:
        """Whether this task carries `tag_id`; False when none is configured."""
        return bool(tag_id) and tag_id in self.tags

    @property
    def is_note(self) -> bool:
        return bool(self.raw.get("isNote"))

    @property
    def schedule_order(self) -> int:
        """The task's place in a hand-set sequence.

        The API stores this as an integer and hands 0 to anything created
        without one, so a missing key and a stored 0 mean the same thing:
        the very start of the order.
        """
        return self.raw.get("scheduleOrder") or 0

    @property
    def deferred(self) -> bool:
        """The API's "someday" flag; always paired with no start date."""
        return bool(self.raw.get("deferred"))

    @property
    def recurring(self) -> bool:
        return bool(self.raw.get("recurrence"))

    @property
    def start(self) -> datetime | None:
        return parse_dt(self.raw.get("start"))

    @property
    def deadline(self) -> datetime | None:
        return parse_dt(self.raw.get("deadline"))

    @property
    def timed(self) -> bool:
        """True when the start carries a meaningful time of day."""
        return bool(self.raw.get("useTime"))

    def local_start(self, tz: tzinfo | None = None) -> datetime | None:
        started = self.start
        return started.astimezone(tz or local_tz()) if started else None

    def start_label(self, tz: tzinfo | None = None) -> str:
        """"HH:MM" for timed tasks, "all-day" otherwise."""
        if not self.timed:
            return "all-day"
        started = self.local_start(tz)
        return started.strftime("%H:%M") if started else "all-day"

    @property
    def display_title(self) -> str:
        """The title as words, with any stored link markup unwrapped.

        Titles arrive from a browser capture as `<a href="...">text</a>`
        embedded in ordinary words, which the board would otherwise print
        verbatim.  The anchor's visible text is what a person wrote, so that
        is what is shown; the target is what `link` opens.  They happen to be
        identical in every stored link today, but that is a coincidence of
        the capture, not a rule.
        """
        title = self.raw.get("title") or ""
        return _ANCHOR.sub(lambda m: m.group(2).strip() or m.group(1), title).strip()

    @property
    def link_text(self) -> str | None:
        """The words in the display title that stand for the link.

        An anchor's visible text, or the address itself when it was written
        plainly.  Needed because the two are not always the same: wrapping
        the address would find nothing to wrap in a title that reads
        "the article" and links elsewhere.
        """
        title = self.raw.get("title") or ""
        for href, text in _ANCHOR.findall(title):
            if openable_url(href):
                return (text.strip() or href)
        for found in _BARE_URL.findall(_ANCHOR.sub(" ", title)):
            if openable_url(found):
                return found
        return None

    @property
    def link(self) -> str | None:
        """The first openable address in the title, or None.

        Anchors are considered before plain addresses, and the first match
        wins; every address stays visible in the title either way.  The
        search itself is `url_in`, which the calendar's events use on their
        own text, so what counts as an address cannot come to differ
        between a title and an event.
        """
        return url_in(self.raw.get("title"))

    def past_due_since(
        self, now: datetime, tz: tzinfo | None = None
    ) -> datetime | None:
        """When this task first became late, or None if it is not.

        Late means an unfinished task whose start day is already over, or
        whose deadline has passed.  When both apply the earlier one wins:
        that is the moment it first slipped, and it is what "how overdue"
        should be measured from.

        A deferred task is never late.  The someday view exists to put a task
        aside, and calling it overdue would drag it back into today.

        Pure in `now` on purpose -- no clock is read here -- so the rule can
        be checked against a fixed instant without touching the API.
        """
        if self.done or self.cancelled or self.deferred:
            return None
        tz = tz or local_tz()
        triggers = []
        started = self.start
        if started is not None:
            # The whole start day has to be over, so compare against the day
            # after it: a task starting later today is not late yet.
            day_after = datetime.combine(
                started.astimezone(tz).date() + timedelta(days=1),
                time.min,
                tzinfo=tz,
            )
            if day_after <= now:
                triggers.append(started)
        deadline = self.deadline
        if deadline is not None and deadline < now:
            triggers.append(deadline)
        return min(triggers) if triggers else None

    @property
    def note_is_plain(self) -> bool:
        """Whether this note is text alone, and so safe to rewrite as text.

        False for a note carrying a styled run, a line kind, or anything
        embedded that is not text.  The board shows a note as text and can
        only store it as text, so rewriting one of these would mean keeping
        the words and dropping everything else -- and a person who cannot see
        what was dropped cannot object to it.  Answered here so that both the
        refusal and the write ask the same question.
        """
        note = self.raw.get("note")
        if not note or not isinstance(note, str):
            return True
        stripped = note.strip()
        if not stripped.startswith("["):
            # An older plain string, which is text by definition.
            return True
        import json

        try:
            ops = json.loads(stripped)
        except json.JSONDecodeError:
            return True
        if not isinstance(ops, list):
            return True
        for op in ops:
            if not isinstance(op, dict):
                continue
            if not isinstance(op.get("insert"), str):
                return False          # an embed: an image, a formula
            if op.get("attributes"):
                return False          # a styled run, or a line kind
        return True

    @property
    def note_text(self) -> str:
        """The note as plain text.

        Notes are stored in Quill delta format -- a JSON array of
        `{"insert": "..."}` ops -- but older tasks hold a plain string, so
        handle both and fall back to the raw value.
        """
        note = self.raw.get("note")
        if not note:
            return ""
        if isinstance(note, str):
            stripped = note.strip()
            if not stripped.startswith("["):
                return note
            import json

            try:
                note = json.loads(stripped)
            except json.JSONDecodeError:
                return note
        if isinstance(note, list):
            parts = []
            for op in note:
                if isinstance(op, dict) and isinstance(op.get("insert"), str):
                    parts.append(op["insert"])
            return "".join(parts).strip()
        return str(note)


@dataclass
class Listing:
    """The tasks a view shows, plus what it deliberately withheld.

    `filed_out` is only ever non-zero for the inbox: it counts the unfinished
    undated tasks kept out for already having a project, so the board can say
    they exist without putting them in the triage queue.
    """

    tasks: list[Task]
    filed_out: int = 0
    #: How many of `tasks` are past due; only today's view gathers any.
    past_due: int = 0
    #: The instant every past-due decision in this listing was made against,
    #: so a caller styling a row asks the same question the counts answered.
    reference: datetime | None = None

    @property
    def due_now(self) -> int:
        """Rows that are not past due -- what the shown day itself holds."""
        return len(self.tasks) - self.past_due

    def __iter__(self):
        return iter(self.tasks)

    def __len__(self) -> int:
        return len(self.tasks)


# --------------------------------------------------------------------------
# client
# --------------------------------------------------------------------------

def load_token(env_path: str | os.PathLike[str] | None = None) -> str:
    """Read SINGULARITY_TOKEN from the environment, loading .env first."""
    load_dotenv(env_path, override=False)
    token = os.getenv("SINGULARITY_TOKEN", "").strip()
    if not token:
        raise SingularityError(
            "SINGULARITY_TOKEN is not set -- put it in .env or the environment"
        )
    return token


def load_work_project(env_path: str | os.PathLike[str] | None = None) -> str | None:
    """The project id that counts as work, or None if none is configured.

    Read from the environment beside the token rather than written into the
    source: a project id names something personal, and `.env` is the one
    place such a thing lives and is already outside version control.

    Absent and blank both mean "not configured", which is a state the board
    reports rather than an error -- the board is perfectly usable without a
    work project, it just cannot hide one.
    """
    load_dotenv(env_path, override=False)
    return os.getenv("WORK_PROJECT", "").strip() or None


def load_green_tag(env_path: str | os.PathLike[str] | None = None) -> str | None:
    """The tag id that marks a task green, or None if none is configured.

    Beside the work project and for the same reason: a tag id names
    something personal, and the board's source should carry neither the id
    nor the tag's name.

    Absent and blank both mean "not configured", which leaves an ordinary
    board that simply marks nothing.
    """
    load_dotenv(env_path, override=False)
    return os.getenv("GREEN_TAG", "").strip() or None


def load_workspace_command(
    env_path: str | os.PathLike[str] | None = None,
) -> str | None:
    """The program that makes a workspace, or None if none is configured.

    A path to something the board execs, never a command line it interprets.
    That is the whole of the safety argument: a version or a project key is a
    value somebody typed into a tracker, and handing one to a shell would make
    what it contains a question about this board rather than about that
    tracker.  There is no shell here to ask.

    Beside the work project and the green tag, and read the same way -- the
    path names a person's own machine, and `.env` is where such a thing
    already lives outside version control.
    """
    load_dotenv(env_path, override=False)
    return os.getenv("WORKSPACE_COMMAND", "").strip() or None


#: The days of the week, as `date.weekday()` numbers them.
WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
            "fri": 4, "sat": 5, "sun": 6}
#: Which days a working window covers when none are configured.  Saturday and
#: Sunday are outside it: made to say so for the ordinary case, a person is
#: being asked to configure the obvious.
WORKING_DAYS = frozenset(range(5))
_RANGE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")
#: Minutes in a day, which is both the largest end a window may have and the
#: one no start may reach.
MINUTES_IN_DAY = 24 * 60


def clock(minutes: int) -> str:
    """Minutes since midnight, written the way the setting is."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass(frozen=True)
class WorkingWindow:
    """The hours and days within which work is shown.

    A value, asked about a moment rather than about the present: the board
    hands it `datetime.now`, and a suite hands it a Friday at 18:01 or a
    Saturday at noon without waiting for one to come round.
    """

    #: When the working day starts and ends, as minutes since local
    #: midnight.  Minutes rather than times so that the end may be 24:00,
    #: which no `time` can hold: without it the last minute of the day is
    #: outside every window that could be written, `18:00-24:00` cannot be
    #: said at all, and a suite asserting on an all-day window is wrong one
    #: run in fourteen hundred.  Inside is `start <= t < end`, so the end
    #: minute itself is already outside.
    start: int
    end: int
    #: The days the window covers, as `date.weekday()` numbers them.
    days: frozenset[int]

    def outside(self, moment: datetime) -> str | None:
        """Why this moment is outside the window, or None if it is inside.

        The answer is the boundary that put it there, in the words the board
        shows: "outside the working week", "after 18:00", "before 08:00".
        One method rather than a token and a phrase derived from it, so the
        reason the board gives and the reason it acts on cannot drift apart.

        A day outside the window is outside it for its whole length, so the
        day is asked first and the hours are never consulted on a Sunday.
        """
        if moment.weekday() not in self.days:
            return "outside the working week"
        minutes = moment.hour * 60 + moment.minute
        if minutes < self.start:
            return f"before {clock(self.start)}"
        if minutes >= self.end:
            return f"after {clock(self.end)}"
        return None

    def label(self) -> str:
        """The window as it was written, for the board to quote back."""
        return f"{clock(self.start)}-{clock(self.end)}"


def parse_days(days: str) -> frozenset[int]:
    """The days those words name, as `date.weekday()` numbers them.

    A comma-separated list of three-letter English abbreviations, each of
    them either a day or a range of days; case and spacing are ignored.  A
    range may run round the end of the week, because a working week that
    starts on Sunday is somebody's ordinary one.

    Blank means the default working week.  Raises ValueError naming what
    could not be read.
    """
    days = days.strip()
    if not days:
        return WORKING_DAYS
    chosen: set[int] = set()
    for piece in days.split(","):
        piece = piece.strip().lower()
        if not piece:
            continue
        ends = piece.split("-")
        if len(ends) > 2 or any(e.strip() not in WEEKDAYS for e in ends):
            raise ValueError(f"{piece!r} is not a day of the week")
        first = WEEKDAYS[ends[0].strip()]
        last = WEEKDAYS[ends[-1].strip()]
        # Inclusive, and round the end of the week when it has to be: the
        # span from `first` to `last` is however many steps forward that is.
        span = (last - first) % 7
        chosen.update((first + step) % 7 for step in range(span + 1))
    if not chosen:
        raise ValueError(f"{days!r} names no day of the week")
    return frozenset(chosen)


def parse_working_window(hours: str, days: str = "") -> WorkingWindow:
    """The window those two settings describe.

    Raises ValueError saying what could not be read.  The board reports that
    and carries on with no window: an unreadable setting costs a person the
    feature, not their board.

    Takes the settings as strings rather than reading them itself, so that
    the self-contained suites can exercise it without going near a file.
    python-dotenv finds `.env` by walking up from this module, so emptying
    the environment does not hide a real one -- four suites here were
    mistaken for self-contained on exactly that point.
    """
    match = _RANGE.match(hours)
    if match is None:
        raise ValueError(f"{hours!r} is not a range of hours like 08:00-18:00")
    start = int(match[1]) * 60 + int(match[2])
    end = int(match[3]) * 60 + int(match[4])
    for hour, minute in ((int(match[1]), int(match[2])),
                         (int(match[3]), int(match[4]))):
        # 24:00 is allowed as an end, and only as an end, because "until
        # midnight" is a thing a person means and no other spelling says it.
        if minute > 59 or hour > 24 or (hour == 24 and minute):
            raise ValueError(f"{hours!r} names no such time as "
                             f"{hour:02d}:{minute:02d}")
    if start >= MINUTES_IN_DAY:
        raise ValueError(f"{hours!r} starts at the end of the day")
    if end <= start:
        # Not wrapped round midnight: a window that wrapped would have no
        # single day that is outside it, and the rule about days would stop
        # meaning anything.
        raise ValueError(f"{hours!r} does not run forwards within one day")
    return WorkingWindow(start=start, end=end, days=parse_days(days))


def load_working_window(
    env_path: str | os.PathLike[str] | None = None,
) -> WorkingWindow | None:
    """The configured working window, or None if none is configured.

    Beside the work project and the green tag, and read the same way: the
    hours a particular person works are theirs, and `.env` is the one place
    such a thing already lives outside version control.

    Absent and blank both mean "not configured", which leaves the board
    exactly as it is without this at all -- nothing hidden until the key is
    pressed.  A window is something a person turns on, never something they
    have to turn off.  Raises ValueError when one is configured and cannot
    be read.
    """
    load_dotenv(env_path, override=False)
    hours = os.getenv("WORK_HOURS", "").strip()
    if not hours:
        return None
    return parse_working_window(hours, os.getenv("WORK_DAYS", "").strip())


class SingularityClient:
    """Thin wrapper over the REST API.

    Only the endpoints this app needs are spelled out; anything else in the
    API is reachable through `request`.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 20.0,
        tz: tzinfo | None = None,
        green: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.tz = tz or local_tz()
        # The tag that orders a task first.  The client holds it because the
        # client is what sorts a fetched listing, and the board would
        # otherwise disagree with the order it was handed.
        self.green = green if green is not None else load_green_tag()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token or load_token()}",
                "Accept": "application/json",
            }
        )

    # -- plumbing ----------------------------------------------------------

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        params = kwargs.pop("params", None)
        if params:
            params = _clean_params(params)
        try:
            response = self.session.request(
                method, url, params=params, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise SingularityError(f"{method} {url} failed: {exc}") from exc

        payload: Any = None
        if response.content:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text

        if not response.ok:
            message = response.reason
            if isinstance(payload, dict):
                detail = payload.get("message") or payload.get("error")
                if isinstance(detail, list):
                    detail = "; ".join(str(d) for d in detail)
                message = detail or message
            elif isinstance(payload, str) and payload:
                message = payload[:200]
            raise ApiError(response.status_code, str(message), payload)
        return payload

    def get(self, path: str, **params: Any) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any] | None = None, **params: Any) -> Any:
        return self.request("POST", path, json=body or {}, params=params)

    def patch(self, path: str, body: dict[str, Any]) -> Any:
        return self.request("PATCH", path, json=body)

    def delete(self, path: str, **params: Any) -> Any:
        return self.request("DELETE", path, params=params)

    # -- tasks -------------------------------------------------------------

    def list_tasks(self, **filters: Any) -> list[Task]:
        """One page of tasks (server default ordering)."""
        payload = self.get("/task", **filters)
        return [Task(row) for row in payload.get("tasks", [])]

    def iter_tasks(self, page_size: int = MAX_PAGE, **filters: Any) -> Iterator[Task]:
        """Every matching task, paging until the server runs out.

        Recurrence instances are forced on: with them off the server
        post-filters each page and offset paging can silently skip rows.
        """
        filters = dict(filters, includeAllRecurrenceInstances=True)
        offset = 0
        while True:
            payload = self.get(
                "/task", maxCount=page_size, offset=offset, paginationData=True, **filters
            )
            rows = payload.get("tasks", [])
            for row in rows:
                yield Task(row)
            page = payload.get("pagination") or {}
            total = page.get("total")
            offset += len(rows)
            if not rows or (total is not None and offset >= total):
                return

    def tasks_for_day(
        self,
        day: date | None = None,
        include_done: bool = True,
        **filters: Any,
    ) -> Listing:
        """Tasks starting on a local calendar day, ordered for display.

        Completed tasks are archived by the app, so `includeArchived` has to
        be on for them to show up at all -- without it a day you have already
        worked through comes back looking empty.
        """
        now = datetime.now(self.tz)
        day = day or now.date()
        lower, upper = day_bounds(day, self.tz)
        filters.setdefault("includeArchived", include_done)

        def day_query() -> list[Task]:
            return self.list_tasks(
                **{"start.gte": lower, "start.lte": upper, "maxCount": MAX_PAGE},
                **filters,
            )

        if day != now.date():
            # Only today gathers, counts, or marks what is past due.  On any
            # other day the tasks shown are that day's own -- and yesterday's
            # unfinished ones are late by definition, so carrying a reference
            # instant here would repaint the whole view as overdue.
            tasks = day_query()
            if not include_done:
                tasks = [t for t in tasks if not t.done and not t.cancelled]
            return Listing(
                sort_for_display(tasks, self.tz, manual=True, green=self.green)
            )

        # Today costs three queries, so they go out together rather than one
        # after another: the day itself plus the two that find what is past
        # due.  Results are collected in a fixed order, never in the order
        # they happen to arrive, so the view does not depend on the timing.
        queries = (day_query, *self._past_due_queries(now, **filters))
        with ThreadPoolExecutor(len(queries)) as pool:
            futures = [pool.submit(q) for q in queries]
            # Reading a future re-raises whatever it raised, so a failure in
            # any one query fails the whole load instead of yielding a day
            # quietly missing some of its tasks.
            tasks, *late = (f.result() for f in futures)

        if not include_done:
            tasks = [t for t in tasks if not t.done and not t.cancelled]

        extra = [t for t in self._combine_past_due(now, late)
                 if t.id not in {x.id for x in tasks}]
        tasks = tasks + extra
        return Listing(
            sort_for_display(tasks, self.tz, now, manual=True, green=self.green),
            past_due=sum(1 for t in tasks if t.past_due_since(now, self.tz)),
            reference=now,
        )

    def _past_due_queries(self, now: datetime, **filters: Any):
        """The two queries whose union is what is past due.

        Two of them, because the filters combine with AND: asking for a
        passed start and a passed deadline in one call returns only tasks
        with both, not either.  They are handed back unrun so a caller can
        issue them alongside its own.
        """
        midnight = iso_z(datetime.combine(now.date(), time.min, tzinfo=self.tz))
        # includeArchived=False is not the same as "unfinished": a task can
        # be completed without being archived, and such tasks do come back
        # from this query.  The completion check in `past_due_since` is what
        # actually keeps them out, so it is not redundant.
        shared = dict(filters, includeArchived=False, maxCount=MAX_PAGE)
        return (
            lambda: self.list_tasks(**{"start.lt": midnight}, **shared),
            lambda: self.list_tasks(**{"deadline.lt": iso_z(now)}, **shared),
        )

    def _combine_past_due(
        self, now: datetime, results: "Iterable[list[Task]]"
    ) -> list[Task]:
        """The union of the past-due queries, de-duplicated by id.

        A task can qualify under both rules, so the first copy seen wins.
        Callers pass results in a fixed order, which is what keeps the union
        the same however the queries were scheduled.
        """
        found: dict[str, Task] = {}
        for task in chain(*results):
            if task.past_due_since(now, self.tz):
                found.setdefault(task.id, task)
        return list(found.values())

    def _past_due_tasks(self, now: datetime, **filters: Any) -> list[Task]:
        """Unfinished tasks whose start day is over or whose deadline passed."""
        queries = self._past_due_queries(now, **filters)
        with ThreadPoolExecutor(len(queries)) as pool:
            futures = [pool.submit(q) for q in queries]
            return self._combine_past_due(now, [f.result() for f in futures])

    def tasks_in_bucket(self, bucket: Bucket, **filters: Any) -> Listing:
        """Unfinished dateless tasks, split by the `deferred` flag.

        Finished tasks are left out on purpose, and this is the one place the
        dateless views diverge from `tasks_for_day`: undated tasks number a
        few dozen while open but a couple of thousand once archived ones are
        counted, so including them would bury whatever is awaiting triage.

        The inbox additionally drops tasks that already have a project -- a
        filed task has been sorted, so it is not awaiting triage -- and
        reports how many it dropped.  The split happens here rather than in
        the query so one request yields both numbers.  The someday view keeps
        filed tasks: something set aside deliberately stays visible whether
        or not it has been filed.
        """
        tasks = self.list_tasks(
            **{
                "start.isSet": False,
                "deferred.eq": bucket.deferred,
                "maxCount": MAX_PAGE,
            },
            **filters,
        )
        tasks = [t for t in tasks if not t.done and not t.cancelled]
        filed_out = 0
        if bucket is Bucket.INBOX:
            unfiled = [t for t in tasks if not t.project_id]
            filed_out = len(tasks) - len(unfiled)
            tasks = unfiled
        return Listing(sort_for_display(tasks, self.tz, green=self.green), filed_out)

    def tasks_at(self, position: "date | Bucket", **filters: Any) -> Listing:
        """Tasks for whichever position the board is showing."""
        if isinstance(position, Bucket):
            return self.tasks_in_bucket(position, **filters)
        return self.tasks_for_day(position, **filters)

    def get_task(self, task_id: str) -> Task:
        payload = self.get(f"/task/{task_id}")
        return Task(payload.get("task", payload))

    def create_task(self, title: str, **fields: Any) -> Task:
        payload = self.post("/task", {"title": title, **fields})
        return Task(payload.get("task", payload))

    def update_task(self, task_id: str, **fields: Any) -> Task:
        payload = self.patch(f"/task/{task_id}", fields)
        return Task(payload.get("task", payload))

    def set_project(self, task_id: str, project_id: str) -> Any:
        """Put a task in a project.

        One way only, and not by choice: the field must match `^(?:P)-`, and
        both an empty value and a null are refused, so nothing that can be
        sent returns a task to having no project.  A task can be moved to a
        different project; it cannot be un-filed.

        This goes through `/move` rather than an ordinary update because
        filing a task also puts it in one of that project's groups, and a
        plain `projectId` update then fails with GROUP_PROJECT_MISMATCH for
        any task that already has one -- its group still belongs to the old
        project.  `/move` reassigns the group along with the project, so it
        is the only call that handles both filing and moving.  It is
        idempotent, and it leaves the title, dates, completion and stored
        order alone.
        """
        return self.post(f"/task/{task_id}/move", {"projectId": project_id})

    def restore(self, task_id: str, fields: dict[str, Any]) -> Any:
        """Put a task's fields back to given values.

        An ordinary update carries all of them but one: a project has to go
        through `/move`, because a task filed into one also holds a group
        belonging to it and a plain `projectId` update is refused.  That is
        the only field with a route of its own, and knowing it here is what
        keeps undo from needing an inverse per action.
        """
        fields = dict(fields)
        project = fields.pop("projectId", None)
        result: Any = None
        if fields:
            result = self.update_task(task_id, **fields)
        if project is not None:
            result = self.set_project(task_id, project)
        return result

    def set_schedule_order(self, task_id: str, order: int) -> Task:
        """Put a task at a given place in a hand-set sequence.

        One write against one task, which is what makes a move impossible to
        half-apply: the alternative, exchanging two tasks' values, needs two
        writes, and `/v2/batch` executes its operations independently rather
        than as one transaction.
        """
        return self.update_task(task_id, scheduleOrder=order)

    def set_schedule(
        self,
        task_id: str,
        position: "date | Bucket",
        use_time: bool = False,
    ) -> Task:
        """Move a task to a day, to someday, or back to the inbox.

        `start` and `deferred` go out in one request because they are two
        halves of one fact and the server will not reconcile them: setting a
        date on a deferred task leaves `deferred` true unless it is cleared
        explicitly, a dated-and-deferred state that no real task is in and
        that no view would show consistently.  Sending both together is what
        makes that state unreachable.

        Clearing a date is the same operation as moving to the inbox, so it
        has no separate method.
        """
        if isinstance(position, Bucket):
            fields: dict[str, Any] = {"start": None, "deferred": position.deferred}
        else:
            fields = {
                "start": iso_z(datetime.combine(position, time.min, tzinfo=self.tz)),
                "useTime": use_time,
                "deferred": False,
            }
        return self.update_task(task_id, **fields)

    def delete_task(self, task_id: str) -> Any:
        return self.delete(f"/task/{task_id}")

    def complete_task(self, task_id: str) -> Any:
        return self.post(f"/task/{task_id}/complete")

    def uncomplete_task(self, task_id: str) -> Any:
        return self.post(f"/task/{task_id}/uncomplete")

    def complete_today(self, task_id: str) -> Any:
        """Tick off one occurrence of a recurring task, keeping the series."""
        return self.post(f"/task/{task_id}/complete-today")

    def cancel_task(self, task_id: str) -> Any:
        return self.post(f"/task/{task_id}/cancel")

    def set_done(self, task: Task, done: bool) -> Any:
        """Flip a task's completion.  Finishing means finishing, for any task.

        This deliberately does not route recurring tasks to `complete-today`.
        That endpoint means "worked on it today", which is a different
        intention and belongs to `done_for_today`; and it refuses any task
        not dated today, so the old routing failed outright for a recurring
        task shown on its own day.
        """
        if not done:
            return self.uncomplete_task(task.id)
        return self.complete_task(task.id)

    def done_for_today(self, task: Task) -> Task:
        """Record today's work on a task and put it up again tomorrow.

        The record has to be attempted before the date moves: the API takes
        `complete-today` only for a task dated today, so rescheduling first
        would make the record impossible.

        A task dated any other day -- every past-due one -- and an undated
        task are refused with 422.  That is an expected outcome for them, not
        a failure, so it is absorbed; every other error propagates, because
        swallowing them all would hide an expired token behind a task that
        looks rescheduled but was never recorded.

        Rescheduling goes through `set_schedule` so an undated deferred task
        loses its deferred flag as it gains a date, keeping "dated or
        deferred, never both" enforced in one place.
        """
        try:
            self.complete_today(task.id)
        except ApiError as exc:
            if exc.status != 422:
                raise
        tomorrow = datetime.now(self.tz).date() + timedelta(days=1)
        return self.set_schedule(task.id, tomorrow)

    # -- projects ----------------------------------------------------------

    def list_projects(self, **filters: Any) -> list[dict[str, Any]]:
        payload = self.get("/project", maxCount=MAX_PAGE, **filters)
        return payload.get("projects", [])

    def project_names(self, **filters: Any) -> dict[str, str]:
        """Map project id -> display title, for labelling tasks."""
        names = {}
        for project in self.list_projects(**filters):
            title = project.get("title") or ""
            emoji = decode_emoji(project.get("emoji"))
            names[project["id"]] = f"{emoji} {title}".strip() if emoji else title
        return names

    # -- tags --------------------------------------------------------------

    def tag_title(self, tag_id: str) -> str | None:
        """The title of one tag, or None if the id names nothing.

        Read one at a time rather than by listing: the account's tags cannot
        be listed with this token, but a tag is readable by its id, which is
        all the board needs to confirm what it was pointed at.
        """
        try:
            payload = self.get(f"/tag/{tag_id}")
        except ApiError as exc:
            if exc.status in (400, 403, 404):
                return None
            raise
        tag = payload.get("tag") if isinstance(payload, dict) and "tag" in payload else payload
        if not isinstance(tag, dict) or tag.get("removed"):
            return None
        return tag.get("title") or None

    def task_tags(self, task_id: str) -> tuple[str, ...]:
        """The tags the store currently holds for one task.

        Read back after a removal, because the store answers a removal it
        then does not apply.  A failure to read is reported as "still
        tagged", so a caller checking its own write tries again rather than
        believing a request that never arrived.
        """
        try:
            payload = self.get(f"/task/{task_id}")
        except SingularityError:
            return ("?",)
        task = payload.get("task") if isinstance(payload, dict) and "task" in payload else payload
        if not isinstance(task, dict):
            return ("?",)
        return tuple(task.get("tags") or ())

    def set_tags(self, task_id: str, tags: Sequence[str]) -> Any:
        """Replace a task's tags outright, which is what the API does.

        The field is not merged upstream, so a caller adding or dropping one
        tag has to send the rest back with it.
        """
        return self.patch(f"/task/{task_id}", {"tags": list(tags)})


#: Only these may be handed to the operating system's opener.  An allowlist
#: rather than a blocklist: a title is text a person typed or a browser
#: extension wrote, and the handler will launch whatever it is given.
OPENABLE_SCHEMES = ("http", "https")

#: `<a href="...">text</a>` as SingularityApp's browser capture stores it.
_ANCHOR = re.compile(r"<a\s[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
#: A plain address written into a title.
_BARE_URL = re.compile(r"https?://[^\s<>\"')\]]+")
#: Something with no scheme that still looks like a host, e.g. `academia.edu`.
_BARE_HOST = re.compile(r"^[\w-]+(?:\.[\w-]+)+(?:/\S*)?$")


def note_document(text: str | None) -> str:
    """Text as a note the store will accept.

    The mirror of `Task.note_text`.  A note is a string holding a delta: a
    document described as the inserts that build it from nothing, not a
    difference against anything.  One insert is enough for text, which is
    the only thing the board writes.

    The trailing newline is not decoration.  A delta document always ends
    with one, and every note on the account this was written against does;
    an encoder that omits it produces a document the editor at the other end
    treats as malformed.  So clearing a note means writing the newline
    alone -- which `note_text` already reads back as nothing, because it
    strips.
    """
    import json

    text = text or ""
    if not text.endswith("\n"):
        text += "\n"
    return json.dumps([{"insert": text}], ensure_ascii=False)


def urls_in(text: str | None) -> list[str]:
    """Every address in a piece of text that may be opened, in order.

    One scanner rather than one per kind of text: a task's title, a task's
    note, a calendar event's location and its description are all ordinary
    text that happens to be searched for something to hand to the system
    opener, and what may be handed over must be decided the same way for all
    of them.  `url_in` is the same walk stopped at the first, so the scheme
    allowlist is applied in exactly one place -- two scanners that had to
    agree about what may be launched is the arrangement worth avoiding.

    Anchors are read before plain addresses.  A stored anchor is the
    deliberate link, where a plain address may be incidental to the words
    around it; and the plain pass reads the text with the anchors taken out,
    so an anchor's own address is not also found loose.
    """
    text = text or ""
    found = []
    for href, _shown in _ANCHOR.findall(text):
        url = openable_url(href)
        if url:
            found.append(url)
    for raw in _BARE_URL.findall(_ANCHOR.sub(" ", text)):
        url = openable_url(raw)
        if url:
            found.append(url)
    return found


def url_in(text: str | None) -> str | None:
    """The first address in a piece of text that may be opened, or None."""
    for url in urls_in(text):
        return url
    return None


def openable_url(value: str | None) -> str | None:
    """The address to hand over, or None if it must not be opened.

    A value with no scheme is read as `https` when it looks like a host --
    one of the stored links is just `academia.edu` and would otherwise never
    open.  Anything whose scheme is not in `OPENABLE_SCHEMES` is refused.
    """
    if not value:
        return None
    value = value.strip()
    if "://" not in value:
        return f"https://{value}" if _BARE_HOST.match(value) else None
    scheme = value.split("://", 1)[0].lower()
    return value if scheme in OPENABLE_SCHEMES else None


def overdue_label(since: datetime, now: datetime) -> str:
    """How overdue, kept short enough for the when-column that shows it.

    Whole days elapsed, so something late this morning reads "1d ago" rather
    than a count of hours.  "999d ago" is the longest this returns, at 8
    cells; anything older saturates instead of being clipped mid-number,
    which would read as a smaller number rather than as a truncation.
    """
    days = max(1, (now - since).days)
    return "999d+" if days > 999 else f"{days}d ago"


def decode_emoji(value: str | None) -> str:
    """Turn a project's stored emoji into a character.

    Projects hold the emoji as hyphen-separated hex codepoints ("1f525", or
    "1f1f7-1f1fa" for a sequence), not as the character itself.  Anything that
    is not codepoints -- including an already-decoded emoji -- is handed back
    untouched.
    """
    if not value:
        return ""
    parts = value.split("-")
    try:
        return "".join(chr(int(part, 16)) for part in parts)
    except (ValueError, OverflowError):
        return value


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    """Drop None values and render booleans the way the API expects."""
    out = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, datetime):
            value = iso_z(value)
        elif isinstance(value, (list, tuple)):
            value = ",".join(str(v) for v in value)
        out[key] = value
    return out


def sort_key(
    task: Task,
    tz: tzinfo | None = None,
    now: datetime | None = None,
    manual: bool = False,
    green: str | None = None,
) -> tuple:
    """How one task orders against another within a view.

    The last two entries are the hand-set order and the title; everything
    before them is the task's group, which a manual sequence may not
    cross.  `group_key` takes exactly that prefix, so the two cannot come
    to disagree about where a group ends.

    `green` names the tag that lifts a task above the rest.  It ranks below
    only whether a task is finished, so it outranks how overdue a task is:
    marking a task is how a person says it comes before the backlog, and a
    rule where lateness won would say the opposite.  Finished work still
    sinks, marked or not.
    """
    tz = tz or local_tz()
    started = task.local_start(tz)
    late = task.past_due_since(now, tz) if now else None
    return (
        task.done or task.cancelled,
        not task.has_tag(green),
        late is None,
        # Most overdue first within the past-due group; constant elsewhere.
        late.timestamp() if late else 0.0,
        not task.pinned,
        not task.timed,
        started.timetuple()[3:5] if (started and task.timed) else (0, 0),
        task.schedule_order if manual else 0,
        task.title.casefold(),
    )


def group_key(
    task: Task,
    tz: tzinfo | None = None,
    now: datetime | None = None,
    green: str | None = None,
) -> tuple:
    """Everything `sort_for_display` decides before the hand-set order.

    Two tasks sharing this are the ones a manual sequence can arrange: a
    move may only carry a task past a neighbour it matches here, or it would
    be lifting the task out of its group and lying about the day.

    Derived from the same expression the sort uses rather than restating the
    conditions, so that adding an ordering key above the manual one keeps
    this honest without a second edit.
    """
    return sort_key(task, tz, now, green=green)[:-2]


def order_between(lower: int | None, upper: int | None) -> int | None:
    """A stored order strictly between two others, or None if there is none.

    `None` for either side means nothing bounds the task there, so it goes a
    step beyond the other.  The field is an integer upstream -- a fractional
    value sent to it is truncated -- so two adjacent values have nothing
    between them and the caller has to make room instead.
    """
    if lower is None and upper is None:
        return 0
    if lower is None:
        return upper - ORDER_STEP
    if upper is None:
        return lower + ORDER_STEP
    if upper - lower < 2:
        return None
    return (lower + upper) // 2


def sort_for_display(
    tasks: list[Task],
    tz: tzinfo | None = None,
    now: datetime | None = None,
    manual: bool = False,
    green: str | None = None,
) -> list[Task]:
    """Open before finished, past due before due today, then time and order.

    Passing `now` enables the past-due dimension; without it the ordering is
    exactly what it was, which is what every view other than today wants.

    Passing `manual` makes a hand-set sequence the last key, with the title
    breaking a tie in it.  Only the calendar days pass it: the dateless
    views are queues rather than sequences of work, and almost every task
    in them carries the same stored order, so ordering by it there would
    shuffle the rows without sequencing anything.  It is deliberately the
    last key and so can never lift a task out of its group -- a day's timed
    tasks stay in ascending start time however they are moved.
    """
    tz = tz or local_tz()
    return sorted(tasks, key=lambda t: sort_key(t, tz, now, manual, green))


# --------------------------------------------------------------------------
# CLI -- `python singularity.py [--date YYYY-MM-DD] [--json] [--open]`
# --------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="List SingularityApp tasks for a day.")
    parser.add_argument("--date", help="day to list, YYYY-MM-DD (default: today)")
    parser.add_argument("--open", action="store_true", help="hide finished tasks")
    parser.add_argument("--json", action="store_true", help="dump raw JSON")
    args = parser.parse_args(argv)

    day = date.fromisoformat(args.date) if args.date else None
    try:
        client = SingularityClient()
        tasks = client.tasks_for_day(day, include_done=not args.open).tasks
        projects = client.project_names() if not args.json else {}
    except SingularityError as exc:
        print(f"error: {exc}")
        return 1

    if args.json:
        print(json.dumps([t.raw for t in tasks], ensure_ascii=False, indent=2))
        return 0

    day = day or datetime.now(client.tz).date()
    print(f"{day:%A %d %B %Y} -- {len(tasks)} task(s)")
    for task in tasks:
        mark = {EMPTY: "[ ]", CHECKED: "[x]", CANCELLED: "[-]"}[task.checked]
        project = projects.get(task.project_id or "", "")
        suffix = f"  ({project})" if project else ""
        print(f"  {mark} {task.start_label(client.tz):>7}  {task.title}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
