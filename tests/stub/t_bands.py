"""An event placed among the bands, not merely by the clock.

Every task and event here is invented.
"""
import asyncio, datetime as dt, sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
from singularity import PINNED
import main, ical, singularity

TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.now(TZ)
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

CFG = ical.Config(work="WorkAcc", personal=("Me",))

def timed(tid, title, hh, mm=0, checked=0, order=None, pinned=False, tags=None):
    t = mk(tid, title, TODAY, checked=checked, timed=True)
    t.raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(hh, mm), tzinfo=TZ))
    if order is not None: t.raw["scheduleOrder"] = order
    if pinned: t.raw["state"] = PINNED
    if tags: t.raw["tags"] = tags
    return t

def untimed(tid, title, day=None, checked=0, pinned=False, tags=None):
    t = mk(tid, title, day or TODAY, checked=checked)
    if pinned: t.raw["state"] = PINNED
    if tags: t.raw["tags"] = tags
    return t

def past_due(tid, title, days=1):
    return untimed(tid, title, TODAY - dt.timedelta(days=days))

def ev(title, hh=None, mm=0, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh or 0, mm))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=hh is None)

async def rows(tasks, events, green=None):
    app = main.TaskApp()
    app.client = StubClient(tasks, reference=NOW)
    app.calendar_config = CFG
    app.tracker_config = None
    app.green_tag = green
    saved = ical.fetch
    ical.fetch = lambda cfg, day: list(events)
    try:
        async with app.run_test(size=(120, 44)) as pilot:
            for _ in range(14): await pilot.pause()
            return app, [(("EVENT" if app.is_event(t) else "task"),
                          t.raw.get("title")) for t in app.tasks]
    finally:
        ical.fetch = saved

# ------------------------------------------------------------------ the key
async def the_key():
    print("the key an event stands on")
    app = main.TaskApp.__new__(main.TaskApp)
    e = singularity.Task({"title": "e", main.EVENT_MINUTES: 1080})
    ekey = main.TaskApp.event_key(app, e)
    tkey = singularity.sort_key(timed("t", "t", 18), TZ, NOW, manual=True, green=None)
    check("same length as a task's key", len(ekey), len(tkey))
    check("same types entry for entry",
          [type(a).__name__ for a in ekey], [type(b).__name__ for b in tkey])
    check("reads as unfinished, untagged, not past due, unpinned, timed",
          ekey[:6], (False, True, True, 0.0, True, False))
    check("carries its hour", ekey[6], (18, 0))
    check("and no hand-set order", ekey[7], 0)
    allday = main.TaskApp.event_key(app, singularity.Task({"title": "a", main.EVENT_MINUTES: None}))
    check("an all-day event reads as all-day", allday[5], True)

# ----------------------------------------------------- the reported case
async def reported():
    print("the reported case: a past-due task is not pushed below an event")
    app, got = await rows(
        [past_due("p1", "past due, no time"),
         timed("t1", "task at 08", 8),
         timed("t2", "task at 18", 18, order=1000),
         untimed("u1", "untimed today")],
        [ev("all day"), ev("event at 18", 18)])
    for line in got: print("     ", line)
    check("the past-due task leads the timed rows",
          got.index(("task", "past due, no time")) < got.index(("EVENT", "event at 18")), True)
    check("the event is not lifted to the top",
          got[1], ("task", "past due, no time"))
    check("the all-day event still leads the day", got[0], ("EVENT", "all day"))
    check("the 08:00 task is above the 18:00 event",
          got.index(("task", "task at 08")) < got.index(("EVENT", "event at 18")), True)
    check("the event and the task at its hour are adjacent",
          abs(got.index(("EVENT", "event at 18")) - got.index(("task", "task at 18"))), 1)
    check("and the untimed task is below both",
          got.index(("task", "untimed today")) > got.index(("EVENT", "event at 18")), True)

# ------------------------------------------------------- a finished task
async def finished():
    print("a finished task stays below an event")
    app, got = await rows(
        [timed("d1", "done at 08", 8, checked=CHECKED),
         timed("t1", "open at 09", 9)],
        [ev("event at 17", 17)])
    for line in got: print("     ", line)
    check("the finished task is last", got[-1], ("task", "done at 08"))
    check("the event is above it",
          got.index(("EVENT", "event at 17")) < got.index(("task", "done at 08")), True)

