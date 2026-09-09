"""Group 2 -- setting a task's project, against the live API."""
import sys, time
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
sys.path.insert(0, _TESTS)   # the support beside the suites
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from datetime import date, datetime, time as _t
from singularity import SingularityClient, load_work_project, iso_z, ApiError
c=SingularityClient(); TZ=c.tz
DAY=date(2099,1,20); P="zz-proj-"
ok=[]
def chk(l,cond,e=""):
    ok.append(bool(cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
def cleanup():
    n=0
    for t in c.tasks_for_day(DAY).tasks:
        if t.title.startswith(P):
            for _ in range(5):
                try: c.delete_task(t.id); n+=1; break
                except Exception: time.sleep(1.5)
    return n
def mk(n): return c.create_task(f"{P}{n}", start=iso_z(datetime.combine(DAY,_t.min,tzinfo=TZ)), useTime=False)
names=c.project_names()
WORK=load_work_project()
others=[p for p in names if p!=WORK]
cleanup()
made=[]
try:
    print("2.1 setting a project through the client")
    a=mk("a"); made.append(a)
    chk("it starts with no project", c.get_task(a.id).project_id is None,
        str(c.get_task(a.id).project_id))
    c.set_project(a.id, WORK)
    chk("set_project files it under the work project",
        c.get_task(a.id).project_id==WORK, str(c.get_task(a.id).project_id))

    print("2.2 what the API refuses (so nothing later assumes otherwise)")
    for label, val in [("an empty value", ""), ("a null", None)]:
        try:
            c.update_task(a.id, projectId=val)
            chk(f"{label} is refused", False, f"ACCEPTED -> {c.get_task(a.id).project_id!r}")
        except ApiError as e:
            chk(f"{label} is refused", True, str(e)[:60])
            chk(f"  and the message names the required pattern", 'Must start with one of: "P-"' in str(e),
                str(e)[:70])
    chk("the task is still filed after both refusals",
        c.get_task(a.id).project_id==WORK, str(c.get_task(a.id).project_id))

    print("2.3 moving between projects")
    if others:
        c.set_project(a.id, others[0])
        chk("it moved to the other project", c.get_task(a.id).project_id==others[0],
            str(c.get_task(a.id).project_id))
        c.set_project(a.id, WORK)
        chk("and back to the work project", c.get_task(a.id).project_id==WORK)
    else:
        chk("skipped: only one project exists", False, "cannot test a move")
finally:
    print(f"\n  cleanup: {cleanup()} removed")
    chk("nothing left behind", not [t for t in c.tasks_for_day(DAY).tasks if t.title.startswith(P)])
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
