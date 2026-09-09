"""Groups 1, 2 and 3 -- the sequences, the guard, and the restore."""
import sys, io, pathlib, subprocess
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import main as M
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))

class FakeTTY(io.StringIO):
    def __init__(self, tty=True): super().__init__(); self._tty = tty
    def isatty(self): return self._tty

def run_with(stream, body=lambda: None):
    old = sys.stdout
    sys.stdout = stream
    try:
        with M.terminal_tab_named(M.TAB_TITLE):
            body()
    finally:
        sys.stdout = old
    return stream.getvalue()

print("1.1 the constants say what they should, and name no terminal")
chk("the name is MyTasks", M.TAB_TITLE == "MyTasks", repr(M.TAB_TITLE))
chk("set is OSC 0", M._TITLE_SET.format("X") == "\x1b]0;X\x07", repr(M._TITLE_SET))
chk("push is CSI 22;2t", M._TITLE_PUSH == "\x1b[22;2t", repr(M._TITLE_PUSH))
chk("pop is CSI 23;2t", M._TITLE_POP == "\x1b[23;2t", repr(M._TITLE_POP))
src = pathlib.Path(_REPO + "/main.py").read_text()
chk("the source names no terminal",
    not any(t in src.lower() for t in ("kitty", "iterm", "alacritty", "wezterm", "xterm", "konsole")))

print("\n1.2/1.3 a terminal is told, in the right order")
out = run_with(FakeTTY(True))
chk("something was written", out != "")
chk("push comes first", out.startswith(M._TITLE_PUSH), repr(out[:12]))
chk("then the name is set", M._TITLE_SET.format(M.TAB_TITLE) in out, repr(out))
chk("and the pop comes last", out.endswith(M._TITLE_POP), repr(out[-12:]))
chk("push before set before pop",
    out.index(M._TITLE_PUSH) < out.index(M._TITLE_SET.format(M.TAB_TITLE)) < out.rindex(M._TITLE_POP))
chk("the previous title is restored, not blanked",
    M._TITLE_SET.format("") not in out and "\x1b]0;\x07" not in out, repr(out))

print("\n1.3 restored however it exits")
class Boom(Exception): pass
s = FakeTTY(True); old = sys.stdout; sys.stdout = s
raised = False
try:
    with M.terminal_tab_named(M.TAB_TITLE):
        raise Boom("the board fell over")
except Boom:
    raised = True
finally:
    sys.stdout = old
chk("the error still propagates", raised)
chk("and the title was still put back", s.getvalue().endswith(M._TITLE_POP), repr(s.getvalue()[-12:]))

print("\n2.1 nothing is written when the output is not a terminal")
out = run_with(FakeTTY(False))
chk("not one byte", out == "", repr(out))
chk("no escape byte at all", "\x1b" not in out)

print("     ...and a stream that cannot answer isatty is treated as not a terminal")
class Odd(io.StringIO):
    def isatty(self): raise ValueError("closed")
out = run_with(Odd())
chk("nothing written, no error raised", out == "", repr(out))

print("\n2.2 the command-line listing is a different entry point")
cli = pathlib.Path(_REPO + "/singularity.py").read_text()
chk("singularity.py sets no title", "TITLE" not in cli and "]0;" not in cli)
chk("run.sh sends --cli to singularity.py",
    "singularity.py" in pathlib.Path(_REPO + "/run.sh").read_text())

print("\n3.1 the board is otherwise untouched")
chk("the entry point still returns 0 on a clean run",
    "return 0" in src and "terminal_tab_named(TAB_TITLE)" in src)
chk("the naming wraps the run, not replaces it",
    "with terminal_tab_named(TAB_TITLE):" in src and "TaskApp(day).run()" in src)

print("\n2.3 a redirected real run carries no escapes")
r = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0,'" + _REPO + "');"
    "import main;\n"
    "with main.terminal_tab_named('MyTasks'):\n"
    "    print('hello')"],
    capture_output=True, text=True, timeout=30)
chk("a piped run prints only its own output", r.stdout == "hello\n", repr(r.stdout))
chk("and exits cleanly", r.returncode == 0, r.stderr[-200:])

# --- 3.2 the name is fixed while the board is used -------------------------
import asyncio
sys.path.insert(0, _TESTS)
from harness import StubClient, mk, TZ
from datetime import datetime as _dt
from main import TaskApp
from singularity import Bucket
ok2 = []
def chk2(l, c, e=""):
    ok2.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))

print("\n3.2 the name does not move as work is done")
NOW = _dt.now(TZ); TODAY = NOW.date()

async def exercise():
    tasks = [mk(f"T-{c}", c*3, start=TODAY) for c in "abcd"]
    stub = StubClient(tasks, reference=NOW)
    def sso(tid, order):                      # the harness stub lacks this one
        stub._record("set_schedule_order", tid, order)
        stub.store[tid].raw["scheduleOrder"] = order
        return stub.store[tid]
    stub.set_schedule_order = sso
    app = TaskApp(TODAY)
    written = FakeTTY(True)
    old = sys.stdout; sys.stdout = written
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            app.client = stub; app.projects = {}; app.tracker_config = None
            app.green_tag = None; app.green_checked = True
            app.load()
            for _ in range(150): await pilot.pause()
            before = written.getvalue()
            app._selected_id = "T-a"; app.repaint(); await pilot.pause()
            for key in ("space", "a", "escape", "K", "J", "i", "s", "t", "u", "w"):
                await pilot.press(key)
                for _ in range(20): await pilot.pause()
            after = written.getvalue()
            return before, after
    finally:
        sys.stdout = old

before, after = asyncio.run(exercise())
chk2("no title sequence is emitted while the board is used",
     M._TITLE_SET.format(M.TAB_TITLE) not in after, repr(after[-60:]))
chk2("no push or pop either", M._TITLE_PUSH not in after and M._TITLE_POP not in after)
chk2("the board sets the name once, at the entry point, not on repaint",
     "terminal_tab_named" not in src.split("def main")[0].split("class TaskApp")[-1]
     or src.count("_TITLE_SET") == 2,
     f"_TITLE_SET appears {src.count('_TITLE_SET')}x (definition + one use)")

print(f"\n{sum(ok)+sum(ok2)}/{len(ok)+len(ok2)} checks passed")
sys.exit(0 if all(ok) and all(ok2) else 1)
