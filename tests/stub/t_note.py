"""Editing a task's note: the round trip, saving, discarding, clearing,
undo, both refusals, and the escaping.  Synthetic tasks only."""
import asyncio, datetime as dt, json, sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
from harness import *
import main, ical, tracker, singularity

TODAY = dt.datetime.now(TZ).date()
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name, "" if good else f"\n        got  {got!r}\n        want {want!r}")

def note_task(tid, title, text=None, raw_note=None):
    t = mk(tid, title, TODAY)
    if raw_note is not None: t.raw["note"] = raw_note
    elif text is not None:   t.raw["note"] = singularity.note_document(text)
    return t

async def board(tasks):
    app = main.TaskApp()
    app.client = StubClient(tasks, reference=dt.datetime.now(TZ))
    app.calendar_config = None
    app.tracker_config = None
    return app

async def settle(pilot, n=12):
    for _ in range(n): await pilot.pause()

async def select(app, pilot, pred):
    row = next(i for i, t in enumerate(app.tasks) if pred(t))
    app.query_one(main.DataTable).move_cursor(row=row)
    app._selected_id = app.tasks[row].id
    await pilot.pause()
    return app.tasks[row]

async def type_into(pilot, text):
    for ch in text:
        await pilot.press("enter" if ch == "\n" else ch)
    await pilot.pause()

# ------------------------------------------------------------- editing
async def editing():
    print("editing a note")
    app = await board([note_task("t1", "has a note", "first line"),
                       note_task("t2", "has none")])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: t.id == "t1")
        await pilot.press("n"); await settle(pilot, 6)
        check("the editor opens", type(app.screen_stack[-1]).__name__, "NoteInput")
        area = app.screen_stack[-1].query_one(main.NoteArea)
        check("holding the note's text", area.text, "first line")
        check("the cursor sits at the end", area.cursor_location, (0, len("first line")))
        await type_into(pilot, "\nsecond line")
        await pilot.press("ctrl+s"); await settle(pilot, 15)
        check("the editor closes", [type(s).__name__ for s in app.screen_stack], ["Screen"])
        stored = app.client.store["t1"].raw["note"]
        check("stored as a delta of one op", len(json.loads(stored)), 1)
        check("the text round trips",
              singularity.Task({"note": stored}).note_text, "first line\nsecond line")
        check("shown at once", app.selected.note_text, "first line\nsecond line")

        # a task that had none
        await select(app, pilot, lambda t: t.id == "t2")
        await pilot.press("n"); await settle(pilot, 6)
        check("opens empty for a task with no note", app.screen_stack[-1].query_one(main.NoteArea).text, "")
        await type_into(pilot, "brand new")
        await pilot.press("f2"); await settle(pilot, 15)
        check("f2 saves too",
              singularity.Task({"note": app.client.store["t2"].raw["note"]}).note_text,
              "brand new")

# ------------------------------------------------------- non-ASCII, lines
async def contents():
    print("what a note may contain")
    app = await board([note_task("t1", "a task")])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: True)
        await pilot.press("n"); await settle(pilot, 6)
        # Typed rather than assigned, so the path a person takes is the one
        # tested -- except the emoji, which the harness cannot deliver as a
        # keypress; that one is placed in the buffer directly.
        await type_into(pilot, "привет\nё ")
        area = app.screen_stack[-1].query_one(main.NoteArea)
        area.insert("🌲")
        await pilot.pause()
        await type_into(pilot, "\n[x] and [bold]loud[/]")
        await pilot.press("ctrl+s"); await settle(pilot, 15)
        got = singularity.Task({"note": app.client.store["t1"].raw["note"]}).note_text
        check("non-ASCII and markup-like text survive",
              got, "привет\nё 🌲\n[x] and [bold]loud[/]")
        check("the detail area shows every character",
              str(app.query_one("#detail", main.Static).render()),
              "привет\nё 🌲\n[x] and [bold]loud[/]")
        check("and applies no styling from it",
              list(getattr(app.query_one("#detail", main.Static).render(), "spans", [])), [])

# ------------------------------------------------ discard, unchanged, clear
async def leaving():
    print("leaving, changing nothing, and clearing")
    app = await board([note_task("t1", "a task", "keep me")])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: True)
        writes = lambda: [c for c, _ in app.client.calls
                          if c not in StubClient.READS | {"tag_title"}]
        # discard
        await pilot.press("n"); await settle(pilot, 6)
        await type_into(pilot, " and more")
        await pilot.press("escape"); await settle(pilot, 12)
        check("discarding writes nothing", writes(), [])
        check("and the note is untouched", app.selected.note_text, "keep me")
        # unchanged
        await pilot.press("n"); await settle(pilot, 6)
        await pilot.press("ctrl+s"); await settle(pilot, 12)
        check("saving unchanged text writes nothing", writes(), [])
        check("and says so", str(app.query_one("#status").render()), "The note is unchanged")
        check("and adds no undo entry", len(app._undo), 0)
        # clear
        await pilot.press("n"); await settle(pilot, 6)
        area = app.screen_stack[-1].query_one(main.NoteArea)
        area.text = ""
        await pilot.pause()
        await pilot.press("ctrl+s"); await settle(pilot, 15)
        check("emptying it clears the note", app.selected.note_text, "")
        check("stored as the newline alone",
              json.loads(app.client.store["t1"].raw["note"])[0]["insert"], "\n")
        # undo
        await pilot.press("u"); await settle(pilot, 15)
        check("undo brings the old note back", app.selected.note_text, "keep me")

