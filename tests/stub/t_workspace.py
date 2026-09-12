"""Starting a workspace from a tracker issue: what is run, and what is not.

Invented issue keys, invented project names, invented versions, and an
invented program that is never on any disk.  Nothing here starts a process:
the board's own launch method is replaced, and a check proves it is the only
way through.
"""
import sys, asyncio
from contextlib import contextmanager
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
# Kept by reference before the harness blanks it, so the absent case can still
# be asked of the real reader.
import singularity
_read_command = singularity.load_workspace_command
from harness import StubClient, mk, TZ
from datetime import datetime
import main as M, tracker, ical
from main import TaskApp, TaskInput, KeyBar
from textual.widgets import DataTable, Input

ok = []
def chk(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

WORK = "P-work-0001"
PROGRAM = "/nowhere/work-on"
TODAY = datetime.now(TZ).date()


def issue(key="AAA-1", versions=(), project="AAA"):
    return tracker.Issue(key=key, summary="a summary nobody wrote",
                         project=project, state="In progress", assignee="me",
                         base_url="https://tracker.invalid", versions=versions)


def build(issues=(), tasks=(), program=PROGRAM):
    """A board with these issues on it and this program configured."""
    app = TaskApp(TODAY)
    app.client = StubClient(list(tasks))
    app.work_project = WORK
    app.projects = {WORK: "Work"}
    app.workspace_command = program
    app.tracker_config = tracker.Config("https://tracker.invalid", "t", "me",
                                        ("AAA",), ("In progress",), "Fix versions")
    app.tracker_issues = list(issues)
    wanted = list(issues)
    def fake_load():
        app.tracker_issues = list(wanted)
        app.repaint()
    app.load_tracker = fake_load
    return app


def watching(app):
    """Replace the board's launch with one that records, and return the log."""
    started = []
    app.launch = lambda argv: started.append(list(argv))
    return started


def failing(app, exc):
    """Replace the board's launch with one that cannot start the program."""
    def boom(argv):
        raise exc
    app.launch = boom


def drawn(app, what="#status"):
    return app.query_one(what).visual.plain


async def settle(pilot, app, n=120):
    for _ in range(n):
        await pilot.pause()
        if not app._pending and not app._draining:
            return True
    return False


async def select(pilot, app, row_id):
    table = app.query_one(DataTable)
    index = next(i for i, t in enumerate(app.tasks) if t.id == row_id)
    table.move_cursor(row=index)
    await pilot.pause()
    return app._selected_id == row_id


async def prompt_open(pilot, app, n=40):
    for _ in range(n):
        await pilot.pause()
        if isinstance(app.screen, TaskInput):
            return True
    return False


async def t_row_carries():
    print("2.2 the row carries the issue's key, project and versions")
    app = build([issue("AAA-1", ("1.6-1", "1.7"))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t))
        chk("its key", row.raw.get(M.TRACKER_KEY) == "AAA-1",
            repr(row.raw.get(M.TRACKER_KEY)))
        chk("its project", row.raw.get(M.TRACKER_PROJECT) == "AAA")
        chk("its versions, in order",
            tuple(row.raw.get(M.TRACKER_VERSIONS)) == ("1.6-1", "1.7"),
            repr(row.raw.get(M.TRACKER_VERSIONS)))
        chk("the key is the issue's, not the row's id",
            row.id != row.raw.get(M.TRACKER_KEY), row.id)
    app = build([issue("AAA-2")])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t))
        chk("an issue with no version carries none",
            tuple(row.raw.get(M.TRACKER_VERSIONS)) == ())


def t_reader_absent():
    print("3.1 the configured program, on the absent case only")
    # python-dotenv finds the real `.env` by walking up from singularity.py,
    # so a check asserting on a configured path would pass or fail by whose
    # machine ran it.
    import tempfile
    kept = _os.environ.pop("WORKSPACE_COMMAND", None)
    empty = _os.path.join(tempfile.mkdtemp(prefix="workspace."), ".env")
    try:
        open(empty, "w").close()
        chk("no WORKSPACE_COMMAND means no program",
            _read_command(empty) is None, repr(_read_command(empty)))
    finally:
        if kept is not None:
            _os.environ["WORKSPACE_COMMAND"] = kept
    chk("and a board built under the harness has none",
        singularity.load_workspace_command() is None)


