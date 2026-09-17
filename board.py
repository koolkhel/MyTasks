"""What the board draws, decided without a terminal.

The rows a view shows, their order and the text of every cell are decided
here, from the board's state alone.  Nothing in this module reads a widget,
starts an application or needs a terminal to exist: a caller with the state in
hand can ask what would be drawn and be answered.

That is the point of the separation rather than a side effect of it.  What is
drawn is the board's largest body of rules -- which rows belong to a view, what
each source contributes, what the work filter and the search take away, how a
past-due row differs from a finished one -- and all of it used to be reachable
only by starting a terminal user interface and reading the cells back out of a
table.

Two kinds of thing live here.  The vocabulary of a row comes first: the raw
keys that mark a row as the tracker's, the mailbox's or the calendar's, the
mark each kind draws, and the widths its columns take.  Then `Board`, built
from the state for one paint and thrown away after it.

Where a decision needs a measurement only the screen can supply -- how wide the
title column came out, what colour the theme resolves for a past-due row -- the
measurement is given to `Board` as a value.  It is never fetched from here.
"""

from __future__ import annotations

import email.utils
from dataclasses import dataclass
from datetime import date, datetime, timezone

from rich.text import Text
from textual.markup import escape

import singularity
from singularity import ARCHIVE, CANCELLED, CHECKED, EMPTY, Bucket, Task

MARKS = {EMPTY: "☐", CHECKED: "☑", CANCELLED: "☒"}
#: Raw keys marking a row as the tracker's rather than the board's.  A row
#: carrying these is drawn, hidden and opened like any other, and refuses
#: every write.
TRACKER_MARK = "_tracker"
TRACKER_URL = "_tracker_url"
TRACKER_PROJECT = "_tracker_project"
TRACKER_STATE = "_tracker_state"
TRACKER_PRIORITY = "_tracker_priority"
TRACKER_PRIORITY_VALUE = "_tracker_priority_value"
#: The issue's own key, carried rather than cut back out of the row's id.
#: The id exists to be unique among rows; the key is a fact about the issue,
#: and a program is told the second, never the first.
TRACKER_KEY = "_tracker_key"
#: The versions the issue is against, in the tracker's order, from whichever
#: custom field the configuration names.  Empty is ordinary.
TRACKER_VERSIONS = "_tracker_versions"
#: Prefixes a tracker row's id so it can never collide with a task's.
TRACKER_PREFIX = "yt:"
#: The mark shown against a tracker row, distinct from a task's checkbox so
#: that read-only is visible rather than discovered by pressing a key.
TRACKER_ROW_MARK = "▸"
#: Raw keys marking a row as the mailbox's.  The same arrangement the tracker
#: and the calendar use, for the same reason: a row carrying these is drawn
#: and counted like any other and refuses every write -- every write that
#: would change it, that is.  Promoting reads one and creates a task, which
#: is the one key a mail row answers.
MAIL_MARK = "_mail"
MAIL_SENDER = "_mail_sender"
MAIL_COUNT = "_mail_count"
MAIL_WHEN = "_mail_when"
MAIL_TEXT = "_mail_text"
#: The thread's own messages, so a promotion can mark them read and an undo
#: can mark them unread again.  The one raw value on this board that is not a
#: plain scalar: nothing else can find a message's file, since an identity is
#: a header and the same header may sit in two folders.
MAIL_MESSAGES = "_mail_messages"
#: Set on a mail row whose issue the tracker has marked finished, read off the
#: newest message in the thread.  Nothing asks the tracker: the notification
#: carries it.
MAIL_DONE = "_mail_done"
#: Prefixes a mail row's id.  Built from the newest message's identity, which
#: is unique within the mailbox.
MAIL_PREFIX = "mail:"
#: The mark shown against a mail row, distinct from a task's checkbox, the
#: tracker's arrow and an event's diamond: four kinds of row that cannot be
#: ticked would otherwise look like four of the same thing.
MAIL_ROW_MARK = "@"
#: Shown beside a row's own mark while it is marked for copying.  The
#: row-mark column is two cells wide and every row draws one character in it,
#: so this costs no width anywhere.
#:
#: Plain ASCII, unlike every other mark on this board.  The rest sit in a
#: column of their own or at the end of a line; this one sits beside another
#: glyph in a fixed two-cell box, where a character the terminal renders two
#: cells wide would push its neighbour out.  Every likely candidate --
#: `▪`, `•`, `▸` -- is East-Asian-Ambiguous and is drawn double
#: width in a CJK-configured terminal.  `+` is one cell everywhere, says
#: "added to what I am taking", and is used nowhere else.
COPY_MARK = "+"
#: Raw keys marking a row as the calendar's.  The same arrangement the
#: tracker's rows use, for the same reason: a row carrying these is drawn,
#: hidden and counted like any other and refuses every write, and nothing
#: outside these few places needs to know where it came from.
EVENT_MARK = "_event"
EVENT_ACCOUNT = "_event_account"
EVENT_CALENDAR = "_event_calendar"
#: How far into the day an event starts, in minutes; absent when it lasts the
#: whole day.  Kept as a number because placing the row is a comparison and
#: nothing else needs the instant.
EVENT_MINUTES = "_event_minutes"
#: The address an event carries, resolved once when the row is built.  Its
#: own key beside the tracker's, so the action that opens a link reads it the
#: same way and the parsing stays off the keystroke.
EVENT_URL = "_event_url"
#: When the event ends, as a timestamp.  Carried so a row can be drawn
#: against the present without the calendar being read again -- the fetch
#: already knows it, and asking again every minute would be absurd.
EVENT_ENDS = "_event_ends"
#: Prefixes an event's row id.  Built from the account, the time and the
#: title rather than the framework's identifier, which repeats across every
#: occurrence of a repeating event and would make them one row.
EVENT_PREFIX = "cal:"
#: The mark shown against an event, distinct from both a task's checkbox and
#: the tracker's arrow: three rows that cannot be ticked would otherwise look
#: like three kinds of the same thing.
EVENT_ROW_MARK = "◇"
#: Drawn in the margin against a task carrying the configured tag.  A star,
#: which says "mine" at a glance where the double rule it replaced rewarded
#: looking twice; it stands alone on its row rather than joining the marks
#: above and below.  Not a colour: the board must stay legible to someone who
#: cannot tell its colours apart, and the tag's own colour is deliberately
#: unused.  Plain ASCII, so it is one cell wide in every locale -- the only
#: mark on the board with no width caveat at all.
GREEN_MARK = "*"
#: How wide the when-column is.  It carries a tracker row's state and a
#: task's own start time or how overdue it is, so it has to hold the widest
#: of both; eleven cells is what the longest state label needs, and the
#: longest a task puts there is shorter.  Named once so the width the label
#: is trimmed to and the width the column is drawn at cannot drift apart.
_WHEN_WIDTH = 11
#: How many of the archive's rows are drawn at once.  The archive is held
#: whole -- thousands of rows -- and a search reaches every one of them, but
#: the table is refilled from scratch on every repaint and a repaint happens
#: on every mark: measured, 500 rows cost 9ms against 158ms for 9,100, and
#: marking a run of rows pays that cost once per press.  What is withheld is
#: reported rather than silently dropped.
ARCHIVE_ROWS = 500
#: How wide the column naming a task's project is.  Eleven cells hold the
#: names in use with room to spare; it was twenty-two, and the eleven given
#: back go to the title, which is the column that runs out of room.
_PROJECT_WIDTH = 11


