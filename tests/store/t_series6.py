"""6.2 -- the real account's repeats have the shape this change assumes.

The recurring view is built on a reading of an object the store's own API
documents as having no fields. Every name in it was learned by observation,
so this suite exists to notice the day the observation stops holding: a new
repeat kind, an ending mode nobody has seen, a generator id pointing at
nothing, or the wait flag no longer meaning what it meant.

Counts only. No title, no note, no project name and no task id is printed
here or anywhere this writes: the account is somebody's real one, the repo is
public, and what this suite needs to know is shape and never content.

Nothing is created, changed or deleted. One sweep, read-only.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
import board
import singularity
from singularity import SingularityClient

ok = []
def chk(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))


print("6.2 one sweep of the account, read-only")
client = SingularityClient()
series, kids, plain, pages = [], [], 0, 0
for page in client.iter_pages(includeArchived=False):
    pages += 1
    for task in page:
        if task.recurring:
            series.append(task)
        elif task.series_id:
            kids.append(task)
        else:
            plain += 1
print(f"       {pages} page(s) · {len(series)} series · {len(kids)} occurrence(s) "
      f"· {plain} with neither")
chk("the sweep returned something to check", len(series) + len(kids) + plain > 0)

print("\n6.2 a series and an occurrence are never the same row")
both = [t for t in series if t.series_id]
chk("no row carries a rule and a parent at once", not both, f"{len(both)} did")

print("\n6.2 every occurrence's parent is a series the sweep found")
held = {t.id for t in series}
orphans = [t for t in kids if t.series_id not in held]
chk("no occurrence points at a series that is not here",
    not orphans, f"{len(orphans)} of {len(kids)} did")

print("\n6.2 every repeat the account holds can be read")
unread = [t for t in series if not t.repeat.readable]
chk("no series carries a repeat the board cannot read",
    not unread, f"{len(unread)} of {len(series)} could not be read")
kinds = {}
for task in series:
    kinds[task.repeat.kind] = kinds.get(task.repeat.kind, 0) + 1
print("       kinds held: " + (", ".join(f"{k}x{n}" for k, n in sorted(
    kinds.items(), key=lambda kv: str(kv[0]))) or "none"))
# A phrase for every one of them, and never the admission: an unreadable
# repeat would already have failed above, so this catches a kind the parser
# accepts and the words do not.
mute = [t for t in series
        if board.repeat_phrase(t.repeat) == "repeat cannot be read"]
chk("and every readable repeat has words for it",
    not mute, f"{len(mute)} had none")

print("\n6.2 the wait flag still means what it was read to mean")
by_series = {}
for task in kids:
    by_series[task.series_id] = by_series.get(task.series_id, 0) + 1
waiting = [by_series.get(t.id, 0) for t in series if t.waits_for_completion]
stacking = [by_series.get(t.id, 0) for t in series if not t.waits_for_completion]
print(f"       waiting: {len(waiting)} series, occurrences each {sorted(waiting)}")
print(f"       stacking: {len(stacking)} series, occurrences each {sorted(stacking)}")
if waiting:
    chk("a series that waits has at most one occurrence alive",
        max(waiting) <= 1, f"most held by one: {max(waiting)}")
else:
    print("  [SKIP] no waiting series on this account to check")
if stacking and waiting:
    chk("and the stacking ones hold more than the waiting ones",
        max(stacking) > max(waiting),
        f"stacking max {max(stacking)}, waiting max {max(waiting)}")
else:
    print("  [SKIP] needs one series of each kind to compare")

print("\n6.2 the ending is in the one mode that was read, or says it is not")
read = [t for t in series if t.ending_read]
chk("every series' ending is either read or admitted",
    all(t.ending_read or not t.ends_never for t in series))
print(f"       {len(read)} of {len(series)} in a mode the board reads")
if len(read) < len(series):
    print("       a mode nobody has seen is on the account · widen "
          "singularity.parse_ending, and the view already says so meanwhile")

print("\n6.2 the view would draw the series and nothing else")
made = board.Board(
    base=[], pending={}, tasks=[], position=singularity.SERIES,
    reference=None, tz=singularity.local_tz(),
    now=__import__("datetime").datetime.now(singularity.local_tz()),
    projects={}, marked=[], marked_rows={}, searching="", hiding_work=False,
    work_project=None, window_reason_now=None, work_override=None,
    green_tag=None, tracker_issues=[], tracker_config=None, events=[],
    events_day=None, calendar_config=None, mail_threads=[], notice=None,
    fetched=True, title_width=60, late_colour="#d17e92",
    series=series, occurrences=kids,
)
rows = made.paint().rows
chk("one row per series", len(rows) == len(series), f"{len(rows)} rows")
chk("and no occurrence among them",
    not [t for t in rows if t.series_id],
    f"occurrences drawn: {len([t for t in rows if t.series_id])}")
counted = sum(made.queued_for(t)[0] for t in series)
chk("every occurrence is counted against its series",
    counted == len(kids) - len(orphans), f"counted {counted} of {len(kids)}")
# Every facts line composes without raising, on real data of every kind the
# account holds.  The lines themselves are not printed: they carry no title,
# but there is no reason to put an account's repeat schedule in a log.
built = 0
for task in series:
    line = made.series_facts_for(task)
    built += 1 if line else 0
chk("every series composes a facts line", built == len(series),
    f"{built} of {len(series)}")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
raise SystemExit(0 if all(ok) else 1)
