"""A terminal task board for SingularityApp.

Run it with the project venv:

    ./.venv/bin/python main.py            # today
    ./.venv/bin/python main.py 2026-09-05 # a specific day

Keys are listed in the footer; `?` shows the full set.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
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
        Binding("escape,n", "no", "No"),
        Binding("y", "yes", "Yes"),
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
        ("n", "never", "Never"),
        ("c", "clear", "Clear date (back to inbox)"),
    ]

    BINDINGS = [Binding("escape", "cancel", "Cancel")] + [
        Binding(key, f"choose('{name}')", label) for key, name, label in CHOICES
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


class Help(ModalScreen[None]):
    BINDINGS = [Binding("escape,question_mark,q", "close", "Close")]

    TEXT = """\
[b]Moving around[/b]
  ↑ / ↓ or k / j     select task
  ← / → or h / l     previous / next day
  t                  jump to today
  i                  inbox — tasks with no date
  n                  never — tasks set aside
  r                  reload from the server

[b]Changing tasks[/b]
  space or enter     tick / untick the selected task
  d                  set the date: today, tomorrow, a
                     given day, never, or cleared
  x                  cancel the task
  a                  add a task to the shown view
  e                  rename the selected task
  delete             delete for good (asks first)

[b]Other[/b]
  ?                  this help
  q                  quit

Giving a task a date takes it out of the inbox. Days do
not apply in the inbox or never, so h / l do nothing
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


class TaskApp(App[None]):
    """Day-at-a-time view of your tasks."""

    TITLE = "Singularity tasks"

    CSS = """
    Screen { layers: base overlay; }

    #body { height: 1fr; }

    #daybar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    DataTable { height: 1fr; }
    DataTable > .datatable--cursor { background: $accent; color: $text; }

    #detail {
        height: auto;
        max-height: 40%;
        border-top: solid $panel;
        padding: 0 1;
        color: $text-muted;
    }

    #status { height: 1; padding: 0 1; color: $text-muted; }
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
    ModalScreen { align: center middle; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("h,left", "prev_day", "Prev day"),
        Binding("l,right", "next_day", "Next day"),
        Binding("t", "today", "Today"),
        Binding("i", "inbox", "Inbox"),
        Binding("n", "never", "Never"),
        Binding("r", "refresh", "Reload"),
        Binding("space,enter", "toggle", "Tick"),
        Binding("a", "add", "Add"),
        Binding("e", "rename", "Rename"),
        Binding("x", "cancel_task", "Cancel"),
        Binding("d", "schedule", "Date"),
        Binding("delete", "delete", "Delete"),
        Binding("question_mark", "help", "Help"),
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
        self.projects: dict[str, str] = {}
        self._busy = False

    # -- layout ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="body"):
            yield Static("", id="daybar")
            yield DataTable(id="tasks", cursor_type="row", zebra_stripes=True)
            yield Static("", id="detail")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
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

    @work(exclusive=False, thread=True)
    def submit_write(self, label: str, func, *args: Any) -> None:
        """Run one write against the API, then reload the day.

        Writes are serialised behind `_busy` so a burst of keypresses cannot
        fire overlapping requests for the same task.  Not named `run_action`:
        that is Textual's own binding dispatcher, and shadowing it silently
        breaks every key in the app.
        """
        if self._busy:
            return
        self._busy = True
        self.call_from_thread(self.set_status, f"{label}…")
        try:
            func(*args)
        except SingularityError as exc:
            self.call_from_thread(self.set_status, str(exc), True)
            return
        finally:
            self._busy = False
        self.load()

    def show_tasks(self, listing: singularity.Listing) -> None:
        table = self.query_one(DataTable)
        previous = table.cursor_row
        tasks = listing.tasks
        self.tasks = tasks
        self.filed_out = listing.filed_out
        table.clear()
        for task in tasks:
            table.add_row(*self.row_for(task))
        if tasks:
            table.move_cursor(row=min(previous, len(tasks) - 1))
        self.update_daybar()
        self.update_detail()
        done = sum(1 for t in tasks if t.done)
        self.set_status(f"{len(tasks)} task(s) · {done} done")

    def row_for(self, task: Task) -> tuple[str, str, str, str]:
        title = task.title
        if task.recurring:
            title = f"↻ {title}"
        if task.is_note:
            title = f"≡ {title}"
        if task.done or task.cancelled:
            title = f"[strike dim]{title}[/]"
        project = self.projects.get(task.project_id or "", "")
        return (
            MARKS[task.checked],
            task.start_label(self.tz),
            title,
            f"[dim]{project}[/dim]" if project else "",
        )

    @property
    def tz(self):
        return self.client.tz if self.client else singularity.local_tz()

    @property
    def selected(self) -> Task | None:
        table = self.query_one(DataTable)
        if not self.tasks or table.cursor_row < 0:
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
    def row_changed(self) -> None:
        self.update_detail()

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

    def action_never(self) -> None:
        self._go(Bucket.NEVER)

    def action_refresh(self) -> None:
        self.projects = {}
        self.load()

    def action_toggle(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        want_done = not task.done
        label = "Ticking" if want_done else "Unticking"
        self.submit_write(label, self.client.set_done, task, want_done)

    def action_cancel_task(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        self.submit_write("Cancelling", self.client.cancel_task, task.id)

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
        elif choice == "never":
            target = Bucket.NEVER
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
        self.submit_write(
            f"Moving to {label}",
            lambda: self.client.set_schedule(task.id, target),
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
        # inbox, deferred in never, or on the shown day at midnight flagged
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
            }
        self.submit_write(
            "Adding",
            lambda: self.client.create_task(title, **fields),
        )

    @work
    async def action_rename(self) -> None:
        task = self.selected
        if task is None or self.client is None:
            return
        title = await self.push_screen_wait(TaskInput("Rename task", task.title))
        if not title or title == task.title:
            return
        self.submit_write("Renaming", lambda: self.client.update_task(task.id, title=title))

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
        self.submit_write("Deleting", self.client.delete_task, task.id)

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