def t_no_shell():
    print("4.4 the board has no way to reach a shell")
    src = open(_os.path.join(_REPO, "main.py")).read()
    chk("shell=True appears nowhere", "shell=True" not in src)
    chk("os.system appears nowhere", "os.system" not in src)
    # Counted by what starts a process, not by the module's name: the name
    # also appears on every stream sent to nowhere, so counting it measured
    # the redirection rather than the starting.
    starters = ("Popen(", "subprocess.run(", "subprocess.call(",
                "subprocess.check_", "os.system", "os.popen", "os.exec",
                "os.spawn")
    chk("exactly one thing in the board starts a process",
        sum(src.count(s) for s in starters) == 1,
        str({s: src.count(s) for s in starters if src.count(s)}))
    launch = src.split("def launch(", 1)[1].split("\n    def ", 1)[0]
    chk("launch starts exactly one thing", launch.count("Popen") == 1)
    chk("the started program gets a session of its own",
        "start_new_session=True" in launch, launch[-200:])
    chk("in the same call that starts it, not somewhere else",
        launch.count("Popen(") == 1
        and "start_new_session=True" in launch.split("Popen(", 1)[1],
        launch.split("Popen(", 1)[-1][:200])
    chk("every stream of the started program goes nowhere",
        launch.count("subprocess.DEVNULL") == 3
        and all(f"{s}=subprocess.DEVNULL" in launch
                for s in ("stdin", "stdout", "stderr")),
        launch[-160:])
    chk("and hands it the list it was given, unformatted",
        "subprocess.Popen(argv" in launch and "f\"" not in launch
        and "%" not in launch and ".join(" not in launch, launch[-200:])


async def t_refusals():
    print("3.3 who may not start a workspace, and what is said")
    task = mk("T-plain", "an ordinary task", TODAY)
    app = build([issue("AAA-1", ("1.6-1",))], tasks=[task])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        started = watching(app)
        chk("an ordinary task is selected", await select(pilot, app, "T-plain"))
        await pilot.press("W")
        await pilot.pause()
        chk("a task starts nothing", not started, str(started))
        chk("and the board says why",
            "Only a tracker issue" in drawn(app), drawn(app))
    # A calendar row, which is not the board's either.  The events go on
    # after the first load, because the load is what sets the day they
    # belong to and would otherwise clear them.
    app = build([issue("AAA-1")])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        app.calendar_config = ical.Config(work="W", personal=("Me",))
        app.events = [ical.Event(
            title="an event nobody scheduled", account="Me", calendar="c",
            start=datetime.combine(TODAY, datetime.min.time()),
            end=datetime.combine(TODAY, datetime.min.time()),
            all_day=True)]
        app.events_day = app.position
        app.repaint()
        await pilot.pause()
        started = watching(app)
        event_row = next((t for t in app.tasks if app.is_event(t)), None)
        chk("a calendar row is on the board", event_row is not None,
            str([t.id for t in app.tasks]))
        if event_row is not None:
            await select(pilot, app, event_row.id)
            await pilot.press("W")
            await pilot.pause()
            chk("a calendar row starts nothing", not started, str(started))
            chk("and says the same thing",
                "Only a tracker issue" in drawn(app), drawn(app))
    # A tracker row with no program configured.
    app = build([issue("AAA-1", ("1.6-1",))], program=None)
    async with app.run_test() as pilot:
        await settle(pilot, app)
        started = watching(app)
        row = next(t for t in app.tasks if app.is_tracker(t))
        await select(pilot, app, row.id)
        await pilot.press("W")
        await pilot.pause()
        chk("no program configured starts nothing", not started, str(started))
        chk("and the board names the setting",
            "WORKSPACE_COMMAND" in drawn(app), drawn(app))
        chk("and does not ask for a version first",
            not isinstance(app.screen, TaskInput))


async def start(pilot, app, row_id, typed=None):
    """Press the key, answer the prompt, and give back what was started."""
    started = watching(app)
    await select(pilot, app, row_id)
    await pilot.press("W")
    opened = await prompt_open(pilot, app)
    prefilled = app.screen.query_one(Input).value if opened else None
    if opened:
        if typed is not None:
            app.screen.query_one(Input).value = typed
        await pilot.press("enter")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.screen, TaskInput):
                break
    await pilot.pause()
    return opened, prefilled, started