def _state_label(state: str) -> str:
    """A tracker state, as the one word that names it.

    The tracker phrases its states itself, and the words that lead them are
    often shared -- "In progress" and "In review" differ only in the last --
    so the last word is the one worth the column.  Lower case because every
    other label in the same column is lower case, which would otherwise hold
    only for as long as the tracker happened to phrase its states that way.
    Anything still too wide is cut rather than allowed to overflow.
    """
    words = state.split()
    return words[-1].lower()[:_WHEN_WIDTH] if words else ""
#: The API's name for the least urgent priority a tracker defines.  The board
#: needs to know which one that is, and only that one, because two of the
#: tracker's own words begin with the same letter -- the most urgent and the
#: least -- so the letter alone cannot tell them apart.  The English name is
#: never shown; it decides a case and nothing else.  A tracker without this
#: priority lower-cases nothing, which is right.
LEAST_URGENT = "Minor"


def _priority_letter(priority: str, value: str) -> str:
    """A tracker priority, as the one letter that names it.

    The tracker words its own priorities, and the first letter is what a
    person already reads off its interface.  Taken from the word rather than
    from a list here, for the reason the state's last word is: a priority the
    tracker renames or adds needs no change in this file.  It is also the only
    part that means the same thing twice -- the same priority is worded
    Обычный in one of this tracker's definitions and Обычная in another, and
    Серьезная against Серьезный, the gender differing while the letter does
    not.

    Upper case, except the least urgent, which is lower.  Неотложн-- (drop
    everything) and Незначительн-- (ignore) both begin with Н, and they are
    the most urgent priority and the least, so a row read wrongly reads as its
    opposite.  The same letter said quietly is the quiet one: it keeps every
    letter meaning what the tracker's word means and does not pretend the two
    words begin differently.

    Not colour, and this is the third reason: the tracker gives one priority
    different colours in different definitions, a person may not read colour
    at all, and the board has two themes against which a fixed hex has already
    measured 2.18:1 once.  A letter reads on both because it is not a colour.
    """
    if not priority:
        return ""
    first = priority[:1]
    return first.lower() if value == LEAST_URGENT else first.upper()


def _mail_who(sender: str) -> str:
    """Who a message is from, in the room a column leaves.

    The display name where there is one, else the part before the @: a
    notification's whole address is mostly the host it came from, which every
    message from that system repeats, so the informative part is the front.
    """
    name, address = email.utils.parseaddr(sender)
    if name:
        return name
    return (address or sender).split("@")[0]


def _event_label(minutes: int | None) -> str:
    """When an event starts, for the column that holds a task's own time.

    An event lasting the whole day says so in words rather than showing a
    midnight it does not mean.  Lower case, as everything else in this
    column is.
    """
    if minutes is None:
        return "all-day"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass(frozen=True)
class Painting:
    """One answer about what the board would draw.

    Frozen, because it is a statement about a moment rather than a thing to
    keep in step: the application assigns what it says and asks again for the
    next paint.
    """

    #: The rows to draw, in the order they are drawn in.
    rows: list[Task]
    #: What each of those rows says, cell by cell, in the same order.  Part
    #: of the answer rather than worked out again on the way to the screen:
    #: two expressions of what a row says would drift the moment one of them
    #: was edited, and nothing would connect them.
    cells: list[tuple]
    #: How many of each source survived the filters, as the status line
    #: reports them.  Counted where they are counted rather than recounted
    #: afterwards: several of these are taken before a filter and several
    #: after, and which is which is the whole of their meaning.
    shown_issues: int
    shown_events: int
    shown_mail: int
    shown_messages: int
    #: How many rows the work filter and the search took away.  Counted over
    #: every source before any of it is dropped, so the number is rows
    #: removed rather than rows removed from one source.
    hidden_work: int
    hidden_by_search: int
    #: How many of the drawn rows are past due, events excepted.
    past_due: int
    #: The line under the rows, and whether it is an error rather than a
    #: report.  Already joined: the application sets the bar to it and does
    #: not assemble anything of its own.
    status: str
    status_error: bool
    #: Which row the cursor lands on, or None where there are no rows, and
    #: the position the view is held at afterwards.
    cursor: int | None
    scroll: int
    #: How many rows the archive holds and how many of them were drawn.  Both
    #: zero in every other view.  Two numbers rather than one because the
    #: difference is what the bound withheld, and a view showing part of the
    #: archive must not read as an archive that small.
    archive_held: int = 0
    archive_drawn: int = 0


