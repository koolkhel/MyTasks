"""The terminal's side of the calendar: who is asking, and what puts it right.

Nothing here reads /Applications, runs `codesign` or `tccutil`, walks the real
process table, or asks the system for anything.  A fake `.app` is built in a
temporary directory, `ps` is answered from a made-up parent chain, and every
command the helper would run is recorded by a stub and answered as the real
one would.  The one machine fact used is that a bundle is a directory with a
`Contents/Info.plist` in it.

Every application, bundle id and path below is invented.
"""
import io
import os as _os
import plistlib
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
from parts import run_parts
import terminal
import calendar_access as CA

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

def make_app(root, name, bundle, keys=()):
    """A bundle that is nothing but a directory and a plist, which is all that is read."""
    app = _os.path.join(root, name + ".app")
    _os.makedirs(_os.path.join(app, "Contents", "MacOS"))
    info = {"CFBundleIdentifier": bundle, "CFBundleExecutable": name}
    for k in keys:
        info[k] = "because"
    with open(terminal.plist_path(app), "wb") as fh:
        plistlib.dump(info, fh)
    return app


def done(stdout="", stderr="", code=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=code)


class Machine:
    """Answers `ps` from a made-up process table and records every other command."""

    def __init__(self, table, codesign="unsigned"):
        self.table = table            # pid -> (ppid, comm)
        self.codesign = codesign      # what `codesign -dv` would print
        self.ran = []

    def run(self, cmd, **kw):
        self.ran.append(list(cmd))
        if cmd[0] == "ps":
            pid = int(cmd[-1])
            if pid not in self.table:
                raise __import__("subprocess").CalledProcessError(1, cmd)
            ppid, comm = self.table[pid]
            return done(f"{ppid:>5} {comm}\n")
        if cmd[0] == "codesign" and cmd[1] == "-dv":
            texts = {
                "unsigned": ("", "x: code object is not signed at all"),
                "adhoc": ("", "Executable=x\nIdentifier=y\nSignature=adhoc\n"),
                "developer": ("", "Executable=x\nAuthority=Developer ID Application: Someone (ABC123)\n"
                                  "Authority=Developer ID Certification Authority\n"),
            }
            out, err = texts[self.codesign]
            return done(out, err)
        return done()


def said_by(fn, *args, **kw):
    lines = []
    code = fn(*args, out=lines.append, **kw)
    return code, "\n".join(lines)


# --------------------------------------------- 2.1 who is asking, and what it declares

def the_host_is_found():
    print("\n2.1 the application that owns a process, up the parent chain")
    chain = {
        400: (300, "/opt/homebrew/bin/bash"),
        300: (200, "/usr/bin/login"),
        200: (1, "/Applications/Fake Term.app/Contents/MacOS/Fake Term"),
    }
    m = Machine(chain)
    check("a shell under a login under a terminal names the terminal",
          terminal.host_app(400, run=m.run), "/Applications/Fake Term.app")
    check("only ps was run", {c[0] for c in m.ran}, {"ps"})

    print("\n     a framework Python is a bundle too, and is skipped")
    chain = {
        500: (400, "/x/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python"),
        400: (300, "/bin/zsh"),
        300: (1, "/Applications/Other.app/Contents/MacOS/Other"),
    }
    check("the terminal, not the interpreter",
          terminal.host_app(500, run=Machine(chain).run), "/Applications/Other.app")

    print("\n     no application up the chain")
    check("reaching pid 1 answers None",
          terminal.host_app(400, run=Machine({400: (1, "/bin/bash")}).run), None)
    check("a pid ps does not know answers None",
          terminal.host_app(999, run=Machine({}).run), None)
    check("odd ps output answers None rather than raising",
          terminal.host_app(7, run=lambda *a, **k: done("garbage\n")), None)


