"""Every label the board draws shows the characters it was given.

Synthetic tasks only, with titles, notes and project names written to read as
markup.  Each check reads what the toolkit *draws* -- a widget's
`visual.plain`, and once the composited screen itself -- rather than the
string the board assembled: the strings were always right, and the drawing
was not.  The bar's own entries and packing are checked by their own suites
and are deliberately not re-checked here.
"""
import asyncio, sys
from contextlib import asynccontextmanager
from datetime import date
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import StubClient, mk, TZ, run_parts
import main
import singularity
from main import (TaskApp, Confirm, DatePicker, LinkPicker, NoteInput,
                  ProjectPicker)
from textual.widgets import OptionList
from textual.visual import visualize

D = date(2099, 9, 1)
#: A title, a project name and a note written the way markup is written.  The
#: brackets are the whole point; the words are meaningless on purpose.
TITLE = "[draft] plan [b]one[/b]"
WORK = "P-mark-0001"
PROJ = {WORK: "[held] later", "P-mark-0002": "Plain"}
#: Two addresses, the first holding a bracket -- which the board's own reader
#: keeps, so a picker really is asked to draw one.
NOTE = "see https://e.invalid/a[1]/b and also https://e.invalid/z"
#: Text shaped the way the two parsers disagree about.  `escape` guards a
#: bracket followed by a lowercase letter, `#`, `/` or `@`, which is Rich's
#: idea of a tag; Textual reads more than that as one.  The first raised and
#: ended the session, the middle ones vanished without a word, the backslashes
#: came back doubled, and the last is the board's own styling written by
#: somebody else.  Every word is meaningless on purpose.
SHAPES = (
    "usage [--opt=A-B] x",
    "[A]",
    "[Ab] text",
    "[ABC=1]",
    "[$var]",
    "[_x]",
    "[--k=SECS] [--v=path] S D",
    "a\\[b]",
    "end\\",
    "[b]one[/b]",
)

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")

def drawn(widget):
    """What the toolkit draws for a widget, as text."""
    return widget.visual.plain

def drawn_options(option_list):
    """What each of a list's options draws as, in order."""
    return [visualize(option_list, o.prompt, markup=True).plain
            for o in option_list._options]

def on_screen(app):
    """The composited screen as text -- what a person actually sees."""
    strips = app.screen._compositor.render_strips()
    return "\n".join("".join(seg.text for seg in strip) for strip in strips)

def prompt_text(app):
    return drawn(app.screen.query_one("#dialog-title"))

@asynccontextmanager
async def board(tasks=None, projects=None, note=None):
    app = TaskApp(D)
    held = tasks if tasks is not None else [mk("T-a", TITLE, D)]
    if note is not None:
        held[0].raw["note"] = singularity.note_document(note)
    app.client = StubClient(held)
    app.calendar_config = None
    app.tracker_config = None
    app.mail_config = None
    app.gateway_config = None
    app.work_project = WORK
    app.projects = dict(projects if projects is not None else PROJ)
    async with app.run_test(size=(120, 44)) as pilot:
        for _ in range(16): await pilot.pause()
        app.projects = dict(projects if projects is not None else PROJ)
        yield app, pilot

async def settle(pilot, n=24):
    for _ in range(n): await pilot.pause()

async def until(pilot, test, n=40):
    for _ in range(n):
        await pilot.pause()
        if test(): return True
    return False

# ------------------------------------------------------------------ the key bar
async def the_key_bar():
    print("the bar draws the bracket keys as brackets")
    async with board() as (app, pilot):
        bar = app.query_one(main.KeyBar)
        text = drawn(bar)
        check("the note keys read as their characters",
              ("[ Note up" in text, "] Note down" in text), (True, True))
        # The failure this replaces: `[` opened a tag and the closing one was
        # left on screen, so the bar read `[[/b] Note up`.
        check("no styling of the bar's own is left as text",
              [t for t in ("[b]", "[/b]", "[dim]", "[/dim]") if t in text], [])
        check("and the screen itself shows the keys",
              ("[ Note up" in on_screen(app), "] Note down" in on_screen(app)),
              (True, True))

# --------------------------------------------------------------- the status line
async def the_status_line():
    print("a message quoting a title keeps every character of it")
    async with board() as (app, pilot):
        # The board's own refusal, reached by the key: one task on the day has
        # no neighbour to pass.
        await pilot.press("K")
        await settle(pilot, 20)
        text = drawn(app.query_one("#status"))
        check("the refusal names the task as written", TITLE in text, True)
        check("and says what it refused",
              "cannot move up from here" in text, True)

    print("what the board writes itself is unchanged")
    async with board() as (app, pilot):
        app.set_status("3 tasks · 1 done")
        await settle(pilot, 6)
        check("an ordinary message draws exactly as given",
              drawn(app.query_one("#status")), "3 tasks · 1 done")
        app.set_status("the store said no", True)
        await settle(pilot, 6)
        status = app.query_one("#status")
        check("an error draws as given too", drawn(status), "the store said no")
        check("and is still marked as an error by class, not by markup",
              status.has_class("error"), True)

