"""5.2 -- today's real block, read only, no writes at all."""
import sys, asyncio
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
from datetime import datetime
import main as M, tracker
from main import TaskApp
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))

cfg = tracker.load_config()
issues = tracker.fetch(cfg)
print(f"the tracker reports {len(issues)} issue(s) in states "
      f"{sorted({i.state for i in issues})}")

async def run():
    app = TaskApp(datetime.now().date())
    async with app.run_test(size=(120, 40)) as pilot:
        app.load()
        for _ in range(400):
            await pilot.pause()
            if app.query("#status"):
                st = str(app.query_one("#status").content)
                if "task(s)" in st and "tracked" in st: break
        for _ in range(120): await pilot.pause()
        rows = [(t.id, app.row_for(t)) for t in app.tasks]
        return rows, str(app.query_one("#status").content)

rows, st = asyncio.run(run())
yt = [(i, r) for i, r in rows if i.startswith(M.TRACKER_PREFIX)]
own = [(i, r) for i, r in rows if not i.startswith(M.TRACKER_PREFIX)]
labels = [r[2] for _, r in yt]
by_key = {i[len(M.TRACKER_PREFIX):]: r[2] for i, r in yt}

chk("the board shows exactly the issues the tracker reports",
    sorted(by_key) == sorted(i.key for i in issues), f"{len(by_key)} vs {len(issues)}")
chk("every state currently reported reads as its last word, lowercased",
    all(by_key[i.key] == i.state.split()[-1].lower() for i in issues),
    str({i.state: by_key[i.key] for i in issues}))
chk("no state label is cut", all(len(l) <= M._WHEN_WIDTH for l in labels),
    f"widest {max(labels, key=len)!r}" if labels else "none")
chk("no state label is empty", all(l for l in labels))
chk("every label reads in lower case", all(l == l.lower() for l in labels), str(sorted(set(labels))))
chk("no task's when-label is cut in the same column",
    all(len(r[2]) <= M._WHEN_WIDTH for _, r in own),
    f"widest {max((r[2] for _, r in own), key=len)!r}" if own else "none")
_ids = [i for i, _ in rows]
_yt = [i for i, _ in yt]
chk("the block is contiguous, wherever it sits",
    _ids[_ids.index(_yt[0]):_ids.index(_yt[0]) + len(_yt)] == _yt if _yt else True)
chk("the issues are counted separately", f"{len(issues)} tracked" in st, st)
print(f"\n  states seen: {sorted(set(labels))}")
print(f"  status: {st}")
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