# ------------------------------------------------------------- undo a first note
async def undo_first():
    print("undo where there was no note at all")
    app = await board([mk("t1", "never had one", TODAY)])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: True)
        check("the task really has no note field", "note" in app.selected.raw, False)
        # The stub records field names only, so capture the values here.
        restored = []
        real_restore = app.client.restore
        app.client.restore = lambda tid, fields: (restored.append(dict(fields)),
                                                  real_restore(tid, fields))[1]
        await pilot.press("n"); await settle(pilot, 6)
        await type_into(pilot, "written")
        await pilot.press("ctrl+s"); await settle(pilot, 15)
        check("it now has one", app.selected.note_text, "written")
        await pilot.press("u"); await settle(pilot, 15)
        check("undo restored it", app.selected.note_text, "")
        check("undo did send a restore", len(restored), 1)
        check("and sent no null",
              [f for f in restored if any(v is None for v in f.values())], [])
        check("it sent an empty document, not nothing",
              json.loads(restored[0]["note"])[0]["insert"], "\n")

# ------------------------------------------------------------- refusals
async def refusals():
    print("what may not be edited")
    E = ical.Event(title="a meeting", account="Me", calendar="c",
                   start=dt.datetime.combine(TODAY, dt.time(9, 0)),
                   end=dt.datetime.combine(TODAY, dt.time(10, 0)),
                   all_day=False, location="", notes="a description")
    app = await board([note_task("t1", "a task", "mine")])
    app.calendar_config = ical.Config(work="W", personal=("Me",))
    saved = ical.fetch; ical.fetch = lambda c, d: [E]
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await settle(pilot)
            app.tracker_issues = [tracker.Issue(key="AB-1", summary="an issue",
                                                project="Proj", state="In progress",
                                                assignee="me", base_url="https://tr.example")]
            app.repaint(); await pilot.pause()
            for pred, what in [(app.is_event, "calendar"), (app.is_tracker, "tracker")]:
                await select(app, pilot, pred)
                await pilot.press("n"); await settle(pilot, 8)
                check(f"{what}: no editor opens",
                      [type(s).__name__ for s in app.screen_stack], ["Screen"])
                check(f"{what}: and says why",
                      what in str(app.query_one("#status").render()).lower(), True)
            writes = [c for c, _ in app.client.calls
                      if c not in StubClient.READS | {"tag_title"}]
            check("nothing was written", writes, [])
    finally:
        ical.fetch = saved

    print("a formatted note is refused")
    rich = json.dumps([{"insert": "bold bit", "attributes": {"bold": True}},
                       {"insert": "\n"}])
    app = await board([note_task("t1", "formatted", raw_note=rich)])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: True)
        await pilot.press("n"); await settle(pilot, 8)
        check("no editor opens", [type(s).__name__ for s in app.screen_stack], ["Screen"])
        said = str(app.query_one("#status").render())
        check("and says what would be lost", "formatting" in said, True)
        writes = [c for c, _ in app.client.calls
                  if c not in StubClient.READS | {"tag_title"}]
        check("nothing was written", writes, [])

# --------------------------------------------- shown before the store answers
async def optimistic():
    print("the note appears without waiting for the store")
    import threading
    app = await board([note_task("t1", "a task", "old text")])
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await select(app, pilot, lambda t: True)
        app.client.gate = threading.Event()          # hold every write open
        await pilot.press("n"); await settle(pilot, 6)
        app.screen_stack[-1].query_one(main.NoteArea).text = "brand new text"
        await pilot.pause()
        await pilot.press("ctrl+s"); await settle(pilot, 12)
        check("on screen while the write is in flight",
              str(app.query_one("#detail", main.Static).render()), "brand new text")
        check("the store has not been told yet",
              singularity.Task({"note": app.client.store["t1"].raw["note"]}).note_text,
              "old text")
        check("and the board says a write is in flight",
              "saving" in str(app.query_one("#status").render()).lower(), True)
        app.client.gate.set()
        for _ in range(60):
            await pilot.pause()
            if not app._pending and not app._draining: break
        check("once it lands, the store agrees",
              singularity.Task({"note": app.client.store["t1"].raw["note"]}).note_text,
              "brand new text")
        check("the key bar names the note key",
              "Note" in str(app.query_one("#keybar").render()), True)


async def main_():
    await editing()
    await contents()
    await leaving()
    await undo_first()
    await refusals()
    await optimistic()
    print()
    print(f"{sum(ok)}/{len(ok)} checks passed")
    return 0 if all(ok) else 1

sys.exit(asyncio.run(main_()))
