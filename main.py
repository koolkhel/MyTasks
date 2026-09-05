"""A terminal task board for SingularityApp.

Run it with the project venv:

    ./.venv/bin/python main.py            # today
    ./.venv/bin/python main.py 2026-09-05 # a specific day

Keys are listed in the footer; `?` shows the full set.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Callable, Iterable

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (
    DataTable,
    Header,
    Input,
    Label,
    Static,
)

import singularity
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
    """
    parts = [k.strip() for k in spec.split(",")]
    twins = [KEY_TWINS[k] for k in parts if k in KEY_TWINS]
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

    #: Textual's key names are not what a person presses.
    KEY_NAMES = {
        "full_stop": ".",
        "question_mark": "?",
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
        self.update(
            "\n".join(
                "  ".join(f"[b]{k}[/b] [dim]{d}[/dim]" for k, d in row)
                for row in rows
            )
        )

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
                yield Static(note, id="focus-note")
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
  i                  inbox — tasks with no date
  s                  someday — tasks put off
  r                  reload from the server

[b]Looking at a task[/b]
  enter              show the selected task in full

[b]Changing tasks[/b]
  space              tick / untick the selected task
  .                  done for today — records the work
                     and moves the task to tomorrow,
                     leaving it unfinished
  d                  set the date: today, tomorrow, a
                     given day, someday, or cleared
  x                  cancel the task
  a                  add a task to the shown view
  e                  rename the selected task
  o                  open the task's link in a browser
  backspace          delete for good (asks first)

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


class TaskApp(App[None]):
    """Day-at-a-time view of your tasks."""

    TITLE = "Singularity tasks"

    CSS = """
    Screen { layers: base overlay; }

    #body { height: 1fr; }

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

    #detail {
        height: auto;
        max-height: 40%;
        border-top: solid $panel;
        padding: 0 1;
        color: $text-muted;
    }

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
    #dialog-title { text-style: bold; }
    #dialog-hint { color: $text-muted; }
    #help-body { padding: 1 0; }
    #picker-body { padding: 1 0; }
    #focus-title { text-style: bold; padding: 1 0 0 0; }
    #focus-facts { color: $text-muted; padding: 1 0 0 0; }
    #focus-note { padding: 1 0 0 0; }
    ModalScreen { align: center middle; }
    """

    BINDINGS = [
        Binding(keys("q"), "quit", "Quit"),
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
        Binding("space", "toggle", "Tick"),
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
        Binding(keys("x"), "cancel_task", "Cancel"),
        Binding(keys("d"), "schedule", "Date"),
        Binding(keys("o"), "open_link", "Link"),
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
        # A refusal to keep on the status line.  Repainting would otherwise
        # replace it with the view's counts the moment another write
        # confirms, leaving the failure effectively unreported.
        self._error: str | None = None

    # -- layout ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="body"):
            yield Static("", id="daybar")
            # No zebra striping: it paints every other row a lighter shade,
            # which stops the ground being the ground.  Turbo C++ had no
            # alternating rows either.
            yield DataTable(id="tasks", cursor_type="row")
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
        table = self.query_one(DataTable)
        table.add_column("", key="mark", width=2)
        table.add_column("When", key="when", width=8)
        table.add_column("Task", key="title")
        table.add_column("Project", key="project", width=22)
        table.focus()
        self.load()

    # -- data --------------------------------------------------------------

    @work(exclusive=True, thread=True)
    def load(self) -> None:
        """Fetch the shown view's tasks off the UI thread."""
        self.call_from_thread(self.set_status, "Loading…")
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

    # -- writes ------------------------------------------------------------

    def submit_write(
        self,
        label: str,
        task: Task,
        run: Callable[[str], Any],
        patch: dict[str, Any] | None = None,
        removes: bool = False,
        creates: bool = False,
        select: str | None = None,
    ) -> None:
        """Show a write's outcome at once, then queue it for the API.

        Nothing waits on the network: the patch goes on, the board repaints,
        and the request follows behind.  Not named `run_action`: that is
        Textual's own binding dispatcher, and shadowing it silently breaks
        every key in the app.
        """
        patch = patch or {}
        # Acting again supersedes the last refusal, so it stops being shown.
        self._error = None
        pending = Pending(
            task_id=task.id,
            label=label,
            run=run,
            patch=patch,
            previous={key: task.raw.get(key) for key in patch},
            removes=removes,
            creates=creates,
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
        if pending.creates:
            # The task never came into being, so its row goes with it.
            self._base = [t for t in self._base if t.id != key]
        also = f" · {abandoned} more dropped" if abandoned else ""
        self._error = f"{pending.label} failed: {message}{also}"
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
        # A fresh view supersedes whatever failed against the old one.
        self._error = None
        self.reference = listing.reference
        self.repaint()

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
        return not isinstance(self.position, Bucket)

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
        return singularity.group_key(task, self.tz, self.reference)

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
        """The task's whole ordering group, in the sequence now shown."""
        mine = self.group_of(task)
        return [t for t in self.tasks if self.group_of(t) == mine]

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
        previous = table.cursor_row
        keep = self._selected_id
        tasks = singularity.sort_for_display(
            [t for t in self.patched() if self.belongs(t)],
            self.tz,
            self.reference,
            manual=self.orders_manually,
        )
        self.tasks = tasks
        self.past_due = (
            sum(1 for t in tasks if t.past_due_since(self.reference, self.tz))
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
            if index is None:
                # The task is gone.  Take the nearest surviving position
                # rather than whatever has moved into the old row.
                index = min(max(previous, 0), len(tasks) - 1)
            table.move_cursor(row=index)
            self._selected_id = tasks[index].id
        else:
            self._selected_id = None
        self.update_daybar()
        self.update_detail()
        done = sum(1 for t in tasks if t.done)
        bits = [f"{len(tasks)} task(s)", f"{done} done"]
        if self.past_due:
            bits.insert(1, f"{self.past_due} past due")
        in_flight = sum(len(q) for q in self._pending.values())
        if in_flight:
            bits.append(f"{in_flight} saving")
        # A refusal outranks the counts until the person acts again or the
        # view is fetched afresh.
        if self._error:
            self.set_status(self._error, True)
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

    def row_for(self, task: Task) -> tuple[str, str, str, str]:
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
            MARKS[task.checked],
            when,
            title,
            f"[dim]{project}[/dim]" if project else "",
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

    def update_daybar(self) -> None:
        bar = self.query_one("#daybar", Static)
        if isinstance(self.position, Bucket):
            parts = [self.position.label, "no date"]
            if self.filed_out:
                parts.append(f"{len(self.tasks)} shown")
                parts.append(f"{self.filed_out} filed, hidden")
            bar.update("  ·  ".join(parts))
            return
        today = datetime.now(self.tz).date()
        delta = (self.position - today).days
        relative = {0: "today", 1: "tomorrow", -1: "yesterday"}.get(
            delta, f"{abs(delta)} days {'ahead' if delta > 0 else 'ago'}"
        )
        bar.update(f"{self.position:%A %d %B %Y}  ·  {relative}")

    def update_detail(self) -> None:
        task = self.selected
        detail = self.query_one("#detail", Static)
        if task is None:
            detail.update("")
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
        note = task.note_text
        sections = [part for part in ("  ·  ".join(bits), note) if part]
        detail.update("\n".join(sections))

    def set_status(self, message: str, error: bool = False) -> None:
        status = self.query_one("#status", Static)
        status.set_class(error, "error")
        status.update(message)

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
        self.update_daybar()
        self.load()

    def _shift_day(self, days: int) -> None:
        """Step to an adjacent day, but only from a day.

        From a bucket there is no adjacent day to step to -- any date it
        picked would be arbitrary -- so the movement does nothing and `t` is
        the way back to the calendar.
        """
        if isinstance(self.position, Bucket):
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
        self.projects = {}
        self.load()

    def action_toggle(self) -> None:
        task = self.selected
        if task is None or self.client is None:
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
        if not self.orders_manually:
            self.set_status(
                f"{self.position.label} is ordered by title · "
                "reordering applies to calendar days",
                True,
            )
            return
        if self.neighbour_to_pass(task, step) is None:
            self.set_status(f"“{task.title}” cannot move {label} from here", True)
            return

        order = self.order_for_move(task, step)
        if order is None:
            # Nothing fits between the destination and the task beyond it.
            # Respace the run into values the day does not use, which is
            # safe to apply in pieces, then place the task in the room made.
            if not self.respace(task):
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
        )

    def respace(self, task: Task) -> bool:
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
            )
        return True

    def action_move_up(self) -> None:
        self.move_task(-1, "up")

    def action_move_down(self) -> None:
        self.move_task(1, "down")

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
        today = datetime.now(self.tz).date()
        choice = await self.push_screen_wait(
            DatePicker(f"Date for “{task.title}”", today)
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
        )

    @work
    async def action_rename(self) -> None:
        task = self.selected
        if task is None or self.client is None:
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
    async def action_delete(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        # The API deletes for real -- a deleted task 404s afterwards, it does
        # not land in the basket -- so this always asks first.
        ok = await self.push_screen_wait(
            Confirm(f"Delete “{task.title}” for good?")
        )
        if not ok:
            return
        client = self.client
        self.submit_write(
            "Deleting",
            task,
            lambda tid: client.delete_task(tid),
            removes=True,
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

    def action_open_link(self) -> None:
        """Hand the selected task's address to the operating system.

        Routed through the app's own opener rather than the standard library
        so a test can intercept it and assert the address without launching
        a browser -- which is what makes this, rather than the clickable
        span, the path that ships verified.
        """
        task = self.selected
        if task is None:
            return
        url = task.link
        if not url:
            self.set_status("That task has no link")
            return
        self.open_url(url)
        self.set_status(f"Opening {url}")

    def action_help(self) -> None:
        self.push_screen(Help())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal task board for SingularityApp.")
    parser.add_argument("day", nargs="?", help="day to open, YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)
    try:
        day = date.fromisoformat(args.day) if args.day else None
    except ValueError:
        parser.error("day must look like YYYY-MM-DD")
    TaskApp(day).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
