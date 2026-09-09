"""Capture the board's tasks, with the calendar's rows set aside.

Event rows are counted and never recorded: an event id carries its title,
and nothing here needs it.
"""
import sys, asyncio, json, pathlib
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
from datetime import datetime, timedelta
import main as M
from main import TaskApp
from singularity import SingularityClient, Bucket
api = SingularityClient(); TZ = api.tz
TODAY = datetime.now(TZ).date()

async def view(position):
    app = TaskApp(position if not isinstance(position, Bucket) else TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        if isinstance(position, Bucket):
            app.position = position
        app.load()
        want_tracker = position == TODAY
        for _ in range(400):
            await pilot.pause()
            if app.query("#status"):
                st = str(app.query_one("#status").content)
                # the tracker lands after the day does, on its own worker
                if "task(s)" in st and ("tracked" in st or not want_tracker): break
        for _ in range(120): await pilot.pause()
        board = [t for t in app.tasks
                 if not (M.TaskApp.is_event(t) or M.TaskApp.is_mail(t))]
        rows = [app.row_for(t) for t in board]
        own = [t for t in board if not t.id.startswith(M.TRACKER_PREFIX)]
        events = sum(1 for t in app.tasks if M.TaskApp.is_event(t))
        mails = sum(1 for t in app.tasks if M.TaskApp.is_mail(t))
        return ([t.id for t in board], app.past_due, app.filed_out,
                str(app.query_one("#status").content),
                [r[-3] for r in rows],         # the When column, per row
                sum(1 for t in own if t.done or t.cancelled),
                [t.local_start(TZ).strftime("%H:%M") for t in own if t.timed],
                events, mails)

async def run():
    out = {}
    ids, pd, fo, st, when, done, timed, events, mails = await view(TODAY)
    own = [i for i in ids if not i.startswith(M.TRACKER_PREFIX)]
    out["today_ids"] = own
    out["today_all_ids"] = ids
    out["today_past_due"] = pd
    out["today_status"] = st
    out["today_when"] = when
    out["today_when_own"] = [w for i, w in zip(ids, when) if not i.startswith(M.TRACKER_PREFIX)]
    out["today_done"] = done
    out["today_timed_starts"] = timed
    out["today_event_count"] = events
    out["today_mail_count"] = mails
    for b in Bucket:
        ids, pd, fo, st, when, _d, _t, _e, _m = await view(b)
        out[f"{b.name}_ids"] = ids
        out[f"{b.name}_filed_out"] = fo
        out[f"{b.name}_when"] = when
    for d in (TODAY - timedelta(days=1), TODAY + timedelta(days=1)):
        ids, *_ = await view(d)
        out[f"day_{d}_ids"] = [i for i in ids if not i.startswith(M.TRACKER_PREFIX)]
    # Which day this describes.  A baseline of "today" is worthless the
    # moment the date rolls over, and silently so -- it goes on comparing
    # today's board against another day's and reporting the difference as a
    # regression.  Recorded so `baseline.py` can refuse instead.
    out["captured_day"] = str(TODAY)
    # Into the excluded directory by default: what this records is one
    # account on one day, and it must not reach the repository.
    where = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
        pathlib.Path(__file__).parent / "local" / "baseline.json")
    where.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(where, "w"), indent=1)
    print(f"captured: today {len(out['today_ids'])} own + "
          f"{len(out['today_all_ids']) - len(out['today_ids'])} tracked, "
          f"inbox {len(out['INBOX_ids'])}, someday {len(out['SOMEDAY_ids'])}")
    print("status:", out["today_status"])
    print("events set aside:", out["today_event_count"],
          "· mail set aside:", out["today_mail_count"])
    print("tracker when-labels:", [w for i, w in zip(out["today_all_ids"], out["today_when"])
                                   if i.startswith(M.TRACKER_PREFIX)])
asyncio.run(run())
