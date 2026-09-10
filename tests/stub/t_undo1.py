"""Groups 1 and 2 -- the record, and reversing a write."""
import sys, asyncio, threading
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_TESTS)
sys.path.insert(0,_REPO)
from harness import StubClient, mk, TZ
from datetime import date
import main as M
from main import TaskApp, Undoable
from singularity import SingularityError, CHECKED, EMPTY, ApiError
from textual.widgets import DataTable
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def three(): return [so(mk("T-a","aaa",D),1000), so(mk("T-b","bbb",D),2000), so(mk("T-c","ccc",D),3000)]
def ids(a): return [t.id for t in a.tasks]
def status(a): return str(a.query_one("#status").content)
def patch(stub):
    def sso(tid,order):
        stub._record("set_schedule_order",tid,order); stub.store[tid].raw["scheduleOrder"]=order
        return stub.store[tid]
    stub.set_schedule_order=sso; return stub
async def settle(p,a,n=200):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return True
    return False

async def t_record():
    print("1.1 + 1.2 a confirmed write leaves one entry")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        chk("nothing to undo to start", app._undo==[], str(app._undo))
        await pilot.press("space")
        await settle(pilot, app)
        chk("one entry after a tick", len(app._undo)==1, str(len(app._undo)))
        e=app._undo[-1]
        chk("it names the action", e.label=="Ticking", e.label)
        chk("it names the task", e.subject=="aaa", e.subject)
        chk("it records only the field the write changed",
            list(e.previous.values())==[{"checked":0}], str(e.previous))
        chk("for exactly one task", list(e.previous)==["T-a"], str(list(e.previous)))
        chk("and is reversible", e.reversible)

async def t_refused():
    print("1.2 a refused write leaves none")
    stub=StubClient(three()); stub.fail["set_done"]=SingularityError("nope")
    app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        chk("nothing recorded", app._undo==[], str(app._undo))
        chk("the failure was reported", "failed" in status(app), status(app))

async def t_unreversible():
    print("1.3 the three that cannot be reversed are recorded, saying why")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("backspace")
        for _ in range(40):
            await pilot.pause()
            if app.screen.query("#dialog-title"): break
        await pilot.press("y"); await settle(pilot, app)
        chk("a deletion is on the stack", len(app._undo)==1)
        e=app._undo[-1]
        chk("marked unreversible", not e.reversible)
        chk("with a reason naming it", "deletion cannot be undone" in e.reason, e.reason)
        chk("and carries nothing to send", e.previous=={}, str(e.previous))

async def t_group():
    print("1.4 one keypress is one entry, however many writes")
    tasks=[so(mk(f"T-{i}",chr(97+i)*3,D),100+i) for i in range(4)]
    stub=patch(StubClient(tasks)); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("J")
        await settle(pilot, app)
        writes=stub.count("set_schedule_order")
        chk("the move took several writes", writes==5, str(writes))
        chk("but left exactly one entry", len(app._undo)==1, str(len(app._undo)))
        e=app._undo[-1]
        chk("naming all four tasks", set(e.previous)=={f"T-{i}" for i in range(4)},
            str(sorted(e.previous)))
        chk("each with its own previous order",
            [e.previous[f"T-{i}"]["scheduleOrder"] for i in range(4)]==[100,101,102,103],
            str(e.previous))

def t_not_persisted():
    print("1.5 the stack does not outlive the board")
    chk("a fresh board has nothing to undo", TaskApp(D)._undo==[])

async def t_reverse():
    print("2.1 reversing a tick sends back only what changed")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        chk("the task is done", stub.store["T-a"].done)
        await pilot.press("u"); await settle(pilot, app)
        chk("it is open again", not stub.store["T-a"].done, str(stub.store["T-a"].checked))
        calls=[a for c,a in stub.calls if c=="restore"]
        chk("one restore was sent", len(calls)==1, str(calls))
        chk("carrying only `checked`", calls[0][1]==("checked",), str(calls[0]))
        chk("the message names what it undid",
            "Undid: ticking" in status(app) and "aaa" in status(app), status(app))
        chk("the stack is empty again", app._undo==[], str(len(app._undo)))