async def t_command_line():
    print("4.1 + 4.2 the prompt, and the command line it leads to")
    app = build([issue("AAA-1", ("1.6-1",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        opened, prefilled, started = await start(pilot, app, row)
        chk("the board asks which version", opened)
        chk("filled in with the issue's own", prefilled == "1.6-1", repr(prefilled))
        chk("and the program is run with exactly three named arguments",
            started == [[PROGRAM, "--key", "AAA-1",
                        "--project", "AAA", "--version", "1.6-1"]],
            str(started))
        chk("the board says it started one",
            "Starting a workspace" in drawn(app), drawn(app))
        # Read again after the detaching went in: what is started has to be
        # what it always was.  A check that only looked at the flag would not
        # notice the call itself breaking.
        chk("and what was handed over is still the whole command line",
            len(started) == 1 and started[0][0] == PROGRAM
            and len(started[0]) == 7, str(started))
    app = build([issue("AAA-2", ("1.6-1", "1.7", "2.0"))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        opened, prefilled, started = await start(pilot, app, row)
        chk("several versions propose the first", prefilled == "1.6-1", repr(prefilled))
        chk("and only the one confirmed is sent",
            started[0].count("--version") == 1 and started[0][-1] == "1.6-1",
            str(started))
    app = build([issue("AAA-3")])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        opened, prefilled, started = await start(pilot, app, row, typed="9.9")
        chk("an issue with no version asks all the same", opened)
        chk("with nothing filled in", prefilled == "", repr(prefilled))
        chk("and the typed version is what goes over",
            started == [[PROGRAM, "--key", "AAA-3",
                         "--project", "AAA", "--version", "9.9"]],
            str(started))
    app = build([issue("AAA-4", ("1.6-1",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        _, _, started = await start(pilot, app, row, typed="1.7")
        chk("a version the issue never names is sent instead of its own",
            started[0][-1] == "1.7", str(started))
        chk("nothing resembling a branch, a directory or a repository is sent",
            not any("/" in part or "release" in part.lower()
                    for part in started[0][1:]),
            str(started))


async def t_leaving():
    print("4.5 leaving the prompt starts nothing")
    app = build([issue("AAA-1", ("1.6-1",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        started = watching(app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        await select(pilot, app, row)
        await pilot.press("W")
        chk("the prompt is open", await prompt_open(pilot, app))
        await pilot.press("escape")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.screen, TaskInput):
                break
        chk("escaping starts nothing", not started, str(started))
    app = build([issue("AAA-1", ("1.6-1",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        _, _, started = await start(pilot, app, row, typed="")
        chk("confirming it empty starts nothing", not started, str(started))


async def t_shell_characters():
    print("4.3 a version a shell would read as syntax")
    nasty = "1.6-1; rm -rf /$(whoami)`id`"
    app = build([issue("AAA-1", (nasty,))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        _, prefilled, started = await start(pilot, app, row)
        chk("it is proposed unaltered", prefilled == nasty, repr(prefilled))
        chk("and arrives as one ordinary argument, unchanged",
            started == [[PROGRAM, "--key", "AAA-1",
                         "--project", "AAA", "--version", nasty]],
            str(started))


async def t_cannot_start():
    print("3.4 a program that cannot be started")
    said = {}
    for exc in (FileNotFoundError("no such file"), PermissionError("denied")):
        app = build([issue("AAA-1", ("1.6-1",))])
        async with app.run_test() as pilot:
            await settle(pilot, app)
            failing(app, exc)
            row = next(t for t in app.tasks if app.is_tracker(t)).id
            await select(pilot, app, row)
            await pilot.press("W")
            await prompt_open(pilot, app)
            await pilot.press("enter")
            for _ in range(40):
                await pilot.pause()
                if not isinstance(app.screen, TaskInput):
                    break
            await pilot.pause()
            line = drawn(app)
            said[type(exc).__name__] = line
            chk(f"{type(exc).__name__} is reported as not started",
                "Could not start" in line, line)
            chk("naming the exception", type(exc).__name__ in line, line)
    chk("and that is not what a started one says",
        all("Starting a workspace" not in line for line in said.values()),
        str(said))


async def t_writes_nothing():
    print("3.5 starting a workspace writes nothing")
    app = build([issue("AAA-1", ("1.6-1",))], tasks=[mk("T-a", "a task", TODAY)])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        before = list(app.client.calls)
        row = next(t for t in app.tasks if app.is_tracker(t)).id
        _, _, started = await start(pilot, app, row)
        chk("the program was started", len(started) == 1)
        chk("and the store was asked nothing more",
            app.client.calls == before, str(app.client.calls[len(before):]))
        chk("and the issue is as it was",
            app.tracker_issues[0].versions == ("1.6-1",))


async def t_named():
    print("5.1 the key is named where the keys are named")
    app = build([issue("AAA-1", ("1.6-1",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        entries = dict(app.query_one(KeyBar).entries())
        chk("the bar names it", entries.get("W") == "Workspace",
            repr(entries.get("W")))
        chk("the help describes it", "start a workspace" in M.Help.TEXT)
        chk("and names the setting it needs",
            "WORKSPACE_COMMAND" in M.Help.TEXT)


# ------------------------------------------- what is being worked on, and since when
@contextmanager
def clock(at):
    """Make the board believe it is `at`, and let a check move it.

    The same seam `t_elapsed` uses -- `main.datetime` rebound to a subclass
    whose `now` answers what the check says -- with the answer held in a dict
    so a check can advance it without leaving the board.

    Only the board's clock moves.  Nothing here waits for a real minute to
    pass: the card is asked to redraw, which is what its own timer does.
    """
    real = M.datetime
    state = {"now": at}

    class Frozen(real):
        @classmethod
        def now(cls, tz=None):
            value = state["now"]
            return value.astimezone(tz) if tz is not None else value

    M.datetime = Frozen
    try:
        yield state
    finally:
        M.datetime = real


def card(app):
    """The card on top, or None where the board is showing the list."""
    return app.screen if isinstance(app.screen, M.TaskFocus) else None


def since_line(app):
    """What the card says about time worked, or None where it says nothing."""
    top = card(app)
    if top is None:
        return None
    found = next(iter(top.query("#focus-since")), None)
    return None if found is None else str(found.visual.plain)


async def close_card(pilot, app, n=30):
    await pilot.press("escape")
    for _ in range(n):
        await pilot.pause()
        if card(app) is None:
            return True
    return False


async def t_working_remembered():
    print("3.1 what the board remembers")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        chk("nothing is being worked on to begin with", app.working is None,
            repr(app.working))
        await start(pilot, app, "yt:AAA-1")
        chk("after starting, one thing is", app.working is not None)
        chk("and it is the row the workspace was started for",
            app.working and app.working[0] == "yt:AAA-1", repr(app.working))

    print("3.2 the card opens on what was started")
    app = build([issue("AAA-1", versions=("1.2",)),
                 issue("AAA-2", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        await start(pilot, app, "yt:AAA-2")
        for _ in range(40):
            await pilot.pause()
            if card(app) is not None:
                break
        chk("the card is shown", card(app) is not None)
        chk("on the issue just started",
            card(app) is not None and card(app).shown_task.id == "yt:AAA-2",
            card(app) and card(app).shown_task.id)
        chk("and it says since when", since_line(app) is not None, since_line(app))
        chk("escape closes it", await close_card(pilot, app))
        chk("leaving the row it was opened from selected",
            app._selected_id == "yt:AAA-2", repr(app._selected_id))

    print("3.3 nothing started, nothing shown")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        await select(pilot, app, "yt:AAA-1")
        await pilot.press("W")
        await prompt_open(pilot, app)
        await pilot.press("escape")          # left the prompt
        for _ in range(30):
            await pilot.pause()
        chk("leaving the prompt opens no card", card(app) is None)
        chk("and nothing is being worked on", app.working is None, repr(app.working))

    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        # Driven by hand rather than through `start`, which installs a launcher
        # of its own and would undo the failure this case is about.
        failing(app, FileNotFoundError("no such program"))
        await select(pilot, app, "yt:AAA-1")
        await pilot.press("W")
        await prompt_open(pilot, app)
        await pilot.press("enter")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.screen, TaskInput):
                break
        for _ in range(20):
            await pilot.pause()
        chk("a program that cannot be started opens no card", card(app) is None)
        chk("and nothing is being worked on", app.working is None, repr(app.working))
        chk("and the board still says why",
            "Could not start" in drawn(app), drawn(app))


async def t_working_one_at_a_time():
    print("3.4 starting another replaces the first")
    app = build([issue("AAA-1", versions=("1.2",)), issue("AAA-2", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        await start(pilot, app, "yt:AAA-1")
        await close_card(pilot, app)
        first = app.working
        await start(pilot, app, "yt:AAA-2")
        await close_card(pilot, app)
        chk("the second is what is being worked on",
            app.working and app.working[0] == "yt:AAA-2", repr(app.working))
        chk("and it is not the first any more", app.working != first)
        await select(pilot, app, "yt:AAA-1")
        await pilot.press("enter")
        for _ in range(30):
            await pilot.pause()
            if card(app) is not None:
                break
        chk("the first issue's card says nothing about time worked",
            since_line(app) is None, since_line(app))
        await close_card(pilot, app)

    print("3.5 starting again restarts the count")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 9, 0, tzinfo=TZ)) as state:
            await start(pilot, app, "yt:AAA-1")
            await close_card(pilot, app)
            state["now"] = datetime(2099, 3, 4, 11, 30, tzinfo=TZ)
            await select(pilot, app, "yt:AAA-1")
            await pilot.press("enter")
            for _ in range(30):
                await pilot.pause()
                if card(app) is not None:
                    break
            chk("two and a half hours in, the card says so",
                since_line(app), "since 09:00  ·  2h 30m")
            await close_card(pilot, app)
            await start(pilot, app, "yt:AAA-1")
            for _ in range(40):
                await pilot.pause()
                if card(app) is not None:
                    break
            chk("starting again counts from the second start",
                since_line(app), "since 11:30  ·  0m")


async def t_working_shown():
    print("3.6 the line is the same whichever key opened the card")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 14, 3, tzinfo=TZ)) as state:
            await start(pilot, app, "yt:AAA-1")
            for _ in range(40):
                await pilot.pause()
                if card(app) is not None:
                    break
            state["now"] = datetime(2099, 3, 4, 14, 45, tzinfo=TZ)
            started_with = since_line(app)
            # Drawn when the card was built, so it still reads the old minute
            # until the card's own timer redraws it -- which is 3.8.
            card(app).keep_up()
            await pilot.pause()
            started_with = since_line(app)
            chk("starting work shows when it began and how long ago",
                started_with, "since 14:03  ·  42m")
            await close_card(pilot, app)
            await select(pilot, app, "yt:AAA-1")
            await pilot.press("enter")
            for _ in range(30):
                await pilot.pause()
                if card(app) is not None:
                    break
            chk("and the key that opens a card on any row says the same",
                since_line(app), started_with)
            await close_card(pilot, app)

    print("3.7 any other row says nothing")
    app = build([issue("AAA-1", versions=("1.2",))],
                tasks=[mk("T-1", "a task of my own", TODAY)])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        await start(pilot, app, "yt:AAA-1")
        await close_card(pilot, app)
        await select(pilot, app, "T-1")
        await pilot.press("enter")
        for _ in range(30):
            await pilot.pause()
            if card(app) is not None:
                break
        chk("a card on another row is shown", card(app) is not None)
        chk("with no line about time worked at all",
            since_line(app) is None, since_line(app))
        chk("not an empty one, and not a zero",
            card(app) is not None and not card(app).query("#focus-since"))
        await close_card(pilot, app)

    print("3.8 the count keeps up with the clock")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 8, 0, tzinfo=TZ)) as state:
            await start(pilot, app, "yt:AAA-1")
            for _ in range(40):
                await pilot.pause()
                if card(app) is not None:
                    break
            chk("the card carries a timer of its own",
                card(app) is not None and card(app)._worked_timer is not None)
            chk("reading nothing yet", since_line(app), "since 08:00  ·  0m")
            state["now"] = datetime(2099, 3, 4, 8, 7, tzinfo=TZ)
            card(app).keep_up()
            await pilot.pause()
            chk("and it advances with no key pressed",
                since_line(app), "since 08:00  ·  7m")
            shown = card(app)
            chk("the timer is given up when the card closes",
                await close_card(pilot, app) and shown._worked_timer is None)


t_reader_absent()
t_no_shell()
for fn in (t_row_carries, t_refusals, t_command_line, t_leaving,
           t_shell_characters, t_cannot_start, t_writes_nothing, t_named,
           t_working_remembered, t_working_one_at_a_time, t_working_shown):
    asyncio.run(fn())

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
