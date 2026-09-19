"""The pictures: the served board is the pictured board, and the CRT capture's decisions.

No window is opened, no terminal is launched, nothing is captured and nothing
real is reachable.  The boards are the invented ones `docs/screenshots.py`
describes; the pilot drives them where a terminal would; every process the
CRT capture would start is a stub that records what it was asked.
"""
import asyncio
import os as _os
import sys
import tempfile
from types import SimpleNamespace
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
sys.path.insert(0, _os.path.join(_REPO, "docs"))
from harness import StubClient, run_parts
import singularity
import screenshots as S

ok = []
def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


async def settle(pilot, n=6):
    for _ in range(n):
        await pilot.pause()


def state_of(app):
    """What a picture would show: the rows, the marks, the selected row."""
    return ([t.id for t in app.tasks], list(app.marked), app._selected_id)


# ------------------------------------------- 2.2 the served board is the pictured one

def the_served_board_is_the_pictured_one():
    print("\n2.2 for every shot, serving builds the board the pilot pictures")
    # A client that must never be built: the served board reads no token.
    real = singularity.SingularityClient
    built = []
    class Forbidden:
        def __init__(self, *a, **k):
            built.append(1)
            raise AssertionError("a real client was constructed")
    singularity.SingularityClient = Forbidden
    try:
        for shot in S.SHOTS:
            name = shot["name"]

            async def pictured():
                make = dict(shot); make.pop("name"); app = make.pop("board")()
                saved = S.replace_sources(make.get("events", ()), make.get("issues", ()))
                try:
                    async with app.run_test(size=(104, 32)):
                        await S.dress(app, **make)
                        return state_of(app), type(app.client).__name__
                finally:
                    S.restore_sources(saved)

            async def served():
                app, how, saved = S.prepared(shot)
                try:
                    async with app.run_test(size=(104, 32)):
                        await S.dress(app, **how)
                        return state_of(app), type(app.client).__name__
                finally:
                    S.restore_sources(saved)

            a, client_a = asyncio.run(pictured())
            b, client_b = asyncio.run(served())
            check(f"{name}: the same rows, marks and selected row", b, a)
            check(f"{name}: rows were drawn at all", len(a[0]) > 0)
            check(f"{name}: the client is the stub", (client_a, client_b), ("StubClient", "StubClient"))
            if shot.get("marks"):
                check(f"{name}: the marks are on", a[1], list(shot["marks"]))
        check("no real client was ever constructed", built, [])
    finally:
        singularity.SingularityClient = real

    print("\n     the cursor lands on the row the shot names")
    async def where():
        shot = S.shot_named("today")
        app, how, saved = S.prepared(shot)
        try:
            async with app.run_test(size=(104, 32)):
                await S.dress(app, **how)
                row = next(t for t in app.tasks if t.id == app._selected_id)
                return row.display_title
        finally:
            S.restore_sources(saved)
    check("today's cursor is on the copier issue", "Copier jams" in asyncio.run(where()))


def the_ready_file_follows_the_cursor():
    print("\n2.2 the ready file is written only once the board is dressed")
    # `serve` itself calls app.run(); its dressing is `dress`, which the part
    # above drives under the pilot.  What is checked here is the order:
    # nothing is written before dress returns, and the file names the shot.
    with tempfile.TemporaryDirectory() as root:
        ready = _os.path.join(root, "ready")
        order = []

        async def run():
            shot = S.shot_named("inbox")
            app, how, saved = S.prepared(shot)
            try:
                async with app.run_test(size=(104, 32)):
                    order.append(("before", _os.path.exists(ready)))
                    await S.dress(app, **how)
                    with open(ready, "w", encoding="utf-8") as fh:
                        fh.write("inbox")
                    order.append(("after", _os.path.exists(ready), open(ready, encoding="utf-8").read()))
            finally:
                S.restore_sources(saved)
        asyncio.run(run())
        check("nothing before dressing", order[0], ("before", False))
        check("the file, naming the shot, after", order[1], ("after", True, "inbox"))


# ------------------------------------------------------- 3.2 the CRT capture's decisions

def the_new_window_is_the_one_that_appeared():
    print("\n3.2 the window is told apart by having appeared")
    check("one new id is picked", S.pick_new({1, 2}, {1, 2, 7}), 7)
    check("no new id: None", S.pick_new({1, 2}, {1, 2}), None)
    check("two new ids: None, never a guess", S.pick_new({1}, {1, 5, 6}), None)
    check("a closed window is not a new one", S.pick_new({1, 2}, {1}), None)

    print("\n     window ids come from the listing's owner name")
    listing = [
        {"kCGWindowOwnerName": "cool-retro-term", "kCGWindowNumber": 399},
        {"kCGWindowOwnerName": "kitty", "kCGWindowNumber": 404},
        {"kCGWindowOwnerName": "cool-retro-term", "kCGWindowNumber": 512},
        {"kCGWindowNumber": 9},
    ]
    check("only the owner's windows", S.window_ids(listing=listing), {399, 512})


