"""Groups 2-5 -- every binding answers both layouts, nothing else changes."""
import sys, asyncio
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
from main import TaskApp, KeyBar, KEY_TWINS, keys, Help, DatePicker, Confirm, TaskFocus, TaskInput
from textual.widgets import DataTable, Input, Static
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
D=date(2099,9,1)
def so(t,v): t.raw["scheduleOrder"]=v; return t
def three(): return [so(mk("T-a","aaa",D),1000), so(mk("T-b","bbb",D),2000), so(mk("T-c","ccc",D),3000)]
def patch(stub):
    def sso(tid,order):
        stub._record("set_schedule_order",tid,order); stub.store[tid].raw["scheduleOrder"]=order
        return stub.store[tid]
    stub.set_schedule_order=sso; return stub

# ---------------- 2.1 every TaskApp letter binding, Russian side ----------
async def t_app():
    print("2.1 TaskApp: each Russian character runs the same action")
    cases=[("й","quit"),("о","cursor_down"),("л","cursor_up"),("Л","move_up"),("О","move_down"),
           ("р","prev_day"),("д","next_day"),("е","today"),("ш","inbox"),("ы","someday"),
           ("к","refresh"),("ю","done_for_today"),("ф","add"),("у","rename"),("ч","cancel_task"),
           ("в","schedule"),("щ","open_link"),("comma","help")]
    # map Russian char -> the action its binding declares
    bound={}
    for b in TaskApp.BINDINGS:
        for k in b.key.split(","):
            bound[k.strip()]=b.action
    for ch,action in cases:
        chk(f"{ch!r} is bound to {action}", bound.get(ch)==action, f"got {bound.get(ch)}")
    # and the English twin still points at the same action
    for eng,ru in [("a","ф"),("e","у"),("d","в"),("x","ч"),("o","щ"),("q","й"),("t","е"),
                   ("i","ш"),("s","ы"),("r","к"),("K","Л"),("J","О"),("h","р"),("l","д"),
                   ("j","о"),("k","л"),("full_stop","ю"),("question_mark","comma")]:
        chk(f"{eng} and {ru} share one action", bound.get(eng)==bound.get(ru) is not None,
            f"{bound.get(eng)} vs {bound.get(ru)}")

# ---------------- 2.1 live: pressing the Russian key really acts ----------
async def t_app_live():
    print("2.1 TaskApp: pressing the Russian key really acts")
    app=TaskApp(D); stub=patch(StubClient(three())); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        table=app.query_one(DataTable)
        chk("cursor starts at row 0", table.cursor_row==0)
        await pilot.press("о"); await pilot.pause()            # down (RU j)
        chk("о moved the cursor down", table.cursor_row==1, f"row={table.cursor_row}")
        await pilot.press("л"); await pilot.pause()            # up (RU k)
        chk("л moved it back up", table.cursor_row==0, f"row={table.cursor_row}")
        before=app.position
        await pilot.press("д"); await pilot.pause()            # next day (RU l)
        chk("д moved to the next day", app.position!=before, str(app.position))
        await pilot.press("р"); await pilot.pause()            # prev day (RU h)
        chk("р moved back", app.position==before, str(app.position))
        await pilot.press("ш")
        for _ in range(40):
            await pilot.pause()
            if app.position is M.Bucket.INBOX: break
        chk("ш opened the inbox", app.position is M.Bucket.INBOX, str(app.position))
        await pilot.press("ы")
        for _ in range(40):
            await pilot.pause()
            if app.position is M.Bucket.SOMEDAY: break
        chk("ы opened someday", app.position is M.Bucket.SOMEDAY, str(app.position))
        await pilot.press("е")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.position, M.Bucket): break
        chk("е returned to today", not isinstance(app.position,M.Bucket), str(app.position))
        # ф opens the add prompt
        await pilot.press("ф")
        for _ in range(40):
            await pilot.pause()
            if app.screen.query(Input): break
        chk("ф opened the add prompt", bool(app.screen.query(Input)))
        await pilot.press("escape"); await pilot.pause()
        # comma opens help
        await pilot.press("comma")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, Help): break
        chk("comma opened help", isinstance(app.screen,Help), type(app.screen).__name__)
        # and й closes it (RU q)
        await pilot.press("й")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.screen, Help): break
        chk("2.4 й closed the help overlay", not isinstance(app.screen,Help))