# --------------------------------------------------- tagged and pinned
async def bands():
    print("a tagged task and a pinned task keep their place")
    app, got = await rows(
        [untimed("g1", "tagged, no time", tags=["G"]),
         timed("p1", "pinned at 20", 20, pinned=True),
         timed("t1", "plain at 09", 9)],
        [ev("event at 10", 10)], green="G")
    for line in got: print("     ", line)
    check("the tagged task leads", got[0], ("task", "tagged, no time"))
    check("the pinned task is above the event",
          got.index(("task", "pinned at 20")) < got.index(("EVENT", "event at 10")), True)
    check("the event still falls after the 09:00 task",
          got.index(("task", "plain at 09")) < got.index(("EVENT", "event at 10")), True)

# ---------------------------------------------------- two at one minute
async def same_minute():
    print("two events at the same minute")
    app, got = await rows([timed("t1", "a task at 12", 12)],
                          [ev("bbb", 11), ev("aaa", 11)])
    for line in got: print("     ", line)
    check("they keep their order between themselves",
          [t for k, t in got if k == "EVENT"], ["aaa", "bbb"])

# ------------------------------------------------------- the guarantee
async def guarantee():
    print("the tasks keep their own order, on a day holding every band")
    tasks = [past_due("p1", "past due A", 3), past_due("p2", "past due B", 1),
             untimed("g1", "tagged", tags=["G"]),
             timed("pin", "pinned at 20", 20, pinned=True),
             timed("t1", "timed 08", 8, order=1000),
             timed("t2", "timed 18", 18, order=2000),
             untimed("u1", "untimed A"), untimed("u2", "untimed B"),
             timed("d1", "done 07", 7, checked=CHECKED),
             untimed("c1", "cancelled", checked=CANCELLED)]
    events = [ev("all day"), ev("e09", 9), ev("e12", 12), ev("e18", 18), ev("e23", 23)]
    app, with_events = await rows(tasks, events, green="G")
    app2, alone = await rows(tasks, [], green="G")
    kept = [t for k, t in with_events if k == "task"]
    check("disregarding the events leaves the tasks as they were",
          kept, [t for k, t in alone])
    for line in with_events: print("     ", line)

    print("and on a day carrying hand-set orders")
    hand = [timed("a", "first by hand", 9, order=3000),
            timed("b", "second by hand", 9, order=1000),
            timed("c", "third by hand", 9, order=2000)]
    app, we = await rows(hand, [ev("e09", 9)])
    app2, al = await rows(hand, [])
    check("the hand-set sequence is not disturbed",
          [t for k, t in we if k == "task"], [t for k, t in al])

# ------------------------------------------- it is an insertion, not a sort
async def insertion():
    print("placing is insertion: the task list is passed through untouched")
    app = main.TaskApp()
    app.client = StubClient([], reference=NOW)
    app.calendar_config = CFG; app.tracker_config = None
    async with app.run_test(size=(120, 40)) as pilot:
        for _ in range(10): await pilot.pause()
        tasks = [past_due("p1", "past due"), timed("t1", "at 08", 8),
                 timed("t2", "at 18", 18), untimed("u1", "untimed")]
        events = []
        for title, hh in [("e09", 9), ("e12", 12), ("all", None)]:
            e = ev(title, hh)
            minutes = None if e.all_day else e.start.hour * 60 + e.start.minute
            events.append(singularity.Task({
                "id": f"cal:{title}", "title": title, "checked": 0,
                "deferred": False, "useTime": False,
                main.EVENT_MARK: True, main.EVENT_MINUTES: minutes}))
        before = list(tasks)
        out = app.place_events(tasks, events)
        kept = [r for r in out if not app.is_event(r)]
        check("every task object comes through, in order and unchanged",
              [id(r) for r in kept], [id(r) for r in before])
        check("the input list itself was not mutated", [id(r) for r in tasks],
              [id(r) for r in before])
        check("nothing was added or lost", len(out), len(before) + len(events))


async def main_():
    await insertion()
    await the_key()
    await reported()
    await finished()
    await bands()
    await same_minute()
    await guarantee()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
