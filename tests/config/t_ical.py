"""Reading the calendar: access trouble, account filtering, ordering."""
import datetime as dt, sys, types
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import ical

# Read before anything here touches the environment: load_dotenv leaves an
# existing variable alone, so a test that sets one would otherwise be read
# back as the machine's real configuration.
REAL = ical.load_config()

ok = []
def check(name, got, want):
    ok.append(got == want)
    print(("  ok  " if got == want else "  FAIL"), name, "" if got == want else f"(got {got!r}, want {want!r})")

print("access trouble becomes the one failure type")
real = ical._status
for status, expect in [(1, "restricted"), (2, "refused"), (4, "in part")]:
    ical._STORE = None
    ical._status = lambda s=status: s
    try:
        ical._store()
        check(f"status {status} raises", False, True)
    except ical.CalendarUnreadable as exc:
        check(f"status {status} -> {expect!r} in the message", expect in str(exc), True)
    except Exception as exc:
        check(f"status {status} raises only CalendarUnreadable", type(exc).__name__, "CalendarUnreadable")
ical._status = real
ical._STORE = None

print("a day is never silently empty when permission is partial")
ical._STORE = None
ical._status = lambda: 4
try:
    ical.fetch(ical.Config(work="W", personal=("P",)), dt.date.today())
    check("fetch refuses rather than returning []", False, True)
except ical.CalendarUnreadable:
    check("fetch refuses rather than returning []", True, True)
ical._status = real
ical._STORE = None

print("the framework being absent is the same failure type")
saved = sys.modules.get("EventKit")
sys.modules["EventKit"] = None
ical._STORE = None
try:
    ical._store()
    check("missing framework raises", False, True)
except ical.CalendarUnreadable as exc:
    check("missing framework -> 'not available'", "not available" in str(exc), True)
except Exception as exc:
    check("missing framework raises only CalendarUnreadable", type(exc).__name__, "CalendarUnreadable")
sys.modules["EventKit"] = saved
ical._STORE = None

print("configuration")
import os
os.environ.pop("CALENDAR_WORK", None); os.environ.pop("CALENDAR_PERSONAL", None)
check("neither key set -> no calendar", ical.load_config("/nonexistent"), None)
os.environ["CALENDAR_PERSONAL"] = "a@b.c, d@e.f"
cfg = ical.load_config("/nonexistent")
check("personal alone works", (cfg.work, cfg.personal), ("", ("a@b.c", "d@e.f")))
check("no work account -> nothing is work", cfg.is_work("a@b.c"), False)
os.environ["CALENDAR_WORK"] = "W"
cfg = ical.load_config("/nonexistent")
check("accounts are work first", cfg.accounts, ("W", "a@b.c", "d@e.f"))
check("work matches regardless of case", cfg.is_work("w"), True)

print("ordering")
def ev(title, hh=None, allday=False):
    start = dt.datetime(2026, 9, 6, hh or 0, 0)
    return ical.Event(title=title, account="W", calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=allday)
rows = sorted([ev("late", 17), ev("all B", allday=True), ev("early", 9),
               ev("all A", allday=True)], key=ical.Event.sort_key)
check("all-day first, then by time", [r.title for r in rows], ["all A", "all B", "early", "late"])
check("all-day label", ev("x", allday=True).label, "all-day")
check("timed label", ev("x", 9).label, "09:00")

print("an account that is not on the machine is reported, not passed over")
import datetime as _dt
try:
    ical.fetch(ical.Config(work="NoSuchAccountHere", personal=()), _dt.date.today())
    check("a missing account raises", False, True)
except ical.CalendarUnreadable as exc:
    check("a missing account is named", "NoSuchAccountHere" in str(exc), True)
try:
    ical.fetch(ical.Config(work=REAL.work, personal=("AlsoMissing",)), _dt.date.today())
    check("one missing among real ones still raises", False, True)
except ical.CalendarUnreadable as exc:
    check("only the missing one is named",
          ("AlsoMissing" in str(exc), REAL.work in str(exc)), (True, False))

print()
print(f"{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