# ------------------------------------------------------------------ the prompts
async def the_prompts():
    for key, kind, name in [("d", DatePicker, "the date picker"),
                            ("p", ProjectPicker, "the project picker"),
                            ("n", NoteInput, "the note editor"),
                            ("backspace", Confirm, "the delete confirmation")]:
        print(f"{name} shows the title as written")
        async with board() as (app, pilot):
            await pilot.press(key)
            opened = await until(pilot, lambda: isinstance(app.screen, kind))
            check(f"{name} opens", opened, True)
            if opened:
                check("and shows every character of the title",
                      TITLE in prompt_text(app), True)

    print("the link picker shows the title as written")
    async with board(note=NOTE) as (app, pilot):
        await pilot.press("o")
        opened = await until(pilot, lambda: isinstance(app.screen, LinkPicker))
        check("the link picker opens", opened, True)
        if opened:
            check("and shows every character of the title",
                  TITLE in prompt_text(app), True)

    print("the filing confirmation shows the title and the project's name")
    async with board(tasks=[mk("T-a", TITLE, D)]) as (app, pilot):
        await pilot.press("p")
        if await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
            await pilot.press("enter")
            opened = await until(pilot, lambda: isinstance(app.screen, Confirm))
            check("the confirmation opens", opened, True)
            if opened:
                text = prompt_text(app)
                check("it names the task as written", TITLE in text, True)
                check("and the project as the store named it",
                      PROJ[WORK] in text or PROJ["P-mark-0002"] in text, True)
        else:
            check("the picker opens", False, True)

# ------------------------------------------------------- things to choose between
async def things_to_choose():
    print("a project named like markup is listed as written")
    async with board() as (app, pilot):
        await pilot.press("p")
        if await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
            drawn_list = drawn_options(app.screen.query_one(OptionList))
            check("every project's name is drawn in full",
                  [n for n in PROJ.values()
                   if not any(n in d for d in drawn_list)], [])
            check("and no option is left holding an unclosed tag",
                  [d for d in drawn_list if "[/" in d], [])
        else:
            check("the picker opens", False, True)

    print("a label holding a bracket is listed as written")
    async with board(note=NOTE) as (app, pilot):
        await pilot.press("o")
        if await until(pilot, lambda: isinstance(app.screen, LinkPicker)):
            drawn_list = drawn_options(app.screen.query_one(OptionList))
            offered = app.screen.choices
            check("more than one address is offered", len(offered) > 1, True)
            check("each label is drawn in full",
                  [shown for shown, _url in offered
                   if not any(shown in d for d in drawn_list)], [])
        else:
            check("the picker opens", False, True)

    print("a label shaped like a tag is listed as written")
    # Handed to the picker directly, because the board's own readers cannot
    # produce such a label: an address stops at the `]`, so a label taken
    # from one can hold a `[` but never a whole tag-shaped run -- and a lone
    # bracket draws correctly whether it is escaped or not.  The check above
    # therefore cannot fail, and this one can: the picker is a dialogue that
    # draws what it is given, and what it is given is not always an address.
    async with board() as (app, pilot):
        app.push_screen(LinkPicker("choose", [("[dim]a build log", "https://e.invalid/x"),
                                              ("plain", "https://e.invalid/y")]))
        opened = await until(pilot, lambda: isinstance(app.screen, LinkPicker))
        check("the picker opens", opened, True)
        if opened:
            drawn_list = drawn_options(app.screen.query_one(OptionList))
            check("the tag-shaped label is drawn as its characters",
                  [d for d in drawn_list if d.endswith("a build log")
                   and "[dim]" in d], drawn_list[:1])


# ----------------------------------------------------- shapes the escape missed
def shaped(note=None):
    """One task per shape, titled with it, each holding `note` or its shape."""
    tasks = [mk(f"T-shape-{i:02}", shape, D) for i, shape in enumerate(SHAPES)]
    for task, shape in zip(tasks, SHAPES):
        task.raw["note"] = singularity.note_document(note if note is not None else shape)
    return tasks

