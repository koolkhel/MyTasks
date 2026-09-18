"""What the runner says about a suite, read off the three shapes a run takes.

No subprocess is started.  The runner reads a suite's output through one
function, and this suite hands that function text: a run whose checks failed,
a run whose process failed after every check passed, and a run that died
before it could print a summary.  Then it reads back the mark, the line, the
block under the run, and the signature the known-failures list would record.

The second shape is why this exists.  The runner once printed
`FAIL   t_bands   23/23 checks passed` and nothing under it: the mark came
from the exit code, the count from a line printed whatever the exit was, and
the one line saying what raised matched no pattern the runner read.

Everything below is invented; no suite named here need exist.
"""
import io
import contextlib
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the runner are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
from parts import run_parts
import run as R
import known_failures as KF

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the three shapes

#: Two checks failed and pytest said so: the ordinary failure.
FAILED_CHECKS = """\
  ok   the first thing
  FAIL the second thing
        got  1
        want 2
  ok   the third thing
  FAIL the fourth thing
        got  []
        want ['x']
..F.F                                                                    [100%]
=================================== FAILURES ===================================
__________________________________ second_part __________________________________
2 of 4 checks failed in second_part; the FAIL lines above name them

7/9 checks passed
=========================== short test summary info ============================
FAILED tests/stub/t_zz.py::second_part - PartFailed: 2 of 4 checks failed in second_part
1 failed, 3 passed in 4.10s
"""

#: Every check passed and a part raised on its way out: the crash.
CRASHED_AFTER = """\
  ok   the event and the task at its hour are adjacent
  ok   nothing was added or lost
......F                                                                  [100%]
=================================== FAILURES ===================================
__________________________________ guarantee ___________________________________
Traceback (most recent call last):
  File "tests/stub/t_zz.py", line 197, in guarantee
    asyncio.run(self.part())
RuntimeError: Event loop is closed

23/23 checks passed
=========================== short test summary info ============================
FAILED tests/stub/t_zz.py::guarantee - RuntimeError: Event loop is closed
1 failed, 6 passed in 9.81s
"""

#: The suite could not even be imported: no summary was ever printed.
CRASHED_BEFORE = """\
==================================== ERRORS ====================================
______________________ ERROR collecting tests/stub/t_zz.py ______________________
ImportError while importing test module 'tests/stub/t_zz.py'.
Traceback:
  File "tests/stub/t_zz.py", line 14, in <module>
    from nowhere import nothing
ModuleNotFoundError: No module named 'nowhere'
=========================== short test summary info ============================
ERROR tests/stub/t_zz.py - ModuleNotFoundError: No module named 'nowhere'
1 error in 0.30s
"""

SHAPES = {
    "failed checks": (FAILED_CHECKS, 1),
    "crashed after": (CRASHED_AFTER, 1),
    "crashed before": (CRASHED_BEFORE, 2),
    "passed": (CRASHED_AFTER.replace("......F", ".......").split("====")[0]
               + "\n23/23 checks passed\n7 passed in 9.81s\n", 0),
}


def parsed(shape):
    out, code = SHAPES[shape]
    return R.parse(out, code, 1.0)


def line_for(name, got, known=None):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        R.report(name, got, known)
    return buf.getvalue().rstrip("\n")


# ----------------------------------------------------- 2.1 which of three things

def the_three_kinds():
    print("\n2.1 a failed check, a crash after the checks, a crash before any")
    check("checks that failed are a failure", R.kind(parsed("failed checks")), "FAIL")
    check("a process that failed with every check passed is a crash",
          R.kind(parsed("crashed after")), "CRASH")
    check("a process that printed no summary is a failure, not a crash",
          R.kind(parsed("crashed before")), "FAIL")
    check("an exit of zero is a pass", R.kind(parsed("passed")), "ok")

    print("\n     what the runner reads off each")
    got = parsed("crashed after")
    check("the summary is still the count", got["summary"], "23/23 checks passed")
    check("no check line says FAIL", [l for l in got["checks"] if "FAIL" in l], [])
    check("what raised is read from pytest's own line",
          got["raised"], [("guarantee", "RuntimeError: Event loop is closed")])
    got = parsed("crashed before")
    check("a collection error names no part",
          got["raised"], [(None, "ModuleNotFoundError: No module named 'nowhere'")])
    got = parsed("failed checks")
    check("a failed check is not read as something raised",
          got["raised"], [("second_part", "PartFailed: 2 of 4 checks failed in second_part")])
    check("and its FAIL lines are still read",
          sum(1 for l in got["checks"] if "FAIL" in l), 2)

    print("\n     the marks on the line")
    check("failed checks", line_for("t_zz", parsed("failed checks")).split()[0], "FAIL")
    check("crashed after", line_for("t_zz", parsed("crashed after")).split()[0], "CRASH")
    check("crashed before", line_for("t_zz", parsed("crashed before")).split()[0], "FAIL")
    check("passed", line_for("t_zz", parsed("passed")).split()[0], "ok")


