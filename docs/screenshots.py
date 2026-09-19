"""Take the README's pictures from the board itself.

    .venv/bin/python docs/screenshots.py               # the SVG pictures
    .venv/bin/python docs/screenshots.py --crt today   # one from cool-retro-term
    .venv/bin/python docs/screenshots.py --serve today # hold a board in this terminal

Not mock-ups: each one is a real board, driven through Textual's own test
pilot and saved with `save_screenshot`, then rendered to PNG because GitHub
does not show an SVG in a README.

Nothing real is read.  The store is the suites' stub, the calendar and the
tracker are replaced, and every task, event, issue and message below is
invented -- which is the point, since these pictures are published.  That is
also why this reaches into `tests/`: the stub is what makes the guarantee.

To show a new feature, add a board to `SHOTS` at the foot of the file.  Put
the cursor on a row that has something to say, or the pane under the list
comes out empty.

The first picture in the README is the board where it lives: cool-retro-term
with the IBM 3278 profile.  No rendering of an SVG can draw phosphor, so that
one is a capture of a real window -- opened by `--crt` for the purpose,
running the same invented board through `--serve`, told apart from any other
window of that terminal by having appeared (the board names its own tab, so
two of its windows share a title), captured with `screencapture`, and
closed.  It is a frame of an animation and never the same twice.  Capturing
needs the terminal running this to be allowed Screen Recording, which no
command can grant; where it is refused this says so and writes nothing.

A served board can reach nothing real, however it is driven: no token is
read, no client is built, every source is a stub.  Keys pressed in that
window change the stub and nothing else.
"""
import argparse
import asyncio
import datetime as dt
import os
import shutil
import subprocess
import sys
import time

# Where this file is, and therefore where the board and its suites are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
DOCS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(DOCS)
sys.path.insert(0, os.path.join(REPO, "tests"))
sys.path.insert(0, REPO)

from harness import StubClient, iso_z, local_tz, mk        # noqa: E402
import ical                                                # noqa: E402
import mail                                                # noqa: E402
import tracker                                             # noqa: E402
from main import TaskApp                                   # noqa: E402
import singularity                                         # noqa: E402
from singularity import (ARCHIVE, Bucket, CANCELLED,     # noqa: E402
                         CHECKED)
from textual.widgets import DataTable                      # noqa: E402

TZ = local_tz()
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)

#: A tag and a project of the board's own, so the star and the project column
#: have something to show.
GREEN = "A-green"
SALES = "P-sales"
CAL = ical.Config(work="Dunder Mifflin", personal=("Michael",))
TRACK = tracker.Config(base_url="https://tickets.dundermifflin.invalid",
                       token="not-a-token", assignee="mscott",
                       projects=("DM",), states=("In progress",))


# ------------------------------------------------------------ the invented data

def task(tid, title, *, hour=None, checked=0, green=False, project=None,
         note=None, day=TODAY):
    t = mk(tid, title, day, checked=checked, timed=hour is not None,
           project=project)
    if hour is not None:
        t.raw["start"] = iso_z(dt.datetime.combine(day, dt.time(*hour), tzinfo=TZ))
    elif day is None:
        t.raw["start"] = None
    if green:
        t.raw["tags"] = [GREEN]
    if note:
        t.raw["note"] = note
    return t


def event(title, hh, mm=0, minutes=60):
    start = dt.datetime.combine(TODAY, dt.time(hh, mm))
    return ical.Event(title=title, account="Michael", calendar="Work",
                      start=start, end=start + dt.timedelta(minutes=minutes),
                      all_day=False)


#: Where the tracker lists each priority, most urgent first -- the position
#: the board orders the block by.  The stub hands the issues over already in
#: that order, as `tracker.parse` would.
RANK = {"Show-stopper": 0, "Critical": 1, "Major": 2, "Normal": 3, "Minor": 4}


