"""2.3 and 3.2/3.3 -- a long title survives, and nothing else broke."""
import sys, asyncio
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from harness import StubClient, mk, TZ
from datetime import datetime as dt
import main as M, tracker
from main import TaskApp, TaskInput, Confirm, DatePicker, ProjectPicker, TaskFocus, Help
from textual.widgets import Input, OptionList
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))
NOW = dt.now(TZ); TODAY = NOW.date()
LONG = "a synthetic title that is deliberately far longer than the widened prompt can ever show at once, to prove the whole of it survives"

async def settle(p, a, n=200):
    for _ in range(n):
        await p.pause()
        if not a._pending and not a._draining: return

async def prompt_roundtrip(text):
    """Type `text` into the prompt and return what it dismisses with."""
    app = TaskApp(TODAY)
    got = {}
    async with app.run_test(size=(120, 40)) as pilot:
        async def drive():
            got["value"] = await app.push_screen_wait(TaskInput("Add task", text))
        app.run_worker(drive())
        for _ in range(40): await pilot.pause()
        inp = app.screen.query_one(Input)
        got["shown"] = inp.content_size.width
        got["held"] = inp.value
        await pilot.press("enter")
        for _ in range(40): await pilot.pause()
    return got

print("2.3 a title longer than the prompt is kept whole")
r = asyncio.run(prompt_roundtrip(LONG))
chk("the prompt holds the entire title", r["held"] == LONG, f"{len(r['held'])} of {len(LONG)}")
chk("it returns the entire title", r["value"] == LONG, f"{len(r['value'] or '')} chars")
chk("only the view of it is limited", r["shown"] < len(LONG), f"{r['shown']} cells shown")
chk("and the view is the widened one", r["shown"] == 78, str(r["shown"]))

print("\n3.2 adding and renaming still work through the widened prompt")
async def add_and_rename():
    stub = StubClient([mk("T-a", "aaa", start=TODAY)], reference=NOW)
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        app.client = stub; app.projects = {}; app.tracker_config = None
        app.green_tag = None; app.green_checked = True
        app.load(); await settle(pilot, app)
        await pilot.press("a")
        for _ in range(40): await pilot.pause()
        chk("the add prompt opened", bool(app.screen.query("Input")))
        await pilot.press(*"новая задача"); await pilot.press("enter")
        await settle(pilot, app)
        titles = [t.title for t in app.tasks]
        chk("a Russian title was added", "новая задача" in titles, str(titles))
        app._selected_id = "T-a"; app.repaint(); await pilot.pause()
        await pilot.press("e")
        for _ in range(40): await pilot.pause()
        chk("the rename prompt opened with the old title",
            app.screen.query_one(Input).value == "aaa", app.screen.query_one(Input).value)
        chk("and it is the widened one too",
            app.screen.query_one(Input).content_size.width == 78,
            str(app.screen.query_one(Input).content_size.width))
        await pilot.press("escape")
        for _ in range(20): await pilot.pause()
        await pilot.press("ф")           # the Russian twin of "a"
        for _ in range(40): await pilot.pause()
        chk("the twin key opens it too", bool(app.screen.query("Input")))
        await pilot.press("escape")
        for _ in range(20): await pilot.pause()
asyncio.run(add_and_rename())

print("\n3.3 the other dialogues still open, answer and dismiss")
async def others():
    app = TaskApp(TODAY)
    async with app.run_test(size=(120, 40)) as pilot:
        for name, screen, key, want in [
            ("Confirm", lambda: Confirm("Sure?"), "y", True),
            ("DatePicker", lambda: DatePicker("When?", TODAY), "escape", None),
            ("ProjectPicker", lambda: ProjectPicker("Project", {"P-1": "One"}, None), "escape", None),
            ("TaskFocus", lambda: TaskFocus(mk("T-1", "a task", start=TODAY), "all-day", "", TZ), "escape", None),
            ("Help", lambda: Help(), "escape", None),
        ]:
            out = {}
            async def drive(s=screen):
                out["v"] = await app.push_screen_wait(s())
            app.run_worker(drive())
            for _ in range(30): await pilot.pause()
            opened = app.screen is not app.screen_stack[0]
            await pilot.press(key)
            for _ in range(30): await pilot.pause()
            chk(f"{name} opened and dismissed", opened and app.screen is app.screen_stack[0],
                f"opened={opened}")
            if want is not None:
                chk(f"{name} returned its answer", out.get("v") == want, repr(out.get("v")))
asyncio.run(others())
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
