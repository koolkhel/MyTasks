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
from datetime import datetime, timedelta, time as time_of_day
import main as M, tracker, ical, mail
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
    # What the program says goes nowhere it could be seen from here.  The
    # spec puts the weight on the session rather than the streams -- a child
    # can open the terminal directly and bypass every stream it inherited --
    # so these say what the streams are for: nothing the program writes may
    # reach the view.
    chk("nothing the started program writes can reach the board",
        all(f"{s}=subprocess.DEVNULL" in launch for s in ("stdout", "stderr")),
        launch[-200:])
    # Its input is the board's to give, and never the terminal.  Either it
    # gets nothing, or it gets exactly the text a caller handed over -- down
    # a pipe, which is closed so the program can finish.
    chk("its input is the board's to give, and is never the terminal",
        "stdin=subprocess.PIPE if feed is not None else subprocess.DEVNULL"
        in launch, launch[-300:])
    chk("and what is fed is closed, so the program can end",
        "stdin.write(feed" in launch and "stdin.close()" in launch,
        launch[-300:])
    chk("no stream is left to be inherited",
        launch.count("stdin=") == 1 and launch.count("stdout=") == 1
        and launch.count("stderr=") == 1, launch[-200:])
    chk("and it hands over the list it was given, unformatted",
        "Popen(\n            argv," in launch and "f\"" not in launch
        and "%" not in launch and ".join(" not in launch, launch[-260:])


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


async def open_card(pilot, app, row_id, n=30):
    """Put the cursor on a row and open its card."""
    await select(pilot, app, row_id)
    await pilot.press("enter")
    for _ in range(n):
        await pilot.pause()
        if card(app) is not None:
            return True
    return False


@contextmanager
def calendar_showing(title="a meeting"):
    """Put one event on today, and take it away again.

    The fetch is replaced rather than a calendar read: this machine has no
    grant to read one, and a suite that needed it would pass or fail by whose
    machine ran it.
    """
    saved = ical.fetch
    at = datetime.combine(TODAY, time_of_day(9, 0))
    ical.fetch = lambda cfg, day: [ical.Event(
        title=title, account="Me", calendar="c", start=at,
        end=at + timedelta(hours=1), all_day=False)]
    try:
        yield
    finally:
        ical.fetch = saved


def a_thread(subject="a thread nobody wrote", ident="m1"):
    when = datetime.combine(TODAY, time_of_day(8, 0)).astimezone(TZ)
    return mail.Thread((mail.Message(
        sender="s@example.invalid", subject=subject, when=when, ident=ident,
        answers=None, body="", text=subject, folder="Feed", key="k1"),))


def mixed(calendar=False, threads=()):
    """A board carrying a row of more than one kind."""
    app = build([issue("AAA-1", versions=("1.2",))],
                tasks=[mk("T-1", "a task of my own", TODAY)])
    app.calendar_config = ical.Config(work="W", personal=("Me",)) if calendar else None
    app.mail_threads = list(threads)
    return app


async def t_counts_on_any_row():
    print("3.5 every card counts, whatever row it was opened on")
    with calendar_showing():
        app = mixed(calendar=True, threads=[a_thread()])
        async with app.run_test() as pilot:
            await settle(pilot, app)
            event = next((t.id for t in app.tasks if app.is_event(t)), None)
            chk("the day carries an event to open a card on", event is not None)
            with clock(datetime(2099, 3, 4, 14, 3, tzinfo=TZ)):
                for what, row in (("a task the board manages", "T-1"),
                                  ("a tracker issue", "yt:AAA-1"),
                                  ("a calendar event", event)):
                    chk(f"the card opens on {what}",
                        row is not None and await open_card(pilot, app, row))
                    line = since_line(app)
                    chk(f"and counts from the moment it opened -- {what}",
                        line == "since 14:03  ·  0m", repr(line))
                    chk(f"the card closes again -- {what}",
                        await close_card(pilot, app))
                # Mail belongs to the inbox, which is where its row is drawn.
                await pilot.press("i")
                await settle(pilot, app)
                thread_row = next((t.id for t in app.tasks if app.is_mail(t)), None)
                chk("the inbox carries a mail row", thread_row is not None)
                chk("the card opens on a mail thread",
                    thread_row is not None and await open_card(pilot, app, thread_row))
                line = since_line(app)
                chk("and counts there too, no row exempt",
                    line == "since 14:03  ·  0m", repr(line))
                await close_card(pilot, app)