def issue(key, summary, priority="Major", versions=(), description=""):
    return tracker.Issue(key=key, summary=summary, project="DM",
                         state="In progress", assignee="mscott",
                         base_url="https://tickets.dundermifflin.invalid",
                         priority=priority, priority_value=priority,
                         priority_rank=RANK[priority],
                         versions=versions, description=description)


def thread(subject, sender, *bodies, hours_ago=2):
    """One mail thread, newest last, with an identity that does not wander."""
    messages = []
    for i, body in enumerate(bodies):
        when = NOW - dt.timedelta(hours=hours_ago - i)
        messages.append(mail.Message(
            sender=sender, subject=subject, when=when,
            ident=f"<{subject.split()[0].strip(':').lower()}-{i}@invalid>",
            answers=None, body=body, text=f"{subject} {body}"))
    return mail.Thread(messages=tuple(messages))


TODAY_TASKS = [
    task("t1", "Plan the Dundies", hour=(9, 30), green=True, project=SALES,
         note="Best Ping-Pong Award needs a new trophy.\n"
              "Do NOT let Kevin near the punch again."),
    task("t2", "Order more paper — Scranton is down to one pallet",
         hour=(11, 0), project=SALES),
    task("t3", "Sign Dwight's Assistant Regional Manager form", green=True),
    task("t4", "Beet farm delivery window", hour=(14, 0)),
    task("t5", "Return Kevin's chili pot", checked=CHECKED),
    task("t6", "Ice cream social in the annexe", checked=CANCELLED),
    task("t7", "Call Bob Vance about the fridge", hour=(16, 30), project=SALES),
    task("t8", "Send Toby's paperwork back to Corporate",
         day=TODAY - dt.timedelta(days=3)),
]

INBOX_TASKS = [
    task("i1", "Decide about the Michael Scott Paper Company", day=None),
    task("i2", "Find a new supplier for the second-floor copier", day=None),
    task("i3", "Ask Creed what he actually does here", day=None),
]

def finished(tid, title, days_ago, checked=CHECKED, project=None, hour=9):
    """A task the store archived `days_ago` days back."""
    t = task(tid, title, checked=checked, project=project,
             day=TODAY - dt.timedelta(days=days_ago))
    when = dt.datetime.combine(TODAY - dt.timedelta(days=days_ago),
                               dt.time(hour, 0), tzinfo=TZ)
    t.raw["journalDate"] = iso_z(when)
    return t


ARCHIVE_TASKS = [
    finished("a1", "Dundies venue confirmed — Chili's, again", 1, project=SALES),
    finished("a2", "Quarterly paper order signed off", 1, project=SALES, hour=16),
    finished("a3", "Fire drill debrief with Dwight", 2),
    finished("a4", "Branch closure rumour — ask Corporate", 3, checked=CANCELLED),
    finished("a5", "Sales call — Vance Refrigeration", 4, project=SALES),
    finished("a6", "Casino Night: hire the tables", 11),
    finished("a7", "Replace the second-floor copier", 18, project=SALES),
    finished("a8", "Health plan choices circulated", 25),
    finished("a9", "Beet farm invoice, second attempt", 40, checked=CANCELLED),
    finished("a10", "Scranton branch: annual review", 63),
    finished("a11", "Print a new Dundie for Best Ping-Pong", 96),
    finished("a12", "Warehouse safety training booked", 140),
]

EVENTS = [
    event("Conference room: Dundies planning", 10, 0, minutes=45),
    event("Sales call — Vance Refrigeration", 13, 30, minutes=30),
]

# Most urgent first, as the board orders the block: the critical issue has the
# larger key and still leads.
ISSUES = [
    issue("DM-214", "Copier jams on double-sided printing", priority="Critical",
          versions=("3.2", "3.3"),
          description="Every duplex job after about forty pages stops with a tray-2 "
                      "jam that is not there.\n\nReproduced on the second-floor "
                      "copier only; the annexe one is fine. Kevin says it started "
                      "after the chili incident, which is not impossible."),
    issue("DM-198", "Warehouse scanner drops the last digit", priority="Minor",
          versions=("3.3",),
          description="Barcodes ending in 0 scan as the code without the 0."),
]