async def t_only_its_fields():
    print("2.2 an undo restores only its own write's fields")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        client=app.client; t=app.tasks[0]
        app.submit_write("Renaming", t, lambda tid: client.update_task(tid, title="zulu"),
                         {"title":"zulu"})
        await settle(pilot, app)
        # something else about the task changes afterwards
        stub.store["T-a"].raw["checked"]=CHECKED
        app._base=[stub.store[i] for i in ("T-a","T-b","T-c")]
        app.repaint()
        await pilot.press("u"); await settle(pilot, app)
        chk("the title came back", stub.store["T-a"].title=="aaa", stub.store["T-a"].title)
        chk("the other change was left alone", stub.store["T-a"].checked==CHECKED,
            str(stub.store["T-a"].checked))

async def t_refused_undo():
    print("2.3 a refused undo is taken back and not retried")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        stub.fail["restore"]=SingularityError("no")
        before=ids(app)
        await pilot.press("u"); await settle(pilot, app)
        chk("the view returned to what it showed", ids(app)==before, f"{before} -> {ids(app)}")
        chk("the refusal is reported", "failed" in status(app), status(app))
        chk("the entry was not left to retry", app._undo==[], str(len(app._undo)))

async def t_gone():
    print("2.4 a task that no longer exists on the server")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        # deleted elsewhere: the restore comes back not-found
        stub.fail["restore"]=ApiError(404, "Task not found")
        await pilot.press("u"); await settle(pilot, app)
        chk("the board says so", "404" in status(app) or "not found" in status(app).lower(),
            status(app))
        chk("and the entry is discarded rather than retried", app._undo==[], str(len(app._undo)))
        chk("it was attempted once, not repeatedly", stub.count("restore")==1,
            str(stub.count("restore")))

async def t_off_view():
    print("2.4b a task merely absent from the shown view is still reachable")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        app._base=[t for t in app._base if t.id!="T-a"]; app.repaint()
        chk("the task is not in the view", "T-a" not in ids(app), str(ids(app)))
        await pilot.press("u"); await settle(pilot, app)
        chk("the undo still reached it", not stub.store["T-a"].done,
            str(stub.store["T-a"].checked))
        chk("and it says what it undid", "Undid: ticking" in status(app), status(app))

async def t_not_self():
    print("2.5 an undo is not itself pushed onto the stack")
    stub=StubClient(three()); app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        table=app.query_one(DataTable)
        await pilot.press("space"); await settle(pilot, app)     # tick a
        await pilot.press("space"); await settle(pilot, app)     # tick b (cursor advanced)
        chk("two entries", len(app._undo)==2, str(len(app._undo)))
        done_before={i:stub.store[i].done for i in ("T-a","T-b")}
        chk("both are done", all(done_before.values()), str(done_before))
        await pilot.press("u"); await settle(pilot, app)
        chk("one press reversed the newer", not stub.store["T-b"].done and stub.store["T-a"].done,
            str({i:stub.store[i].done for i in ("T-a","T-b")}))
        chk("one entry left", len(app._undo)==1, str(len(app._undo)))
        await pilot.press("u"); await settle(pilot, app)
        chk("the second press reached back, not turned round",
            not stub.store["T-a"].done and not stub.store["T-b"].done,
            str({i:stub.store[i].done for i in ("T-a","T-b")}))
        chk("nothing left", app._undo==[], str(len(app._undo)))
        await pilot.press("u"); await pilot.pause()
        chk("and it says so", "Nothing left to undo" in status(app), status(app))


async def t_partial_group():
    print("1.2b one refusal among an action's writes does not lose the rest")
    tasks=[so(mk(f"T-{i}",chr(97+i)*3,D),100+i) for i in range(4)]
    stub=patch(StubClient(tasks)); app=TaskApp(D); app.client=stub
    # the third respace write is refused; the others land
    stub.fail_ids[("set_schedule_order","T-2")]=SingularityError("transient")
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("J"); await settle(pilot, app)
        chk("some writes landed", stub.count("set_schedule_order")>=3,
            str(stub.count("set_schedule_order")))
        chk("the entry survives the one refusal", len(app._undo)==1, str(len(app._undo)))
        chk("the failure was reported", "failed" in status(app), status(app))
        # Unguarded.  This used to read `if app._undo:` because the entry
        # might not be there, which is why a failing run reported 46 checks
        # rather than 47 -- a count that varied with the race was part of its
        # recorded signature.  The entry always survives now, so the guard
        # has nothing to protect and the suite reports the same count every
        # run.
        await pilot.press("u"); await settle(pilot, app)
        chk("and it can still be undone", "Undid" in status(app), status(app))

