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
# -- the priority letter, against whatever the tracker actually holds -------
# The letter is the first character of the tracker's own word for a priority,
# upper case except for the least urgent, whose word begins with the same
# letter as the most urgent one's.  Checked against the live vocabulary rather
# than against a list here, since not carrying such a list is the point.
#
# Reported as counts and letters only.  No issue key, summary, project or
# person's name is printed by this suite.
letters = {i[len(M.TRACKER_PREFIX):]: str(r[0]) for i, r in yt}
by_key_issue = {i.key: i for i in issues}
wrong = []
for key, shown in letters.items():
    got = by_key_issue.get(key)
    if got is None:
        continue
    want = M._priority_letter(got.priority, got.priority_value)
    if shown != want:
        wrong.append(f"{shown!r} vs {want!r}")
chk("every row's letter is the one its priority gives", wrong == [], str(wrong))
chk("each is one character or empty",
    all(len(l) <= 1 for l in letters.values()), str(sorted(set(letters.values()))))
chk("a letter is shown exactly where the tracker holds a priority",
    {k for k, v in letters.items() if v}
    == {k for k, i in by_key_issue.items() if i.priority and k in letters},
    f"{sum(1 for v in letters.values() if v)} shown, "
    f"{sum(1 for k, i in by_key_issue.items() if i.priority and k in letters)} held")
chk("every letter comes from the tracker's own word",
    all(not v or v.lower() == by_key_issue[k].priority[:1].lower()
        for k, v in letters.items() if k in by_key_issue),
    str(sorted(set(letters.values()))))
chk("the least urgent reads lower case, and nothing else does",
    all((v.islower() if by_key_issue[k].priority_value == M.LEAST_URGENT
         else v.isupper())
        for k, v in letters.items() if v and k in by_key_issue),
    str(sorted(set(letters.values()))))
seen = sorted({v for v in letters.values() if v})
print(f"\n  priority letters seen: {seen}")
print(f"  rows with a letter: {sum(1 for v in letters.values() if v)}"
      f" of {len(letters)}")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