THREADS = [
    thread("Re: paper shipment delayed", "bvance@vancerefrigeration.invalid",
           "The pallet is on the Tuesday truck instead.",
           "Confirmed for Tuesday.", hours_ago=2),
    thread("Fire safety training — mandatory", "toby@dundermifflin.invalid",
           "Thirty minutes. Please actually attend this one.", hours_ago=5),
    thread("Your expense report needs a receipt", "angela@dundermifflin.invalid",
           "The one for the ice cream.", hours_ago=9),
]


# ------------------------------------------------------------------ the picture

def stub(position, tasks, *, events=(), issues=()):
    app = TaskApp(position if isinstance(position, dt.date) else TODAY)
    app.client = StubClient(list(tasks), reference=NOW)
    app.client.project_names = lambda **kw: {SALES: "Sales"}
    app.client.green = GREEN
    app.client.tag_titles[GREEN] = "Today"
    app.green_tag = GREEN
    app.calendar_config = CAL if events else None
    app.tracker_config = TRACK if issues else None
    return app


def replace_sources(events=(), issues=()):
    """Answer the calendar and the tracker from the invented lists.

    Returns what to put back.  Both are module attributes the board reads at
    fetch time, so replacing them here is what keeps a real calendar and a
    real tracker out of every picture.
    """
    saved = (ical.fetch, tracker.fetch)
    ical.fetch = lambda cfg, day: list(events)
    tracker.fetch = lambda cfg, **kw: list(issues)
    return saved


def restore_sources(saved):
    ical.fetch, tracker.fetch = saved


def settled(app, position):
    """Whether the shown view's own rows have arrived."""
    if position is ARCHIVE:
        return app.archive is not None and not app.archive_loading
    return bool(app._fetched)


async def dress(app, *, position=TODAY, events=(), issues=(), threads=(),
                marks=(), cursor=None, timeout=15.0):
    """Give a started board the shot's view, sources, marks and cursor.

    One function for both ways of drawing a board -- under the test pilot for
    the SVG pictures, and in a real terminal for the CRT one -- so that the
    served board cannot drift from the pictured one.  Waits for the view's
    own fetch rather than sleeping a fixed time: a wait that is too short
    dresses a board with no rows on it, and one that is too long is a wait
    for nothing.
    """
    async def until(done):
        deadline = time.monotonic() + timeout
        while not done() and time.monotonic() < deadline:
            await asyncio.sleep(0.05)

    await until(lambda: settled(app, app.position))
    if not isinstance(position, dt.date):
        app.position = position
        app._fetched = False
        app.load()
        await until(lambda: settled(app, position))
    app.mail_threads = list(threads)
    if events:
        app.events, app.events_day = list(events), app.position
    for ident in marks:
        app.marked.append(ident)
        app._marked_rows[ident] = app.client.store[ident]
    app.repaint()
    await asyncio.sleep(0.2)
    if cursor is not None:
        table = app.query_one(DataTable)
        at = next(i for i, t in enumerate(app.tasks) if cursor in t.display_title)
        table.move_cursor(row=at)
        await asyncio.sleep(0.3)


def shot_named(name):
    shot = next((s for s in SHOTS if s["name"] == name), None)
    if shot is None:
        raise SystemExit(f"no shot named {name!r}; there are: "
                         + ", ".join(s["name"] for s in SHOTS))
    return shot


def prepared(shot):
    """The shot's board with its sources replaced, and what `dress` needs."""
    make = dict(shot)
    make.pop("name")
    app = make.pop("board")()
    make.pop("size", None)
    saved = replace_sources(make.get("events", ()), make.get("issues", ()))
    return app, make, saved