class Fake:
    """Every process the capture would start, answered without starting one."""

    def __init__(self, *, ready_after=1, new_window=True, captures=True, installed=True):
        self.polls = 0
        self.ready_after = ready_after
        self.new_window = new_window
        self.captures = captures
        self.installed = installed
        self.launched = []
        self.ran = []
        self.terminated = 0
        self.ready_path = None
        self.said = []

    def exists(self, path):
        if path == S.CRT:
            return self.installed
        if path.endswith(_os.sep + f".ready-today") or ".ready-" in path:
            self.ready_path = path
            self.polls += 1
            return self.polls > self.ready_after
        return _os.path.exists(path)

    def launch(self, cmd, **kw):
        self.launched.append(list(cmd))
        fake = self
        class Child:
            pid = 4242
            def terminate(self_inner):
                fake.terminated += 1
        return Child()

    def windows(self):
        return {1, 2, 7} if (self.launched and self.new_window) else {1, 2}

    def run(self, cmd, **kw):
        self.ran.append(list(cmd))
        if cmd[0] == "screencapture" and self.captures:
            with open(cmd[-1], "wb") as fh:
                fh.write(b"\x89PNG not really but bytes")
        return SimpleNamespace(returncode=0 if self.captures else 1, stdout="", stderr="")

    def sleep(self, _s):
        pass


def the_capture_and_its_refusals():
    print("\n3.2 the capture, and what is said when it cannot happen")
    saved_docs = S.DOCS
    with tempfile.TemporaryDirectory() as root:
        S.DOCS = root
        try:
            f = Fake()
            path = S.crt("today", launch=f.launch, windows=f.windows, run=f.run,
                         exists=f.exists, sleep=f.sleep, out=f.said.append, timeout=5)
            check("a picture is written", path is not None and _os.path.exists(path))
            check("named for the shot", _os.path.basename(path or ""), "crt-today.png")
            check("cool-retro-term was launched with the profile",
                  f.launched and f.launched[0][:3] == [S.CRT, "-p", S.PROFILE])
            check("serving this very script, with a ready file",
                  f.launched and "--serve" in f.launched[0] and "--ready" in f.launched[0])
            check("the new window was captured", any(c[0] == "screencapture" and "-l7" in c for c in f.ran))
            check("the served board was ended afterwards", f.terminated, 1)
            check("nothing was said", f.said, [])
            check("no attempt was made to resize the window: nothing does",
                  [c for c in f.ran if c[0] == "osascript"], [])

            print("\n     the board never comes up")
            f = Fake(ready_after=10**6)
            path = S.crt("today", launch=f.launch, windows=f.windows, run=f.run,
                         exists=f.exists, sleep=f.sleep, out=f.said.append, timeout=0.01)
            check("no picture", path, None)
            check("it says the board did not come up", any("did not come up" in s for s in f.said))
            check("nothing was captured", [c for c in f.ran if c[0] == "screencapture"], [])
            check("the child is still ended", f.terminated, 1)

            print("\n     no window appeared")
            f = Fake(new_window=False)
            path = S.crt("today", launch=f.launch, windows=f.windows, run=f.run,
                         exists=f.exists, sleep=f.sleep, out=f.said.append, timeout=5)
            check("no picture", path, None)
            check("it says the window could not be told apart", any("could not tell" in s for s in f.said))

            print("\n     the screen may not be recorded")
            f = Fake(captures=False)
            path = S.crt("today", launch=f.launch, windows=f.windows, run=f.run,
                         exists=f.exists, sleep=f.sleep, out=f.said.append, timeout=5)
            check("no picture, and none left behind", (path, _os.path.exists(_os.path.join(root, "crt-today.png"))), (None, False))
            check("it names the setting", any(S.SETTINGS_PATH in s for s in f.said))
            check("and says to restart the terminal", any("start it again" in s for s in f.said))

            print("\n     cool-retro-term is not installed")
            f = Fake(installed=False)
            path = S.crt("today", launch=f.launch, windows=f.windows, run=f.run,
                         exists=f.exists, sleep=f.sleep, out=f.said.append, timeout=5)
            check("no picture, nothing launched", (path, f.launched), (None, []))
            check("and it says so", any("not at" in s for s in f.said))
        finally:
            S.DOCS = saved_docs


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_served_board_is_the_pictured_one,
    the_ready_file_follows_the_cursor,
    the_new_window_is_the_one_that_appeared,
    the_capture_and_its_refusals,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
