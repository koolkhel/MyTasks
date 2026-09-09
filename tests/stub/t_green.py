"""Group 2 -- where green sits in the order."""
import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import mk, TZ
import singularity
from datetime import datetime, timedelta
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
G = "A-green"; OTHER = "A-other"
NOW = datetime.now(TZ); TODAY = NOW.date()

def t(name, late=None, hour=None, green=False, done=0, pinned=False, order=None):
    start = TODAY - timedelta(days=late) if late else TODAY
    x = mk(name, name, start=start, checked=done, timed=hour is not None)
    if hour is not None:
        x.raw["start"] = singularity.iso_z(datetime.combine(
            start, datetime.min.time().replace(hour=hour), tzinfo=TZ))
    if green: x.raw["tags"] = [G]
    if pinned: x.raw["state"] = singularity.PINNED
    if order is not None: x.raw["scheduleOrder"] = order
    return x

def order(tasks, now=NOW, manual=True, green=G):
    return [x.id for x in singularity.sort_for_display(tasks, TZ, now, manual=manual, green=green)]

print("2.1 a marked task due today leads an unmarked one long past due")
tasks = [t("work-16d", late=16), t("GREEN-today", green=True), t("work-2d", late=2)]
o = order(tasks)
chk("marked first", o[0] == "GREEN-today", str(o))
chk("the overdue ones follow, most overdue first", o[1:] == ["work-16d", "work-2d"], str(o))

print("\n2.2 a finished marked task still sinks")
tasks = [t("GREEN-done", green=True, done=1), t("work-open"), t("GREEN-open", green=True)]
o = order(tasks)
chk("open marked leads", o[0] == "GREEN-open", str(o))
chk("finished marked is last", o[-1] == "GREEN-done", str(o))

print("\n2.3 past-due tasks form two runs, each by how overdue")
tasks = [t("work-16d", late=16), t("GREEN-3d", late=3, green=True),
         t("work-2d", late=2), t("GREEN-9d", late=9, green=True)]
o = order(tasks)
chk("the marked run leads, most overdue first", o[:2] == ["GREEN-9d", "GREEN-3d"], str(o))
chk("the rest follow, ordered the same way", o[2:] == ["work-16d", "work-2d"], str(o))

print("     ...and an untagged day is ordered exactly as before")
tasks = [t("a-16d", late=16), t("b-2d", late=2), t("c-09", hour=9),
         t("d-allday"), t("e-done", done=1), t("f-pinned", pinned=True)]
before = [x.id for x in singularity.sort_for_display(tasks, TZ, NOW, manual=True)]
after = order(tasks)
chk("identical with no marked task present", before == after, f"{before} vs {after}")
chk("identical when no tag is configured", order(tasks, green=None) == before)

print("\n2.4 the dateless views")
tasks = [mk("plain", "plain"), mk("pinned", "pinned"), mk("green", "green")]
tasks[1].raw["state"] = singularity.PINNED
tasks[2].raw["tags"] = [G]
o = [x.id for x in singularity.sort_for_display(tasks, TZ, green=G)]
chk("marked leads the pinned one", o == ["green", "pinned", "plain"], str(o))
o2 = [x.id for x in singularity.sort_for_display(tasks, TZ)]
chk("unchanged when no tag is passed", o2 == ["pinned", "plain"] or o2[0] == "pinned", str(o2))

print("\n2.5 group_key picked the key up with no edit of its own")
a = t("GREEN", green=True); b = t("plain")
chk("a marked and an unmarked task are different groups",
    singularity.group_key(a, TZ, NOW, G) != singularity.group_key(b, TZ, NOW, G))
chk("and the same group when the tag is not configured",
    singularity.group_key(a, TZ, NOW, None) == singularity.group_key(b, TZ, NOW, None))
chk("group_key is still sort_key minus its last two",
    singularity.group_key(a, TZ, NOW, G) == singularity.sort_key(a, TZ, NOW, green=G)[:-2])
chk("the tag sits second, right under finishedness",
    singularity.sort_key(a, TZ, NOW, green=G)[1] is False
    and singularity.sort_key(b, TZ, NOW, green=G)[1] is True)

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