# ------------------------------------------------------------ 2.2 the cause

def the_cause_is_on_the_line():
    print("\n2.2 a crash says what raised, on the line and in the block")
    line = line_for("t_zz", parsed("crashed after"))
    check("the count is still there", "23/23 checks passed" in line, True)
    check("and the part that raised", "guarantee raised" in line, True)
    check("and the exception's last line",
          "RuntimeError: Event loop is closed" in line, True)
    check("the whole line, as printed",
          line, "  CRASH  t_zz           23/23 checks passed  · guarantee raised "
                "RuntimeError: Event loop is closed")

    print("\n     the block under the run")
    check("a crash's block names what raised",
          R.explain(parsed("crashed after")),
          ["guarantee raised RuntimeError: Event loop is closed"])
    check("a failure's block still echoes its FAIL lines, and only those",
          R.explain(parsed("failed checks")),
          ["FAIL the second thing", "FAIL the fourth thing"])
    check("a crash before any summary names the collection error",
          R.explain(parsed("crashed before")),
          ["collection raised ModuleNotFoundError: No module named 'nowhere'"])

    print("\n     a failed check's line is as it was")
    line = line_for("t_zz", parsed("failed checks"))
    check("no cause is put on it", "raised" in line, False)
    check("it reads as before", line, "  FAIL   t_zz           7/9 checks passed")

    print("\n     a process that died with no line from pytest at all")
    got = R.parse("  ok   one\n\n3/3 checks passed\n", 137, 1.0)
    check("is still a crash", R.kind(got), "CRASH")
    check("and says the exit code, having nothing else",
          R.cause(got), "exited 137, no check failed")
    check("which is also its block", R.explain(got), ["exited 137, no check failed"])

    print("\n     several parts raised")
    two = CRASHED_AFTER.replace(
        "1 failed, 6 passed",
        "FAILED tests/stub/t_zz.py::insertion - StopIteration\n1 failed, 6 passed")
    got = R.parse(two, 1, 1.0)
    check("the line names the first and counts the rest",
          R.cause(got), "guarantee raised RuntimeError: Event loop is closed (and 1 more)")
    check("the block names them all",
          R.explain(got), ["guarantee raised RuntimeError: Event loop is closed",
                           "insertion raised StopIteration"])


# ------------------------------------------------- 2.3 known and fixed still work

def known_and_fixed_for_a_crash():
    print("\n2.3 a known crash reads known; a listed suite that passes reads FIXED")
    saved = dict(R.KNOWN)
    try:
        R.KNOWN.clear()
        R.KNOWN["t_zz"] = ("crash:RuntimeError", "raises on the way out; not diagnosed")
        line = line_for("t_zz", parsed("crashed after"), R.KNOWN["t_zz"])
        check("the same crash is known", line.split()[0], "known")
        check("with its reason", "not diagnosed" in line, True)
        line = line_for("t_zz", parsed("passed"), R.KNOWN["t_zz"])
        check("passing is FIXED", line.split()[0], "FIXED")
        line = line_for("t_zz", parsed("failed checks"), R.KNOWN["t_zz"])
        check("failing a check instead is not the recorded failure",
              line.split()[0], "FAIL")
        check("and the line says what was recorded and what happened",
              "listed as crash:RuntimeError failing, now 2" in line, True)
        R.KNOWN["t_zz"] = (0, "an entry recorded from a crash, before this change")
        line = line_for("t_zz", parsed("crashed after"), R.KNOWN["t_zz"])
        check("an entry recording zero no longer absorbs a crash",
              line.split()[0], "FAIL")
    finally:
        R.KNOWN.clear()
        R.KNOWN.update(saved)


# ------------------------------------------------------ 3.1 what the list records

def the_signature_tells_them_apart():
    print("\n3.1 how each shape signs")
    check("failed checks sign as how many", KF.signature(parsed("failed checks")), 2)
    check("a crash after the checks signs as the exception",
          KF.signature(parsed("crashed after")), "crash:RuntimeError")
    check("a crash before any summary signs as its exception",
          KF.signature(parsed("crashed before")), "crash:ModuleNotFoundError")
    got = R.parse("  ok   one\n\n3/3 checks passed\n", 137, 1.0)
    check("a crash pytest never named signs as unknown",
          KF.signature(got), "crash:unknown")
    got = R.parse("Traceback (most recent call last):\n  File x\nsome.mod.OddError: boom\n", 1, 1.0)
    check("with no pytest line, the traceback's last exception is used",
          KF.signature(got), "crash:OddError")
    check("a crash never signs as zero",
          KF.signature(parsed("crashed after")) == 0, False)


# ------------------------------------------ 3.1 what the children are told