async def stays_open(site, body):
    """Run one site's checks; a failure to draw is reported, not raised.

    The failure this suite was extended for ended the session, and a part
    that raised would say only that something did -- not which site, and not
    what the other sites made of the same shapes.
    """
    try:
        await body()
    except Exception as error:
        check(f"{site}: the board stays open",
              f"{type(error).__name__}: {str(error)[:90]}", None)

async def select(app, pilot, i):
    from textual.widgets import DataTable
    app.query_one(DataTable).move_cursor(row=i)
    await settle(pilot, 4)

async def shapes_in_the_detail_and_focus():
    print("the detail area and the focus card draw every shape as written")
    async def body():
        async with board(tasks=shaped()) as (app, pilot):
            for i in range(len(app.tasks)):
                await select(app, pilot, i)
                task = app.tasks[i]
                check(f"the detail area shows {task.note_text!r}",
                      task.note_text in drawn(app.query_one("#detail")), True)
                await pilot.press("enter")
                await until(pilot, lambda: bool(app.screen.query("#focus-title")))
                check(f"the focus card's title is {task.display_title!r}",
                      drawn(app.screen.query_one("#focus-title")), task.display_title)
                check("and its note is the note as written",
                      task.note_text in drawn(app.screen.query_one("#focus-note")), True)
                await pilot.press("escape")
                await until(pilot, lambda: not app.screen.query("#focus-title"))
    await stays_open("detail and focus", body)

async def shapes_in_the_status_line():
    print("the status line draws every shape as written")
    async def body():
        async with board() as (app, pilot):
            for shape in SHAPES:
                for error in (False, True):
                    said = f"moved “{shape}” to tomorrow"
                    app.set_status(said, error)
                    await settle(pilot, 3)
                    check(f"{'an error' if error else 'a message'} quoting {shape!r}",
                          drawn(app.query_one("#status")), said)
    await stays_open("status line", body)

async def shapes_in_the_prompts():
    for key, kind, name in [("d", DatePicker, "the date picker"),
                            ("p", ProjectPicker, "the project picker"),
                            ("n", NoteInput, "the note editor"),
                            ("backspace", Confirm, "the delete confirmation"),
                            ("o", LinkPicker, "the link picker")]:
        print(f"{name} shows every shape of title as written")
        async def body():
            async with board(tasks=shaped(note=NOTE)) as (app, pilot):
                for i in range(len(app.tasks)):
                    await select(app, pilot, i)
                    title = app.tasks[i].display_title
                    await pilot.press(key)
                    if not await until(pilot, lambda: isinstance(app.screen, kind)):
                        check(f"{name} opens on {title!r}", False, True)
                        continue
                    check(f"{name} names {title!r}", title in prompt_text(app), True)
                    await pilot.press("escape")
                    await until(pilot, lambda: not isinstance(app.screen, kind))
        await stays_open(name, body)

async def shapes_among_things_to_choose():
    print("a project named in every shape is listed as written")
    async def body():
        names = {f"P-shape-{i:02}": shape for i, shape in enumerate(SHAPES)}
        async with board(projects=names) as (app, pilot):
            await pilot.press("p")
            if not await until(pilot, lambda: isinstance(app.screen, ProjectPicker)):
                check("the picker opens", False, True)
                return
            drawn_list = drawn_options(app.screen.query_one(OptionList))
            check("every name is drawn in full",
                  [n for n in names.values() if not any(n in d for d in drawn_list)], [])
    await stays_open("project picker options", body)

async def shapes_searched_for():
    print("the bar names a search term of every shape as typed")
    async def body():
        from textual.widgets import Input
        async with board() as (app, pilot):
            for shape in SHAPES:
                await pilot.press("slash")
                await settle(pilot)
                app.screen.query_one(Input).value = shape
                await pilot.press("enter")
                await settle(pilot)
                check(f"the bar names {shape!r}",
                      f'search "{shape}"' in drawn(app.query_one("#daybar")), True)
    await stays_open("search bar", body)

# ------------------------------------------------------------------- the rows
def cell(value):
    """A row cell as the table draws it: a string is parsed, text is not."""
    from textual.widgets._data_table import default_cell_formatter
    return default_cell_formatter(value)

def cut(text, width):
    """What a column of `width` shows of `text`, by the board's own rule."""
    from rich.text import Text
    shown = Text(text)
    if len(shown) > width:
        shown.truncate(width, overflow="ellipsis")
    return shown.plain

def styles(text):
    """Every style a cell carries, its own and its spans', as one string."""
    return " ".join([str(text.style)] + [str(span.style) for span in text.spans])