def what_the_plist_declares():
    print("\n2.1 what an application declares, and how it is signed")
    with tempfile.TemporaryDirectory() as root:
        none = make_app(root, "Bare", "org.invalid.bare")
        older = make_app(root, "Older", "org.invalid.older", ["NSCalendarsUsageDescription"])
        both = make_app(root, "Both", "org.invalid.both", list(terminal.USAGE_KEYS))
        check("neither key: declares no reason", terminal.declares_calendar_reason(none), False)
        check("and both are missing", terminal.usage_keys_missing(none), list(terminal.USAGE_KEYS))
        check("the older key alone is a reason", terminal.declares_calendar_reason(older), True)
        check("with the newer one missing",
              terminal.usage_keys_missing(older), ["NSCalendarsFullAccessUsageDescription"])
        check("both keys: nothing missing", terminal.usage_keys_missing(both), [])
        check("the bundle id is read", terminal.bundle_id(none), "org.invalid.bare")

        print("\n     three ways codesign answers")
        for kind in ("unsigned", "adhoc"):
            check(f"{kind} reads as {kind}",
                  terminal.signature(none, run=Machine({}, codesign=kind).run), kind)
        check("a developer signature reads as its authority",
              terminal.signature(none, run=Machine({}, codesign="developer").run),
              "Developer ID Application: Someone (ABC123)")


# ------------------------------------------------------------ 2.2 the helper's decisions

CHAIN = {
    400: (300, "/opt/homebrew/bin/bash"),
    300: (200, "/usr/bin/login"),
}

def host_chain(app):
    exe = _os.path.join(app, "Contents", "MacOS", _os.path.basename(app)[:-4])
    return {**CHAIN, 200: (1, exe)}


def the_diagnosis():
    print("\n2.2 the report")
    with tempfile.TemporaryDirectory() as root:
        bare = make_app(root, "Bare", "org.invalid.bare")
        m = Machine(host_chain(bare))
        d = CA.diagnose(bare, run=m.run, ppid=400, status=0)
        check("names the application", d["app"], bare)
        check("says it declares none", d["declares_none"], True)
        check("and how it is signed", d["signature"], "unsigned")
        check("knows the answer is its own", d["same"], True)
        code, text = said_by(CA.main, ["--app", bare], run=m.run, ppid=400, status=0)
        check("the report says the system will not ask",
              "the system will not ask on this app's behalf" in text, True)
        check("and says to fix", "--fix" in text, True)
        check("and exits 1", code, 1)

        print("\n     asked about a different application than the host")
        other = make_app(root, "Other", "org.invalid.other", list(terminal.USAGE_KEYS))
        d = CA.diagnose(other, run=m.run, ppid=400, status=3)
        check("the answer is marked as the host's",
              (d["same"], d["status_is_for"]), (False, "Bare.app"))
        _, text = said_by(CA.say, d)
        check("and the line says so", "for Bare.app, which this runs in; not for Other.app" in text, True)

        print("\n     an application already allowed")
        code, text = said_by(CA.main, ["--app", bare], run=m.run, ppid=400, status=3)
        check("says so and exits 0", (code, "Already allowed" in text), (0, True))