async def t_coming_back_starts_again():
    print("3.6 coming back to a card starts the count again")
    app = mixed()
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 14, 0, tzinfo=TZ)) as state:
            chk("the card opens", await open_card(pilot, app, "T-1"))
            line = since_line(app)
            chk("and starts at nothing", line == "since 14:00  ·  0m", repr(line))
            state["now"] = datetime(2099, 3, 4, 14, 20, tzinfo=TZ)
            # Drawn when the card was built, so it reads the old minute until
            # the card's own timer redraws it.  That is what is called here.
            card(app).keep_up()
            await pilot.pause()
            line = since_line(app)
            chk("twenty minutes later the open card says so",
                line == "since 14:00  ·  20m", repr(line))
            chk("the card closes", await close_card(pilot, app))
            state["now"] = datetime(2099, 3, 4, 14, 25, tzinfo=TZ)
            chk("the card opens again", await open_card(pilot, app, "T-1"))
            line = since_line(app)
            chk("and counts from the second opening, not the first",
                line == "since 14:25  ·  0m", repr(line))
            await close_card(pilot, app)


async def t_workspace_counts_like_the_rest():
    print("3.7 the key that starts a workspace counts like any other")
    app = build([issue("AAA-1", versions=("1.2",))])
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 14, 3, tzinfo=TZ)):
            opened, _prefilled, started = await start(pilot, app, "yt:AAA-1")
            chk("the prompt was answered and the program started",
                opened and len(started) == 1, repr(started))
            for _ in range(40):
                await pilot.pause()
                if card(app) is not None:
                    break
            by_key = since_line(app)
            chk("the card it opens counts from that moment",
                by_key == "since 14:03  ·  0m", repr(by_key))
            chk("the card closes", await close_card(pilot, app))
            chk("the same row opens by hand",
                await open_card(pilot, app, "yt:AAA-1"))
            by_hand = since_line(app)
            chk("and says exactly what the other key's card said",
                by_hand == by_key, f"{by_hand!r} vs {by_key!r}")
            await close_card(pilot, app)


async def t_nothing_is_added_up():
    print("3.8 nothing is carried from one card to the next")
    app = mixed()
    async with app.run_test() as pilot:
        await settle(pilot, app)
        with clock(datetime(2099, 3, 4, 9, 0, tzinfo=TZ)) as state:
            seen = []
            for hour, minute in ((9, 0), (9, 30), (9, 55)):
                state["now"] = datetime(2099, 3, 4, hour, minute, tzinfo=TZ)
                chk(f"the card opens at {hour:02d}:{minute:02d}",
                    await open_card(pilot, app, "T-1"))
                seen.append(since_line(app))
                chk(f"and closes again at {hour:02d}:{minute:02d}",
                    await close_card(pilot, app))
            chk("each opening counts from itself alone",
                seen == ["since 09:00  ·  0m", "since 09:30  ·  0m",
                         "since 09:55  ·  0m"], repr(seen))
        held = vars(app)
        for name in ("working", "worked", "since", "total"):
            chk(f"the board holds no attribute called {name!r}",
                name not in held)
        chk("and the only working- name left is the working hours",
            [k for k in held if k.startswith("working")] == ["working_window"],
            repr([k for k in held if k.startswith("working")]))


t_reader_absent()
t_no_shell()
for fn in (t_row_carries, t_refusals, t_command_line, t_leaving,
           t_shell_characters, t_cannot_start, t_writes_nothing, t_named,
           t_counts_on_any_row, t_coming_back_starts_again,
           t_workspace_counts_like_the_rest, t_nothing_is_added_up):
    asyncio.run(fn())

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
