"""Take the README's pictures from the board itself.

    .venv/bin/python docs/screenshots.py

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
"""
import asyncio
import datetime as dt
import os
import shutil
import subprocess
import sys

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


def issue(key, summary, priority="Major", versions=(), description=""):
    return tracker.Issue(key=key, summary=summary, project="DM",
                         state="In progress", assignee="mscott",
                         base_url="https://tickets.dundermifflin.invalid",
                         priority=priority, priority_value=priority,
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

ISSUES = [
    issue("DM-214", "Copier jams on double-sided printing", versions=("3.2", "3.3"),
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


async def shoot(name, app, *, position=TODAY, events=(), issues=(), threads=(),
                marks=(), cursor=None, size=(104, 32)):
    saved_cal, saved_track = ical.fetch, tracker.fetch
    ical.fetch = lambda cfg, day: list(events)
    tracker.fetch = lambda cfg, **kw: list(issues)
    try:
        async with app.run_test(size=size) as pilot:
            for _ in range(14):
                await pilot.pause()
            if not isinstance(position, dt.date):
                app.position = position
                app.load()
                for _ in range(40):
                    await pilot.pause()
            app.mail_threads = list(threads)
            if events:
                app.events, app.events_day = list(events), app.position
            for ident in marks:
                app.marked.append(ident)
                app._marked_rows[ident] = app.client.store[ident]
            app.repaint()
            for _ in range(6):
                await pilot.pause()
            if cursor is not None:
                table = app.query_one(DataTable)
                at = next(i for i, t in enumerate(app.tasks)
                          if cursor in t.display_title)
                table.move_cursor(row=at)
                for _ in range(8):
                    await pilot.pause()
            svg = os.path.join(DOCS, name + ".svg")
            app.save_screenshot(svg)
            return svg
    finally:
        ical.fetch, tracker.fetch = saved_cal, saved_track


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


if __name__ == "__main__":
    asyncio.run(main_())
