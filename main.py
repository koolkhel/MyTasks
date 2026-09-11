"""A terminal task board for SingularityApp.

Run it with the project venv:

    ./.venv/bin/python main.py            # today
    ./.venv/bin/python main.py 2026-09-05 # a specific day

Keys are listed in the footer; `?` shows the full set.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import threading
import uuid
from contextlib import contextmanager
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
# `time` above is datetime's class, not the module, so the two clock
# functions this needs are imported by name rather than shadowed.
from time import monotonic, sleep
from typing import Any, Callable, Iterable, Iterator

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.markup import escape
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (
    DataTable,
    Header,
    Input,
    Label,
    OptionList,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

import singularity
import email.utils

import gateway
import ical
import journal
import mail
import tracker
from singularity import (
    CANCELLED,
    CHECKED,
    EMPTY,
    Bucket,
    SingularityClient,
    SingularityError,
    Task,
)

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
#: Prefixes a mail row's id.  Built from the newest message's identity, which
#: is unique within the mailbox.
MAIL_PREFIX = "mail:"
#: The mark shown against a mail row, distinct from a task's checkbox, the
#: tracker's arrow and an event's diamond: four kinds of row that cannot be
#: ticked would otherwise look like four of the same thing.
MAIL_ROW_MARK = "@"
#: The three things the mailbox indicator says, in one cell at the right of
#: the day bar.  Chosen for width as much as for looks: every glyph here is
#: unambiguously one terminal cell, where `◐` and `◑` are width-ambiguous
#: and would make the bar's right edge jitter between frames in a
#: CJK-configured terminal.  `✓` and `✗` rather than `☑` and `☒`, which are
#: already this board's ticked and cancelled task marks and would say the
#: wrong thing in the corner of the eye.
MAIL_IDLE_MARK = "✓"
MAIL_FAILED_MARK = "✗"
#: A rotating arc.  Animated because a still mark cannot be told from a
#: stuck one, and these operations last tens of seconds -- motion is the
#: information.
MAIL_BUSY_MARKS = ("◜", "◝", "◞", "◟")
#: How often the arc turns.  Fast enough to read as motion, and it runs only
#: while there is work, so nothing moves while nothing is happening.
MAIL_SPIN_SECONDS = 0.25

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
#: What the terminal is asked to call the tab the board runs in, so that the
#: tab holding it can be found among others without opening it.  Fixed rather
#: than describing the day or the counts: a tab bar is scanned, not read, and
#: a name that moves as work is done is noise where a stable one is a landmark.
TAB_TITLE = "MyTasks"
#: Asking a terminal to name its tab is an escape sequence, not an API.  The
#: form below sets window and icon name together, which is what a tab picks
#: up, and the pair after it remember and restore whatever was there before --
#: the board is quit often, and a tab left misnamed is worse than one never
#: named.  A terminal that understands none of these consumes them silently
#: rather than printing them.
_TITLE_SET = "\x1b]0;{}\x07"
_TITLE_PUSH = "\x1b[22;2t"
_TITLE_POP = "\x1b[23;2t"
#: How long a write that takes the tag off waits behind the previous tag
#: write to the same task.  The store answers such a write and then does not
#: apply it when it arrives soon after another.  Only a removal waits, and
#: only behind a recent write, so taking the mark off a task marked on an
#: earlier day is immediate.  See design.md for the measurements.
TAG_SETTLE_SECONDS = 2.5
#: How many times a removal is re-sent when the store says it applied the
#: write but a read shows the tag still there.  Waiting makes that rare
#: rather than impossible, and the board must not settle for rare: it reads
#: back and sends again.  Two extra attempts, spaced by the same wait.
TAG_REMOVAL_ATTEMPTS = 3
#: How often the board looks at whether an event has ended.  A minute,
#: because a row's time is drawn to the minute and a busier timer could not
#: show anything this one misses.
ELAPSED_CHECK_SECONDS = 60
#: How wide the when-column is.  It carries a tracker row's state and a
#: task's own start time or how overdue it is, so it has to hold the widest
#: of both; eleven cells is what the longest state label needs, and the
#: longest a task puts there is shorter.  Named once so the width the label
#: is trimmed to and the width the column is drawn at cannot drift apart.
_WHEN_WIDTH = 11

#: How wide the column naming a task's project is.  Eleven cells hold the
#: names in use with room to spare; it was twenty-two, and the eleven given
#: back go to the title, which is the column that runs out of room.
_PROJECT_WIDTH = 11
#: What every column other than the title costs, including the two cells of
#: padding the table puts around each of the five.  Measured rather than
#: derived: the padding is not declared anywhere, and assuming it would put
#: the title a few cells too wide and leave the table scrolling after all.
_ROW_OVERHEAD = 1 + 2 + _WHEN_WIDTH + _PROJECT_WIDTH + 2 * 5
#: The narrowest the title column is allowed to be.  Below this a title stops
#: being recognisable, so the board keeps this much and lets the list scroll
#: instead -- which is what it did at every width before.
_TITLE_MIN = 30
#: Put at the end of text the column had to cut, so that a person can tell a
#: title that ends from one that carries on.  The column alone would cut it
#: silently.
_ELLIPSIS = "…"


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

# Every printable key, paired with what the same physical key types on a
# Russian keyboard.  A binding lists both, so the key a person presses is the
# one printed on the keycap whichever layout is active -- otherwise a Russian
# title costs two layout switches, one to type it and one to reach any action
# afterwards.
#
# The whole layout is recorded, not just the keys bound today, because this
# describes the keyboard rather than this app: a binding added later gets its
# twin without anyone having to remember that this table exists.
#
# Letters are keyed by their character, which is what Textual delivers for
# them in either alphabet.  Punctuation is keyed by Textual's own name for it,
# because that is what a binding on it has to say -- pressing "." arrives as
# `full_stop`, never as ".".
_LETTERS = dict(zip("qwertyuiopasdfghjklzxcvbnm",
                    "йцукенгшщзфывапролдячсмить"))
KEY_TWINS: dict[str, str] = dict(_LETTERS)
KEY_TWINS.update({k.upper(): v.upper() for k, v in _LETTERS.items()})
KEY_TWINS.update({
    "left_square_bracket": "х",
    "right_square_bracket": "ъ",
    "semicolon": "ж",
    "apostrophe": "э",
    "comma": "б",
    "full_stop": "ю",
    # A Russian layout types "." on the key that carries "/", and Textual
    # calls that arriving character `full_stop`.
    "slash": "full_stop",
    # The one key that is not a letter-for-letter swap: a Russian layout puts
    # the comma where the question mark is.
    "question_mark": "comma",
})


def keys(spec: str) -> str:
    """A binding's keys, followed by the Russian twin of each that has one.

    `"a"` becomes `"a,ф"` and `"j,down"` becomes `"j,down,о"`.  Twins go at
    the end so the keys a person reads first are the ones the board is
    written in, and so the key bar -- which shows the first key of a binding
    -- goes on naming the English one.  A key with no twin, such as `escape`
    or an arrow, is left exactly as it was.

    A modifier keeps its key company: `"ctrl+s"` becomes `"ctrl+s,ctrl+ы"`.
    Whether a terminal sends the Latin letter or the Cyrillic one for a
    combination depends on the terminal, so the board binds both rather than
    depending on which -- the same answer it gives for a plain letter, and
    one that costs nothing to be wrong about.
    """
    def twin(key: str) -> str | None:
        head, _, tail = key.rpartition("+")
        base = KEY_TWINS.get(tail)
        return None if base is None else (f"{head}+{base}" if head else base)

    parts = [k.strip() for k in spec.split(",")]
    twins = [t for t in (twin(k) for k in parts) if t]
    return ",".join(parts + twins)

# The Turbo C++ editor theme, in the two moods it ships: near-black and the
# classic Borland blue.  Every value below is the one that theme's own files
# declare -- the DOS 16-colour set -- so "looks like Turbo C++" is checkable
# rather than a matter of taste.  The two share their text, selection, error
# and link colours and differ only in the ground and the chrome, which is
# how the source has it.
_TURBO_YELLOW = "#FFFF55"   # editor.foreground -- all ordinary text
_TURBO_CYAN = "#00AAAA"     # the selection bar; the theme's signature
_TURBO_BRIGHT_CYAN = "#55FFFF"  # textLink.foreground
_TURBO_RED = "#FF5555"      # errorForeground
_TURBO_GREEN = "#00AA00"
_TURBO_MAGENTA = "#FF55FF"
_TURBO_GREY = "#AAAAAA"
_TURBO_WHITE = "#FFFFFF"    # list.activeSelectionForeground

TURBO_DARK = Theme(
    name="turbo-cpp-dark",
    dark=True,
    # Pure black rather than the editor theme's #0C0C0C: a deliberate
    # departure, chosen because it blends with a black terminal and widens
    # the gap to the #141414 chrome from 8 to 20 points of luminance, so the
    # day header and key bar read as separate from the list.
    background="#000000",
    surface="#1A1A1A",      # input.background
    panel="#141414",        # statusBar.background
    foreground=_TURBO_YELLOW,
    accent=_TURBO_CYAN,
    primary=_TURBO_BRIGHT_CYAN,
    secondary=_TURBO_MAGENTA,
    error=_TURBO_RED,
    warning=_TURBO_YELLOW,
    success=_TURBO_GREEN,
    variables={
        "text-muted": _TURBO_GREY,          # sideBar.foreground
        "block-cursor-foreground": _TURBO_WHITE,
    },
)

TURBO_BLUE = Theme(
    name="turbo-cpp-blue",
    dark=True,
    background="#0000AA",   # editor.background -- the Borland blue
    surface="#0000CC",      # the theme's raised blue
    panel=_TURBO_GREY,      # statusBar.background -- a light grey bar
    foreground=_TURBO_YELLOW,
    accent=_TURBO_CYAN,
    primary=_TURBO_BRIGHT_CYAN,
    secondary=_TURBO_MAGENTA,
    error=_TURBO_RED,
    warning=_TURBO_YELLOW,
    success=_TURBO_GREEN,
    variables={
        # Stated rather than derived: this theme's own muted colour is the
        # same value as its foreground, so deriving would leave muted text
        # indistinguishable from an ordinary title.
        "text-muted": "#BFBF80",
        "block-cursor-foreground": _TURBO_WHITE,
    },
)


class KeyBar(Static):
    """Every binding the board advertises, wrapped over as many rows as it takes.

    The built-in footer is one row and cannot wrap, so at any realistic width
    it truncates -- the last entries, `? Help` among them, simply vanish.
    This packs the same entries by measured width instead.

    Entries come from the app's own bindings rather than a hand-written list,
    so the bar cannot advertise a key that does nothing or omit one that
    works.  It is a display only: `can_focus` stays false so the keys it
    names keep reaching the app.
    """

    #: Textual's key names are not what a person presses.  Every key bound
    #: for display whose name is words rather than its character belongs
    #: here; the brackets were bound without being added, and the bar
    #: advertised `left_square_bracket` until somebody saw it on screen.
    KEY_NAMES = {
        "full_stop": ".",
        "question_mark": "?",
        "left_square_bracket": "[",
        "right_square_bracket": "]",
        "space": "space",
        "enter": "enter",
    }
    #: Kept so the existing route into Textual's palette survives the swap.
    PALETTE_ENTRY = ("^p", "palette")

    can_focus = False
    can_focus_children = False

    def entries(self) -> list[tuple[str, str]]:
        """(key, description) for every shown binding, in binding order."""
        out = []
        for binding in self.app.BINDINGS:
            if not binding.show or not binding.description:
                continue
            first = binding.key.split(",")[0].strip()
            out.append((self.KEY_NAMES.get(first, first), binding.description))
        out.append(self.PALETTE_ENTRY)
        return out

    @staticmethod
    def pack(entries: list[tuple[str, str]], width: int) -> list[list[tuple[str, str]]]:
        """Greedy left-to-right packing into rows that fit `width`.

        Greedy rather than balanced: an even right edge would reorder the
        entries away from the order they are learnt in, and reading order
        matters more here than tidiness.  An entry wider than the whole
        terminal still gets its own row rather than being dropped -- the
        point of this widget is that nothing disappears.
        """
        rows: list[list[tuple[str, str]]] = []
        row: list[tuple[str, str]] = []
        used = 0
        for key, desc in entries:
            cost = len(key) + len(desc) + 1 + (2 if row else 0)
            if row and used + cost > width:
                rows.append(row)
                row, used = [], 0
                cost = len(key) + len(desc) + 1
            row.append((key, desc))
            used += cost
        if row:
            rows.append(row)
        return rows

    def rebuild(self) -> None:
        width = max(self.size.width or self.app.size.width, 1)
        rows = self.pack(self.entries(), width)
        self.styles.height = len(rows)
        # Assembled as styled text, not written as markup.  One of the keys
        # the bar names is a `[`, and a bracket put into a markup string
        # opens a tag: the bar read `[[/b] Note up` where it should have read
        # `[ Note up`.  Rich's parser had tolerated it and Textual's own does
        # not, so the string stopped meaning what it said with no change
        # here.
        #
        # Escaping does not fix this one.  `textual.markup.escape` escapes a
        # bracket that begins something tag-shaped, which is what text needs;
        # a lone `[` begins nothing, so it comes back unchanged and then
        # merges with the `[/b]` written after it.  Text that carries its own
        # styles is never parsed at all, so no key can break the bar again,
        # whatever character it turns out to be.
        drawn = [
            Content("  ").join([
                Content.assemble((key, "bold"), " ", (desc, "dim"))
                for key, desc in row
            ])
            for row in rows
        ]
        self.update(Content("\n").join(drawn))

    def on_mount(self) -> None:
        self.rebuild()

    def on_resize(self) -> None:
        # Re-pack rather than measuring once: a bar packed for the startup
        # width would clip again the moment the terminal narrowed.
        self.rebuild()


class TaskInput(ModalScreen[str]):
    """One-line prompt used for adding and renaming tasks."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, prompt: str, value: str = ""):
        super().__init__()
        self.prompt = prompt
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.prompt, id="dialog-title")
            yield Input(value=self.value, id="dialog-input")
            yield Label("enter to confirm · esc to cancel", id="dialog-hint")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Submitted)
    def submit(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.dismiss(text)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class NoteArea(TextArea):
    """The board's own text area, for editing a task's note.

    Nothing is added to it yet, and that is the point: keys that act on the
    text -- a template inserted, a date stamped, a line transformed, a marker
    toggled -- belong on a class of the board's rather than on the framework's
    own.  Having the class now costs a name and means adding such a key later
    is a binding rather than a rebuild.

    What it inherits is already an editor: several lines, soft wrapping, undo
    and redo, cut, copy, paste and line deletion.
    """


class NoteInput(ModalScreen[str]):
    """Where a task's note is written.

    Dismisses with the text on saving and with nothing on leaving, so the
    caller cannot mistake "saved an empty note" -- which clears it -- for
    "changed nothing".
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        # Enter belongs to the text, so saving needs a key of its own.
        # `f2` stands beside the usual combination because it is the same
        # key on every keyboard layout, where a combination's letter may
        # not be.
        Binding(keys("ctrl+s") + ",f2", "save", "Save"),
    ]

    def __init__(self, title: str, value: str = ""):
        super().__init__()
        self.title_text = title
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, id="dialog-title")
            yield NoteArea(self.value, soft_wrap=True, id="dialog-note")
            yield Label(
                "ctrl+s or f2 to save · esc to discard · empty clears the note",
                id="dialog-hint",
            )

    def on_mount(self) -> None:
        area = self.query_one(NoteArea)
        area.focus()
        # At the end rather than the start: a note is opened far more often
        # to add a line than to correct the first word.
        area.move_cursor(area.document.end)

    def action_save(self) -> None:
        self.dismiss(self.query_one(NoteArea).text)

    def action_cancel(self) -> None:
        self.dismiss(None)


class LinkPicker(ModalScreen[str]):
    """Pick which of a task's links to open.

    The shape `ProjectPicker` uses, because it is the same act: a list, the
    list's own movement, escape to leave.  Two dialogues that ask a person to
    choose one of several things should not look different from each other.

    Dismisses with the address, so the caller opens what was chosen without
    having to find it again.
    """

    BINDINGS = [Binding(keys("escape,q"), "cancel", "Cancel")]

    def __init__(self, title: str, choices: list[tuple[str, str]]):
        super().__init__()
        self.title_text = title
        self.choices = choices

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, id="dialog-title")
            yield OptionList(
                # Numbered by position, not keyed: a task can hold more
                # links than there are comfortable keys, and the list moves
                # by arrows anyway.
                # Escaped: a label comes from a task's title, its note or
                # a message, and the list draws its options as markup.
                *(Option(escape(shown), id=str(i))
                  for i, (shown, _url) in enumerate(self.choices)),
                id="link-list",
            )
            yield Label("enter to open · esc to leave it", id="dialog-hint")

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    @on(OptionList.OptionSelected)
    def chose(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(self.choices[int(event.option.id)][1])

    def action_cancel(self) -> None:
        self.dismiss(None)


class Confirm(ModalScreen[bool]):
    """Yes/no gate for the destructive actions."""

    BINDINGS = [
        Binding(keys("escape,n"), "no", "No"),
        Binding(keys("y"), "yes", "Yes"),
    ]

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.question, id="dialog-title")
            yield Label("y to confirm · esc to cancel", id="dialog-hint")

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)


class DatePicker(ModalScreen[str]):
    """Choose where the selected task should sit.

    Returns one of the choice keys below, or None if abandoned.  "pick" means
    the caller should go on to ask for a date; the other choices are complete
    in themselves.
    """

    CHOICES = [
        ("t", "today", "Today"),
        ("m", "tomorrow", "Tomorrow"),
        ("p", "pick", "Pick a date…"),
        ("s", "someday", "Someday"),
        ("c", "clear", "Clear date (back to inbox)"),
    ]

    BINDINGS = [Binding("escape", "cancel", "Cancel")] + [
        Binding(keys(key), f"choose('{name}')", label) for key, name, label in CHOICES
    ]

    def __init__(self, title: str, today: date):
        super().__init__()
        self.title_text = title
        self.today = today

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, id="dialog-title")
            lines = []
            for key, name, label in self.CHOICES:
                when = ""
                if name == "today":
                    when = f"{self.today:%Y-%m-%d}"
                elif name == "tomorrow":
                    when = f"{self.today + timedelta(days=1):%Y-%m-%d}"
                lines.append(f"  [b]{key}[/b]   {label:26} [dim]{when}[/dim]")
            yield Static("\n".join(lines), id="picker-body")
            yield Label("esc to cancel", id="dialog-hint")

    def action_choose(self, name: str) -> None:
        self.dismiss(name)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ProjectPicker(ModalScreen[str]):
    """Pick a project for a task, or leave it where it is.

    Every project is listed rather than a keyed handful: the board cannot
    know how many there are, and a list that quietly stopped at nine would
    hide the rest.  Movement is the list's own -- arrows or the keys it
    binds -- so no key has to be found for each project.
    """

    BINDINGS = [Binding(keys("escape,q"), "cancel", "Cancel")]

    def __init__(self, title: str, projects: dict[str, str], current: str | None):
        super().__init__()
        self.title_text = title
        self.projects = projects
        self.current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, id="dialog-title")
            here = self.projects.get(self.current) if self.current else None
            yield Label(
                f"now in: {here}" if here else "now in: no project",
                id="dialog-where",
            )
            options = [
                # The task's own project is marked rather than left out, so
                # the list always reads the same way and choosing it again
                # is harmless.
                # The name is the store's, and the list draws it as markup.
                Option(f"{'* ' if pid == self.current else '  '}{escape(title)}",
                       id=pid)
                for pid, title in sorted(self.projects.items(), key=lambda kv: kv[1])
            ]
            yield OptionList(*options, id="project-list")
            yield Label("enter to choose · esc to cancel", id="dialog-hint")

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    @on(OptionList.OptionSelected)
    def chose(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class TaskFocus(ModalScreen[None]):
    """The selected task, shown in full and shown only.

    The task list gives a title whatever width is left over, so a long one is
    clipped there; this is the view that shows all of it.  Nothing here writes
    -- the key that opens it deliberately does not tick, so a task cannot be
    completed by looking at it.
    """

    BINDINGS = [Binding(keys("escape,enter,q"), "close", "Close")]

    # Deliberately not `task` or `_task`: `Screen` exposes a read-only `task`
    # property, and `_task` is the message-pump coroutine MessagePump sets in
    # its own __init__ -- assigning over either breaks the screen.
    def __init__(self, task: Task, when: str, project: str, tz):
        super().__init__()
        self.shown_task = task
        self.shown_when = when
        self.shown_project = project
        self.shown_tz = tz

    def compose(self) -> ComposeResult:
        task = self.shown_task
        with Vertical(id="dialog"):
            yield Label("Now", id="dialog-title")
            yield Static(escape(task.display_title), id="focus-title")
            # Only the lines the task actually has something for, so a bare
            # task does not render empty labels or stray separators.
            facts = [self.shown_when]
            if self.shown_project:
                facts.append(self.shown_project)
            deadline = task.deadline
            if deadline:
                facts.append(f"deadline {deadline.astimezone(self.shown_tz):%a %d %b %H:%M}")
            if task.recurring:
                facts.append("recurring")
            if task.pinned:
                facts.append("pinned")
            yield Static("  ·  ".join(facts), id="focus-facts")
            note = task.note_text
            if note:
                # Escaped, as the pane below the list escapes it and for the
                # same reason: a note holding square brackets is a note
                # holding square brackets, and the two places a note is
                # shown must not disagree about that.  This card did not
                # escape it until the pane was given a fixed height, which
                # is when the disagreement was noticed.
                yield Static(escape(note), id="focus-note")
            yield Label("esc to close", id="dialog-hint")

    def action_close(self) -> None:
        self.dismiss(None)


class Help(ModalScreen[None]):
    BINDINGS = [Binding(keys("escape,question_mark,q"), "close", "Close")]

    TEXT = """\
[b]Moving around[/b]
  ↑ / ↓ or k / j     select task
  K / J              move the selected task up / down
                     in the day's order — calendar
                     days only, and never past a task
                     the day orders differently
  ← / → or h / l     previous / next day
  t                  jump to today
  i                  inbox — tasks with no date, and the
                     mail awaiting a decision below them.
                     o opens what a thread points at;
                     space files it away; f turns it into
                     a task on today
  s                  someday — tasks put off
  r                  reload from the server
  w                  hide the work project's tasks,
                     and press again to bring them back
  u                  undo the last change, then the one
                     before it — says what it undid;
                     never deletes anything

[b]Looking at a task[/b]
  enter              show the selected task in full
  [ / ]              scroll the note area up / down —
                     the area below the list keeps one
                     height whatever the note is, so the
                     list never moves under the cursor,
                     and a note taller than it scrolls
                     rather than being cut. A scrollbar
                     appears when there is more to see.
                     Reading a note changes nothing, so
                     these work on a mail, calendar or
                     tracker row too

[b]Changing tasks[/b]
  space              tick / untick the selected task —
                     on a mail row it reviews the message
                     instead: see below
  .                  done for today — records the work
                     and moves the task to tomorrow,
                     leaving it unfinished
  d                  set the date: today, tomorrow, a
                     given day, someday, or cleared
  p                  put the task in a project — filing one
                     that has none asks first, because it
                     cannot be un-filed from here
  x                  cancel the task
  a                  add a task to the shown view
  e                  rename the selected task
  n                  write the selected task's note —
                     ctrl+s or f2 saves, esc discards,
                     an empty note clears it
  o                  open the task's link in a browser,
                     a tracker issue's page, or the
                     address a calendar event carries.
                     A task that mentions one of your
                     configured projects' issues opens it
                     too, from its title or its note;
                     where a task offers more than one,
                     o asks which
  W                  start a workspace for the selected
                     tracker issue — asks which version,
                     filled in with the issue's own, then
                     runs the program named by
                     WORKSPACE_COMMAND with the issue's
                     key, its project and that version.
                     The board makes no workspace itself
                     and waits for nothing
  f                  turn the selected mail thread into a
                     task on today, carrying what the
                     message said in its note. The thread's
                     messages are filed away as well, so
                     the row leaves the inbox; u puts both
                     back
  backspace          delete for good (asks first)

[b]Is the mailbox busy?[/b]
  One cell at the right of the second line says so,
  in every view:
    ✓   nothing in flight, nothing wrong
    ◜   turning while messages are being filed away
    ✗   something failed since you last pressed r
  Filing a row away takes ten seconds or more and they
  go one at a time, so ticking several leaves the later
  ones waiting. q asks before quitting while any of it
  is outstanding — the ones that had not started would
  come back at the next launch. r takes the ✗ down.
  Everything the board does to your mail is written to
  logs/mytasks.log: what, which folder, how many, how
  long, and how it ended. Identities and counts only —
  no subject, no sender, nothing from a message body.

[b]Mail awaiting a decision[/b]
  The inbox also lists what the folders you configure
  hold, marked @ and newest first, below your own tasks
  — there is far more mail than there are tasks, and
  your own work should not be behind a scroll. Each row
  shows who it is from and how many messages it stands
  for: updates about one issue in a project you have
  configured are one row, so a discussion is one
  decision rather than five. Only unread mail: a message
  dealt with, here or in whatever program you read mail
  with, is out of the queue.
  What the newest message says is shown in the area
  below the list — [ and ] scroll it, and it is where a
  notification longer than the area is read —
  HTML rendered as text. o opens what the row points at
  — where its messages carry an address with a #fragment
  it offers the earliest of them, so a discussion reads
  downward from where you left off.
  Two keys act on a mail row. o reads it, and space
  reviews it: every message the row stands for is moved
  to your account's archive folder, which is not
  mirrored here — so a reviewed message is gone from
  this queue for good rather than merely marked. Once
  the move is confirmed they are marked read, so nothing
  you have dealt with is still new mail to your other
  programs. f does both, making a task first. Nothing is
  deleted, nothing goes anywhere but the archive, no
  flag is set outside it, and nothing at all is written
  to the mail on this disk. u moves them back, unread
  again, and the row returns when the mailbox next
  catches up.
  Every other key that changes a task refuses a mail
  row. Reviewing needs the mail gateway configured;
  reading does not.

[b]Issues from the tracker[/b]
  Today lists the issues assigned to you in the
  states you configure — in progress, in review —
  below the day's unfinished tasks and above the
  finished ones, each showing which state it is
  in. They are read-only here: open one with
  o, work on it in the tracker. They count as work,
  so w hides them. Without a VPN the board says so
  and carries on without them.

[b]Events from the calendar[/b]
  Each day also shows what your calendar holds for it,
  from the accounts you configure, marked ◇ and placed
  among the tasks by the hour they start — those lasting
  the whole day lead the day. They are read-only here:
  changing one would need the change to travel back, so
  every key that writes refuses and says so. Work-account
  events count as work, so w hides them too.
  o opens the address a meeting carries — taken from
  where the calendar put it, its location or its
  description — and the description is shown below the
  list while the event is selected. An event whose end
  has passed is dimmed, so a day reads as what is left
  of it; one that has started but not finished is not,
  since there is still a chance of joining. The clock
  top right is the current time.

[b]Other[/b]
  ?                  this help
  q                  quit

The keys above work whichever keyboard layout is active: press the key
where it sits on the keyboard, and it does the same thing.

Giving a task a date takes it out of the inbox. Days do
not apply in the inbox or someday, so h / l do nothing
there — press t to get back to the calendar.

Recurring tasks are ticked for the shown day only, so the
series keeps going.\
"""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Keys", id="dialog-title")
            yield Static(self.TEXT, id="help-body")
            yield Label("esc to close", id="dialog-hint")

    def action_close(self) -> None:
        self.dismiss(None)


@dataclass
class Pending:
    """One write applied to the board before the API has confirmed it.

    `patch` holds the raw task keys the write expects to change and
    `previous` their values beforehand, so the outcome can be shown at once
    and taken back should the API refuse it.  The patch is kept beside the
    fetched task rather than written into it: that is what lets a fetch land
    mid-write without discarding the change, and what leaves something to
    restore when a write fails.
    """

    task_id: str
    label: str
    # Takes the id to write to rather than closing over it: a task created
    # here is queued under a placeholder id, and whatever is queued behind
    # its creation must go to the real id the server hands back.
    run: Callable[[str], Any]
    patch: dict[str, Any] = field(default_factory=dict)
    previous: dict[str, Any] = field(default_factory=dict)
    # Deleting is a change of existence, not of fields, so no patch can
    # express it -- there is no value of any key that means "gone".
    removes: bool = False
    # Creating is the other way round: the row exists only because this
    # write is pending, and confirming it settles the task's real id.
    creates: bool = False
    # Which action this write belongs to.  Several writes can share one, so
    # that a single keypress is a single undo however many requests it took.
    group: str = ""


@dataclass
class Undoable:
    """What one action changed, kept so it can be put back.

    `previous` maps a task id to the values its fields held before the
    action, which is what `Pending` already records to roll a refused write
    back -- undo is that record played forward again after the write stuck.

    One entry covers one action, not one request: moving a task can write
    every task in its run, and a person who pressed one key expects one
    press to reverse it.

    An entry that cannot be reversed is still kept, carrying `reason`, so
    that pressing undo after a deletion says so rather than silently
    reversing something older that the person was not asking about.
    """

    group: str
    label: str
    subject: str
    previous: dict[str, dict[str, Any]] = field(default_factory=dict)
    # The tasks themselves, so an undo can reach a task that is not in the
    # view any more -- the board writes what it wrote, wherever the person
    # has navigated to since.
    tasks: dict[str, Task] = field(default_factory=dict)
    #: How many of this action's writes the API has accepted.  An action
    #: can take several, and one of them failing does not unhappen the rest.
    applied: int = 0
    reason: str = ""
    note: str = ""
    #: Where reversing an action is not a matter of putting fields back.
    #: Called with the tasks this entry wrote, keyed by the id they hold
    #: now, and is then the whole of the undo.  Creating a task cannot be
    #: reversed by restoring anything -- there was nothing before it -- so
    #: an action that creates and can still be taken back needs this.
    undo_action: "Callable[[dict[str, Task]], bool] | None" = None

    @property
    def reversible(self) -> bool:
        return not self.reason


class TaskApp(App[None]):
    """Day-at-a-time view of your tasks."""

    TITLE = "Singularity tasks"

    CSS = """
    Screen { layers: base overlay; }

    #body { height: 1fr; }

    /* The framework draws the header as $foreground on $panel.  In the blue
       theme those are the palette's yellow on its grey -- #FFFF55 on
       #AAAAAA, a measured 2.18:1, which is not readable; the dark theme's
       #141414 gives 17.27:1 and is fine.  A deliberate departure from using
       the declared panel colour here, recorded like the others: $surface
       measures 16.32:1 on the dark theme and 10.52:1 on the blue, so the
       header reads in both.  This was always true of the title; the clock is
       what made it worth fixing, having put something there worth reading. */
    Header {
        background: $surface;
        color: $foreground;
    }

    #daybar {
        height: 1;
        background: $panel;
        /* `auto`, not a fixed colour: this bar is near-black under one Turbo
           theme and light grey under the other, and `auto` resolves to white
           or black to suit.  A fixed value would be unreadable in one. */
        color: auto;
        padding: 0 1;
    }

    DataTable {
        height: 1fr;
        /* The list sits on the ground, not on $surface: a DataTable defaults
           to the raised surface colour and then blends 5% of the foreground
           over it, which together turned a black ground into #25251C. */
        background: $background;
        background-tint: transparent;
    }
    DataTable > .datatable--cursor { background: $accent; color: $text; }

    #notes {
        /* Nine, for eight rows of text: `border-top` counts inside the
           height box.  Fixed against the note, which is the whole point --
           an area sized to its content moves the list under the hand that
           is moving through it.  Capped against the window as well, because
           eight rows of note on a twelve-row terminal would leave a list of
           four; the cap bites below about 22 rows and never above. */
        height: 9;
        max-height: 40%;
        border-top: solid $panel;
        padding: 0 1;
        color: $text-muted;
    }
    /* Free to be taller than the pane: that is what there is to scroll. */
    #detail { height: auto; }

    #status { height: 1; padding: 0 1; color: $text-muted; }
    #keybar { padding: 0 1; background: $panel; color: auto; }
    #status.error { color: $error; }

    #dialog {
        width: 62;
        max-width: 90%;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: round $accent;
    }
    /* The prompt that adds and renames a task sets its own width, and only
       its width: a title is often longer than the 50 cells the shared box
       leaves for text, and a person editing what they cannot see is
       guessing.  The other five dialogues keep the shared rule -- a short
       question reads worse stretched.  `max-width` above still clamps this
       on a narrow terminal, so no second rule is needed to make it safe. */
    TaskInput #dialog { width: 90; }
    /* The note editor takes the same width as the title prompt, for the same
       reason, and a height that shows several lines without swallowing the
       list behind it. */
    NoteInput #dialog { width: 90; }
    #dialog-note { height: 12; border: none; background: $surface; }
    #dialog-title { text-style: bold; }
    #dialog-hint { color: $text-muted; }
    #dialog-where { color: $text-muted; padding: 0 0 1 0; }
    #project-list { height: auto; max-height: 12; background: $surface; }
    #link-list { height: auto; max-height: 12; background: $surface; }
    #help-body { padding: 1 0; }
    #picker-body { padding: 1 0; }
    #focus-title { text-style: bold; padding: 1 0 0 0; }
    #focus-facts { color: $text-muted; padding: 1 0 0 0; }
    #focus-note { padding: 1 0 0 0; }
    ModalScreen { align: center middle; }
    """

    BINDINGS = [
        # Not Textual's own quit: while the mailbox is busy this asks
        # first.  Quitting mid-queue abandons the reviews that have not
        # started -- nothing is lost, because they moved nothing, but the
        # rows return at the next start and are then indistinguishable from
        # a message the local mirror has not caught up on.
        Binding(keys("q"), "leave", "Quit"),
        Binding(keys("j,down"), "cursor_down", "Down", show=False),
        Binding(keys("k,up"), "cursor_up", "Up", show=False),
        # Uppercase moves the task, lowercase the cursor: the same gesture
        # with more force.  Plain characters, so no terminal can swallow
        # them -- cmd+arrow cannot work at all, since Textual has no super
        # modifier and macOS does not forward Cmd to the terminal.
        Binding(keys("K"), "move_up", "Move up"),
        Binding(keys("J"), "move_down", "Move down"),
        Binding(keys("h,left"), "prev_day", "Prev day"),
        Binding(keys("l,right"), "next_day", "Next day"),
        Binding(keys("t"), "today", "Today"),
        Binding(keys("i"), "inbox", "Inbox"),
        Binding(keys("s"), "someday", "Someday"),
        Binding(keys("r"), "refresh", "Reload"),
        Binding(keys("w"), "toggle_work", "Hide work"),
        Binding(keys("u"), "undo", "Undo"),
        # Named for both things it does: on a task it ticks, on a mail row
        # it files the message away where the board cannot show it again,
        # and the bar is where a person finds that out before pressing it.
        Binding("space", "toggle", "Tick / review"),
        # Its own key, never shared with tick: "." mirrors the app's cmd+.
        Binding(keys("full_stop"), "done_for_today", "Did today"),
        # Not priority: a priority binding fires ahead of every focused
        # widget, including the Input inside the rename, add, and date
        # prompts, which then can never be confirmed with enter.  On the
        # board the focused DataTable turns enter into RowSelected, which
        # `row_selected` below acts on; this entry names the key in the
        # footer and covers the case where the table is not focused.
        Binding("enter", "focus_task", "Focus"),
        Binding(keys("a"), "add", "Add"),
        Binding(keys("e"), "rename", "Rename"),
        Binding(keys("n"), "note", "Note"),
        Binding(keys("x"), "cancel_task", "Cancel"),
        Binding(keys("d"), "schedule", "Date"),
        Binding(keys("p"), "project", "Project"),
        Binding(keys("g"), "green", "Green"),
        Binding(keys("o"), "open_link", "Link"),
        Binding(keys("W"), "start_workspace", "Workspace"),
        # The note pane's own two keys, so reading a note that does not fit
        # never costs the list its arrows.  Plain characters, for the reason
        # the movement keys are: a terminal cannot swallow them the way it
        # can a modified arrow.  Both already have Cyrillic twins in the key
        # table, so `keys()` needs nothing new.
        Binding(keys("left_square_bracket"), "note_up", "Note up"),
        Binding(keys("right_square_bracket"), "note_down", "Note down"),
        Binding(keys("f"), "promote", "To task"),
        # Both keys, and deliberately NOT priority: a Mac laptop has no
        # forward-delete, so its Delete key arrives as backspace, while an
        # external keyboard sends delete.  A priority binding would take
        # backspace away from the text prompts, where it erases characters.
        Binding("backspace,delete", "delete", "Delete"),
        Binding(keys("question_mark"), "help", "Help"),
    ]

    def __init__(self, position: "date | Bucket | None" = None):
        super().__init__()
        self.client: SingularityClient | None = None
        # What the board is showing: a calendar day, or one of the two
        # dateless buckets.  One value, so no view can be half-selected.
        self.position: "date | Bucket" = (
            position if position is not None
            else datetime.now(singularity.local_tz()).date()
        )
        self.tasks: list[Task] = []
        # How many tasks the shown view withheld; only the inbox withholds.
        self.filed_out = 0
        # How many rows are past due, and the instant that was decided
        # against.  Only today's view gathers any, so elsewhere this is
        # 0 / None and no row is marked.
        self.past_due = 0
        #: How many rows the work filter removed from the shown view.
        self.hidden_work = 0
        #: Whether the shown view's own tasks have arrived yet.  The
        #: calendar answers in a couple of milliseconds where the store
        #: takes hundreds, so without this the board would report "0
        #: task(s)" beside the events for as long as the fetch lasts --
        #: a day that looks empty rather than one still loading.
        self._fetched = False
        #: How many mail threads the shown view holds, and how many messages
        #: they stand for.
        self.shown_mail = 0
        self.shown_messages = 0
        #: How many calendar events the shown view holds.
        self.shown_events = 0
        #: How many of them were already over when the rows were last drawn.
        #: What the timer compares against, so a redraw happens on a change
        #: and not on a schedule.
        self._ended_shown = 0
        #: How many tracker issues the shown view holds.
        self.shown_issues = 0
        self.reference: datetime | None = None
        self.projects: dict[str, str] = {}
        # What the last fetch reported, kept apart from the pending writes
        # layered over it so a refresh can replace one without disturbing
        # the other.  `tasks` is what is on screen: the two combined.
        self._base: list[Task] = []
        # Writes awaiting the API, queued per task.  Per task rather than
        # globally so writes to different tasks go out together while one
        # task's own writes stay in the order they were performed.
        self._pending: dict[str, deque[Pending]] = {}
        self._draining: set[str] = set()
        # The selected task's id, so the cursor can follow the task through
        # the reordering a write causes instead of holding a row number.
        self._selected_id: str | None = None
        # Something to keep on the status line until the person acts again.
        # Repainting rewrites the status from the view's counts, so anything
        # said once is gone the moment the next write confirms -- which is
        # exactly when a refusal or an "undid this" most needs to still be
        # readable.  Held as (message, is_error).
        self._notice: tuple[str, bool] | None = None
        # Whether the work project's tasks are being hidden.  A mode over
        # the views rather than part of what a view holds, so `belongs` goes
        # on answering only where a task lives.  It lasts as long as the
        # board is open and writes nothing.
        self.hiding_work = False
        # What the working window last said, and whether a press is
        # overruling it.  The mode stays a plain boolean because `repaint`
        # reads it three times and must see one answer; a property reading
        # the clock would make every redraw depend on when it happened.
        #
        # Nothing records when a press expires.  Each tick asks the window
        # about now and compares with `_window_hides`: the same answer
        # changes nothing, a different one clears the overrule.  The
        # comparison is the expiry.
        self._window_hides: bool | None = None
        #: Why the window is hiding the work, in the words the board shows,
        #: or None while it is not.  Kept rather than recomputed where it is
        #: drawn: the status line would otherwise read the clock on every
        #: redraw, and the mode is exactly the thing that must not depend on
        #: when a redraw happened.
        self._window_reason: str | None = None
        self._work_override: bool | None = None
        # What this session has written, most recent last, so the undo key
        # can walk back through it.  Session-long: nothing is kept on disk.
        self._undo: list[Undoable] = []
        # The issue tracker: read-only, today only, and entirely optional.
        # A board with none configured is an ordinary board.
        self.tracker_config = tracker.load_config()
        self.tracker_issues: list[tracker.Issue] = []
        #: Why the tracker could not be read, when it could not be.  Kept
        #: apart from the day's own errors: an unreachable tracker must
        #: never be reported as the day failing to load.
        self.tracker_error: str | None = None
        # The mailbox: read except for the seen flag a promotion sets, shown
        # in the inbox, and equally optional.  A board with none configured
        # is an ordinary board.
        self.mail_config = mail.load_config()
        #: How to reach the mail gateway, or None.  Its own configuration,
        #: separate from the mailbox's: reading needs no credentials and no
        #: network, and a board that can read mail and not file it away is
        #: a real state rather than a broken one.
        self.gateway_config = gateway.load_config()
        #: How a connection to the gateway is opened, or None for the real
        #: one.  The single seam through which the board reaches a mail
        #: server, so a suite can drive every path of a review -- including
        #: the ones that must fail -- without an account.
        self.gateway_connect = None
        #: Identities the gateway has confirmed are in the archive, for this
        #: session only.  The folders are a mirror, refreshed on a timer of
        #: its own, so for up to one sync interval a read still returns a
        #: message that has already been filed away -- and every view change
        #: re-reads.  Without this the queue would not drain: a person who
        #: reviewed ten rows and pressed `i` would meet them all again, which
        #: is the one thing this whole change exists to prevent.
        #:
        #: Nothing is written anywhere, and nothing survives the session: the
        #: account is still the record of what has been reviewed.  This only
        #: keeps the board from showing what it has already been told is
        #: gone.  Pruned on every read to what the mailbox still holds, so it
        #: stays the size of the mirror's lag rather than growing all day.
        self.reviewed: set[str] = set()
        #: Set when the board is leaving, so a review that is part way
        #: through confirming gives up instead of holding the run open.
        #: Quitting used to wait five minutes on a worker blocked in the
        #: gateway, saying nothing.
        #:
        #: Emphatically NOT `_closing`: that name belongs to Textual's
        #: message pump, whose loop reads it -- `while not (self._closed or
        #: self._closing)` -- so assigning it told the framework the app was
        #: shutting down and stopped it accepting messages while it was
        #: still running.  The same collision this file already records
        #: against `_task` on the focus card.
        self._leaving = False
        #: Held for the length of one review, so reviews reach the gateway
        #: one at a time.  Without it a person ticking ten rows in a row
        #: opened ten connections at once, each holding the archive open
        #: for the minutes a confirmation takes -- which is slower for all
        #: ten than doing them in turn, and is a load the account did not
        #: ask for.  The rows have already left the screen, so waiting here
        #: costs a person nothing.
        self._mail_gate = threading.Lock()
        #: Which row the note pane was last drawn for.  The pane returns to
        #: the top when that changes and not otherwise: the text is written
        #: on every repaint, and repaints happen for reasons that are
        #: nothing to do with the person -- a mail load returning, a write
        #: confirming, a timer noticing an event has ended.  Resetting on
        #: each of those would yank a half-read note back to its beginning.
        self._detail_for: str | None = None
        #: Which view the table was last drawn for.  A different one is a
        #: different list, so the row NUMBER the cursor was on means
        #: nothing in it -- carrying it over put today's last row under the
        #: cursor when the inbox had been scrolled to row 300, and then
        #: carried that back into the inbox as row 20.
        self._drawn_for: "date | Bucket | None" = None
        #: How many operations on the mail account are in flight.  Counted
        #: here rather than asked of the worker manager, which offers no
        #: count by group: a number the board owns is a number a suite can
        #: drive, and the board already counts its store writes this way.
        #:
        #: Every path on which an operation ends must bring this down --
        #: there are six, and one missed would leave the board saying "wait"
        #: for the rest of the session, which is worse than saying nothing.
        self.mail_busy = 0
        #: Set by any failed operation, cleared by an explicit reload.  Not
        #: cleared by a later success: a failure among ten reviews would
        #: otherwise be painted over before it was seen, which is the whole
        #: reason for showing it.
        #:
        #: `mail_broken`, not `mail_failed`: that name is already a method
        #: on this class -- the one that reports an unreadable mailbox --
        #: and an attribute of the same name shadowed it, so
        #: `call_from_thread(self.mail_failed, ...)` was handed `False` and
        #: raised.  The second name collision in this one change; the first
        #: was Textual's `_closing`.
        self.mail_broken = False
        #: Which frame of the arc is showing, and the timer turning it.  The
        #: timer exists only while there is work: the clock's requirement
        #: already says nothing here may move for nothing.
        self._spin = 0
        self._spinner = None
        self.mail_threads: list = []
        #: Why the mailbox could not be read, when it could not be.  Kept
        #: apart from the day's own errors for the reason the tracker's and
        #: the calendar's are: an unreadable mailbox is not the day failing.
        self.mail_error: str | None = None
        # The calendar: read-only, for whichever day is shown, and equally
        # optional.  A board with no accounts configured is an ordinary board.
        self.calendar_config = ical.load_config()
        self.events: list[ical.Event] = []
        #: Which day the events on hand belong to, so a day change is never
        #: shown the day before's events while the new day is being read.
        self.events_day: date | None = None
        #: Why the calendar could not be read, when it could not be.  Kept
        #: apart from the day's own errors for the tracker's reason: an
        #: unreadable calendar is not the day failing to load.
        self.calendar_error: str | None = None
        self.work_project: str | None = singularity.load_work_project()
        #: The hours and days work is shown in, when any are configured, and
        #: why the setting could not be read when it could not.  An
        #: unreadable window costs a person the feature, not their board, so
        #: it is reported and then behaves as though none were configured.
        #: The program that makes a workspace, when one is configured.  A
        #: path the board execs, never a command line it interprets.
        self.workspace_command: str | None = singularity.load_workspace_command()
        self.working_window: singularity.WorkingWindow | None = None
        self.window_error: str | None = None
        try:
            self.working_window = singularity.load_working_window()
        except ValueError as exc:
            self.window_error = f"WORK_HOURS could not be read: {exc}"
        self.green_tag: str | None = singularity.load_green_tag()
        #: What the configured tag turned out to be, once looked up, and
        #: whether that lookup has happened.  The two are separate because
        #: "not looked up yet" and "looked up, and it names nothing" call
        #: for opposite answers when the key is pressed.
        self.green_title: str | None = None
        self.green_checked: bool = False
        #: When each task's tag was last written, so a removal knows whether
        #: it has to wait.  Keyed by task id; absent means "not this sitting".
        self._tag_written: dict[str, float] = {}

    # -- layout ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        # The clock is the framework's own: it owns its interval, refreshes
        # itself, and does not touch the table to do it.  To the minute --
        # seconds would move several times a second in the corner of the eye
        # for a precision nothing here acts on, and every other time this
        # board shows is to the minute.
        yield Header(show_clock=True, time_format="%H:%M")
        with Vertical(id="body"):
            yield Static("", id="daybar")
            # No zebra striping: it paints every other row a lighter shade,
            # which stops the ground being the ground.  Turbo C++ had no
            # alternating rows either.
            yield DataTable(id="tasks", cursor_type="row")
            # The pane scrolls, and the text still goes to `#detail`.  Two
            # widgets rather than one scrollable `Static` because that id is
            # an interface: four suites read the note back through it, and
            # the pane is a new thing that deserves a new name rather than
            # a change to what has always held the text.
            # Not focusable, and not merely by default: a scrollable
            # container takes focus willingly, and a pane that could hold it
            # would take the arrow keys off the list the moment it was
            # tabbed into -- a mode, which this board does not have.  Its
            # own keys reach it while the table keeps focus.
            with VerticalScroll(id="notes", can_focus=False,
                                can_focus_children=False):
                yield Static("", id="detail")
        yield Static("", id="status")
        yield KeyBar(id="keybar")

    def on_mount(self) -> None:
        for theme in (TURBO_DARK, TURBO_BLUE):
            self.register_theme(theme)
        # Assigned here rather than as a class attribute: the class default
        # is read before these are registered, and assigning the same name
        # twice would not fire the watcher that recomputes the palette.
        # Registering also puts both in the command palette's theme picker,
        # so switching needs no binding of its own.
        self.theme = TURBO_DARK.name
        # How often to look at whether an event has ended.  A minute is the
        # granularity the rows are drawn to, so a shorter interval could not
        # show anything a longer one missed.
        self.set_interval(ELAPSED_CHECK_SECONDS, self.each_minute)
        table = self.query_one(DataTable)
        table.add_column("", key="mark_green", width=1)
        table.add_column("", key="mark", width=2)
        table.add_column("When", key="when", width=_WHEN_WIDTH)
        table.add_column("Task", key="title", width=self.title_width)
        table.add_column("Project", key="project", width=_PROJECT_WIDTH)
        table.focus()
        # The state the board opens in comes from the clock, before the
        # first fetch: opening the board in the evening should find the work
        # already gone rather than watch it leave.
        self.apply_window()
        if self.window_error is not None:
            # Said once, here, and never from the tick: a complaint repeated
            # every minute about a setting nobody can fix from inside the
            # board would sit on the counts forever.
            self.notice(self.window_error, True)
        self.load()

    # -- data --------------------------------------------------------------

    @work(exclusive=True, thread=True)
    def load(self) -> None:
        """Fetch the shown view's tasks off the UI thread."""
        self.call_from_thread(self.set_status, "Loading…")
        # Started before the day is asked for, not after: the calendar is on
        # its own path entirely, so a store that is slow or unreachable does
        # not decide whether the day's events are read.
        self.call_from_thread(self.load_calendar)
        self.call_from_thread(self.load_mail)
        try:
            if self.client is None:
                self.client = SingularityClient()
            if not self.projects:
                self.projects = self.client.project_names()
            listing = self.client.tasks_at(self.position)
        except SingularityError as exc:
            self.call_from_thread(self.set_status, str(exc), True)
            return
        self.call_from_thread(self.show_tasks, listing)
        if self.green_tag and not self.green_checked:
            # After the day is on screen, for the same reason the tracker is:
            # nothing about the mark needs this, only the name the board says
            # back, so making the first paint wait on it would buy nothing.
            # Read back rather than trusted -- an id left behind by a deleted
            # tag would otherwise mark nothing and look like a quiet day.
            try:
                self.green_title = self.client.tag_title(self.green_tag)
            except SingularityError:
                self.green_title = None
            self.green_checked = True
        # Started once the day is on screen, and never awaited: the day
        # appears in its own time whatever the tracker does.
        if self.shows_tracker:
            self.call_from_thread(self.load_tracker)
        else:
            self.call_from_thread(self.clear_tracker)

    # -- the tracker -------------------------------------------------------

    @work(exclusive=True, thread=True, group="tracker")
    def load_tracker(self) -> None:
        """Read the tracker's issues, off the UI thread and off the day's path.

        Its own worker on purpose.  The day must not wait for it -- a fetch
        takes about as long again as loading today does -- and a tracker that
        cannot be reached must not surface as the day failing to load, which
        is what would happen if this were raised where the day's own errors
        are caught.
        """
        config = self.tracker_config
        if config is None:
            return
        try:
            issues = tracker.fetch(config)
        except tracker.TrackerUnreachable as exc:
            self.call_from_thread(self.tracker_failed, str(exc))
            return
        self.call_from_thread(self.tracker_loaded, issues)

    def clear_tracker(self) -> None:
        """Forget the tracker's rows where they cannot apply to the view."""
        if self.tracker_issues or self.tracker_error:
            self.tracker_issues = []
            self.tracker_error = None
            self.repaint()

    def tracker_loaded(self, issues: list[tracker.Issue]) -> None:
        """Take what the tracker reported, and stop saying it was unreachable.

        The message about being unreachable is sticky, so that a repaint
        cannot wipe it -- which means recovering has to take it down
        explicitly, or the board would go on claiming a tracker it has just
        read.  Only the tracker's own message is cleared; anything else
        being shown is left alone.
        """
        was = self.tracker_error
        self.tracker_issues = issues
        self.tracker_error = None
        if was and self._notice and self._notice[0] == was:
            self._notice = None
        self.repaint()

    def tracker_failed(self, message: str) -> None:
        """Remember that the tracker is unreachable, and say so.

        Said rather than left silent: with one issue typically in progress,
        an empty block is the ordinary case, so a quiet failure would be
        indistinguishable from a quiet day.
        """
        self.tracker_issues = []
        self.tracker_error = message
        self.repaint()
        self.notice(message, True)

    # -- the calendar ------------------------------------------------------

    @work(exclusive=True, thread=True, group="calendar")
    def load_calendar(self) -> None:
        """Read the shown day's events, off the UI thread and off the day's path.

        Its own worker for the tracker's reasons, and asked afresh for every
        day rather than cached: a day costs a couple of milliseconds, so
        there is nothing to keep in step and nothing to go stale.

        A view that is not a day -- the inbox, someday -- has no date for the
        calendar to answer, so it holds no events rather than today's.
        """
        config = self.calendar_config
        day = self.position
        # Asked positively -- "is this a day" rather than "is this a bucket".
        # The negative form was a bug the moment a third kind of position
        # existed: one that was neither a Bucket nor a date fell through
        # here, and the calendar was asked for the events of something that
        # is not a day.
        if config is None or not isinstance(day, date):
            self.call_from_thread(self.clear_calendar)
            return
        try:
            events = ical.fetch(config, day)
        except ical.CalendarUnreadable as exc:
            self.call_from_thread(self.calendar_failed, day, str(exc))
            return
        self.call_from_thread(self.calendar_loaded, day, events)

    def clear_calendar(self) -> None:
        """Forget the events where they cannot apply to the view."""
        if self.events or self.calendar_error or self.events_day is not None:
            self.events = []
            self.events_day = None
            self.calendar_error = None
            self.repaint()

    def calendar_loaded(self, day, events: list[ical.Event]) -> None:
        """Take the day's events, and stop saying the calendar was unreadable.

        The day the read was for is checked against the day now shown: a
        slow read finishing after the person has moved on must not put one
        day's events under another's date.
        """
        if day != self.position:
            return
        was = self.calendar_error
        self.events = events
        self.events_day = day
        self.calendar_error = None
        if was and self._notice and self._notice[0] == was:
            self._notice = None
        self.repaint()

    def calendar_failed(self, day, message: str) -> None:
        """Remember that the calendar is unreadable, and say so once.

        Said rather than left silent for the tracker's reason: a day with no
        events is perfectly ordinary, so a quiet failure would be
        indistinguishable from a free day.
        """
        if day != self.position:
            return
        self.events = []
        self.events_day = day
        if self.calendar_error == message:
            # Already said, and the day has not changed underneath it.
            # Repeating it on every refresh would bury whatever else the
            # board has to say.
            return
        self.calendar_error = message
        self.repaint()
        self.notice(message, True)

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

    def minutes_into_day(self, task: Task) -> int | None:
        """How far into the day a row happens, or None if it names no time.

        One answer for both kinds of row, so placing an event among the
        tasks is a comparison of like with like.
        """
        if self.is_event(task):
            return task.raw.get(EVENT_MINUTES)
        if not task.timed:
            return None
        started = task.local_start(self.tz)
        return None if started is None else started.hour * 60 + started.minute

    def event_key(self, event: Task) -> tuple:
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

    def has_ended(self, task: Task) -> bool:
        """Whether this row's event is already over.

        Against the present rather than against `reference`: that instant is
        the fetch's, and is absent on every day but today, so a rule measured
        by it would simply never fire elsewhere.  The two are deliberately
        different clocks answering different questions -- see design.md.
        """
        ends = task.raw.get(EVENT_ENDS)
        return ends is not None and ends <= datetime.now(self.tz).timestamp()

    def ended_count(self) -> int:
        """How many shown rows are events already over.

        What the timer compares.  Cheap, and enough: the set only ever grows
        as time passes within one fetch, so a change in its size is a change
        in the set.
        """
        return sum(1 for t in self.tasks if self.is_event(t) and self.has_ended(t))

    @staticmethod
    def is_event(task: Task | None) -> bool:
        """Whether a row came from the calendar rather than the board."""
        return bool(task is not None and task.raw.get(EVENT_MARK))

    # -- the mailbox -------------------------------------------------------

    @property
    def shows_mail(self) -> bool:
        """Whether the shown view is the one mail belongs to.

        The inbox: the board's queue of things that have arrived and not been
        decided about, which is what mail read daily is.  Not a view of its
        own -- see design.md, where the reasoning that first gave it one is
        recorded along with why it was wrong.
        """
        return self.position is Bucket.INBOX

    @work(exclusive=True, thread=True, group="mail")
    def load_mail(self) -> None:
        """Read the mailbox, off the UI thread and off the day's path.

        Its own worker for the reasons the tracker's and the calendar's are:
        a mailbox can be large, and a day must not wait for it, nor be
        reported as failing when it is the mailbox that could not be read.
        """
        config = self.mail_config
        if config is None:
            return
        try:
            raw = mail.read(config)
        except mail.MailboxUnreadable as exc:
            self.call_from_thread(self.mail_failed, str(exc))
            return
        held = {message.ident for message in raw}
        # Filtered before grouping, not after: a row can hold messages from
        # a folder that has caught up and one that has not, and dropping the
        # whole row would hide mail that is still there.
        filed = self.reviewed
        found = mail.threads([m for m in raw if m.ident not in filed],
                             fold=self.mail_fold)
        self.call_from_thread(self.mail_loaded, found, held)

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

    def mail_loaded(self, found: list, held: "set[str] | None" = None) -> None:
        """Take what the mailbox held, and stop saying it was unreadable."""
        was = self.mail_error
        self.mail_threads = found
        if held is not None:
            # Only what the mirror still returns.  An identity it has caught
            # up on needs remembering no longer, and forgetting it is what
            # keeps this bounded by the sync interval.
            self.reviewed &= held
        self.mail_error = None
        if was and self._notice and self._notice[0] == was:
            self._notice = None
        self.repaint()

    def mail_failed(self, message: str) -> None:
        """Remember that the mailbox is unreadable, and say so once."""
        self.mail_threads = []
        if self.mail_error == message:
            return
        self.mail_error = message
        self.repaint()
        self.notice(message, True)

    def _mail_when(self, stamp: float) -> str:
        """When a message arrived, in the room the column leaves.

        The time alone for today, the date for anything older -- which is
        what every mail client does, and what fits: a date and a time
        together is twelve cells against the eleven this column has, and
        would be cut just where the minutes are.
        """
        when = datetime.fromtimestamp(stamp, self.tz)
        if when.date() == datetime.now(self.tz).date():
            return when.strftime("%H:%M")
        return when.strftime("%d %b")

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
                # Where a task keeps its note, so the detail area shows what
                # the message says with no knowledge of mail at all -- the
                # same path a calendar event's description takes.  The
                # newest message's, consistent with the links offered.
                "note": newest.body,
            }))
        return rows

    @staticmethod
    def is_mail(task: Task | None) -> bool:
        """Whether a row came from the mailbox rather than the board."""
        return bool(task is not None and task.raw.get(MAIL_MARK))

    @staticmethod
    def by_folder(messages: Iterable[Any]) -> dict[str, list[str]]:
        """These messages' identities, grouped by the folder each was read from.

        A row can hold messages from more than one folder -- what folds them
        is the issue they are about -- and the gateway addresses a message
        within a folder, so the folder has to travel with the identity.
        """
        out: dict[str, list[str]] = {}
        for message in messages:
            out.setdefault(message.folder, []).append(message.ident)
        return out

    def drop_thread(self, task: Task) -> tuple[Any, int] | None:
        """Take the row's thread out of the queue, and hand it back.

        With the position it held, so an archive that cannot be confirmed
        puts the row back where the person last saw it rather than at the
        end of a queue of hundreds.
        """
        ident = task.id[len(MAIL_PREFIX):]
        for where, thread in enumerate(self.mail_threads):
            if thread.newest.ident == ident:
                self.mail_threads = (self.mail_threads[:where]
                                     + self.mail_threads[where + 1:])
                return thread, where
        return None

    def restore_thread(self, thread: Any, where: int | None) -> None:
        """Put a thread back in the queue, where it was."""
        if any(t.newest.ident == thread.newest.ident for t in self.mail_threads):
            return
        at = len(self.mail_threads) if where is None else where
        self.mail_threads = (self.mail_threads[:at] + [thread]
                             + self.mail_threads[at:])
        self.repaint()

    def review(self, task: Task) -> None:
        """File the selected mail row away, and take it out of the queue.

        The row goes at once and the moving happens behind the screen, as
        every write on this board does.  It does not go through
        `submit_write`, though: that machinery speaks to the task store and
        carries a patch to apply to a task, and neither is what this is.

        The row leaves the queue before the move is confirmed, and comes
        back if it cannot be.  The other order -- wait, then retire -- would
        leave a person looking at a row for the second a confirmation takes,
        with no way to tell it from one the key had missed.
        """
        messages = list(task.raw.get(MAIL_MESSAGES) or ())
        title = task.title
        config = self.gateway_config
        if config is None:
            # Reading mail needs nothing; filing it away needs an account.
            # Said plainly rather than refused as unownable: the row is the
            # board's to act on, and this is the one thing missing.
            self.notice(
                "reviewing files the message away on the server · "
                "no mail gateway is configured",
                True,
            )
            return
        if not messages:
            self.notice(f"“{title}” holds no message to file away", True)
            return
        # The selection is read before the row goes, from the list on
        # screen, so it lands where the person was looking.
        after = self.next_open_after(task)
        dropped = self.drop_thread(task)
        if dropped is None:
            # The queue was re-read between the keypress and here.  Nothing
            # to file away that the next read will not show again.
            self.notice(f"“{title}” is no longer in the queue", True)
            return
        thread, where = dropped
        self._selected_id = after
        self.notice(f"Reviewing “{title}” · filing {len(messages)} away")
        self.repaint()
        self.remember_review(task, title, messages)
        self.mail_started()
        self.file_away(config, self.by_folder(messages), title, thread, where)

    def remember_review(self, task: Task, title: str,
                        messages: list[Any]) -> None:
        """Record a review so the undo key can move the mail back.

        Its own entry rather than one made by `submit_write`: there is no
        task to put fields back on, and reversing this is a move on the
        server.
        """
        config = self.gateway_config

        def reverse(_wrote: dict[str, Task]) -> bool:
            if config is None:
                return False
            self.mail_started()
            self.put_back(config, self.by_folder(messages), title)
            return True

        entry = Undoable(
            group=str(uuid.uuid4()),
            label="Reviewing",
            subject=title,
            # What the board can honestly promise: the folder is a mirror,
            # so the row returns when whatever fills it next catches up.
            note="the row returns when the mailbox next catches up",
            undo_action=reverse,
        )
        entry.tasks[task.id] = task
        self._undo.append(entry)

    @work(thread=True, group="mail-write")
    def file_away(self, config: Any, by_folder: dict[str, list[str]],
                  title: str, thread: Any, where: int) -> None:
        """Move a reviewed row's messages to the archive, and confirm it.

        Off the UI thread: the move is one round trip, but confirming is a
        search a message, about a second each, and the board must stay under
        a person's hands throughout.
        """
        started = monotonic()
        count = sum(len(idents) for idents in by_folder.values())
        where_from = ", ".join(sorted(by_folder))
        journal.ok(f"review of {count} message(s) from {where_from}: starting")
        try:
            with self._mail_gate:
                if self._leaving:
                    # Given up: the board is going.  What was moved is in
                    # the archive either way and the next run finds it.
                    journal.warn(
                        f"review of {count} message(s) from {where_from}: "
                        f"given up, the board is closing")
                    return
                outcome = gateway.archive(config, by_folder,
                                          connect=self.gateway_connect,
                                          stop=lambda: self._leaving)
        except (gateway.MoveFailed, gateway.GatewayUnreachable) as exc:
            # The row comes back.  A row retired on an unconfirmed move is a
            # message a person believes they have dealt with.
            journal.error(f"review of {count} message(s) from {where_from} "
                          f"after {monotonic() - started:.1f}s: {exc}")
            self.call_from_thread(self.review_failed, title, thread, where,
                                  str(exc))
            return
        finally:
            self.call_from_thread(self.mail_settled)
        journal.ok(
            f"review of {count} message(s) from {where_from} confirmed in "
            f"{monotonic() - started:.1f}s: {len(outcome.archived)} archived, "
            f"{len(outcome.already)} already there, "
            f"{len(outcome.missing)} in neither")
        for ident in outcome.missing:
            journal.warn(f"{ident} is in neither {where_from} nor the archive")
        self.call_from_thread(self.review_done, title, outcome)

    def forget_reviewed(self, idents: "set[str]") -> None:
        """Stop holding these back from the queue.  UI thread only."""
        self.reviewed -= idents

    def mail_started(self) -> None:
        """One more operation on the account is in flight.  UI thread only."""
        self.mail_busy += 1
        self.update_daybar()
        self.turn_indicator()

    def mail_broke(self) -> None:
        """Remember that something went wrong.  UI thread only.

        Not cleared by a later operation succeeding: a failure among ten
        reviews would otherwise be painted over before it was seen.
        """
        self.mail_broken = True
        self.update_daybar()

    def mail_settled(self) -> None:
        """One fewer, however it ended.  UI thread only.

        Called from a `finally`, so that the six ways an operation can end
        -- confirmed, unconfirmed, already archived, in neither place,
        unreachable, and given up because the board is closing -- all reach
        it by one route rather than six that could each be forgotten.
        """
        self.mail_busy = max(0, self.mail_busy - 1)
        self.update_daybar()
        self.turn_indicator()

    def _handle_exception(self, error: Exception) -> None:
        """Write a failure down before the session goes.

        Deliberately overriding the framework's own name -- the one place
        every unhandled exception arrives, worker failures included, and the
        only one that sees a failure raised on a worker thread.  A
        `sys.excepthook` never fires for those, and wrapping `run()` never
        sees them either: the framework handles them itself and re-raises
        only under a test pilot.

        The session still ends, by the same route it ended by before.  A
        failure nothing anticipated is evidence of a defect, not a state to
        keep working in, and a board that carried on after one could not be
        trusted afterwards about what it had done to the account.

        Which file, and what may be said about the failure in the log
        beside it, is `journal`'s business: it owns both files and the rule
        about what each may hold.
        """
        journal.crash(error)
        super()._handle_exception(error)

    def on_unmount(self) -> None:
        """Tell whatever is still confirming a review to stop waiting.

        A row's confirmation is a search of the archive a message, and the
        archive is slow: a person quitting mid-review would otherwise wait
        on it, with the board gone and nothing said.  What was moved is in
        the archive either way, and the next run finds it there.
        """
        self._leaving = True

    def review_done(self, title: str, outcome: Any) -> None:
        """Say what became of a reviewed row's messages."""
        parts = []
        if outcome.archived:
            parts.append(f"{len(outcome.archived)} filed away")
        if outcome.already:
            parts.append(f"{len(outcome.already)} already reviewed")
        if outcome.missing:
            # Not a failure of the move and not a success: something else
            # moved that message, and saying which is more use than either.
            parts.append(
                f"{len(outcome.missing)} in neither the folder nor the archive")
        # Both count as in the archive, and both must stay out of the queue
        # until the mirror agrees: one was just moved, the other was already
        # there when we looked.
        self.reviewed |= set(outcome.archived) | set(outcome.already)
        said = " · ".join(parts) or "nothing to file away"
        if outcome.missing:
            # Not the move failing, but not nothing either: something else
            # moved that message, and the mark should say so.
            self.mail_broke()
        else:
            self.update_daybar()
        self.notice(f"Reviewed “{title}” · {said}", bool(outcome.missing))

    def review_failed(self, title: str, thread: Any, where: int,
                      why: str) -> None:
        """Put a row back, and say why it is back."""
        self.restore_thread(thread, where)
        self.mail_broke()
        self.notice(f"“{title}” is back in the queue · {why}", True)

    @work(thread=True, group="mail-write")
    def put_back(self, config: Any, by_folder: dict[str, list[str]],
                 title: str) -> None:
        """Move a reviewed row's messages out of the archive again."""
        # Forgotten first, so the row is free to come back the moment the
        # mailbox shows it again.  Before the move rather than after: a
        # restore that half succeeded must not leave the board hiding mail
        # that is back in the folder.
        self.call_from_thread(self.forget_reviewed,
                              {i for idents in by_folder.values() for i in idents})
        started = monotonic()
        count = sum(len(idents) for idents in by_folder.values())
        where_to = ", ".join(sorted(by_folder))
        journal.ok(f"undo of {count} message(s) to {where_to}: starting")
        try:
            with self._mail_gate:
                outcome = gateway.restore(config, by_folder,
                                          connect=self.gateway_connect)
        except (gateway.MoveFailed, gateway.GatewayUnreachable) as exc:
            journal.error(f"undo of {count} message(s) to {where_to} after "
                          f"{monotonic() - started:.1f}s: {exc}")
            self.call_from_thread(self.mail_broke)
            self.call_from_thread(
                self.notice,
                f"“{title}” could not be put back in the mailbox: {exc}", True)
            return
        finally:
            self.call_from_thread(self.mail_settled)
        journal.ok(f"undo of {count} message(s) to {where_to} done in "
                   f"{monotonic() - started:.1f}s: {len(outcome.archived)} "
                   f"moved back, {len(outcome.missing)} not in the archive")
        if outcome.missing:
            self.call_from_thread(self.mail_broke)
            self.call_from_thread(
                self.notice,
                f"“{title}”: {len(outcome.missing)} were not in the archive "
                f"to put back", True)

    # -- writes ------------------------------------------------------------

    def openable(self, task: Task) -> list[tuple[str, str]]:
        """Everything the task offers to open, as (what to show, address).

        Read from the title and then the note, each scanned for issues the
        tracker knows and for addresses.  Reading order rather than an order
        by kind: it needs no rule to be predictable, and the answer does not
        depend on which kind happens to be looked for first.

        A note is read for exactly what a title is read for.  A rule that
        found an issue key in a note but not an address, or the reverse,
        could not be remembered.

        Two candidates resolving to the same address collapse to one, so an
        issue mentioned both by key and by its own link is offered once
        rather than twice under different names.
        """
        found = (
            self.mail_openable(task) if self.is_mail(task)
            else self.candidates(
                (task.raw.get("title") or "", task.note_text))
        )
        seen, unique = set(), []
        for shown, url in found:
            if url in seen:
                continue
            seen.add(url)
            unique.append((shown, url))
        return unique

    def candidates(self, texts: Iterable[str]) -> list[tuple[str, str]]:
        """What these texts offer to open, in the order they are read in.

        Issues the tracker knows first, then addresses, per text -- reading
        order rather than an order by kind, so the answer does not depend on
        which kind happens to be looked for first.
        """
        config = self.tracker_config
        found: list[tuple[str, str]] = []
        for text in texts:
            if config is not None:
                for key in config.keys_in(text):
                    found.append((key, config.issue_url(key)))
            for url in singularity.urls_in(text):
                found.append((url, url))
        return found

    def mail_openable(self, task: Task) -> list[tuple[str, str]]:
        """What a mail row offers to open.  Two rules, each where its
        evidence lies.

        An address carrying a fragment names a place *within* a page, which
        is where a discussion should be entered so that it reads downward: a
        person opening thirty comments wants to begin where they left off,
        not land at the newest remark and scroll up.  So where the row's
        messages carry such addresses, the earliest of them is what is
        offered -- earliest and latest differ in 75 of 121 folded rows, so
        this is not a distinction without a difference.  The issues the
        row's text names are offered beside it, as they are for a task.

        Where no message carries one, the candidates come from the newest
        message alone, exactly as they did before this: a run of
        notifications about one thing holds one near-identical address per
        message -- four builds of a job give four console addresses
        differing in a number -- and offering every one would ask a person
        to choose between things they cannot tell apart.  The folder that
        reasoning was formed on carries no fragments at all, so it keeps
        precisely the behaviour it has.

        This is why the change reads as a reversal and is not one.
        """
        messages = list(task.raw.get(MAIL_MESSAGES) or ())
        anchored = next(
            (url for message in messages
             for url in singularity.urls_in(message.text) if "#" in url),
            None,
        )
        if anchored is None:
            return self.candidates((task.raw.get(MAIL_TEXT) or "",))
        # The issues the whole row names, then the one address.  Not the
        # row's other addresses: they are the near-identical run the
        # fall-through exists to collapse, and the anchored one is the
        # answer to where this row should be opened.
        config = self.tracker_config
        whole = "\n".join(message.text for message in messages)
        found: list[tuple[str, str]] = []
        if config is not None:
            for key in config.keys_in(whole):
                found.append((key, config.issue_url(key)))
        found.append((anchored, anchored))
        return found

    def recheck_elapsed(self) -> None:
        """Redraw when an event has fallen behind the present, and not otherwise.

        A timer that redrew on every tick would move the list under a
        person's hands fifty-nine times out of sixty for nothing, so this
        compares how many shown events are over against how many were and
        leaves the board alone when that is the same.

        Nothing is fetched to decide it: the ends are already on the rows.
        """
        now_ended = self.ended_count()
        if now_ended == self._ended_shown:
            return
        self._ended_shown = now_ended
        self.repaint()

    def apply_window(self, moment: datetime | None = None) -> None:
        """Set the mode from the working window, and redraw only if it moved.

        The comparison against what the window last said is the whole rule.
        The same answer changes nothing -- for `recheck_elapsed`'s reason,
        which holds here fifty-nine ticks out of sixty as well.  A different
        answer is a crossing: the overrule goes, the clock's answer stands,
        and the rows move once.

        That is also why a press lapses invisibly.  A press sets the mode to
        the opposite of what is in force, and with no earlier press what is
        in force is the window's own answer -- so the press disagrees with
        the window, and when the window later comes round to saying the same
        thing, dropping the overrule changes nothing on screen.  Press twice
        and you agree with the window again; the overrule is then worth
        nothing and the crossing moves rows as it would have anyway.

        The moment is an argument so that a suite can ask about a Friday at
        18:01 without waiting for one.
        """
        if self.working_window is None or self.work_project is None:
            # Nothing to act on: a clock cannot know which rows are work,
            # and a window that hid nothing while saying it had would be the
            # quietly-shorter view the reporting rule exists to prevent.
            return
        moment = moment or datetime.now(self.tz)
        reason = self.working_window.outside(moment)
        if reason == self._window_reason:
            return
        hides = reason is not None
        crossed = hides != self._window_hides
        self._window_reason = reason
        self._window_hides = hides
        if crossed:
            self._work_override = None
            self.hiding_work = hides
        # Redrawn for a changed reason as well as a crossing, which happens
        # once a week -- at the midnight where "after 18:00" becomes "outside
        # the working week".  Without it the board would go on giving
        # Friday's reason all weekend.
        self.repaint()

    def each_minute(self) -> None:
        """The one slow tick: what has ended, and where the clock now is.

        Two facts on one timer rather than a timer each.  Neither redraws
        unless its own fact changed, so the pair costs what reading a clock
        twice a minute costs.

        The window is polled rather than a crossing being scheduled: a
        machine shut at five and opened at seven must come back with the
        work hidden, and a one-shot set for a wall-clock instant does not
        reliably survive a suspend.  Reading the clock on the next tick
        after waking is right by construction, at the price of a crossing
        landing up to a minute late.
        """
        self.recheck_elapsed()
        self.apply_window()

    def refuse_foreign(self, task: Task | None) -> bool:
        """Say a row is not the board's to change, and report having said so.

        Every write passes through this on its way to the funnel, so it
        covers every action the board offers and every one added later.  It
        is also called by the actions that gather something first -- a date,
        a name, a confirmation -- because asking for input and refusing
        afterwards offers a choice that was never on the table.  Both callers
        share it so the two refusals cannot come to be worded differently.
        """
        if self.is_mail(task):
            # The same one place again: the board does not own the message,
            # so a change to it shown here would be a change that happened
            # nowhere.  Two keys do not come through here: reviewing and
            # promoting, which do not change the row but file the message
            # away on the server, each by its own path.
            self.notice(
                f"{_mail_who(task.raw.get(MAIL_SENDER) or '') or 'That message'} "
                f"lives in the mailbox · not editable here",
                True,
            )
            return True
        if self.is_event(task):
            # The board can read the calendar and nothing more, so a change
            # it showed would be a change that never happened anywhere.
            self.notice(
                f"{task.raw.get(EVENT_ACCOUNT) or 'The event'} "
                f"lives in the calendar · not editable here",
                True,
            )
            return True
        if self.is_tracker(task):
            # Likewise: showing a change the tracker never made would be
            # worse than refusing.
            self.notice(
                f"{task.raw.get(TRACKER_PROJECT) or 'The issue'} "
                f"lives in the tracker · not editable here",
                True,
            )
            return True
        return False

    def submit_write(
        self,
        label: str,
        task: Task,
        run: Callable[[str], Any],
        patch: dict[str, Any] | None = None,
        removes: bool = False,
        creates: bool = False,
        select: str | None = None,
        group: str | None = None,
        subject: str | None = None,
        undo_reason: str | None = None,
        undo_note: str = "",
        undo_action: "Callable[[dict[str, Task]], bool] | None" = None,
        record: bool = True,
    ) -> None:
        """Show a write's outcome at once, then queue it for the API.

        Nothing waits on the network: the patch goes on, the board repaints,
        and the request follows behind.  Not named `run_action`: that is
        Textual's own binding dispatcher, and shadowing it silently breaks
        every key in the app.
        """
        if self.refuse_foreign(task):
            return
        patch = patch or {}
        # Acting again supersedes whatever was last said, so it stops
        # being shown.
        self._notice = None
        group = group or str(uuid.uuid4())
        if record:
            self.remember(
                group, label, subject or task.title, task, patch,
                undo_reason, undo_note, undo_action,
            )
        pending = Pending(
            task_id=task.id,
            label=label,
            run=run,
            patch=patch,
            previous={key: task.raw.get(key) for key in patch},
            removes=removes,
            creates=creates,
            group=group,
        )
        self._pending.setdefault(task.id, deque()).append(pending)
        if select is not None:
            self._selected_id = select
        self.repaint()
        if task.id not in self._draining:
            self._draining.add(task.id)
            self.drain(task.id)

    def next_open_after(self, task: Task) -> str | None:
        """The unfinished task to move to once `task` is ticked off.

        The one after it in the order now on screen, or the one before it
        when it was last.  Chosen by identity from the list the person can
        see, so the selection lands where they were looking rather than on
        whatever the reordering brings into a row.
        """
        try:
            here = next(
                i for i, t in enumerate(self.tasks) if t.id == task.id
            )
        except StopIteration:
            return None
        rest = self.tasks[here + 1:]
        earlier = list(reversed(self.tasks[:here]))
        for candidate in (*rest, *earlier):
            if not candidate.done and not candidate.cancelled:
                return candidate.id
        return None

    def remember(
        self,
        group: str,
        label: str,
        subject: str,
        task: Task,
        patch: dict[str, Any],
        reason: str | None,
        note: str,
        undo_action: "Callable[[dict[str, Task]], bool] | None" = None,
    ) -> None:
        """Note what a write is about to replace, so it can be put back.

        Writes sharing a group join one entry rather than making their own,
        which is what keeps a move that respaced its whole run to a single
        press of the undo key.
        """
        for entry in reversed(self._undo):
            if entry.group == group:
                break
        else:
            entry = Undoable(group=group, label=label, subject=subject,
                             reason=reason or "", note=note,
                             undo_action=undo_action)
            self._undo.append(entry)
        if undo_action is not None:
            # The reversal knows what to do with the task; there are no
            # previous values, because there was no task before this.
            entry.tasks[task.id] = task
            return
        if reason:
            # Nothing to put back; the entry exists only to say so.
            return
        entry.previous.setdefault(task.id, {}).update(
            {key: task.raw.get(key) for key in patch}
        )
        entry.tasks[task.id] = task

    def _group_in_flight(self, group: str) -> int:
        """How many of one action's writes are still queued.  UI thread only.

        Counted from the queues that hold them rather than kept as a number
        of its own.  The board already derives its in-flight total this way
        for the status line, and the one count it does keep carries a warning
        worth heeding here: every path an operation can end on has to bring
        it down, there are six of them, and one missed lasts the session.  A
        number read off the queues has no path to miss.

        Writes abandoned behind a refusal do not count, the refusal having
        taken them out of the queue: they can never settle, so waiting for
        them would wait forever.
        """
        return sum(1 for queue in self._pending.values()
                   for pending in queue if pending.group == group)

    def forget(self, group: str) -> None:
        """Drop an entry whose action left nothing behind.  UI thread only.

        A refused write is not something to undo, because it never
        happened.  But an action can take several writes -- a move that
        respaces its run takes one per task -- and one of them failing does
        not unhappen the others: this API refuses a write now and then and
        succeeds on a retry, so a single refusal among five would otherwise
        throw away the ability to undo the four that landed.  The entry goes
        only when nothing of it was applied.

        Which is a question that cannot be answered while any of the action's
        writes is still in flight, and answering it anyway is what this used
        to do.  Called at the first refusal, with three writes still out, it
        read `applied` as nothing and dropped the entry -- and the three then
        landed and counted themselves against a list that no longer held it.
        Three writes succeeded, the board went on showing them, and the undo
        key could not reach them.  Which of the answers came back first was
        the whole of the difference.

        So the decision waits.  Where the action still has writes outstanding
        this does nothing at all; the last of them to settle comes back here
        and decides on a complete answer.  No note of the refusal is kept
        because none is needed: the rule is to keep the entry if anything
        landed, and that does not mention refusals.

        Nor does the confirmed-write path call this, though it looks as
        though it should have to.  A write that has just applied something
        cannot cause a drop: the call would return early while writes remain
        and keep the entry once they do not -- a no-op reading as though it
        were load-bearing.  Every case works out on the refusals alone,
        whichever of them settles last asking the question once the answer
        is complete.
        """
        if self._group_in_flight(group):
            return
        self._undo = [
            e for e in self._undo if e.group != group or e.applied
        ]

    def _next_write(self, task_id: str) -> "Pending | None":
        """Hand a drain its next write, or release it.  UI thread only.

        Emptiness is decided here, on the thread that also enqueues, so a
        keypress arriving exactly as a queue runs dry cannot find both no
        drain running and no drain about to start.
        """
        queue = self._pending.get(task_id)
        if queue:
            return queue[0]
        self._pending.pop(task_id, None)
        self._draining.discard(task_id)
        return None

    @work(exclusive=False, thread=True)
    def drain(self, task_id: str) -> None:
        """Send one task's queued writes, in order, until it runs dry.

        The key can change under this loop exactly once: when the first
        write was a creation, confirming it trades the placeholder id for
        the real one, and everything queued behind it goes to that.
        """
        key = task_id
        while True:
            pending = self.call_from_thread(self._next_write, key)
            if pending is None:
                return
            try:
                result = pending.run(key)
            except SingularityError as exc:
                self.call_from_thread(self._write_failed, key, pending, str(exc))
                return
            key = self.call_from_thread(self._write_done, key, pending, result)

    def _write_done(self, key: str, pending: Pending, result: Any) -> str:
        """Fold a confirmed write into the base and drop its patch.

        Committing the patch rather than refetching is what keeps a
        successful write from costing a round trip: the board already
        showed this outcome, and the server has now agreed to it.

        Returns the key the task's remaining writes should use.
        """
        queue = self._pending.get(key)
        if queue and queue[0] is pending:
            queue.popleft()
        for entry in self._undo:
            if entry.group == pending.group:
                entry.applied += 1
                break
        if pending.creates:
            return self._adopt_created(key, result)
        if pending.removes:
            self._base = [t for t in self._base if t.id != key]
        else:
            for task in self._base:
                if task.id == key:
                    task.raw.update(pending.patch)
        self.repaint()
        return key

    def _adopt_created(self, key: str, result: Any) -> str:
        """Trade a placeholder id for the real one the server assigned.

        The queue, the drain and the selection are all filed under the
        placeholder, so each moves across together -- otherwise a write
        queued behind the creation would be sent to an id that never
        existed.
        """
        if not isinstance(result, Task):
            self.repaint()
            return key
        new = result.id
        self._base = [result if t.id == key else t for t in self._base]
        queue = self._pending.pop(key, None)
        if queue:
            self._pending[new] = queue
            for pending in queue:
                pending.task_id = new
        self._draining.discard(key)
        self._draining.add(new)
        if self._selected_id == key:
            self._selected_id = new
        # An undo entry filed under the placeholder would reach an id that
        # never existed.  Only an action carrying its own reversal can be
        # undone after creating anything, so this had nothing to correct
        # until one existed.
        for entry in self._undo:
            if key in entry.tasks:
                entry.tasks[new] = result
                del entry.tasks[key]
            if key in entry.previous:
                entry.previous[new] = entry.previous.pop(key)
        self.repaint()
        return new

    def _write_failed(self, key: str, pending: Pending, message: str) -> None:
        """Take back a refused write and say so.

        Whatever was queued behind it for the same task goes too: those
        writes were chosen against a state that never came about, so
        sending them would apply them to something else.  Other tasks'
        writes are untouched.
        """
        queue = self._pending.pop(key, None)
        self._draining.discard(key)
        abandoned = max(len(queue) - 1, 0) if queue else 0
        self.forget(pending.group)
        if pending.creates:
            # The task never came into being, so its row goes with it.
            self._base = [t for t in self._base if t.id != key]
        also = f" · {abandoned} more dropped" if abandoned else ""
        self._notice = (f"{pending.label} failed: {message}{also}", True)
        self.repaint()

    # -- rendering ---------------------------------------------------------

    def show_tasks(self, listing: singularity.Listing) -> None:
        """Adopt a fetched view as the base, keeping pending writes on top.

        The fetch replaces what the server told us and nothing else, so a
        refresh landing while a write is still in flight cannot put the
        server's older copy of that task back on screen.
        """
        # A task created here and not yet confirmed stays on screen: this
        # board's own pending write is what will make the server aware of
        # it, so a fetch that predates it is not evidence it is gone.
        unborn = [
            t for t in self._base
            if any(p.creates for p in self._pending.get(t.id, ()))
        ]
        known = {t.id for t in listing.tasks}
        self._base = listing.tasks + [t for t in unborn if t.id not in known]
        self.filed_out = listing.filed_out
        self._fetched = True
        # A fresh view supersedes whatever was said about the old one --
        # except what an outside source is standing on.  The calendar
        # answers in a couple of milliseconds and so nearly always reports
        # before the day's own fetch returns; wiping its message here would
        # mean an unreadable calendar was never once seen.  Each source
        # takes its own message down when it recovers.
        standing = {m for m in (self.calendar_error, self.tracker_error,
                                self.mail_error, self.window_error) if m}
        if not (self._notice and self._notice[0] in standing):
            self._notice = None
        self.reference = listing.reference
        self.repaint()

    def hold_view(self, table, was_at: int, index: int) -> None:
        """Put the view back where it was, and move it only to find a row.

        The list moves when a person moves it and at no other time.  A
        redraw happens for reasons that are nothing to do with them -- a
        write confirming, mail arriving, the calendar or the tracker
        answering -- and a view that scrolled on each of those would move
        under the hand that was working it.

        Two things it must still do.  A list that has become shorter than
        the position it was scrolled to shows its end rather than an empty
        area past it, which `scroll_to` handles by clamping.  And a selected
        row that the restored view does not show is brought into view --
        which is what ticking a task creates, completion being the first
        ordering key, so the ticked task moves away among the finished ones.

        It is centred when that happens, not merely revealed: revealing by
        the shortest distance is exactly what put a row on the last line
        with nothing after it.
        """
        table.scroll_to(y=was_at, animate=False)
        # Read back rather than assumed: a shorter list clamps this, and
        # what decides whether the row is visible is where the view
        # actually ended up.
        top = int(table.scroll_y)
        height = table.size.height
        if not height or top <= index < top + height:
            return
        table.scroll_to(y=max(0, index - height // 2), animate=False)

    def patched(self) -> list[Task]:
        """The fetched tasks with every pending write applied on top.

        Rows come only from what the last fetch reported, so a pending
        write is never itself a reason for a row to exist -- an orphan
        patch, for a task the fetch no longer knows about, shows nothing.
        """
        out: list[Task] = []
        for task in self._base:
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

    def next_order(self) -> int:
        """A stored order past every task in the shown day."""
        if not self.tasks:
            return singularity.ORDER_STEP
        return (
            max(t.schedule_order for t in self.tasks) + singularity.ORDER_STEP
        )

    def group_of(self, task: Task) -> tuple:
        """The task's ordering group in the shown view.

        Tasks sharing it are the ones a hand-set sequence can arrange; a
        move may not carry a task past one that differs here.
        """
        return singularity.group_key(task, self.tz, self.reference, self.green_tag)

    def neighbour_to_pass(self, task: Task, step: int) -> "Task | None":
        """The task a move would carry the selected one past, if any.

        `step` is -1 to move up and 1 to move down.  Answers None at the
        edge of the group, whether because the view ends there or because
        the adjacent task is ordered by a key above the manual one and so
        cannot be traded with.
        """
        try:
            here = next(i for i, t in enumerate(self.tasks) if t.id == task.id)
        except StopIteration:
            return None
        there = here + step
        if not 0 <= there < len(self.tasks):
            return None
        other = self.tasks[there]
        if self.is_event(other):
            # An event is placed by the clock, not by any order a person
            # sets, so there is no sequence to trade places in.  It ends the
            # run rather than being stepped over: a task landing on the far
            # side of it would be claiming a position the next repaint would
            # take straight back.
            return None
        if self.group_of(other) != self.group_of(task):
            return None
        return other

    def order_for_move(self, task: Task, step: int) -> "int | None":
        """The stored order that puts `task` on the far side of its neighbour.

        The moved task lands between the neighbour it passes and whatever
        lies beyond that neighbour in its own group -- so only this one task
        is written, and a move can never be half applied.

        Answers None when there is no room, which is the caller's signal to
        make some by respacing the run first.
        """
        other = self.neighbour_to_pass(task, step)
        if other is None:
            return None
        beyond = self.neighbour_to_pass(other, step)
        near = other.schedule_order
        far = beyond.schedule_order if beyond is not None else None
        # Moving down, the task ends above `near`; moving up, below it.
        if step > 0:
            return singularity.order_between(near, far)
        return singularity.order_between(far, near)

    def run_around(self, task: Task) -> list[Task]:
        """The task's whole ordering group, in the sequence now shown.

        The board's own rows alone.  A calendar event or a tracker issue can
        land in the same group by the keys that decide one, but neither has
        an order to set, and respacing a run that included them would ask
        for writes that must be refused and leave the run half spaced.
        """
        mine = self.group_of(task)
        return [
            t for t in self.tasks
            if not (self.is_event(t) or self.is_tracker(t))
            and self.group_of(t) == mine
        ]

    @property
    def shows_tracker(self) -> bool:
        """Whether the shown view is the one the tracker block belongs to.

        Today alone.  An issue in progress is what is being worked on now
        rather than something scheduled, so repeating it under every date
        would say it was scheduled for each of them.
        """
        return (
            isinstance(self.position, date)
            and self.position == datetime.now(self.tz).date()
        )

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

    @staticmethod
    def is_tracker(task: Task | None) -> bool:
        """Whether a row came from the tracker rather than the board."""
        return bool(task is not None and task.raw.get(TRACKER_MARK))

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

    def repaint(self) -> None:
        """Rebuild the table from the fetched tasks and the pending writes.

        Everything derived is recomputed rather than adjusted -- the
        ordering, what is past due, the counts -- and by the same functions
        the fetched path uses, so an optimistic view and a fetched one
        cannot come to disagree.
        """
        table = next(iter(self.query(DataTable)), None)
        if table is None:
            # Confirming a write can land as the app is shutting down, by
            # which time there is nothing left to paint.
            return
        # The title column was declared before the table had a size, so the
        # first paint is where it learns how wide it really is.
        self.fit_columns()
        previous = table.cursor_row
        # Where the view was, because rebuilding the table loses it:
        # `DataTable.clear()` sets its scroll position to zero, and
        # `move_cursor` then scrolls the minimum distance that reveals the
        # cursor's row -- which, from the top, puts that row on the last
        # visible line.  Measured on a 600-row inbox: ticking a row on line
        # 7 of 20 scrolled the view thirteen rows and left the cursor on
        # line 20, with nothing below it.
        was_at = int(table.scroll_y)
        keep = self._selected_id
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
        self.shown_issues = len(issues)
        events = self.event_rows()
        # Every source is built before the filter and filtered with the
        # day's tasks, because a source appended afterwards is a source the
        # key cannot reach however its rows are marked.  That was written
        # here for the tracker's rows -- the most work-like on screen -- and
        # then mail was appended afterwards anyway and went unhidden for
        # three changes.  So: build them all here, filter them all here, and
        # let the placing below arrange what survives.
        mails = self.mail_rows()
        self.hidden_work = (
            sum(1 for t in tasks + issues + events + mails if self.is_work(t))
            if self.hiding_work else 0
        )
        if self.hiding_work:
            tasks = [t for t in tasks if not self.is_work(t)]
            issues = [t for t in issues if not self.is_work(t)]
            events = [t for t in events if not self.is_work(t)]
            mails = [t for t in mails if not self.is_work(t)]
            self.shown_issues = len(issues)
        # The events take their place among the day's tasks by when they
        # happen; the tracker's block goes in whole, where the day's
        # unfinished work ends.
        self.shown_events = len(events)
        tasks = self.place_issues(self.place_events(tasks, events), issues)
        # Counted after the filter, as the issues are: both numbers say what
        # is on screen, which is what the inbox undertakes to report -- how
        # many rows of mail it is showing.  Filtering the rows carries the
        # message count with them, the sum being taken over what is left.
        self.shown_mail = len(mails)
        self.shown_messages = sum(t.raw.get(MAIL_COUNT, 1) for t in mails)
        # Mail follows the inbox's tasks.  It once led them, so that the
        # daily processing started at the top rather than after a scroll --
        # and that reasoning is why it now goes last: mail arrives in far
        # greater quantity than a person files tasks, some 460 rows against
        # 35, so leading with it guarantees the scroll it was meant to
        # avoid.  Appended, never sorted in, so the tasks keep exactly the
        # order they had alone -- and filtered before this, so hiding work
        # cannot disturb that order either.
        tasks = tasks + mails
        self.tasks = tasks
        self.past_due = (
            sum(
                1 for t in tasks
                if not self.is_event(t) and t.past_due_since(self.reference, self.tz)
            )
            if self.reference
            else 0
        )
        table.clear()
        for task in tasks:
            table.add_row(*self.row_for(task))
        if tasks:
            index = next(
                (i for i, t in enumerate(tasks) if t.id == keep), None
            )
            if index is None and self.position != self._drawn_for:
                # A different view.  It begins at its beginning: its rows
                # have nothing to do with the last one's, so neither the
                # row the cursor was on nor the position it was scrolled
                # to carries any meaning here.
                #
                # Both are said, though the reveal below would reach the
                # top on its own from row 0.  Saying it is the rule; the
                # reveal reaching the same place is arithmetic, and a
                # reader who removed this would be depending on it.
                index, was_at = 0, 0
            elif index is None:
                # The same view, and the task is gone.  Take the nearest
                # surviving position rather than whatever has moved into
                # the old row.
                index = min(max(previous, 0), len(tasks) - 1)
            # Not scrolling: the view is put back below instead, so that a
            # redraw a person did not ask for does not move the list they
            # are working down.
            table.move_cursor(row=index, scroll=False)
            self._selected_id = tasks[index].id
            self.hold_view(table, was_at, index)
        else:
            self._selected_id = None
        # Recorded after the rows are drawn, so the next redraw compares
        # against the view these rows belong to.
        self._drawn_for = self.position
        # Recorded after the rows are built, so the timer compares what is
        # on screen rather than what was on screen a fetch ago.
        self._ended_shown = self.ended_count()
        self.update_daybar()
        self.update_detail()
        own = [t for t in tasks
               if not (self.is_tracker(t) or self.is_event(t) or self.is_mail(t))]
        done = sum(1 for t in own if t.done)
        # The task count is what the board manages; issues are counted
        # beside it, never folded into it.
        bits = [f"{len(own)} task(s)", f"{done} done"]
        if self.shown_issues:
            # Not named for any one state: more than one may be shown, and
            # which state each issue is in is on its own row.
            bits.append(f"{self.shown_issues} tracked")
        if self.shown_mail:
            # Both queues, side by side: the size of each is visible without
            # counting rows, and neither is folded into the other.
            bits.append(f"{self.shown_mail} thread(s)")
            bits.append(f"{self.shown_messages} message(s)")
        if self.shown_events:
            # Counted beside the tasks rather than among them: the board
            # manages the tasks and only reports these.
            bits.append(f"{self.shown_events} event(s)")
        if self.past_due:
            bits.insert(1, f"{self.past_due} past due")
        green = sum(1 for t in own if self.is_green(t))
        if green:
            # Beside the other counts, as the tracker's and the work
            # filter's are: none of them replaces the number of rows.
            bits.append(f"{green} green")
        if self.hidden_work:
            # Beside the other counts, never instead of them: the shown
            # count stays the number of rows, as the inbox already does for
            # the tasks it withholds.
            why = self.window_reason()
            bits.append(f"{self.hidden_work} work hidden"
                        + (f" ({why})" if why else ""))
        in_flight = sum(len(q) for q in self._pending.values())
        if in_flight:
            bits.append(f"{in_flight} saving")
        # A notice outranks the counts until the person acts again or the
        # view is fetched afresh.
        if self._notice:
            self.set_status(*self._notice)
        elif not self._fetched:
            # The events can be on screen before the day's tasks are; saying
            # how many tasks there are before they have arrived would name a
            # number that is about to change.
            self.set_status("Loading…")
        else:
            self.set_status(" · ".join(bits))

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

    def fit_columns(self) -> bool:
        """Give the title column the room the terminal currently leaves.

        Returns whether the width changed, so a caller can skip redrawing
        when it did not.  Called after the first layout as well as on every
        resize: a column is declared before the table has a size, so its
        width would otherwise be stuck at the minimum forever.
        """
        table = next(iter(self.query(DataTable)), None)
        if table is None:
            return False
        column = table.columns.get("title")
        if column is None:
            return False
        wanted = self.title_width
        if column.width == wanted:
            return False
        column.width = wanted
        return True

    def on_resize(self) -> None:
        """Follow the terminal: refit the columns and redraw what they hold.

        The rows carry text already cut to a width, so a resize has to build
        them again -- widening a column without rebuilding would leave the
        old ellipsis in a row with room to spare.

        Deferred until the layout has settled: this arrives before the table
        has been given its new size, so fitting here would measure the width
        the table is about to stop having.
        """
        self.call_after_refresh(self._refit)

    def _refit(self) -> None:
        if self.fit_columns():
            self.repaint()

    @property
    def title_width(self) -> int:
        """How much room the title column has, from the terminal as it is now.

        The other columns cost a fixed amount, so the title takes what they
        leave rather than a share of the screen -- a share would have the
        fixed cost added to it and overflow at every width.  Never below the
        minimum: past that the list scrolls, which it did anyway before.

        Read afresh each time rather than stored, so a resized terminal needs
        nothing kept in step.
        """
        # Measured from the app rather than from the table, because a resize
        # reaches the app first: asking the table during one returns the
        # width it is about to stop having, and the rows come out a size
        # behind.  The table fills the app's width -- there is nothing
        # beside it -- which a test pins so this cannot drift unnoticed.
        return max(_TITLE_MIN, self.size.width - _ROW_OVERHEAD)

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
                TRACKER_ROW_MARK,
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
            return (
                "",
                MAIL_ROW_MARK,
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
                EVENT_ROW_MARK,
                _event_label(task.raw.get(EVENT_MINUTES)),
                self.shortened(f"[dim]{name}[/dim]" if over else name, self.title_width),
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
            singularity.overdue_label(late, self.reference)
            if late
            else task.start_label(self.tz)
        )
        if task.done or task.cancelled:
            title = f"[strike dim]{title}[/]"
        elif late:
            title = f"[{self.late_colour}]{title}[/]"
        project = self.projects.get(task.project_id or "", "")
        return (
            mark,
            MARKS[task.checked],
            when,
            self.shortened(title, self.title_width),
            self.shortened(f"[dim]{project}[/dim]", _PROJECT_WIDTH) if project else "",
        )

    @property
    def late_colour(self) -> str:
        """The colour a past-due title is drawn in, resolved from the theme.

        Table cells are rendered with Rich markup, which does not understand
        Textual's `$name` variables, so the value has to be resolved here and
        embedded literally.

        `text-error` rather than `text-warning`: in the bundled themes
        `warning` and `text-warning` are the *same values* as `accent` and
        `text-accent`, and `accent` is the selected row's background, so a
        warning-coloured title would be indistinguishable from the cursor.
        The cursor style replaces a cell's colour outright on the selected
        row -- for every row, not just these -- so a past-due row that is
        selected is told apart by its age label instead.
        """
        return self.theme_variables.get("text-error", "#d17e92")

    @property
    def tz(self):
        return self.client.tz if self.client else singularity.local_tz()

    @property
    def selected(self) -> Task | None:
        # Queried tolerantly rather than with `query_one`: repainting moves
        # the cursor, and the message that causes can still be delivered
        # after the table has gone during shutdown.
        table = next(iter(self.query(DataTable)), None)
        if table is None or not self.tasks or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self.tasks):
            return None
        return self.tasks[table.cursor_row]

    # -- chrome ------------------------------------------------------------

    def mail_mark(self) -> str:
        """The one cell at the right of the day bar.

        Three things, in order of what a person needs to know: something is
        happening, something went wrong, or neither.  In flight wins over
        failed, because what is running now is what they are waiting on.
        """
        if self.mail_busy:
            return MAIL_BUSY_MARKS[self._spin % len(MAIL_BUSY_MARKS)]
        return MAIL_FAILED_MARK if self.mail_broken else MAIL_IDLE_MARK

    def turn_indicator(self) -> None:
        """Start the arc turning while there is work, and stop it after.

        A timer that ran always would move a mark in the corner of the eye
        for nothing, which is what the clock's requirement forbids of
        anything that animates on this board.
        """
        if self.mail_busy and self._spinner is None:
            self._spinner = self.set_interval(MAIL_SPIN_SECONDS, self.spin)
        elif not self.mail_busy and self._spinner is not None:
            self._spinner.stop()
            self._spinner = None
            self._spin = 0

    def spin(self) -> None:
        """Advance the arc by one frame, and redraw nothing but the bar."""
        self._spin += 1
        self.update_daybar()

    def window_reason(self) -> str | None:
        """Why the window is hiding the work, or None if it is not doing it.

        A press outranks it: having pressed the key, a person knows what
        hid the rows, and naming a boundary they overruled would be a
        reason that is not the reason.
        """
        if self._work_override is not None or not self.hiding_work:
            return None
        return self._window_reason

    def work_note(self) -> list[str]:
        """What the daybar says about the work filter, if anything.

        Said even when it hides nothing: a view that is quietly shorter is
        otherwise indistinguishable from a day with less on it, and a mode
        that hides nothing is indistinguishable from a key that does not
        work.
        """
        if not self.hiding_work:
            return []
        why = self.window_reason()
        count = f" ({self.hidden_work})" if self.hidden_work else ""
        return [f"work hidden{count}" + (f", {why}" if why else "")]

    def update_daybar(self) -> None:
        bar = self.query_one("#daybar", Static)
        if isinstance(self.position, Bucket):
            parts = [self.position.label, "no date"]
            if self.filed_out:
                parts.append(f"{len(self.tasks)} shown")
                parts.append(f"{self.filed_out} filed, hidden")
            parts += self.work_note()
            bar.update(self.with_mark("  ·  ".join(parts), bar))
            return
        today = datetime.now(self.tz).date()
        delta = (self.position - today).days
        relative = {0: "today", 1: "tomorrow", -1: "yesterday"}.get(
            delta, f"{abs(delta)} days {'ahead' if delta > 0 else 'ago'}"
        )
        parts = [f"{self.position:%A %d %B %Y}", relative, *self.work_note()]
        bar.update(self.with_mark("  ·  ".join(parts), bar))

    def with_mark(self, said: str, bar: Static) -> str:
        """The bar's text with the mailbox mark pushed to its right edge.

        Shown in every view: mailbox work outstands whichever view is being
        looked at, and whether it is safe to leave is the same question in
        all of them.

        Padded rather than laid out, because the bar is one `Static` and the
        board already owns it -- a second widget would be a layout change
        for one cell.  Where the terminal is too narrow for both, the text
        wins and the mark is dropped: a truncated day bar reads as a fault,
        where a missing mark reads as nothing at all.
        """
        mark = self.mail_mark()
        room = bar.content_size.width or bar.size.width
        if not room or len(said) + 2 > room:
            return said
        return said + " " * (room - len(said) - len(mark)) + mark

    def update_detail(self) -> None:
        task = self.selected
        detail = self.query_one("#detail", Static)
        if task is None:
            detail.update("")
            self.rewound("")
            return
        bits = []
        if task.recurring:
            bits.append("recurring")
        if task.pinned:
            bits.append("pinned")
        deadline = task.deadline
        if deadline:
            bits.append(f"deadline: {deadline.astimezone(self.tz):%d %b %H:%M}")
        # A task can now have no flags at all, so drop the empty halves
        # rather than joining them into a stray blank line.
        # This area renders its text as markup, so everything drawn in it is
        # escaped: a calendar description because somebody else wrote it, and
        # a task's own note because a person who has just typed square
        # brackets and watched them vanish has been told the board destroyed
        # their work -- while the store holds it perfectly, which leaves them
        # nothing to find when they go looking.
        note = escape(task.note_text)
        sections = [part for part in ("  ·  ".join(bits), note) if part]
        detail.update("\n".join(sections))
        self.rewound(task.id)

    def rewound(self, task_id: str) -> None:
        """Show the top of this row's note if it is not the row we were on.

        A note carried over at the offset the last one was read to would open
        part way through, at a place that means nothing.
        """
        if task_id == self._detail_for:
            return
        self._detail_for = task_id
        pane = next(iter(self.query("#notes")), None)
        if pane is not None:
            pane.scroll_to(y=0, animate=False)

    def notice(self, message: str, error: bool = False) -> None:
        """Say something that survives the next repaint.

        Repainting rewrites the status from the view's counts, so anything
        worth reading after the next write confirms has to be held rather
        than simply shown.
        """
        self._notice = (message, error)
        self.set_status(message, error)

    def set_status(self, message: str, error: bool = False) -> None:
        # Queried tolerantly: a worker can answer after the app has begun
        # shutting down, and the tracker's is a network call that routinely
        # outlives a short run.  The notice is still remembered either way,
        # so nothing is lost if there is no longer a bar to write it on.
        status = next(iter(self.query("#status")), None)
        if status is None:
            return
        status.set_class(error, "error")
        # Escaped here, once, rather than at each of the calls that reach
        # this: the board's messages quote a task's title, and a title
        # holding square brackets lost them on screen while remaining whole
        # in the store.  Nothing that arrives here is markup -- every caller
        # passes a sentence -- and the error colour is a CSS class rather
        # than markup, so escaping the message takes nothing away.
        status.update(escape(message))

    @on(DataTable.RowHighlighted)
    def row_changed(self, event: DataTable.RowHighlighted) -> None:
        """Follow the cursor: remember which task it is on, not which row.

        Moving the cursor is the only way the selection changes that does
        not go through `repaint`, so between them the remembered id is
        always the task the person can see is selected.
        """
        row = event.cursor_row
        if 0 <= row < len(self.tasks):
            self._selected_id = self.tasks[row].id
        if self.query("#detail"):
            self.update_detail()

    @on(DataTable.RowSelected)
    def row_selected(self) -> None:
        """Enter (or a click) on a row opens the focus card."""
        self.action_focus_task()

    # -- actions -----------------------------------------------------------

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_cursor_up()

    def _go(self, position: "date | Bucket") -> None:
        self.position = position
        # The withheld count belongs to the view being left, so clear it
        # before repainting; load() sets the new one.
        self.filed_out = 0
        # The new view's tasks have not arrived, whatever the old one's did.
        self._fetched = False
        self.update_daybar()
        self.load()

    def _shift_day(self, days: int) -> None:
        """Step to an adjacent day, but only from a day.

        From a bucket there is no adjacent day to step to -- any date it
        picked would be arbitrary -- so the movement does nothing and `t` is
        the way back to the calendar.
        """
        if not isinstance(self.position, date):
            self.set_status(f"{self.position.label} has no days · press t for today")
            return
        self._go(self.position + timedelta(days=days))

    def action_prev_day(self) -> None:
        self._shift_day(-1)

    def action_next_day(self) -> None:
        self._shift_day(1)

    def action_today(self) -> None:
        self._go(datetime.now(self.tz).date())

    def action_inbox(self) -> None:
        self._go(Bucket.INBOX)

    def action_someday(self) -> None:
        self._go(Bucket.SOMEDAY)


    def action_refresh(self) -> None:
        # Asking for a reload is the gesture that already means "start
        # again", so it is what takes the mailbox's failure mark down.  Not
        # a later success: a failure among ten reviews would otherwise be
        # painted over before it was seen.
        self.mail_broken = False
        self.projects = {}
        self.load()

    def action_toggle(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        if self.is_mail(task):
            # The same key, two different things: on a task it records work
            # finished, on a mail row it files the message away where the
            # board cannot show it again.  One key because a review is a
            # hundred keystrokes a day, and the wording carries the
            # distinction that a confirmation on each would carry worse.
            self.review(task)
            return
        want_done = not task.done
        label = "Ticking" if want_done else "Unticking"
        client = self.client
        # Ticking moves on to the next unfinished task, so a list can be
        # worked down with one key.  Unticking stays where it is: the task
        # has just come back, and that is what is being looked at.
        self.submit_write(
            label,
            task,
            lambda tid: client.set_done(task, want_done),
            {"checked": CHECKED if want_done else EMPTY},
            select=self.next_open_after(task) if want_done else None,
        )

    def action_done_for_today(self) -> None:
        """Record today's work on the selected task and move it to tomorrow.

        Distinct from ticking on purpose: this leaves the task open.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        client = self.client
        # Where it lands: tomorrow, all-day, and no longer set aside -- the
        # same schedule `done_for_today` applies once the record is in.
        tomorrow = datetime.now(self.tz).date() + timedelta(days=1)
        self.submit_write(
            "Done for today",
            task,
            lambda tid: client.done_for_today(task),
            {
                "start": singularity.iso_z(
                    datetime.combine(tomorrow, time.min, tzinfo=self.tz)
                ),
                "useTime": False,
                "deferred": False,
            },
            undo_note=(
                "the date came back, but the record of the day's work "
                "cannot be withdrawn"
            ),
        )

    def move_task(self, step: int, label: str) -> None:
        """Carry the selected task past its neighbour and store where it lands.

        Only the moved task is written.  Its new order sits between the
        neighbour it passes and whatever lies beyond that neighbour, so one
        write is the whole move and it cannot be left half applied.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        if self.is_event(task):
            self.notice(
                f"“{task.title}” lives in the calendar · it cannot be reordered here",
                True,
            )
            return
        if self.is_tracker(task):
            self.notice(
                f"“{task.title}” lives in the tracker · it cannot be reordered here",
                True,
            )
            return
        if not self.orders_manually:
            # A notice, not a plain status: a refusal has to survive the next
            # repaint, and repaints now also come from the tracker answering.
            self.notice(
                f"{self.position.label} is ordered by title · "
                "reordering applies to calendar days",
                True,
            )
            return
        if self.neighbour_to_pass(task, step) is None:
            self.notice(f"“{task.title}” cannot move {label} from here", True)
            return

        # One keypress is one undo, so any respacing this needs and the
        # move it serves share a group and become a single entry.
        group = str(uuid.uuid4())
        order = self.order_for_move(task, step)
        if order is None:
            # Nothing fits between the destination and the task beyond it.
            # Respace the run into values the day does not use, which is
            # safe to apply in pieces, then place the task in the room made.
            if not self.respace(task, group):
                return
            order = self.order_for_move(task, step)
            if order is None:
                self.set_status(f"“{task.title}” cannot move {label} from here", True)
                return

        client = self.client
        self.submit_write(
            f"Moving {label}",
            task,
            lambda tid: client.set_schedule_order(tid, order),
            {"scheduleOrder": order},
            group=group,
        )

    def respace(self, task: Task, group: str | None = None) -> bool:
        """Spread the task's ordering group out so a move has somewhere to go.

        The new values sit past everything the day uses, which is what lets
        a partly-applied respacing still leave every order distinct.  It is
        one write per task in the run, so it goes as its own pending write
        rather than through the single-task path.
        """
        run = self.run_around(task)
        if len(run) < 2:
            return False
        base = max(t.schedule_order for t in self.tasks) + singularity.ORDER_STEP
        client = self.client
        fresh = {t.id: base + i * singularity.ORDER_STEP for i, t in enumerate(run)}
        for item in run:
            self.submit_write(
                "Respacing",
                item,
                (lambda tid, value=fresh[item.id]:
                 client.set_schedule_order(tid, value)),
                {"scheduleOrder": fresh[item.id]},
                group=group,
                subject=task.title,
            )
        return True

    def action_move_up(self) -> None:
        self.move_task(-1, "up")

    def action_move_down(self) -> None:
        self.move_task(1, "down")

    def action_undo(self) -> None:
        """Reverse the most recent write, then the one before it.

        Needs no task selected and no particular view: it acts on what the
        board wrote, wherever that task is now, and names what it reversed
        -- a person pressing this key does not necessarily know what
        happened, and being told is most of what they came for.
        """
        if not self._undo:
            self.set_status("Nothing left to undo")
            return
        entry = self._undo.pop()
        if not entry.reversible:
            self.set_status(entry.reason, True)
            return
        if self.client is None:
            return
        client = self.client
        # The shown view's copy where there is one, the remembered copy
        # otherwise: an undo reaches the task it wrote even after the person
        # has navigated somewhere that does not hold it.
        known = {t.id: t for t in self._base}
        if entry.undo_action is not None:
            # An action that created something cannot be reversed by putting
            # fields back -- there was nothing before it to put back.  It
            # carries its own reversal, and that is the whole of the undo.
            wrote = {
                task_id: known.get(task_id) or task
                for task_id, task in entry.tasks.items()
            }
            if not entry.undo_action(wrote):
                return
            note = f" · {entry.note}" if entry.note else ""
            self.notice(f"Undid: {entry.label.lower()} “{entry.subject}”{note}")
            return
        restored = 0
        for task_id, fields in entry.previous.items():
            task = known.get(task_id) or entry.tasks.get(task_id)
            if task is None:
                continue
            self.submit_write(
                f"Undoing {entry.label.lower()}",
                task,
                (lambda tid, values=dict(fields): client.restore(tid, values)),
                dict(fields),
                # An undo is not itself something to undo: pressing the key
                # again reaches further back rather than turning round.
                record=False,
            )
            restored += 1
        if not restored:
            self.set_status(
                f"“{entry.subject}” no longer exists · nothing to undo there", True
            )
            return
        note = f" · {entry.note}" if entry.note else ""
        gone = ""
        # A notice rather than a plain status: the writes this just queued
        # will repaint as they confirm, and the counts would otherwise
        # replace the one thing the person pressed the key to find out.
        self.notice(f"Undid: {entry.label.lower()} “{entry.subject}”{note}{gone}")

    def action_toggle_work(self) -> None:
        """Hide the work project's tasks, or bring them back.

        Writes nothing: the mode only decides which of the rows a view
        already chose are painted.
        """
        if self.work_project is None:
            self.set_status(
                "No work project is set · put WORK_PROJECT in .env to hide one",
                True,
            )
            return
        if self.projects and self.work_project not in self.projects:
            # A setting left behind by a renamed or deleted project would
            # otherwise hide nothing and look exactly like a quiet day.
            self.set_status(
                f"The configured work project {self.work_project} was not found",
                True,
            )
            return
        self.hiding_work = not self.hiding_work
        # Recorded as well as applied, so the board can say whether the
        # clock or a person is hiding the work -- and so the next crossing
        # of the window knows there is an overrule to drop.
        self._work_override = self.hiding_work
        self.repaint()

    def action_cancel_task(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        client = self.client
        self.submit_write(
            "Cancelling",
            task,
            lambda tid: client.cancel_task(tid),
            {"checked": CANCELLED},
        )

    @work
    async def action_schedule(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        if self.refuse_foreign(task):
            return
        today = datetime.now(self.tz).date()
        choice = await self.push_screen_wait(
            DatePicker(f"Date for “{escape(task.title)}”", today)
        )
        if choice is None:
            return
        if choice == "today":
            target: "date | Bucket" = today
        elif choice == "tomorrow":
            target = today + timedelta(days=1)
        elif choice == "someday":
            target = Bucket.SOMEDAY
        elif choice == "clear":
            target = Bucket.INBOX
        else:
            typed = await self.push_screen_wait(
                TaskInput("Date as YYYY-MM-DD", f"{today:%Y-%m-%d}")
            )
            if not typed:
                return
            try:
                target = date.fromisoformat(typed.strip())
            except ValueError:
                self.set_status(f"“{typed}” is not a YYYY-MM-DD date", True)
                return
        label = target.label if isinstance(target, Bucket) else f"{target:%d %b}"
        client = self.client
        # Mirrors what `set_schedule` sends: start and deferred are two
        # halves of one fact, so the patch moves both together.
        if isinstance(target, Bucket):
            patch: dict[str, Any] = {"start": None, "deferred": target.deferred}
        else:
            patch = {
                "start": singularity.iso_z(
                    datetime.combine(target, time.min, tzinfo=self.tz)
                ),
                "useTime": False,
                "deferred": False,
            }
        self.submit_write(
            f"Moving to {label}",
            task,
            lambda tid: client.set_schedule(tid, target),
            patch,
        )

    @work
    async def action_add(self) -> None:
        where = (
            self.position.label
            if isinstance(self.position, Bucket)
            else f"{self.position:%d %b}"
        )
        title = await self.push_screen_wait(TaskInput(f"New task in {where}"))
        if not title or self.client is None:
            return
        # The new task belongs to whatever is on screen: undated in the
        # inbox, deferred in someday, or on the shown day at midnight flagged
        # as all-day -- a time of day is set in the app itself.
        if isinstance(self.position, Bucket):
            # No projectId, so a task added from the inbox lands in the inbox
            # rather than being filtered straight back out of it.  The field
            # is omitted rather than sent empty: the API rejects both "" and
            # null with `Must start with one of: "P-"`, and a task created
            # without it comes back unfiled, which is what is wanted.
            fields = {"deferred": self.position.deferred}
        else:
            fields = {
                "start": singularity.iso_z(
                    datetime.combine(self.position, time.min, tzinfo=self.tz)
                ),
                "useTime": False,
                # Past everything the day holds, so a new task joins the end
                # of a sequence rather than disturbing it.  The order has to
                # be sent: the API's own default is 0, the lowest value
                # there is, which would put every added task at the head of
                # its group and tie it with every other one added here.
                # Taken from the day already on screen, so no extra request.
                "scheduleOrder": self.next_order(),
            }
        client = self.client
        # The row appears at once under a placeholder id; confirming the
        # creation trades it for the real one.  The placeholder carries the
        # same fields the creation sends, so the view sorts and filters it
        # exactly as it will once the server has it.
        placeholder = Task({"id": f"tmp:{uuid.uuid4()}", "title": title, **fields})
        self._base = self._base + [placeholder]
        self._selected_id = placeholder.id
        self.submit_write(
            "Adding",
            placeholder,
            lambda tid: client.create_task(title, **fields),
            creates=True,
            undo_reason=(
                "adding cannot be undone · delete the task with backspace "
                "if you meant to"
            ),
        )

    def action_promote(self) -> None:
        """Turn the selected mail thread into a task on today.

        The one place a row from a source becomes the board's own.  Nothing
        is asked first: the decision that a message is work is the whole of
        the input, and a dialogue here would make the queue slower to drain
        than it is worth -- the rename key is one press away for a title
        somebody else chose.

        Two halves, in this order.  The task is created, and then the
        thread's messages are filed away in the archive, by the same means
        and with the same confirmation as reviewing one -- so the row leaves
        the queue for the same reason.  A task made and not filed shows the
        row once more, which a person can see and act on; mail filed away
        with no task made is work that has silently left the queue.  Only
        the first of those is repairable, so the task goes first.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        if not self.is_mail(task):
            self.notice(
                "f turns a mail thread into a task · "
                "this row is not one of those",
                True,
            )
            return
        messages = list(task.raw.get(MAIL_MESSAGES) or ())
        title = task.title
        today = datetime.now(self.tz).date()
        # What the message said, and which message it was.  The body because
        # a task holding the message is the work where one naming it is a
        # reminder -- and because the addresses a notification carries are
        # in its own text, so `o` reaches the build or the issue through the
        # note with nothing extracted.  The identity so the message can
        # still be found in the mailbox afterwards.
        #
        # Both read off the message rather than off the row's note field,
        # which happens to hold the same body: what the task carries should
        # not depend on how the row was drawn.
        newest = messages[-1] if messages else None
        body = (newest.body if newest is not None else "").strip()
        ident = (newest.ident if newest is not None else "").strip()
        # A bare label is worse than no label, so the identity goes in only
        # when there is one.
        parts = [p for p in (body, f"Message-ID: {ident}" if ident else "") if p]
        note = "\n\n".join(parts)
        fields: dict[str, Any] = {
            "start": singularity.iso_z(
                datetime.combine(today, time.min, tzinfo=self.tz)
            ),
            "useTime": False,
            "note": singularity.note_document(note),
        }
        # Filed as work in the request that makes the task.  Pressing this key
        # is the declaration that a message is work, and the task it makes
        # should not be the one task the key for work cannot hide.
        #
        # In the creation rather than a filing afterwards, which the store
        # would take as readily: a task created filed holds a group belonging
        # to its project, so every later write to it is accepted, and there is
        # no moment at which a promoted task is on the board unfiled.  It also
        # keeps this from being a *first filing* -- the irreversible action the
        # board confirms before performing -- because no task exists yet to
        # file, and undoing a promotion deletes the task outright.
        #
        # Added as a key rather than assigned a value that might be missing:
        # the store refuses both "" and null for this field, and where no work
        # project is configured a promotion is an ordinary unfiled task.  The
        # key that hides work is where that setting is answered for.
        if self.work_project is not None:
            fields["projectId"] = self.work_project
        client = self.client
        config = self.gateway_config

        def create(_tid: str) -> Any:
            # The day's own tasks, fetched here rather than read off the
            # screen: mail is shown in the inbox and the task goes to today,
            # so the shown view's orders say nothing about where this
            # belongs.  On the write thread, so the row is on screen before
            # this runs.
            try:
                held = client.tasks_for_day(today).tasks
                order = max(
                    (t.schedule_order for t in held),
                    default=0,
                ) + singularity.ORDER_STEP
            except Exception:
                # A day that could not be read is not a reason to lose the
                # task.  The API's own default is 0, the lowest there is.
                order = singularity.ORDER_STEP
            return client.create_task(title, scheduleOrder=order, **fields)

        placeholder = Task({"id": f"tmp:{uuid.uuid4()}", "title": title, **fields})
        self._base = self._base + [placeholder]

        def reverse(wrote: dict[str, Task]) -> bool:
            """Delete the task and put the thread back in the queue."""
            made = next(iter(wrote.values()), None)
            if made is None:
                # Nothing to delete means nothing to reverse.  Said rather
                # than passed over: the entry has been taken off the stack
                # by now, so silence would look like a key that did nothing.
                self.notice(
                    f"“{title}” is no longer here · nothing to undo there",
                    True,
                )
                return False
            self.submit_write(
                "Deleting", made, lambda tid: client.delete_task(tid),
                removes=True, record=False,
            )
            if config is not None and messages:
                self.mail_started()
                self.put_back(config, self.by_folder(messages), title)
            return True

        self.submit_write(
            "Promoting",
            placeholder,
            create,
            creates=True,
            subject=title,
            undo_action=reverse,
            undo_note="the mail goes back to the folder it came from",
        )
        if not messages:
            return
        if config is None:
            # The task stands, which is the half that matters.  The row
            # comes back at the next read, which is visible and harmless,
            # where refusing the promotion would throw away the decision
            # that made it.
            self.notice(
                f"“{title}” added · no mail gateway is configured, so the "
                f"thread is still in the queue",
                True,
            )
            return
        dropped = self.drop_thread(task)
        if dropped is None:
            return
        thread, where = dropped
        self.repaint()
        self.mail_started()
        self.file_away(config, self.by_folder(messages), title, thread, where)

    @work
    async def action_project(self) -> None:
        """Put the selected task in a project.

        Filing a task that has none is confirmed first: the API takes only a
        project id and refuses both an empty value and none, so nothing the
        board can send un-files a task.  That makes a first filing the second
        irreversible action after deleting, and it is asked the same way.
        Moving a task that is already filed gives up nothing it still has, so
        it is not asked.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        if self.refuse_foreign(task):
            return
        if not self.projects:
            self.set_status("No projects to file into", True)
            return
        chosen = await self.push_screen_wait(
            ProjectPicker(f"Project for “{escape(task.title)}”", self.projects,
                          task.project_id)
        )
        if chosen is None or chosen == task.project_id:
            return
        if task.project_id is None:
            ok = await self.push_screen_wait(
                Confirm(
                    f"File “{escape(task.title)}” under "
                    f"{escape(self.projects[chosen])}? "
                    "It cannot be un-filed here."
                )
            )
            if not ok:
                return
        client = self.client
        self.submit_write(
            f"Filing under {self.projects[chosen]}",
            task,
            lambda tid: client.set_project(tid, chosen),
            {"projectId": chosen},
            # A task that had no project cannot be returned to having none:
            # the API refuses every value that would.  Moving between
            # projects is ordinary, because a project to go back to exists.
            undo_reason=(
                "filing a task that had no project cannot be undone · "
                "the API cannot return it to having none"
                if task.project_id is None else None
            ),
        )

    def action_green(self) -> None:
        """Mark the selected task as green, or take the mark off again.

        One key for both directions: a person wants the task marked or not
        marked, and should not have to know which it is now to say so.

        The API replaces a task's tags outright rather than merging, so the
        write carries every other tag the task has back with it.  That makes
        this the board's only read-modify-write, and it is built from the
        task on screen rather than a fresh fetch, so it stays on the same
        optimistic path as every other action.

        Nothing is confirmed and nothing is irreversible: unlike a project,
        the tag comes off again, so pressing the key twice leaves the task
        exactly as it was found.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        if self.green_tag is None:
            self.set_status(
                "No tag is set · put GREEN_TAG in .env to mark tasks", True
            )
            return
        if (
            self.green_checked and self.green_title is None
            and not (self.is_tracker(task) or self.is_event(task))
        ):
            # Configured but resolving to nothing: marking would write a tag
            # the account does not have, and the API would refuse it anyway.
            self.set_status(
                f"The configured tag {self.green_tag} was not found", True
            )
            return
        # A task the API answered without the field carries no tags, which
        # is an empty list rather than nothing.  Settling that before the
        # write is recorded matters: an undo sends the previous value back,
        # and the API refuses a null where it wants an array.
        task.raw.setdefault("tags", [])
        marked = task.has_tag(self.green_tag)
        tags = [t for t in task.tags if t != self.green_tag]
        if not marked:
            tags.append(self.green_tag)
        client, wanted = self.client, list(tags)

        def write(tid: str) -> Any:
            """Send the tags, and for a removal make sure it actually took.

            Runs on the queue that serialises this one task's writes, so
            neither the wait nor a re-read holds up anything else: the board
            has already shown the row without its mark and answers every key
            meanwhile.

            A removal waits behind a recent tag write, because the store
            drops one that arrives too soon.  Waiting makes that rare, not
            impossible, so the removal is then read back and sent again if
            the tag is still there.  Only a removal needs this; setting a
            tag was never seen to fail.
            """
            if wanted:
                result = client.set_tags(tid, wanted)
                self._tag_written[tid] = monotonic()
                return result
            result = None
            for attempt in range(TAG_REMOVAL_ATTEMPTS):
                since = self._tag_written.get(tid)
                if since is not None:
                    left = TAG_SETTLE_SECONDS - (monotonic() - since)
                    if left > 0:
                        sleep(left)
                result = client.set_tags(tid, wanted)
                self._tag_written[tid] = monotonic()
                if attempt == TAG_REMOVAL_ATTEMPTS - 1:
                    break
                if not client.task_tags(tid):
                    break
            return result

        self.submit_write(
            f"Unmarking {self.green_title or 'green'}" if marked
            else f"Marking {self.green_title or 'green'}",
            task,
            write,
            {"tags": wanted},
        )

    @work
    async def action_rename(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        if self.refuse_foreign(task):
            return
        title = await self.push_screen_wait(TaskInput("Rename task", task.title))
        if not title or title == task.title:
            return
        client = self.client
        self.submit_write(
            "Renaming",
            task,
            lambda tid: client.update_task(tid, title=title),
            {"title": title},
        )


    @work
    async def action_note(self) -> None:
        """Write the selected task's note.

        Gathers before it writes, so it asks the shared guard first: a row
        the board does not own must refuse at once rather than open an
        editor over a note it could never save.
        """
        task = self.selected
        if task is None or self.client is None:
            return
        if self.refuse_foreign(task):
            return
        if not task.note_is_plain:
            # Saving would keep the words and drop everything else.  Said
            # rather than done, because what would be lost is exactly what
            # cannot be seen here.
            self.notice(
                f"“{task.title}” has a formatted note · "
                "it cannot be edited here without losing the formatting",
                True,
            )
            return
        before = task.note_text
        written = await self.push_screen_wait(
            NoteInput(f"Note for “{escape(task.title)}”", before)
        )
        if written is None:
            return
        if written.strip() == before.strip():
            # A write that changes nothing still spends a request and still
            # occupies a place in the undo history.
            self.set_status("The note is unchanged")
            return
        # A task the API answered without the field carries no note, which is
        # an empty document rather than nothing.  Settled before the write is
        # recorded: an undo sends the previous value back, and the API refuses
        # a null where it wants a string.
        task.raw.setdefault("note", singularity.note_document(""))
        document = singularity.note_document(written.strip())
        client = self.client
        self.submit_write(
            "Clearing the note" if not written.strip() else "Writing the note",
            task,
            (lambda tid, value=document: client.update_task(tid, note=value)),
            {"note": document},
        )

    @work
    async def action_delete(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        if self.refuse_foreign(task):
            return
        # The API deletes for real -- a deleted task 404s afterwards, it does
        # not land in the basket -- so this always asks first.
        ok = await self.push_screen_wait(
            Confirm(f"Delete “{escape(task.title)}” for good?")
        )
        if not ok:
            return
        client = self.client
        self.submit_write(
            "Deleting",
            task,
            lambda tid: client.delete_task(tid),
            removes=True,
            undo_reason="a deletion cannot be undone · the task is gone for good",
        )

    def action_focus_task(self) -> None:
        task = self.selected
        if task is None:
            return
        self.push_screen(
            TaskFocus(
                task,
                task.start_label(self.tz),
                self.projects.get(task.project_id or "", ""),
                self.tz,
            )
        )

    @work
    async def action_open_link(self) -> None:
        """Hand the selected row's address to the operating system.

        Routed through the app's own opener rather than the standard library
        so a test can intercept it and assert the address without launching
        a browser -- which is what makes this, rather than the clickable
        span, the path that ships verified.

        A task may offer several things to open, in which case it asks.  A
        person pressing the key never has to know in advance whether they
        will be asked: one is opened, several are offered, none is said.
        """
        task = self.selected
        if task is None:
            return
        # A tracker row carries its own page and an event the address found
        # in it, rather than anything written in a title -- so the same key
        # opens all three with no separate action for any of them.  Neither
        # ever offers a choice: each has exactly one address, by
        # construction.
        if self.is_tracker(task):
            self.hand_over(task.raw.get(TRACKER_URL), task)
            return
        if self.is_event(task):
            self.hand_over(task.raw.get(EVENT_URL), task)
            return
        # A mail row offers what its newest message points at, collected the
        # same way a task's candidates are -- so one opens, several ask, and
        # none says so, exactly as for a task.
        choices = self.openable(task)
        if len(choices) <= 1:
            self.hand_over(choices[0][1] if choices else None, task)
            return
        chosen = await self.push_screen_wait(
            LinkPicker(f"Open from “{escape(task.title)}”", choices)
        )
        if chosen:
            self.hand_over(chosen, task)

    def hand_over(self, url: str | None, task: Task) -> None:
        """Open one address, or say the row has none."""
        if not url:
            # Named for what the row is: "that task" would be wrong on two
            # of the three kinds of row this key now serves.
            kind = ("event" if self.is_event(task)
                    else "thread" if self.is_mail(task) else "task")
            self.set_status(f"That {kind} has no link")
            return
        self.open_url(url)
        self.set_status(f"Opening {url}")

    @work
    async def action_start_workspace(self) -> None:
        """Start work on the selected issue, by running one configured program.

        The board does not check anything out, reach any host, or know what a
        repository is.  It knows three things the program does not -- which
        issue, which tracker project, which version -- and hands them over.
        Everything that changes often lives in the program.

        The version is asked rather than assumed, with the issue's own filled
        in.  An issue is recorded against the version where a problem was
        found or is due, which is not always the version somebody is about to
        work in, so what the tracker holds is a proposal and the person has
        the last word.  Leaving the prompt, or emptying it, starts nothing --
        as it does for renaming and for adding.
        """
        task = self.selected
        if task is None:
            return
        if not self.is_tracker(task):
            # Only a tracker row carries the three facts.  A task that merely
            # mentions an issue's key has no issue behind it, so the board
            # knows neither its project nor its version.
            self.set_status("Only a tracker issue can start a workspace")
            return
        if self.workspace_command is None:
            self.set_status(
                "No workspace program is set · put WORKSPACE_COMMAND in .env",
                True,
            )
            return
        key = task.raw.get(TRACKER_KEY) or ""
        versions = tuple(task.raw.get(TRACKER_VERSIONS) or ())
        version = await self.push_screen_wait(
            # Escaped: the prompt is drawn as markup, and while an issue key
            # has never yet held a bracket, the rule this board settled is
            # that foreign text is escaped wherever it is drawn rather than
            # wherever somebody expects trouble.
            TaskInput(f"Work on {escape(key)} at which version?",
                      versions[0] if versions else "")
        )
        if not version:
            return
        argv = [self.workspace_command,
                "--key", key,
                "--project", task.raw.get(TRACKER_PROJECT) or "",
                "--version", version]
        try:
            self.launch(argv)
        except OSError as exc:
            # Said differently from "starting": a program that is not there
            # and a program that ran and failed are different problems, and
            # only the first is the board's to report.
            self.set_status(
                f"Could not start {self.workspace_command}: "
                f"{type(exc).__name__}", True)
            return
        self.set_status(f"Starting a workspace for {key} at {version}")

    def launch(self, argv: list[str]) -> None:
        """Run a program and do not wait for it.

        A list of arguments and no shell, ever: the values in it come from a
        tracker and from a person, and neither is the board's to vouch for.
        With no shell there is nothing for them to mean.

        Routed through a method of its own for the reason the link opener is
        -- so a suite can assert what would be run without running it, which
        is what makes this the path that ships verified rather than the one
        nobody could test.

        Nothing is awaited and no exit code is ever read.  What the program
        goes on to do is visible where the program puts it.

        All three streams go nowhere, and the last two are the point: a child
        writes to the terminal's own file descriptors, which no redirection
        inside this process can reach.  The board draws a full screen on those
        descriptors, so a program that printed one line -- a warning, a usage
        message, a progress bar -- would write it across the task list, and
        nothing here could take it back.  A program with something to say has
        to say it where it can be read afterwards.
        """
        subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def note_step(self) -> int:
        """How far one press of a scrolling key moves the pane.

        A page less one line.  A whole page drops the line being read off
        the top; keeping one is what a pager does, and for the same reason.
        Never less than one, so a pane squeezed to a single row still moves.
        """
        return max(1, self.query_one("#notes").size.height - 1)

    def action_note_up(self) -> None:
        """Scroll the note pane up.  Writes nothing, and moves no selection.

        Reading is not a change, so this is offered on every row the board
        draws -- a mail row, a calendar row, a tracker row included.  Those
        are the rows whose notes least often fit.
        """
        self.query_one("#notes").scroll_relative(
            y=-self.note_step(), animate=False)

    def action_note_down(self) -> None:
        """Scroll the note pane down.  The same, in the other direction."""
        self.query_one("#notes").scroll_relative(
            y=self.note_step(), animate=False)

    @work
    async def action_leave(self) -> None:
        """Quit, asking first if the mailbox is busy.

        Nothing in flight and it goes at once: a question asked every time
        is a question that stops being read.  Declining leaves everything
        as it was, work included.
        """
        busy = self.mail_busy
        if busy:
            outstanding = f"{busy} mailbox operation{'' if busy == 1 else 's'}"
            if not await self.push_screen_wait(
                Confirm(f"{outstanding} still finishing.  Quit anyway?")
            ):
                return
            journal.warn(f"quit with {busy} operation(s) still in flight")
        self.exit()

    def action_help(self) -> None:
        self.push_screen(Help())


@contextmanager
def terminal_tab_named(title: str) -> "Iterator[None]":
    """Name the terminal's tab for the duration, then give the name back.

    Writes nothing unless the output really is a terminal, so a piped or
    redirected run carries no control sequences.  The restore runs however
    the board leaves -- a crash is no reason for a terminal to keep the wrong
    name -- and a terminal that cannot remember a previous title simply keeps
    the new one, which the shell's next prompt usually replaces anyway.
    """
    stream = sys.stdout
    naming = False
    try:
        naming = stream.isatty()
    except (ValueError, AttributeError):
        # A stream that has been closed or replaced by something without the
        # question: not a terminal as far as this is concerned.
        naming = False
    if naming:
        stream.write(_TITLE_PUSH + _TITLE_SET.format(title))
        stream.flush()
    try:
        yield
    finally:
        if naming:
            try:
                stream.write(_TITLE_POP)
                stream.flush()
            except ValueError:
                # Shutting down took the stream with it; the terminal keeps
                # the name, which is the lesser fault and never an error here.
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal task board for SingularityApp.")
    parser.add_argument("day", nargs="?", help="day to open, YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)
    try:
        day = date.fromisoformat(args.day) if args.day else None
    except ValueError:
        parser.error("day must look like YYYY-MM-DD")
    with terminal_tab_named(TAB_TITLE):
        TaskApp(day).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
