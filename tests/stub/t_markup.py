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
from harness import StubClient, mk, TZ
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

async def main_():
    for part in (the_key_bar, the_status_line, the_prompts, things_to_choose):
        await part()
    print(f"\n{sum(ok)}/{len(ok)} checks passed")
    sys.exit(0 if all(ok) else 1)

asyncio.run(main_())