async def shoot(name, app, *, size=(104, 32), **how):
    """One SVG, through the test pilot."""
    saved = replace_sources(how.get("events", ()), how.get("issues", ()))
    try:
        async with app.run_test(size=size):
            await dress(app, **how)
            svg = os.path.join(DOCS, name + ".svg")
            app.save_screenshot(svg)
            return svg
    finally:
        restore_sources(saved)


def serve(name, ready=None):
    """Run one invented board in this terminal and hold it there.

    What `--crt` opens inside cool-retro-term.  The board is dressed once
    its own fetch has settled, and the ready file -- where one is asked
    for -- is written only after the cursor has landed, so that a capture
    taken on it shows the right row.  `q` leaves, as on any board.
    """
    app, how, _saved = prepared(shot_named(name))

    async def when_ready(_pilot):
        # Textual runs this once the app is up and keeps the app running
        # when it returns; the board stays on screen until `q`.
        await dress(app, **how)
        if ready:
            with open(ready, "w", encoding="utf-8") as fh:
                fh.write(name)

    app.run(auto_pilot=when_ready)


CHROME = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
          "/Applications/Chromium.app/Contents/MacOS/Chromium")


def to_png(svg):
    """Render an SVG beside itself as a PNG, which is what GitHub shows.

    A browser rather than a converter: the picture is a page of styled text
    in a web font, and the renderers that do not run CSS make a poor job of
    it.  Where none is to be found the SVG is left and said so -- a wrong
    picture would be worse than a missing one.
    """
    png = svg[:-4] + ".png"
    width, height = 1287, 1000
    with open(svg, encoding="utf-8") as fh:
        head = fh.read(800)
    if 'viewBox="' in head:
        box = head.split('viewBox="', 1)[1].split('"', 1)[0].split()
        width, height = (int(float(box[2])), int(float(box[3])))
    browser = next((b for b in CHROME if os.path.exists(b)), None) \
        or shutil.which("chromium") or shutil.which("google-chrome")
    if browser is None:
        print(f"  no browser to render {os.path.basename(svg)}; the SVG is kept")
        return None
    subprocess.run([browser, "--headless", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--screenshot={png}",
                    f"--window-size={width},{height}", "file://" + svg],
                   capture_output=True, check=True)
    os.remove(svg)
    return png



# ------------------------------------------------------------- the CRT picture

CRT = "/Applications/cool-retro-term.app/Contents/MacOS/cool-retro-term"
PROFILE = "IBM 3278"
OWNER = "cool-retro-term"
SETTINGS_PATH = "System Settings > Privacy & Security > Screen & System Audio Recording"
def window_ids(owner=OWNER, listing=None):
    """The ids of the on-screen windows owned by `owner`, through CoreGraphics."""
    if listing is None:
        try:
            import Quartz
        except ImportError:
            raise SystemExit("the window list needs pyobjc-framework-Quartz; run\n"
                             "    .venv/bin/python -m pip install -r requirements.txt")
        listing = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
    return {int(w["kCGWindowNumber"]) for w in listing
            if str(w.get("kCGWindowOwnerName", "")) == owner}


def pick_new(before, after):
    """The one window that appeared, or None -- never a guess among several."""
    new = set(after) - set(before)
    return next(iter(new)) if len(new) == 1 else None


def capture(win_id, path, run=subprocess.run):
    """Capture one window; True where a picture was written.

    Refused recording leaves no file: `screencapture` says so on stderr and
    writes nothing, and this says nothing else -- a black picture written
    as if it were the board would be worse than none.
    """
    if os.path.exists(path):
        os.remove(path)
    run(["screencapture", "-x", "-o", f"-l{win_id}", path],
        capture_output=True, text=True, encoding="utf-8")
    return os.path.exists(path) and os.path.getsize(path) > 0