def the_fix():
    print("\n2.2 the fix, on a fake application, with every command stubbed")
    with tempfile.TemporaryDirectory() as root:
        bare = make_app(root, "Bare", "org.invalid.bare")
        m = Machine(host_chain(bare), codesign="unsigned")
        d = CA.diagnose(bare, run=m.run, ppid=400, status=0)
        code, text = said_by(CA.fix, bare, d, yes=True, run=m.run, ask=lambda _p: "n")
        check("it succeeds", code, 0)
        info = terminal.read_plist(bare)
        check("both keys are in the plist now",
              [k for k in terminal.USAGE_KEYS if k in info], list(terminal.USAGE_KEYS))
        check("a copy of the original was kept",
              _os.path.exists(terminal.plist_path(bare) + ".before-calendar-access"), True)
        with open(terminal.plist_path(bare) + ".before-calendar-access", "rb") as fh:
            check("and it is the original", "NSCalendarsUsageDescription" in plistlib.load(fh), False)
        cmds = [c[0:2] for c in m.ran if c[0] != "ps"]
        check("re-signed ad hoc through the stub", ["codesign", "--force"] in cmds, True)
        check("cleared the remembered answer through the stub", ["tccutil", "reset"] in cmds, True)
        check("the reset names the bundle", [c for c in m.ran if c[0] == "tccutil"][0][-1], "org.invalid.bare")
        check("and says to quit and restart", "quit" in text and "start it again" in text, True)
        check("nothing was asked with --yes", True, True)

        print("\n     declined at the prompt")
        again = make_app(root, "Again", "org.invalid.again")
        m2 = Machine(host_chain(again))
        d = CA.diagnose(again, run=m2.run, ppid=400, status=0)
        code, text = said_by(CA.fix, again, d, yes=False, run=m2.run, ask=lambda _p: "n")
        check("nothing changed", (code, "Nothing changed." in text), (1, True))
        check("the plist is as it was", terminal.declares_calendar_reason(again), False)
        check("no command but ps and codesign -dv ran",
              [c[0] for c in m2.ran if c[0] not in ("ps", "codesign")], [])
        check("and codesign only looked",
              all(c[1] == "-dv" for c in m2.ran if c[0] == "codesign"), True)

        print("\n     a developer-signed application is refused")
        signed = make_app(root, "Signed", "org.invalid.signed")
        m3 = Machine(host_chain(signed), codesign="developer")
        d = CA.diagnose(signed, run=m3.run, ppid=400, status=0)
        code, text = said_by(CA.fix, signed, d, yes=True, run=m3.run, ask=lambda _p: "y")
        check("it refuses", code, 2)
        check("and says why", "break that signature" in text, True)
        check("the plist is untouched", terminal.declares_calendar_reason(signed), False)
        check("nothing was signed or reset",
              [c for c in m3.ran if c[0] == "tccutil" or (c[0] == "codesign" and c[1] != "-dv")], [])

        print("\n     an application already allowed is left alone")
        fine = make_app(root, "Fine", "org.invalid.fine", ["NSCalendarsUsageDescription"])
        m4 = Machine(host_chain(fine), codesign="adhoc")
        d = CA.diagnose(fine, run=m4.run, ppid=400, status=3)
        code, text = said_by(CA.fix, fine, d, yes=True, run=m4.run, ask=lambda _p: "y")
        check("nothing to fix", (code, "nothing to fix" in text), (0, True))
        check("and nothing ran but the look",
              [c for c in m4.ran if c[0] == "tccutil" or (c[0] == "codesign" and c[1] != "-dv")], [])


# ----------------------------------------------------- 4.1 quiet, for the launcher

def quiet_speaks_only_when_it_matters():
    print("\n4.1 --quiet: nothing when all is well, the diagnosis when it is not")
    with tempfile.TemporaryDirectory() as root:
        fine = make_app(root, "Fine", "org.invalid.fine", ["NSCalendarsUsageDescription"])
        m = Machine(host_chain(fine))
        code, text = said_by(CA.main, ["--app", fine, "--quiet"], run=m.run, ppid=400, status=3)
        check("a granted host prints nothing", text, "")
        check("and exits 0", code, 0)

        bare = make_app(root, "Bare", "org.invalid.bare")
        m = Machine(host_chain(bare))
        code, text = said_by(CA.main, ["--app", bare, "--quiet"], run=m.run, ppid=400, status=0)
        check("a keyless host is reported", "may not be readable from Bare.app" in text, True)
        check("with the fix command", "--fix" in text, True)
        check("and an exit the launcher ignores", code, 1)
        check("no request was made", [c for c in m.ran if c[0] not in ("ps", "codesign")], [])

        code, text = said_by(CA.main, ["--app", fine, "--quiet"], run=Machine(host_chain(fine)).run, ppid=400, status=2)
        check("a denied host is reported too", "Privacy & Security" in text, True)


def the_launcher_checks_first():
    print("\n4.1 run.sh runs the check before the board, and only when it should")
    src = open(_os.path.join(_REPO, "run.sh"), encoding="utf-8").read()
    check("the helper is run quietly", 'calendar_access.py --quiet' in src, True)
    check("its exit is ignored", 'calendar_access.py --quiet || true' in src, True)
    check("guarded by the calendar settings",
          "CALENDAR_WORK" in src and "CALENDAR_PERSONAL" in src, True)
    check("before the board starts",
          src.index("calendar_access.py --quiet") < src.index('exec "${PYTHON}" main.py'), True)
    check("and after the command-line listing has already left",
          src.index('exec "${PYTHON}" singularity.py') < src.index("calendar_access.py --quiet"), True)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_host_is_found,
    what_the_plist_declares,
    the_diagnosis,
    the_fix,
    quiet_speaks_only_when_it_matters,
    the_launcher_checks_first,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