def the_children_print_utf8():
    import testtoken
    print("\n3.1 every child is told to read, write and print UTF-8")
    env = testtoken.child_env(_REPO, base={"PATH": "/bin"})
    check("a child without the setting gets it", env.get("PYTHONUTF8"), "1")
    env = testtoken.child_env(_REPO, base={"PATH": "/bin", "PYTHONUTF8": "0"})
    check("one already set outside is left as it was", env.get("PYTHONUTF8"), "0")
    check("nothing else about the base is lost", env.get("PATH"), "/bin")


# ------------------------------------------ 4.1 nothing is read without saying how

def _call_span(src, open_at):
    """Index of the ')' closing the call whose '(' is at `open_at`."""
    depth, i, quote = 0, open_at, None
    while i < len(src):
        c = src[i]
        if quote:
            if c == "\\":
                i += 1
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(src)


def _enclosing_call(src, at):
    """Index of the '(' of the innermost call still open at `at`."""
    depth = 0
    for i in range(at - 1, -1, -1):
        c = src[i]
        if c == ")":
            depth += 1
        elif c == "(":
            if depth == 0:
                return i
            depth -= 1
    return -1


import io as _io
import re as _re
import tokenize as _tokenize
_TEXT_CALL = _re.compile(r"(?<![\w.])open\(|\.(?:read_text|write_text)\(")
_BINARY = _re.compile(r"""['"][rwax+]*b[rwax+]*['"]""")


def _quoted(src):
    """Offset ranges of every string and comment token in `src`.

    A call mentioned in a docstring, a comment or a check's own text is not a
    call, and this scanner lives in a file full of such mentions.
    """
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    at = lambda row, col: starts[row - 1] + col
    spans = []
    try:
        for tok in _tokenize.generate_tokens(_io.StringIO(src).readline):
            if tok.type in (_tokenize.STRING, _tokenize.COMMENT):
                spans.append((at(*tok.start), at(*tok.end)))
    except (_tokenize.TokenError, SyntaxError, IndexError):
        pass
    return spans


def unencoded(src):
    """Line numbers of text reads, writes and decodes that name no encoding."""
    quoted = _quoted(src)
    inside = lambda pos: any(a <= pos < b for a, b in quoted)
    found = []
    for m in _TEXT_CALL.finditer(src):
        if inside(m.start()):
            continue
        close = _call_span(src, m.end() - 1)
        args = src[m.end():close]
        if "encoding" in args or _BINARY.search(args):
            continue
        if args.strip().startswith(("sys.", "fd", "os.dup")):
            continue
        found.append(src.count("\n", 0, m.start()) + 1)
    for m in _re.finditer(r"text=True", src):
        if inside(m.start()):
            continue
        o = _enclosing_call(src, m.start())
        if o >= 0 and "encoding" in src[o:_call_span(src, o)]:
            continue
        found.append(src.count("\n", 0, m.start()) + 1)
    return sorted(set(found))


def offenders_under(root):
    out = []
    for here, _dirs, names in _os.walk(root):
        if "__pycache__" in here or "fixtures" in here:
            continue
        for name in sorted(names):
            if name.endswith(".py"):
                path = _os.path.join(here, name)
                for line in unencoded(open(path, encoding="utf-8").read()):
                    out.append(f"{_os.path.relpath(path, _REPO)}:{line}")
    return out


def nothing_is_read_without_saying_how():
    print("\n4.1 every text read, write and decode under tests/ names its encoding")
    check("the scanner sees an unencoded open",
          unencoded('src = open(path).read()\n'), [1])
    check("and an unencoded read_text", unencoded('x = pathlib.Path(p).read_text()\n'), [1])
    check("and a decoded child without an encoding",
          unencoded('r = subprocess.run(cmd, capture_output=True,\n    text=True)\n'), [2])
    check("but not a binary open", unencoded('open(p, "rb").read()\n'), [])
    check("nor one that names its encoding",
          unencoded('open(p, encoding="utf-8").read()\nrun(x, text=True, encoding="utf-8")\n'), [])
    check("nor a call mentioned inside a string or a comment",
          unencoded('s = "open(path).read()"  # open(other)\n"""text=True"""\n'), [])
    check("nor a decode whose call names one, with a nested call before it",
          unencoded('subprocess.run(command_for(tier, name), capture_output=True, text=True, timeout=600, encoding="utf-8")\n'), [])
    check("nor a mention in a comment", unencoded('# open(x) is not called here\n'), [])
    found = offenders_under(_TESTS)
    check("no file under tests/ reads, writes or decodes text without an encoding",
          found, [])


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    the_three_kinds,
    the_cause_is_on_the_line,
    known_and_fixed_for_a_crash,
    the_signature_tells_them_apart,
    the_children_print_utf8,
    nothing_is_read_without_saying_how,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
