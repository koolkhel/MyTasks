"""Promoting against the live store, once, and cleaned up afterwards.

A copy of the synthetic sample maildir, never the real one, and a task
prefixed `zz-` so it is unmistakable and deleted in a `finally`.  Nothing
about the account is printed but ids and lengths.
"""
import asyncio, datetime as dt, os, shutil, sys, tempfile
import os as _os, sys as _sys
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
import main as M
import mail
from main import TaskApp
from singularity import SingularityClient, Bucket
from textual.widgets import DataTable

HERE = os.path.dirname(os.path.abspath(__file__))
api = SingularityClient(); TZ = api.tz
TODAY = dt.datetime.now(TZ).date()
ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got {got!r}\n        want {want!r}")

path = os.path.join(tempfile.mkdtemp(prefix="prolive."), "mail")
shutil.copytree(_os.path.join(_TESTS, "fixtures", "sample_mail"), path)
cfg = mail.Config(path)
# The thread promoted is renamed first, so the task this creates on the live
# account cannot be mistaken for anything real and is trivially findable.
threads = mail.threads(mail.read(cfg))
target = threads[0]
made_id = None

async def go():
    global made_id
    app = TaskApp()
    app.mail_config = cfg
    async with app.run_test(size=(120, 44)) as pilot:
        app.position = Bucket.INBOX
        app.load()
        for _ in range(500):
            await pilot.pause()
            if any(app.is_mail(t) for t in app.tasks): break
        for _ in range(120): await pilot.pause()

        rows = [t for t in app.tasks if app.is_mail(t)]
        check("the copy's threads are shown", len(rows), len(threads))
        row = rows[0]
        marked = [m.key for m in row.raw[M.MAIL_MESSAGES]]
        # Rename it in place so the created task is obviously a test's.
        row.raw["title"] = f"zz-promote-{row.raw['title'][:20]}"
        table = app.query_one(DataTable)
        table.move_cursor(row=app.tasks.index(row))
        app._selected_id = row.id
        await pilot.pause()

        before = len(mail.read(cfg))
        app.action_promote()
        for _ in range(500):
            await pilot.pause()
            if not app._pending and not app._draining: break
        for _ in range(150): await pilot.pause()

        new = [t for t in app._base if t.title.startswith("zz-promote-")]
        if not new:
            new = [t for t in app.tasks if t.title.startswith("zz-promote-")]
        check("a task exists on the account", len(new), 1)
        if new:
            made_id = new[0].id
        check("with a real id, not a placeholder",
              bool(made_id) and not made_id.startswith("tmp:"), True)
        check("the thread left the queue", len(mail.read(cfg)), before - row.raw[M.MAIL_COUNT])
        check("and the messages marked are the thread's",
              sorted(m.key for m in row.raw[M.MAIL_MESSAGES]), sorted(marked))

try:
    asyncio.run(go())
    if made_id:
        fetched = api.tasks_for_day(TODAY).tasks
        mine = [t for t in fetched if t.id == made_id]
        check("the store hands it back on today", len(mine), 1)
        if mine:
            note = mine[0].note_text
            check("with a note that is not empty", bool(note.strip()), True)
            check("carrying the message's identity", "Message-ID: <" in note, True)
            check("and read back as the characters written",
                  note == mine[0].note_text, True)
            print(f"       note length: {len(note)} chars")
            check("all day", mine[0].raw.get("useTime"), False)
            order = mine[0].schedule_order
            others = [t.schedule_order for t in fetched if t.id != made_id]
            check("ordered past everything else the day held",
                  bool(others) and order > max(others), True)
finally:
    if made_id:
        api.delete_task(made_id)
        left = [t for t in api.tasks_for_day(TODAY).tasks if t.id == made_id]
        check("deleted afterwards, leaving nothing behind", left, [])
    shutil.rmtree(os.path.dirname(path), ignore_errors=True)

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