def crt(name, *, launch=subprocess.Popen, windows=window_ids, run=subprocess.run,
        exists=os.path.exists, sleep=time.sleep, timeout=30.0, out=print):
    """One picture of one invented board, in cool-retro-term.

    Every process this touches is a parameter, so a suite can drive the
    decisions with none of them real.  Returns the picture's path, or None
    having said why not.
    """
    if not exists(CRT):
        out(f"cool-retro-term is not at {CRT}; the SVG pictures need nothing new")
        return None
    shot_named(name)                                   # a bad name is said now
    ready = os.path.join(DOCS, f".ready-{name}")
    if os.path.exists(ready):
        os.remove(ready)
    before = windows()
    child = launch([CRT, "-p", PROFILE, "--workdir", REPO, "-T", f"MyTasks picture: {name}",
                    "-e", sys.executable, os.path.abspath(__file__),
                    "--serve", name, "--ready", ready])
    try:
        deadline = time.monotonic() + timeout
        while not exists(ready) and time.monotonic() < deadline:
            sleep(0.2)
        if not exists(ready):
            out(f"the served board did not come up within {timeout:.0f}s; nothing captured")
            return None
        win = None
        deadline = time.monotonic() + 5
        while win is None and time.monotonic() < deadline:
            win = pick_new(before, windows())
            if win is None:
                sleep(0.2)
        if win is None:
            out("could not tell the new cool-retro-term window from the others; nothing captured")
            return None
        # The window is cool-retro-term's own size, and stays so.  Every way
        # of making it larger was tried and is recorded in the change that
        # brought this: System Events reports a resize it never performs,
        # Qt's scale factor enlarges the glyphs and not the grid, the xterm
        # resize escape is dropped, and --fullscreen gives a window the size
        # of the display, not of the request.  A hand on the window's edge
        # is what changes the grid, and this script has no hands.
        sleep(1.0)                                     # let the phosphor settle
        path = os.path.join(DOCS, f"crt-{name}.png")
        if not capture(win, path, run=run):
            out(f"the screen could not be recorded, so no picture was written.\n"
                f"  Allow the terminal this runs in under {SETTINGS_PATH},\n"
                f"  then quit that terminal and start it again.")
            return None
        return path
    finally:
        try:
            child.terminate()
        except Exception:
            pass
        if os.path.exists(ready):
            os.remove(ready)


#: What the README shows.  Each entry is one board and where its cursor sits.
SHOTS = [
    dict(name="today",
         board=lambda: stub(TODAY, TODAY_TASKS, events=EVENTS, issues=ISSUES),
         position=TODAY, events=EVENTS, issues=ISSUES,
         marks=["t2", "t3"], cursor="Copier jams"),
    dict(name="inbox",
         board=lambda: stub(Bucket.INBOX, INBOX_TASKS),
         position=Bucket.INBOX, threads=THREADS,
         cursor="Fire safety training"),
    dict(name="archive",
         board=lambda: stub(ARCHIVE, ARCHIVE_TASKS),
         position=ARCHIVE, marks=["a1", "a2", "a3"],
         cursor="Casino Night"),
]


async def main_():
    for shot in SHOTS:
        make = dict(shot)
        name, app = make.pop("name"), make.pop("board")()
        svg = await shoot(name, app, **make)
        png = to_png(svg)
        print("  wrote", os.path.relpath(png or svg, REPO))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--serve", metavar="SHOT", help="run this invented board in the terminal and hold it")
    ap.add_argument("--ready", metavar="PATH", help="with --serve: write this file once the board is dressed")
    ap.add_argument("--crt", metavar="SHOT", help="capture this board in cool-retro-term (IBM 3278)")
    args = ap.parse_args(argv)
    if args.serve:
        serve(args.serve, ready=args.ready)
        return 0
    if args.crt:
        path = crt(args.crt)
        if path:
            print("  wrote", os.path.relpath(path, REPO))
        return 0 if path else 1
    asyncio.run(main_())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