async def shapes_in_the_rows():
    print("every kind of row draws every shape as written")
    import board as B
    from board import (MAIL_MARK, MAIL_SENDER, MAIL_COUNT, MAIL_WHEN, MAIL_DONE,
                      TRACKER_MARK, TRACKER_PROJECT, TRACKER_STATE,
                      EVENT_MARK, EVENT_CALENDAR, EVENT_ENDS, EVENT_MINUTES)
    def other(tid, title, **marks):
        return singularity.Task({"id": tid, "title": title, "checked": 0,
                                 "deferred": False, "useTime": False, **marks})
    names = {f"P-shape-{i:02}": shape for i, shape in enumerate(SHAPES)}
    async with board(projects=names) as (app, pilot):
        drawn_board = app.board()
        drawn_board.projects = names
        wide, narrow = drawn_board.title_width, B._PROJECT_WIDTH
        for i, shape in enumerate(SHAPES):
            pid = f"P-shape-{i:02}"
            row = [cell(c) for c in drawn_board.row_for(mk("T-r", shape, D, project=pid))]
            check(f"a task titled {shape!r}", row[3].plain, cut(shape, wide))
            check("  and its project's name", row[4].plain, cut(shape, narrow))
            done = [cell(c) for c in drawn_board.row_for(mk("T-d", shape, D, checked=1))]
            check("  finished, still as written", done[3].plain, cut(shape, wide))
            check("  and struck", "strike" in styles(done[3]), True)
            mail = [cell(c) for c in drawn_board.row_for(other(
                "mail:r", shape, **{MAIL_MARK: True, MAIL_SENDER: shape,
                                    MAIL_WHEN: 0, MAIL_COUNT: 2}))]
            check("  a mail subject, with its count", mail[3].plain, cut(f"{shape} (2)", wide))
            check("  and its sender", mail[4].plain, cut(B._mail_who(shape), narrow))
            gone = [cell(c) for c in drawn_board.row_for(other(
                "mail:d", shape, **{MAIL_MARK: True, MAIL_SENDER: "x@e.invalid",
                                    MAIL_WHEN: 0, MAIL_DONE: True}))]
            check("  a finished mail subject", gone[3].plain, cut(shape, wide))
            check("  and struck", "strike" in styles(gone[3]), True)
            issue = [cell(c) for c in drawn_board.row_for(other(
                "yt:r", shape, **{TRACKER_MARK: True, TRACKER_PROJECT: shape,
                                  TRACKER_STATE: "Open"}))]
            check("  an issue's title", issue[3].plain, cut(shape, wide))
            check("  and its project", issue[4].plain, cut(shape, narrow))
            event = [cell(c) for c in drawn_board.row_for(other(
                "cal:r", shape, **{EVENT_MARK: True, EVENT_CALENDAR: shape,
                                   EVENT_ENDS: 0, EVENT_MINUTES: 600}))]
            check("  an event that is over", event[3].plain, cut(shape, wide))
            check("  and dimmed", "dim" in styles(event[3]), True)
            check("  and its calendar", event[4].plain, cut(shape, narrow))
        bold = [cell(c) for c in drawn_board.row_for(mk("T-b", "[b]one[/b]", D))]
        check("a title naming the board's styling makes nothing bold",
              "bold" in styles(bold[3]), False)
        linked = mk("T-l", '<a href="https://e.invalid/x">[A] log</a> after', D)
        row = [cell(c) for c in drawn_board.row_for(linked)]
        check("a linked title reads as its words", row[3].plain, "[A] log after")
        check("  and the link is still on them",
              any("e.invalid/x" in str(s.style) and row[3].plain[s.start:s.end] == "[A] log"
                  for s in row[3].spans), True)


# -------------------------------------------------------------- the guard
def escapes_imported(path):
    """Every `escape` the file imports from a markup module, as `module.name`."""
    import ast
    found = []
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if isinstance(node, ast.ImportFrom) and node.module in ("textual.markup", "rich.markup"):
            found += [f"{node.module}.{a.name}" for a in node.names if a.name == "escape"]
    return found

async def nothing_escapes():
    print("the board draws foreign text as text, so nothing imports escape")
    # Escaping is what failed: it guards the brackets one parser reads as a
    # tag, and the board is drawn by two.  Once nothing escapes, the next
    # site to reach for it is a site about to be written the old way.
    for name in ("main.py", "board.py"):
        check(f"{name} imports no markup escape",
              escapes_imported(_os.path.join(_REPO, name)), [])


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_key_bar,
    the_status_line,
    the_prompts,
    things_to_choose,
    shapes_in_the_detail_and_focus,
    shapes_in_the_status_line,
    shapes_in_the_prompts,
    shapes_among_things_to_choose,
    shapes_searched_for,
    shapes_in_the_rows,
    nothing_escapes,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