# ---------------- 2.2 DatePicker ----------
async def t_picker():
    print("2.2 DatePicker: each Russian choice key is taken")
    for ru,eng,expect in [("е","t","today"),("ь","m","tomorrow"),("ы","s","someday"),("с","c","clear")]:
        app=TaskApp(D); stub=patch(StubClient(three())); app.client=stub
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("в")                        # RU d -> open the picker
            for _ in range(40):
                await pilot.pause()
                if isinstance(app.screen, DatePicker): break
            opened=isinstance(app.screen,DatePicker)
            await pilot.press(ru)
            for _ in range(60):
                await pilot.pause()
                if not isinstance(app.screen, DatePicker): break
            closed=not isinstance(app.screen,DatePicker)
            chk(f"в opened the picker and {ru!r} ({eng}={expect}) answered it",
                opened and closed, f"opened={opened} closed={closed}")
            for _ in range(60):
                await pilot.pause()
                if not app._pending and not app._draining: break

# ---------------- 2.3 Confirm ----------
async def t_confirm():
    print("2.3 Confirm: both Russian answers work")
    for ru,label,should_delete in [("н","yes",True),("т","no",False)]:
        app=TaskApp(D); stub=patch(StubClient(three())); app.client=stub
        async with app.run_test() as pilot:
            await pilot.pause()
            n0=len(app.tasks)
            await pilot.press("backspace")
            for _ in range(40):
                await pilot.pause()
                if isinstance(app.screen, Confirm): break
            chk(f"the confirmation opened (for {label})", isinstance(app.screen,Confirm))
            await pilot.press(ru)
            for _ in range(80):
                await pilot.pause()
                if not isinstance(app.screen, Confirm) and not app._pending and not app._draining: break
            gone = len(app.tasks) < n0
            chk(f"{ru!r} answered {label}", gone==should_delete,
                f"{n0} -> {len(app.tasks)} tasks")

# ---------------- 2.4 TaskFocus ----------
async def t_focus():
    print("2.4 TaskFocus closes on the Russian close key")
    app=TaskApp(D); stub=patch(StubClient(three())); app.client=stub
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        for _ in range(40):
            await pilot.pause()
            if isinstance(app.screen, TaskFocus): break
        chk("the focus card opened", isinstance(app.screen,TaskFocus))
        await pilot.press("й")
        for _ in range(40):
            await pilot.pause()
            if not isinstance(app.screen, TaskFocus): break
        chk("й closed it", not isinstance(app.screen,TaskFocus))

# ---------------- 2.5 / 3.3 keys that need nothing ----------
def t_untouched():
    print("2.5 + 3.3 keys that need nothing are left alone")
    for k in ("space","enter","escape","backspace","delete","up","down","left","right"):
        chk(f"{k} has no twin", k not in KEY_TWINS, str(KEY_TWINS.get(k)))
        chk(f"keys({k!r}) is unchanged", keys(k)==k, keys(k))
    chk("TaskInput binds only layout-independent keys",
        all(k.strip() not in KEY_TWINS for b in TaskInput.__dict__.get("BINDINGS",[])
            for k in b.key.split(",")),
        str([b.key for b in TaskInput.__dict__.get("BINDINGS",[])]))

# ---------------- 3.1 / 3.2 the property over every binding ----------
def t_property():
    print("3.1 every binding that could have a twin has one")
    missing=[]
    for name in ("TaskApp","Confirm","DatePicker","TaskFocus","Help","TaskInput"):
        cls=getattr(M,name)
        for b in cls.__dict__.get("BINDINGS",[]):
            parts=[k.strip() for k in b.key.split(",")]
            # A key that is itself the twin of another key in the same binding
            # was added by the expansion; asking for its twin would be asking
            # for a twin of a twin.
            added={KEY_TWINS[k] for k in parts if k in KEY_TWINS}
            for k in parts:
                if k in added: continue
                t=KEY_TWINS.get(k)
                if t is not None and t not in parts:
                    missing.append(f"{name}: {b.key} lacks the twin of {k} ({t})")
    chk("no binding is missing a twin", not missing, "; ".join(missing))
    print("3.2 no twin collides")
    problems=[]
    for name in ("TaskApp","Confirm","DatePicker","TaskFocus","Help","TaskInput"):
        cls=getattr(M,name); seen={}
        for b in cls.__dict__.get("BINDINGS",[]):
            for k in [x.strip() for x in b.key.split(",")]:
                if k in seen and seen[k]!=b.action:
                    problems.append(f"{name}: {k!r} wanted by {seen[k]} and {b.action}")
                seen[k]=b.action
    chk("no key in any context is claimed by two actions", not problems, "; ".join(problems))

for fn in (t_app, t_app_live, t_picker, t_confirm, t_focus):
    asyncio.run(fn())
t_untouched(); t_property()
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
