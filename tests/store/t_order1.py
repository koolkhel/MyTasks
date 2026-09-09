import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_TESTS)
sys.path.insert(0,_REPO)
import baseline
import sys, json
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt(_REPO)
from harness import mk, TZ
from datetime import date, datetime, timedelta
from singularity import Task, sort_for_display, SingularityClient, Bucket
ok=[]
def check(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))

D = date(2099,6,1)
def so(t, v):
    t.raw["scheduleOrder"] = v; return t

print("1.1 reading scheduleOrder")
absent = Task({"id":"T-1","title":"x"})
zero   = Task({"id":"T-2","title":"x","scheduleOrder":0})
set_   = Task({"id":"T-3","title":"x","scheduleOrder":12345})
check("a missing key reads 0", absent.schedule_order == 0, str(absent.schedule_order))
check("a stored 0 reads 0", zero.schedule_order == 0)
check("a stored 12345 reads 12345", set_.schedule_order == 12345)
check("a stored None reads 0", Task({"id":"T-4","title":"x","scheduleOrder":None}).schedule_order == 0)

print("1.2 the manual order as the last key")
# titles chosen so alphabetical and manual order DISAGREE
a = so(mk("T-a","aaa",D), 3); b = so(mk("T-b","bbb",D), 1); c3 = so(mk("T-c","ccc",D), 2)
on  = [t.id for t in sort_for_display([a,b,c3], TZ, manual=True)]
off = [t.id for t in sort_for_display([a,b,c3], TZ)]
check("manual on  -> 1,2,3 by stored order", on == ["T-b","T-c","T-a"], str(on))
check("manual off -> alphabetical, as before", off == ["T-a","T-b","T-c"], str(off))
# title breaks a tie in the manual order
x = so(mk("T-x","zzz",D), 5); y = so(mk("T-y","mmm",D), 5)
tie = [t.id for t in sort_for_display([x,y], TZ, manual=True)]
check("title breaks a tie in the manual order", tie == ["T-y","T-x"], str(tie))

print("1.3 the manual order cannot override a key above it")
early = so(mk("T-08","early",D,timed=True), 900); late = so(mk("T-18","late",D,timed=True), 100)
early.raw["start"]=f"2099-06-01T08:00:00Z"; late.raw["start"]=f"2099-06-01T18:00:00Z"
res = [t.id for t in sort_for_display([late,early], TZ, manual=True)]
check("08:00 leads 18:00 despite a lower stored order on 18:00", res == ["T-08","T-18"], str(res))
now = datetime.now(TZ); today = now.date()
pd = so(mk("T-pd","pastdue",today-timedelta(days=2)), 99999)
td = so(mk("T-td","dueto",today), 1)
res = [t.id for t in sort_for_display([td,pd], TZ, now, manual=True)]
check("a past-due task with the highest order still leads", res == ["T-pd","T-td"], str(res))
fin = so(mk("T-fin","finished",D,checked=1), 1); opn = so(mk("T-open","open",D), 9999)
res = [t.id for t in sort_for_display([fin,opn], TZ, manual=True)]
check("an unfinished task still leads a finished one", res == ["T-open","T-fin"], str(res))
pin = so(mk("T-pin","pinned",D), 9999); pin.raw["state"]=0  # PINNED is 0, not 1
plain = so(mk("T-plain","plain",D), 1)
res = [t.id for t in sort_for_display([plain,pin], TZ, manual=True)]
check("a pinned task still leads", res == ["T-pin","T-plain"], str(res))

print("1.4 day views order manually, the buckets do not")
base = baseline.load(TZ)
api = SingularityClient()
l = api.tasks_for_day()
ids = [t.id for t in l.tasks]
check("today: same set of tasks as before", set(ids)==set(base["today_ids"]), f"{len(ids)} vs {len(base['today_ids'])}")
check("today: past-due count unchanged", l.past_due==base["today_past_due"], f"{l.past_due}")
check("today: finished count unchanged",
      sum(1 for t in l.tasks if t.done or t.cancelled)==base["today_done"])
check("today: timed tasks still ascending",
      [t.local_start(TZ).strftime('%H:%M') for t in l.tasks if t.timed]==base["today_timed_starts"],
      str([t.local_start(TZ).strftime('%H:%M') for t in l.tasks if t.timed]))
# drift-independent: the day's order IS the manual one, and is NOT the
# order the same tasks would take without the manual key
check("today: the order is the manual one",
      ids == [t.id for t in sort_for_display(list(l.tasks), TZ, l.reference,
                                             manual=True, green=api.green)],
      "matches manual ordering")
check("today: and differs from the order without it",
      ids != [t.id for t in sort_for_display(list(l.tasks), TZ, l.reference,
                                             green=api.green)],
      "manual makes a difference to this day")
for b in Bucket:
    lb = api.tasks_in_bucket(b)
    bids=[t.id for t in lb.tasks]
    check(f"{b.name.lower()}: ids AND order identical to before",
          bids==base[f"{b.name}_ids"], f"{sum(1 for i,j in zip(bids,base[f'{b.name}_ids']) if i!=j)} rows differ")
    check(f"{b.name.lower()}: withheld count unchanged", lb.filed_out==base[f"{b.name}_filed_out"])
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