async def t_forced_orderings():
    """The same action, its refusal answered first and then last.

    These cases were a probe -- `tests/probes/t_race.py`, removed with the
    fix -- which asserted nothing, because the two orderings disagreed and
    there was no right answer to state.  The entry was dropped when the refusal was answered
    before any of the action's other writes and kept when it was answered
    after, and nothing but timing separated them.  Worse: the writes that
    then landed counted themselves against a list no longer holding the
    entry, so three writes succeeded, the board went on showing them, and
    the undo key could not reach them.

    They agree now, so there is an answer to assert and it lives here,
    beside the check it explains.
    """
    print("1.2d the order the answers arrive in makes no difference")
    #: Long enough that the side meant to lose certainly settles after the
    #: other, short enough that the suite finishes.
    DAWDLE = 0.4
    left = {}
    for refusal_first in (True, False):
        tasks = [so(mk(f"T-{i}", chr(97 + i) * 3, D), 100 + i)
                 for i in range(4)]
        stub = patch(StubClient(tasks))
        recorded = stub._record

        def paced(name, *args, _first=refusal_first, _rec=recorded):
            # Whichever side is meant to lose the race dawdles.
            mine = bool(args) and args[0] == "T-2"
            if name == "set_schedule_order" and mine is not _first:
                threading.Event().wait(DAWDLE)
            return _rec(name, *args)

        stub._record = paced
        stub.fail_ids[("set_schedule_order", "T-2")] = \
            SingularityError("transient")
        app = TaskApp(D)
        app.client = stub
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("J")
            await settle(pilot, app, 400)
            left[refusal_first] = len(app._undo)
            chk(f"refusal answered {'first' if refusal_first else 'last'}: "
                f"the entry survives", len(app._undo) == 1,
                str(len(app._undo)))
            chk(f"refusal answered {'first' if refusal_first else 'last'}: "
                f"some writes landed",
                stub.count("set_schedule_order") >= 3,
                str(stub.count("set_schedule_order")))
    chk("and both orderings agree", left[True] == left[False],
        f"first={left[True]} last={left[False]}")


async def t_all_on_one_queue():
    """An action whose writes are all one task's, and whose first is refused.

    The refusal takes the rest of that task's queue with it, so nothing of
    the action is left to settle and the decision can be taken at once.  It
    matters because a decision that waited for writes which will never be
    sent would wait forever, and the entry would linger with nothing applied.
    """
    print("1.2e a refusal that abandons the rest decides at once")
    stub = patch(StubClient(three()))
    stub.fail_ids[("set_schedule_order", "T-a")] = SingularityError("nope")
    app = TaskApp(D)
    app.client = stub
    async with app.run_test() as pilot:
        await pilot.pause()
        #: One task, two writes queued behind each other for it.
        task = next(t for t in app.tasks if t.id == "T-a")
        for order in (1500, 1600):
            app.submit_write(
                "Reordering", task,
                lambda tid, o=order: stub.set_schedule_order(tid, o),
                {"scheduleOrder": order}, group="zz-one")
        await settle(pilot, app, 400)
        chk("nothing of the action is left queued",
            app._group_in_flight("zz-one") == 0,
            str(app._group_in_flight("zz-one")))
        chk("and no entry survives, nothing having landed",
            not [e for e in app._undo if e.group == "zz-one"],
            str([e.group for e in app._undo]))
        chk("the second write was abandoned, not sent",
            stub.count("set_schedule_order") == 1,
            str(stub.count("set_schedule_order")))


async def t_single_refusal_drops():
    print("1.2c a lone refused write still leaves nothing")
    stub=StubClient(three()); stub.fail["set_done"]=SingularityError("nope")
    app=TaskApp(D); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("space"); await settle(pilot, app)
        chk("nothing recorded", app._undo==[], str(len(app._undo)))

for fn in (t_record, t_refused, t_partial_group, t_single_refusal_drops, t_unreversible, t_group, t_reverse,
           t_only_its_fields, t_refused_undo, t_gone, t_off_view, t_not_self,
           t_forced_orderings, t_all_on_one_queue):
    asyncio.run(fn())
t_not_persisted()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