class Board:
    """What one paint of the board would draw, from the state it was given.

    Built for a paint and thrown away after it.  Everything derived is
    recomputed rather than carried over, which is the rule the repaint
    already worked by: an optimistic view and a fetched one cannot then come
    to disagree.

    The attributes are named exactly as the application names them, so that
    what moved here reads as it read there.
    """

    def __init__(self, *, base: list[Task], pending: dict, tasks: list[Task],
                 position, reference: datetime | None, tz, now: datetime,
                 projects: dict[str, str], marked: list[str],
                 marked_rows: dict[str, Task], searching: str,
                 hiding_work: bool, work_project: str | None,
                 window_reason_now: str | None, work_override,
                 green_tag: str | None, tracker_issues: list,
                 tracker_config, events: list, events_day, calendar_config,
                 mail_threads: list, notice: tuple[str, bool] | None,
                 fetched: bool, title_width: int, late_colour: str,
                 archive: list[Task] | None = None,
                 archive_loading: bool = False,
                 archive_error: str | None = None):
        #: The ids of the rows a person has marked, in the order they marked
        #: them.  A list rather than a set: that order is what a copy comes
        #: out in.
        #: What the last fetch reported for the shown view, before any
        #: pending write is applied on top of it.
        self._base = base
        #: Writes in flight, by task id.
        self._pending = pending
        #: The rows the board is showing at the moment this was built.
        self.tasks = tasks
        #: The day or bucket being shown.
        self.position = position
        self.marked = marked
        #: Project id to name, for the column that names a task's project.
        self.projects = projects
        #: The instant the shown view was fetched at, or None where the view
        #: has no date for a row to be overdue against.
        self.reference = reference
        self.tz = tz
        #: The present, as the application read it when this board was built.
        #: Given rather than fetched, for the reason the width and the colour
        #: are: a clock is something outside this module answers, and one
        #: paint should see one instant rather than a different one per row.
        self.now = now
        #: The rows the marks were made on, by id, so a mark on a row the
        #: view no longer holds can still be recognised.
        self._marked_rows = marked_rows
        #: The term being searched for, or empty while no search is in force.
        self.searching = searching
        #: Whether work is being hidden, and which project counts as work.
        self.hiding_work = hiding_work
        self.work_project = work_project
        #: What the working window last said, and whether a press is
        #: overruling it -- the words the status line gives for hidden work.
        self._window_reason = window_reason_now
        self._work_override = work_override
        #: The tag that counts as green, or None where none is configured.
        self.green_tag = green_tag
        #: What the other three sources last answered, with the configuration
        #: that says whether each is being read at all.
        self.tracker_issues = tracker_issues
        self.tracker_config = tracker_config
        self.events = events
        self.events_day = events_day
        self.calendar_config = calendar_config
        self.mail_threads = mail_threads
        #: What the board last said that outranks the counts, or None.
        self.notice = notice
        #: Whether the shown view's own tasks have arrived yet.
        self.fetched = fetched
        #: How much room the title column has.  Measured from the screen and
        #: handed over, because the screen is the only thing that knows.
        self.title_width = title_width
        #: The colour a past-due title is drawn in, resolved from the theme
        #: for the same reason.
        self.late_colour = late_colour
        #: Every archived task the application has fetched, in whatever order
        #: the store answered in.  Given rather than fetched, as every other
        #: source is: ordering, narrowing and bounding it is this module's
        #: work, reaching the store is not.  None until the view has been
        #: asked for, which is not the same as an archive that is empty.
        self.archive = archive
        #: Whether pages of it are still arriving, and what went wrong if the
        #: fetch failed.  Both are said in the line under the rows, so that a
        #: partial archive is never mistaken for the whole of it.
        self.archive_loading = archive_loading
        self.archive_error = archive_error

    def paint(self, *, keep: str | None = None, previous: int = 0,
              scroll: int = 0, drawn_for=None) -> "Painting":
        """What this view would draw, and the numbers that describe it.

        Every source is built, then filtered, then placed, in that order and
        in one place: a source narrowed anywhere else is a source a key
        cannot reach however its rows are marked, which is a fault this
        board has had twice.

        Nothing here is remembered.  The application takes the answer and
        assigns it, so that what it holds and what was drawn are the same
        thing rather than two computations of it.
        """
        if self.position is ARCHIVE:
            # The archive is not a day's fetch with a membership rule applied
            # to it; it is its own body of rows, held whole and ordered by
            # when the store archived them.  No pending write is applied,
            # because nothing in this view writes.
            tasks = self.archive_rows()
        else:
            shown = [t for t in self.patched() if self.belongs(t)]
            tasks = singularity.sort_for_display(
                shown, self.tz, self.reference, manual=self.orders_manually,
                green=self.green_tag,
            )
        # The tracker's rows join outside the ordering, never during it: an
        # issue has no date, so the day's own membership rule would reject
        # it anyway, and joining afterwards is the same fact as "not part of
        # the day's order" seen from the other side.  They go in front,
        # because they are what is being worked on now and the foot of the
        # list -- past the finished tasks -- is where a person stops looking.
        issues = self.tracker_rows()
        shown_issues = len(issues)
        events = self.event_rows()
        # Every source is built before the filter and filtered with the
        # day's tasks, because a source appended afterwards is a source the
        # key cannot reach however its rows are marked.  That was written
        # here for the tracker's rows -- the most work-like on screen -- and
        # then mail was appended afterwards anyway and went unhidden for
        # three changes.  So: build them all here, filter them all here, and
        # let the placing below arrange what survives.
        mails = self.mail_rows()
        hidden_work = (
            sum(1 for t in tasks + issues + events + mails if self.is_work(t))
            if self.hiding_work else 0
        )
        if self.hiding_work:
            tasks = [t for t in tasks if not self.is_work(t)]
            issues = [t for t in issues if not self.is_work(t)]
            events = [t for t in events if not self.is_work(t)]
            mails = [t for t in mails if not self.is_work(t)]
            shown_issues = len(issues)
        # The search narrows what the work filter left, in the same place and
        # for the same reason the comment above gives: a source narrowed
        # anywhere but here is a source this key cannot reach, however its
        # rows are marked.  Counted over all four before any is dropped, so
        # the number reported is the number of rows removed rather than the
        # number removed from one source.
        hidden_by_search = (
            sum(1 for t in tasks + issues + events + mails if not self.matches(t))
            if self.searching else 0
        )
        if self.searching:
            tasks = [t for t in tasks if self.matches(t)]
            issues = [t for t in issues if self.matches(t)]
            events = [t for t in events if self.matches(t)]
            mails = [t for t in mails if self.matches(t)]
            shown_issues = len(issues)
        # The events take their place among the day's tasks by when they
        # happen; the tracker's block goes in whole, where the day's
        # unfinished work ends.
        shown_events = len(events)
        tasks = self.place_issues(self.place_events(tasks, events), issues)
        # Counted after the filter, as the issues are: both numbers say what
        # is on screen, which is what the inbox undertakes to report -- how
        # many rows of mail it is showing.  Filtering the rows carries the
        # message count with them, the sum being taken over what is left.
        shown_mail = len(mails)
        shown_messages = sum(t.raw.get(MAIL_COUNT, 1) for t in mails)
        # Mail follows the inbox's tasks.  It once led them, so that the
        # daily processing started at the top rather than after a scroll --
        # and that reasoning is why it now goes last: mail arrives in far
        # greater quantity than a person files tasks, some 460 rows against
        # 35, so leading with it guarantees the scroll it was meant to
        # avoid.  Appended, never sorted in, so the tasks keep exactly the
        # order they had alone -- and filtered before this, so hiding work
        # cannot disturb that order either.
        tasks = tasks + mails
        past_due = (
            sum(
                1 for t in tasks
                if not self.is_event(t) and t.past_due_since(self.reference, self.tz)
            )
            if self.reference
            else 0
        )
        # The bound goes here: after both filters, so that what is drawn is
        # the newest of what survived them, and before the cells, so that the
        # rows withheld cost nothing to draw.  Held and drawn are both
        # reported; the search above has already reached every held row.
        archive_held = len(tasks) if self.position is ARCHIVE else 0
        if self.position is ARCHIVE and len(tasks) > ARCHIVE_ROWS:
            tasks = tasks[:ARCHIVE_ROWS]
        archive_drawn = len(tasks) if self.position is ARCHIVE else 0
        cells = [self.row_for(task) for task in tasks]
        cursor, scroll = self.cursor_after(
            tasks, keep=keep, previous=previous, scroll=scroll,
            drawn_for=drawn_for)
        status, status_error = self.says(
            tasks, shown_issues, shown_events, shown_mail, shown_messages,
            hidden_work, hidden_by_search, past_due,
            archive_held=archive_held, archive_drawn=archive_drawn)
        return Painting(
            rows=tasks, cells=cells, shown_issues=shown_issues, shown_events=shown_events,
            shown_mail=shown_mail, shown_messages=shown_messages,
            hidden_work=hidden_work, hidden_by_search=hidden_by_search,
            past_due=past_due, status=status, status_error=status_error,
            cursor=cursor, scroll=scroll,
            archive_held=archive_held, archive_drawn=archive_drawn,
        )

    def has_ended(self, task: Task) -> bool:
        """Whether this row's event is already over.

        Against the present rather than against `reference`: that instant is
        the fetch's, and is absent on every day but today, so a rule measured
        by it would simply never fire elsewhere.  The two are deliberately
        different clocks answering different questions -- see design.md.
        """
        ends = task.raw.get(EVENT_ENDS)
        return ends is not None and ends <= self.now.timestamp()

    @staticmethod
    def is_event(task: Task | None) -> bool:
        """Whether a row came from the calendar rather than the board."""
        return bool(task is not None and task.raw.get(EVENT_MARK))

    def _mail_when(self, stamp: float) -> str:
        """When a message arrived, in the room the column leaves.

        The time alone for today, the date for anything older -- which is
        what every mail client does, and what fits: a date and a time
        together is twelve cells against the eleven this column has, and
        would be cut just where the minutes are.
        """
        when = datetime.fromtimestamp(stamp, self.tz)
        if when.date() == self.now.date():
            return when.strftime("%H:%M")
        return when.strftime("%d %b")

    @staticmethod
    def is_mail(task: Task | None) -> bool:
        """Whether a row came from the mailbox rather than the board."""
        return bool(task is not None and task.raw.get(MAIL_MARK))

    @staticmethod
    def is_tracker(task: Task | None) -> bool:
        """Whether a row came from the tracker rather than the board."""
        return bool(task is not None and task.raw.get(TRACKER_MARK))

    @staticmethod
    def _markup_title(task: Task) -> str:
        """The task's title as markup: its own characters escaped, link marked.

        Escaping happens before anything is added, and only to the task's own
        text.  The other order would neuter the span just inserted, and
        neither order would let a title's own brackets survive -- titles are
        already rendered as markup, so `Plan [urgent] thing` would otherwise
        lose the bracketed part.

        The address is quoted because Textual requires it: `[link=https://x]`
        raises a markup error, `[link='https://x']` does not.
        """
        text = escape(task.display_title)
        url, shown = task.link, task.link_text
        if url and shown:
            marked = escape(shown)
            if marked in text:
                text = text.replace(marked, f"[link='{url}']{marked}[/link]", 1)
        return text

    def is_green(self, task: Task | None) -> bool:
        """Whether this task carries the configured tag.

        False when no tag is configured, and for a tracker row, which the
        board made up rather than fetched and which carries no tags at all.
        """
        return task is not None and task.has_tag(self.green_tag)

    @staticmethod
    def shortened(markup: str, width: int) -> Text:
        """Cell text cut to `width`, saying so, with its styling intact.

        Built as text that carries its own styling rather than as markup,
        because the cut has to fall in the words and not in the middle of a
        link.  The column would cut it too, but silently -- the whole point
        is that a shortened title looks shortened.
        """
        text = Text.from_markup(markup)
        if len(text) > width:
            text.truncate(width, overflow="ellipsis")
        return text

    def marked_cell(self, task: Task, mark: str) -> str:
        """A row's own mark, with the copy mark in front of it if it carries one.

        The column is two cells and every kind of row draws one character
        there, so the mark goes in the cell already paid for rather than in
        a column of its own -- which every view would pay for, on a board
        that fits its title column to the terminal.

        A character rather than a colour, for a reason measured on this
        board before: the row cursor replaces a colour outright while a
        style survives it, so a coloured mark would vanish on exactly the
        row a person is looking at.  A glyph is neither, and survives by
        being there.
        """
        return f"{COPY_MARK}{mark}" if task.id in self.marked else mark

    def row_for(self, task: Task) -> tuple[str, str, str, str, str]:
        mark = GREEN_MARK if self.is_green(task) else ""
        if self.is_tracker(task):
            # Its own mark, so read-only is visible rather than found out by
            # pressing a key; and the tracker's project rather than the work
            # project the row belongs to, because that is what names the
            # issue to a person.
            # The leftmost cell carries the configured tag's mark for a
            # task, and a tracker row carries no tags at all -- so it is free
            # here, and the priority takes it rather than costing a column of
            # every view for a value only these rows have.
            return (
                _priority_letter(task.raw.get(TRACKER_PRIORITY) or "",
                                 task.raw.get(TRACKER_PRIORITY_VALUE) or ""),
                self.marked_cell(task, TRACKER_ROW_MARK),
                _state_label(task.raw.get(TRACKER_STATE) or ""),
                self.shortened(escape(task.raw.get("title") or ""), self.title_width),
                self.shortened(
                    f"[dim]{escape(task.raw.get(TRACKER_PROJECT) or '')}[/dim]",
                    _PROJECT_WIDTH,
                ),
            )
        if self.is_mail(task):
            # Its own mark, and the sender where a task names its project --
            # who sent it is what places a message.  The count of messages
            # behind the thread goes with the subject, being about the
            # subject rather than a column of its own.
            count = task.raw.get(MAIL_COUNT) or 1
            subject = escape(task.raw.get("title") or "")
            if count > 1:
                subject = f"{subject} [dim]({count})[/dim]"
            if task.raw.get(MAIL_DONE):
                # Struck, which is how the board already draws a task that is
                # finished and how the notification itself draws the issue's
                # key.  One vocabulary for "this is done" rather than two.
                # The row keeps its own mark, so it is still a mail row.
                #
                # The dimming goes while the row is marked, for the reason
                # the same drop is made on a task below: dimmed text on the
                # bar cannot be read.  The strike stays, being a style.
                subject = (f"[strike]{subject}[/]" if task.id in self.marked
                           else f"[strike dim]{subject}[/]")
            return (
                "",
                self.marked_cell(task, MAIL_ROW_MARK),
                self._mail_when(task.raw.get(MAIL_WHEN) or 0),
                self.shortened(subject, self.title_width),
                self.shortened(
                    f"[dim]{escape(_mail_who(task.raw.get(MAIL_SENDER) or ''))}[/dim]",
                    _PROJECT_WIDTH,
                ),
            )
        if self.is_event(task):
            # Its own mark, so read-only is visible rather than found out by
            # pressing a key; and the calendar it came from where a task
            # names its project, because that is what places the event.
            #
            # An event already over recedes.  Dim rather than a colour, and
            # measured rather than assumed: with the row cursor on it, a dim
            # cell keeps its dimness while its colours are replaced, where a
            # coloured cell loses the colour outright -- the trap
            # `late_colour` documents.  So this is the one expression that
            # survives being the selected row.  Not struck out: nothing about
            # an event was completed.
            over = self.has_ended(task)
            name = escape(task.raw.get("title") or "")
            return (
                "",
                self.marked_cell(task, EVENT_ROW_MARK),
                _event_label(task.raw.get(EVENT_MINUTES)),
                self.shortened(
                    f"[dim]{name}[/dim]" if over and task.id not in self.marked
                    else name,
                    self.title_width),
                self.shortened(
                    f"[dim]{escape(task.raw.get(EVENT_CALENDAR) or '')}[/dim]",
                    _PROJECT_WIDTH,
                ),
            )
        title = self._markup_title(task)
        if task.recurring:
            title = f"↻ {title}"
        if task.is_note:
            title = f"≡ {title}"
        late = task.past_due_since(self.reference, self.tz) if self.reference else None
        when = (
            # In the archive the column carries the date the store archived
            # the row.  Nothing in that view is due, so the time of day it was
            # once scheduled at is the one thing the column could say that
            # nobody is looking for.
            self.archived_label(task)
            if self.position is ARCHIVE
            else singularity.overdue_label(late, self.reference)
            if late
            else task.start_label(self.tz)
        )
        # A marked row is drawn on a bar, and neither of these survives it.
        # Measured against that bar: the past-due colour comes out at 1.30
        # to 1 and dimmed text lower still, where the ordinary colour is
        # 2.68 to 1 -- so a marked row keeping them would be a row nobody
        # could read.  Dropping them is not a new rule: the selected row
        # already loses its title colour, and a past-due row that is
        # selected is told apart by the age it shows instead.  A marked one
        # is told apart the same way.
        #
        # The strike stays.  It is a style rather than a colour and is as
        # legible on the bar as off it.
        marked = task.id in self.marked
        if task.done or task.cancelled:
            title = f"[strike]{title}[/]" if marked else f"[strike dim]{title}[/]"
        elif late and not marked:
            title = f"[{self.late_colour}]{title}[/]"
        project = self.projects.get(task.project_id or "", "")
        return (
            mark,
            self.marked_cell(task, MARKS[task.checked]),
            when,
            self.shortened(title, self.title_width),
            self.shortened(f"[dim]{project}[/dim]", _PROJECT_WIDTH) if project else "",
        )

    def event_rows(self) -> list[Task]:
        """The day's events, as rows the board can draw.

        Each carries the work project's id when it came from the work
        account, so the key that hides work hides these too and `is_work`
        needs to know nothing about the calendar.  The marker is what every
        write checks before refusing.
        """
        config = self.calendar_config
        if config is None or self.events_day != self.position:
            return []
        rows = []
        for event in self.events:
            minutes = None if event.all_day else event.start.hour * 60 + event.start.minute
            # The location first, the description second: a calendar system
            # may fill either, and where both were filled they named the
            # same address -- but the location is usually the bare address
            # where the description is prose with one somewhere inside.
            address = (
                singularity.url_in(event.location)
                or singularity.url_in(event.notes)
            )
            rows.append(Task({
                "id": f"{EVENT_PREFIX}{event.account}:{event.label}:{event.title}",
                "title": event.title,
                "checked": EMPTY,
                "deferred": False,
                "useTime": False,
                # Belonging to the work project is what makes `w` hide it.
                "projectId": (
                    self.work_project if config.is_work(event.account) else None
                ),
                # Where a task keeps its note, so the detail area draws an
                # event's description with no knowledge of events at all.
                "note": event.notes,
                EVENT_MARK: True,
                EVENT_ENDS: event.end.timestamp(),
                EVENT_URL: address,
                EVENT_ACCOUNT: event.account,
                EVENT_CALENDAR: event.calendar,
                EVENT_MINUTES: minutes,
            }))
        return rows

    @staticmethod
    def event_key(event: Task) -> tuple:
        """Where an event stands in the ordering the tasks are placed by.

        An event has no opinion about being finished or overdue, but it still
        has to be placed against rows that do -- so it stands in the same
        ordering as what it is: not finished, not tagged, not past due, not
        pinned, happening at its own hour.  Every band then falls out with no
        special handling: a past-due task leads because the third entry
        separates it, a finished task sinks because the first does, and the
        event lands among the timed rows of the ordinary band.

        The shape is `singularity.sort_key`'s and must stay so.  The
        alternative -- a key of this function's own invention -- would drift
        the first time a band was added, as one was when the tag arrived.

        The hand-set order is nothing, which is what the store gives a task
        created without one, so an event ties with such a task at the same
        minute and is separated from it by title.  Which of a pair at the
        same minute leads is arbitrary; being arbitrary in a stated direction
        is better than being arbitrary by accident.
        """
        minutes = event.raw.get(EVENT_MINUTES) or 0
        return (
            False,                              # never finished
            True,                               # never tagged
            True,                               # never past due
            0.0,                                # and so never overdue by any amount
            True,                               # never pinned
            event.raw.get(EVENT_MINUTES) is None,   # all-day sorts as all-day
            (minutes // 60, minutes % 60),
            0,                                  # carries no hand-set order
            (event.raw.get("title") or "").casefold(),
        )

    def place_events(self, tasks: list[Task], events: list[Task]) -> list[Task]:
        """Put the events among the day's tasks, each where its hour belongs.

        Insertion, never a re-sort.  The tasks arrive in the order the
        board's own rules put them in and leave in exactly that order,
        whatever the events do -- no task key is recomputed and no task moves
        relative to another.  That is the property the requirement asks for,
        and it holds because of the shape of this function rather than
        because a test happens to cover it.

        Which matters here more than most places: the rule this replaced was
        wrong, and the test written for it passed anyway.  It compared only
        the clock, and counted a row naming no time as later than any event
        -- on the assumption that untimed rows sit at the end of a day.  They
        do not.  A past-due task names no time and leads the day, so every
        timed event was inserted above it and the whole calendar collected at
        the top.

        An event lasting the whole day still leads the day, above every row
        that happens at a time, because it describes the day rather than a
        moment in it.
        """
        def when(row: Task) -> tuple:
            minutes = row.raw.get(EVENT_MINUTES)
            return (minutes or 0, (row.raw.get("title") or "").casefold())

        all_day = sorted(
            (e for e in events if e.raw.get(EVENT_MINUTES) is None), key=when
        )
        placed = list(tasks)
        for event in sorted(
            (e for e in events if e.raw.get(EVENT_MINUTES) is not None), key=when
        ):
            key = self.event_key(event)
            where = len(placed)
            for i, row in enumerate(placed):
                if self.ordering_key(row) > key:
                    where = i
                    break
            placed.insert(where, event)
        return all_day + placed

    def place_issues(self, rows: list[Task], issues: list[Task]) -> list[Task]:
        """Put the tracker's block where the day's unfinished work ends.

        After every unfinished row and before the first finished or
        cancelled one.  An issue names no hour and no date, which makes it
        kin to the day's untimed work rather than to the appointments and
        the overdue tasks that lead the day.

        Before the finished rows rather than after them, which is the whole
        of the difference between this and putting the block at the foot of
        the list.  By the end of a day most of the list is finished -- more
        finished rows than live ones, measured -- and a block below them is
        a block nobody reads, which is the reason it used to sit on top.

        The block goes in whole rather than being ordered row by row: its
        rows are grouped by the configured state, and giving each one a
        place of its own would sort them among the day's untimed tasks by
        title and lose that grouping.
        """
        if not issues:
            return rows
        where = next(
            (i for i, row in enumerate(rows)
             if not self.is_event(row) and (row.done or row.cancelled)),
            len(rows),
        )
        return rows[:where] + issues + rows[where:]

    def ordering_key(self, row: Task) -> tuple:
        """The key a row is placed by, whichever kind of row it is.

        An event's is made up; a task's comes from the function that ordered
        it in the first place, so the comparison cannot read the task
        differently from the sort that produced the list.
        """
        if self.is_event(row):
            return self.event_key(row)
        return singularity.sort_key(
            row, self.tz, self.reference,
            manual=self.orders_manually, green=self.green_tag,
        )

    def ended_count(self) -> int:
        """How many shown rows are events already over.

        What the timer compares.  Cheap, and enough: the set only ever grows
        as time passes within one fetch, so a change in its size is a change
        in the set.
        """
        return sum(1 for t in self.tasks if self.is_event(t) and self.has_ended(t))

    @property
    def shows_mail(self) -> bool:
        """Whether the shown view is the one mail belongs to.

        The inbox: the board's queue of things that have arrived and not been
        decided about, which is what mail read daily is.  Not a view of its
        own -- see design.md, where the reasoning that first gave it one is
        recorded along with why it was wrong.
        """
        return self.position is Bucket.INBOX

    def mail_fold(self, message: Any) -> object | None:
        """What a message is about, or None where the board cannot tell.

        Two things together: the issue its text names in a configured
        tracker project, and the first address it carries.  Messages
        agreeing on both are one row.

        Both, not either.  In one of the folders read daily, mail about a
        merge request names the issue it mentions, so several unrelated
        requests cite one issue -- the key alone merged 24 of 38 groups
        wrongly.  This matters more than tidiness: reviewing a row files
        away every message in it, so a wrong fold does not merely misdraw a
        row, it archives mail nobody looked at.

        A configured project's key, not a general pattern for
        letters-dash-digits: that pattern also matches a version or a
        standard, and the board has one place that knows which projects
        count.

        A message carrying no address at all is left alone.  The rule is
        that the first address each carries is the same, and a message with
        none has no such address to agree about -- and where the rule cannot
        be shown to hold, not folding is the safe direction.

        This is what `mail.threads` takes as its `fold`: knowing which
        projects are configured and how to find an address in text belongs
        here, not in a module whose whole job is reading a maildir.
        """
        config = self.tracker_config
        if config is None:
            return None
        keys = config.keys_in(message.text)
        if not keys:
            return None
        urls = singularity.urls_in(message.text)
        if not urls:
            return None
        return (keys[0], urls[0])

    def mail_rows(self) -> list[Task]:
        """The mailbox's threads, as rows the board can draw.

        Only in the inbox: a thread belongs to no day, and repeating it
        under every date would say it did.  The marker is what every write
        that would change a row checks before refusing -- reviewing and
        promoting are the two keys that read it and answer.
        """
        if not self.shows_mail:
            return []
        rows = []
        for thread in self.mail_threads:
            newest = thread.newest
            rows.append(Task({
                "id": f"{MAIL_PREFIX}{newest.ident}",
                "title": newest.subject or "(no subject)",
                "checked": EMPTY,
                "deferred": False,
                "useTime": False,
                MAIL_MARK: True,
                MAIL_SENDER: newest.sender,
                MAIL_COUNT: thread.count,
                MAIL_WHEN: newest.when.timestamp(),
                # The newest message's text, which is what the row offers
                # to open where no message carries an anchored address: a
                # run of notifications about one thing carries one
                # near-identical address per message -- four builds of a job
                # give four console addresses differing in a number -- and
                # offering every one would ask a person to choose between
                # things they cannot tell apart.
                MAIL_TEXT: newest.text,
                # Every message in the thread, not only the newest.  Two
                # things need all of them: reviewing files away the whole
                # row, and an anchored address is looked for across it.
                MAIL_MESSAGES: thread.messages,
                # What the newest message says about the issue, that being the
                # most recent word on it and the message this row already
                # shows.  False for every row that is not about an issue.
                MAIL_DONE: newest.issue_done,
                # Where a task keeps its note, so the detail area shows what
                # the message says with no knowledge of mail at all -- the
                # same path a calendar event's description takes.  The
                # newest message's, consistent with the links offered.
                "note": newest.body,
            }))
        return rows

    def patched(self, rows: list[Task] | None = None) -> list[Task]:
        """The fetched tasks with every pending write applied on top.

        Rows come only from what the last fetch reported, so a pending
        write is never itself a reason for a row to exist -- an orphan
        patch, for a task the fetch no longer knows about, shows nothing.

        Over the day's base unless told otherwise; the archive hands its
        own rows in, so that a task brought back from it is drawn as
        brought back by the same overlay a day's tick is.
        """
        out: list[Task] = []
        for task in (self._base if rows is None else rows):
            queue = self._pending.get(task.id)
            if not queue:
                out.append(task)
                continue
            if any(p.removes for p in queue):
                continue
            raw = dict(task.raw)
            for pending in queue:
                raw.update(pending.patch)
            out.append(Task(raw))
        return out

    @property
    def orders_manually(self) -> bool:
        """Whether the shown view carries a sequence a person has set.

        Calendar days do; the inbox and someday view are queues awaiting
        triage rather than sequences of work, and are ordered by title.
        This is the one place that decides, so the fetched view and the
        repainted one cannot disagree about it.
        """
        return isinstance(self.position, date)

    @property
    def shows_tracker(self) -> bool:
        """Whether the shown view is the one the tracker block belongs to.

        Today alone.  An issue in progress is what is being worked on now
        rather than something scheduled, so repeating it under every date
        would say it was scheduled for each of them.
        """
        return (
            isinstance(self.position, date)
            and self.position == self.now.date()
        )

    def archive_rows(self) -> list[Task]:
        """The archive's rows, in the order this view puts them.

        Most recently archived first, ties by title -- so that the order
        never depends on the order the store answered in, which is its own
        and is not any order at all.

        What was fetched, with pending writes laid over it, and nothing
        taken away: a task brought back from here stays on its row, drawn
        as brought back, until the archive is next read.  The row is what a
        person is looking at when they decide where to send it, and the one
        thing this view lets them do after un-ticking is date.  Which rows
        are the archive's -- finished, and archived by the store -- was
        decided when they were fetched.  A row whose stamp the board could
        not read sorts to the end rather than taking the view down with it.

        The tag that marks a task green does not lift a row here.  Every row
        in this view was finished when it was read, and the tag already
        ranks below that.
        """
        rows = self.patched(self.archive or [])
        # Two stable sorts rather than one key that negates a timestamp: the
        # second keeps the first's order within equal dates, and neither has
        # to express "descending by one thing, ascending by another" as
        # arithmetic.
        rows.sort(key=lambda t: t.display_title.casefold())
        oldest = datetime.min.replace(tzinfo=timezone.utc)
        rows.sort(key=lambda t: t.archived_at or oldest, reverse=True)
        return rows

    def archived_label(self, task: Task) -> str:
        """When the store archived a row, in the room the column leaves.

        A date and not a time of day.  The column is eleven cells and
        "17 Sep 2026" is eleven exactly; a row four years old wants its year
        far more than it wants the minute it was filed.

        Empty where the stamp could not be read, which is the same answer the
        ordering gives such a row: it is drawn, and it says nothing it does
        not know.
        """
        when = task.archived_at
        return f"{when.astimezone(self.tz):%d %b %Y}" if when else ""

    def tracker_rows(self) -> list[Task]:
        """The tracker's issues, as rows the board can draw.

        Each carries the work project's id, so the key that hides work hides
        these too and `is_work` needs to know nothing about the tracker; and
        its own page as a link, so the key that opens a link opens the issue;
        and its key, project and versions, which are what the key that starts
        a workspace hands to the program that makes one.  The marker is what
        every write checks before refusing.
        """
        if not self.shows_tracker:
            return []
        rows = []
        for issue in self.tracker_issues:
            rows.append(Task({
                "id": f"{TRACKER_PREFIX}{issue.key}",
                "title": f"{issue.key} — {issue.summary}",
                "checked": EMPTY,
                "deferred": False,
                "useTime": False,
                # Belonging to the work project is what makes `w` hide it.
                "projectId": self.work_project,
                TRACKER_MARK: True,
                TRACKER_URL: issue.url,
                TRACKER_KEY: issue.key,
                TRACKER_PROJECT: issue.project,
                TRACKER_STATE: issue.state,
                TRACKER_PRIORITY: issue.priority,
                TRACKER_PRIORITY_VALUE: issue.priority_value,
                TRACKER_VERSIONS: issue.versions,
            }))
        return rows

    def is_work(self, task: Task) -> bool:
        """Whether a row counts as work, and so is hidden by the key for it.

        Two ways of counting, and this is the one place that decides.

        A task counts by its project.  A mail row counts because it is mail:
        every message the board reads comes from a corporate account, so
        there is no mail it reads that is not work.  Not gated on a work
        project being configured -- that setting says which *task* project
        counts, and mail does not need it to be work.  The key refuses to
        turn on without one anyway, so nothing on screen turns on this.

        A rule rather than a project stamped onto the row, which is how the
        tracker's rows and the work account's events are recognised.  The
        focus card is why: enter opens it on any row, mail rows included, and
        it is handed the name of the row's project -- so a stamped mail row
        would announce the work project on its card.  A tracker row's card
        already does that; this declines to spread it rather than matching
        it.  `row_for` would not have minded either way, returning its own
        tuple for a mail row before it reads a project at all.
        """
        if self.is_mail(task):
            return True
        return self.work_project is not None and task.project_id == self.work_project

    def belongs(self, task: Task) -> bool:
        """Whether a task belongs in the shown view, by that view's own rule.

        Asked of the task rather than assumed from the action that changed
        it, so moving today's task to today keeps it where it was, and a
        past-due task moved further into the past stays in today's view
        because today's past-due rule still claims it.
        """
        position = self.position
        if position is ARCHIVE:
            # A row belongs because it was fetched, and for as long as what
            # was fetched is held.  The two writes this view allows change
            # what a row says, not whether it is here: a task brought back
            # stays on its row until the archive is next read.
            return any(t.id == task.id for t in (self.archive or []))
        if isinstance(position, Bucket):
            if task.done or task.cancelled or task.start is not None:
                return False
            if task.deferred != position.deferred:
                return False
            # A filed task has been sorted, so the inbox does not want it.
            return not (position is Bucket.INBOX and task.project_id)
        started = task.local_start(self.tz)
        if started is not None and started.date() == position:
            return True
        # `reference` is set for today alone, so only today keeps what is
        # past due; elsewhere a task that is not the day's own is not shown.
        return bool(
            self.reference and task.past_due_since(self.reference, self.tz)
        )

    @staticmethod
    def search_text(task: Task) -> str:
        """What a row's title reads as to a search.

        The title the row carries, not what the cell ends up showing.  Two
        things happen to a title on its way to the table: a mail subject
        gains ` (3)` for the messages folded behind it, and `shortened` cuts
        it to the width of the column.  Searching what is drawn would mean a
        search for a number matching thread counts, and a long subject
        findable only by its first few words.

        A third thing happens and then unhappens, which is the trap: the
        cell is built as markup, so a `[` is escaped to `\\[` -- and
        `shortened` then parses that markup back into text, leaving the
        bracket as itself.  Matching the half-built markup string would
        therefore break a search for a bracket while the finished cell looks
        innocent.  Taking the title from the row settles all three.

        One function, read by the search alone, so that what is drawn and
        what is searched cannot drift apart as the row format changes.
        `display_title` covers every kind of row: mail, calendar and tracker
        rows keep their subject or title in the same place a task keeps its
        own, which is what lets the rest of the board draw them without
        knowing which source they came from.
        """
        return task.display_title

    def matches(self, task: Task) -> bool:
        """Whether this row's title contains the term being searched for.

        A plain substring, and `casefold` rather than `lower` so that the
        two alphabets the board is written in both fold: a subject is found
        however its sender capitalised it.

        True for every row while no search is in force, so that the caller
        reads the same whether or not one is.
        """
        if not self.searching:
            return True
        return self.searching.casefold() in self.search_text(task).casefold()

    def window_reason(self) -> str | None:
        """Why the window is hiding the work, or None if it is not doing it.

        A press outranks it: having pressed the key, a person knows what
        hid the rows, and naming a boundary they overruled would be a
        reason that is not the reason.
        """
        if self._work_override is not None or not self.hiding_work:
            return None
        return self._window_reason

    def says(self, tasks: list[Task], shown_issues: int, shown_events: int,
             shown_mail: int, shown_messages: int, hidden_work: int,
             hidden_by_search: int, past_due: int, *,
             archive_held: int = 0,
             archive_drawn: int = 0) -> tuple[str, bool]:
        """The line under the rows, and whether it is an error.

        Every count is beside the others rather than instead of them: the
        number of rows stays the number of rows, and what a filter withheld
        is said next to it.  A notice outranks the lot until the person acts
        again or the view is fetched afresh.
        """
        own = [t for t in tasks
               if not (self.is_tracker(t) or self.is_event(t) or self.is_mail(t))]
        done = sum(1 for t in own if t.done)
        if self.position is ARCHIVE:
            # How many the archive holds, and -- only when the bound withheld
            # some -- how many of them were drawn.  A view showing part of
            # the archive must not read as an archive that small.  "Done" is
            # not said: every row in this view is finished, so a count of
            # them would be the same number twice.
            bits = [f"{archive_held} archived"]
            if archive_drawn < archive_held:
                bits.append(f"{archive_drawn} shown")
        else:
            # The task count is what the board manages; issues are counted
            # beside it, never folded into it.
            bits = [f"{len(own)} task(s)", f"{done} done"]
        if shown_issues:
            # Not named for any one state: more than one may be shown, and
            # which state each issue is in is on its own row.
            bits.append(f"{shown_issues} tracked")
        if shown_mail:
            # Both queues, side by side: the size of each is visible without
            # counting rows, and neither is folded into the other.
            bits.append(f"{shown_mail} thread(s)")
            bits.append(f"{shown_messages} message(s)")
        if shown_events:
            # Counted beside the tasks rather than among them: the board
            # manages the tasks and only reports these.
            bits.append(f"{shown_events} event(s)")
        if past_due:
            bits.insert(1, f"{past_due} past due")
        green = sum(1 for t in own if self.is_green(t))
        if green:
            # Beside the other counts, as the tracker's and the work
            # filter's are: none of them replaces the number of rows.
            bits.append(f"{green} green")
        if hidden_work:
            # Beside the other counts, never instead of them: the shown
            # count stays the number of rows, as the inbox already does for
            # the tasks it withholds.
            why = self.window_reason()
            bits.append(f"{hidden_work} work hidden"
                        + (f" ({why})" if why else ""))
        if hidden_by_search:
            # Beside the other counts, as the work filter's is: the shown
            # count stays the number of rows drawn.  The term itself is on
            # the day bar rather than repeated here, so that a long search
            # does not push the counts off a narrow line.
            bits.append(f"{hidden_by_search} hidden by search")
        if self.marked:
            # Every mark, not the ones this view draws.  Marks follow a
            # person between views, so the count is the only place a mark
            # made somewhere else -- or one a filter is hiding here -- can
            # be seen at all.  Nothing is said with none marked: this
            # reports something a person did, not a permanent fixture.
            bits.append(f"{len(self.marked)} marked")
        in_flight = sum(len(q) for q in self._pending.values())
        if in_flight:
            bits.append(f"{in_flight} saving")
        # A notice outranks the counts until the person acts again or the
        # view is fetched afresh.
        if self.notice:
            return self.notice
        if self.position is ARCHIVE:
            # Both of these outrank the counts and neither is a notice: they
            # are what this view is doing, not what a person's last press
            # did, and they must not be painted over by the next repaint.
            if self.archive_error:
                return self.archive_error, True
            if self.archive_loading:
                # Beside the counts rather than instead of them: the rows
                # that have arrived are on screen and saying nothing about
                # them would make a partial archive look like the whole one.
                return " · ".join(["Reading the archive…"] + bits), False
        if not self.fetched:
            # The events can be on screen before the day's tasks are; saying
            # how many tasks there are before they have arrived would name a
            # number that is about to change.
            return "Loading…", False
        return " · ".join(bits), False

    def cursor_after(self, rows: list[Task], *, keep: str | None,
                     previous: int, scroll: int,
                     drawn_for) -> tuple[int | None, int]:
        """Which row the cursor lands on after a redraw, and where to hold.

        The row a person was on, wherever it has moved to.  Where it has
        gone entirely the answer depends on why: a different view begins at
        its beginning, and the same view keeps the line the departed row
        occupied so that a list is worked down in one place rather than
        chasing the cursor across the screen.

        The previous position and the scroll are given rather than read:
        only the table knows them, and this has to be answerable without one.
        """
        if not rows:
            return None, scroll
        index = next((i for i, t in enumerate(rows) if t.id == keep), None)
        if index is None and self.position != drawn_for:
            # A different view.  It begins at its beginning: its rows have
            # nothing to do with the last one's, so neither the row the
            # cursor was on nor the position it was scrolled to carries any
            # meaning here.
            #
            # Both are said, though revealing row 0 would reach the top on
            # its own.  Saying it is the rule; the reveal reaching the same
            # place is arithmetic, and a reader who removed this would be
            # depending on it.
            return 0, 0
        if index is None:
            # The same view, and the task is gone.  Take the nearest
            # surviving position rather than whatever has moved into the
            # old row.
            index = min(max(previous, 0), len(rows) - 1)
        return index, scroll

    def surviving_marks(self) -> list[str]:
        """The marked ids the shown view cannot say have gone, in their order.

        A task deleted, or a message filed away somewhere else, would
        otherwise leave a mark that can be neither seen nor taken off -- and
        counted, so the board would go on reporting a row that is gone.

        A row counts as gone only where the shown view would have drawn it
        and did not.  The board fetches one view at a time, so a task missing
        from what is in hand is usually missing because the person walked to
        another day -- reading that as a deletion cleared every mark on the
        first view change, which is the whole reason this is asked of the
        view rather than of the fetch.

        The calendar and the tracker are left alone entirely.  The calendar
        is fetched a day at a time and the tracker answers for today, so
        neither can say whether a row it is not currently reporting still
        exists.  A mark on one of those lasts until it is taken off or
        escape clears it.

        Answered rather than performed: the marks belong to the application,
        and a board is thrown away after the paint it was built for.
        """
        held = {t.id for t in self._base}
        held |= {f"{MAIL_PREFIX}{t.newest.ident}" for t in self.mail_threads}
        # The archive is what this view has in hand, where `_base` is what a
        # day's fetch put in hand.  Without this a row marked in the archive
        # is read as one the view would have drawn and did not -- which is
        # what "gone" means here -- and the mark is taken off by the next
        # repaint, which in this view is the next arriving page.
        if self.position is ARCHIVE:
            held |= {t.id for t in (self.archive or [])}

        def gone(ident: str) -> bool:
            if ident in held:
                return False
            task = self._marked_rows.get(ident)
            if task is None or self.is_event(task) or self.is_tracker(task):
                return False
            if self.is_mail(task):
                # Mail is drawn in the inbox and nowhere else, so only the
                # inbox can say a thread has left the folder.
                return self.shows_mail
            return self.belongs(task)

        return [i for i in self.marked if not gone(i)]
