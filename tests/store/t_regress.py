"""7.3 -- the board still shows what the API reports, in every view.

Read-only: no writes at all.  Compared two ways -- against a fresh fetch
(robust to the day's data changing) and against the capture taken before
any of this change was written.
"""
import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import baseline
import sys, asyncio, json
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from datetime import datetime, timedelta
import main as M
from main import TaskApp
import singularity
from singularity import SingularityClient, Bucket
api = SingularityClient(); TZ = api.tz
TODAY = datetime.now(TZ).date()
base = baseline.load(TZ)
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))

async def view(position):
    """What the board renders for a position."""
    app = TaskApp(position if not isinstance(position, Bucket) else TODAY)
    async with app.run_test(size=(120,40)) as pilot:
        if isinstance(position, Bucket):
            app.position = position
        app.load()
        for _ in range(200):
            await pilot.pause()
            if app.tasks or app._base is not None and app.query("#status"): 
                st = str(app.query_one("#status").content)
                if "task(s)" in st: break
        # The board's own tasks, not every row it draws.  A calendar event,
        # a tracker issue and a mail thread are rows the API was never
        # asked about, so counting them here compares a board against a
        # fetch that could not contain them -- which is how this read as
        # broken by exactly the number of event and mail rows.
        own = [t for t in app.tasks
               if not (app.is_event(t) or app.is_mail(t) or app.is_tracker(t))]
        return ([t.id for t in own], app.past_due, app.filed_out,
                str(app.query_one("#status").content),
                [t.title for t in app.tasks])

async def run():
    print("comparing the board against a fresh fetch, per view")
    for label, pos in [("today", TODAY), ("yesterday", TODAY-timedelta(days=1)),
                       ("tomorrow", TODAY+timedelta(days=1)),
                       ("inbox", Bucket.INBOX), ("someday", Bucket.SOMEDAY)]:
        ids, past_due, filed_out, status, _ = await view(pos)
        fresh = api.tasks_at(pos)
        want = [t.id for t in fresh.tasks]
        check(f"{label}: same tasks in the same order as the API reports",
              ids == want, f"board {len(ids)} vs api {len(want)}")
        check(f"{label}: past-due count agrees", past_due == fresh.past_due,
              f"{past_due} vs {fresh.past_due}")
        check(f"{label}: withheld count agrees", filed_out == fresh.filed_out,
              f"{filed_out} vs {fresh.filed_out}")
        check(f"{label}: the count it reports matches the rows",
              f"{len(ids)} task(s)" in status, status)
        if past_due:
            check(f"{label}: reports the past-due count", f"{past_due} past due" in status, status)

    print("comparing against the pre-change capture")
    ids, past_due, *_ = await view(TODAY)
    ids = [i for i in ids if not i.startswith(M.TRACKER_PREFIX)]
    check("today: same set of tasks as before the change",
          set(ids) == set(base["today_ids"]),
          f"now {len(ids)} vs then {len(base['today_ids'])}")
    check("today: same past-due count as before", past_due == base["today_past_due"],
          f"{past_due} vs {base['today_past_due']}")
    for b in Bucket:
        ids, _, filed_out, *_ = await view(b)
        check(f"{b.name.lower()}: same set of tasks as before",
              set(ids) == set(base[f"{b.name}_ids"]),
              f"now {len(ids)} vs then {len(base[f'{b.name}_ids'])}")
        check(f"{b.name.lower()}: same withheld count as before",
              filed_out == base[f"{b.name}_filed_out"],
              f"{filed_out} vs {base[f'{b.name}_filed_out']}")
    for d in (TODAY-timedelta(days=1), TODAY+timedelta(days=1)):
        ids, *_ = await view(d)
        ids = [i for i in ids if not i.startswith(M.TRACKER_PREFIX)]
        key = f"day_{d}_ids"
        if key in base:
            check(f"{d}: same set of tasks as before", set(ids) == set(base[key]),
                  f"now {len(ids)} vs then {len(base[key])}")
asyncio.run(run())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
