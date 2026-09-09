"""Groups 1 and 2 -- the labelling rule and the width it is trimmed to."""
import sys, re, pathlib
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
from main import _state_label as lab
ok = []
def chk(l, c, e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}" + (f"  {e}" if e else ""))

print("1.1 each configured state renders as expected")
for s, want in [("In progress", "progress"), ("In review", "review"),
                ("Requires improvement", "improvement")]:
    chk(f"{s!r} -> {want!r}", lab(s) == want, repr(lab(s)))

print("\n1.2 a state with no words is empty, not an error")
for s in ("", "   ", "\t\n"):
    try:
        chk(f"{s!r} -> ''", lab(s) == "", repr(lab(s)))
    except Exception as e:
        chk(f"{s!r} -> ''", False, f"raised {type(e).__name__}")

print("\n1.3 a last word wider than the column is cut, not overflowed")
long = "Needs " + "x" * 40
chk("cut to the column width", len(lab(long)) == M._WHEN_WIDTH, f"{len(lab(long))}")
chk("cut from the last word", lab(long) == "x" * M._WHEN_WIDTH, repr(lab(long)))
chk("no state ever exceeds the width",
    all(len(lab(s)) <= M._WHEN_WIDTH for s in
        ["In progress", "In review", "Requires improvement", "Submitted",
         "Waiting for a very long reply indeed", "", long]))

print("\n1.4 case is the rule's, not the tracker's")
chk("an already-lowercase state is unchanged in case", lab("in review") == lab("In review"))
chk("a capitalised state lowercases", lab("Requires Improvement") == "improvement", lab("Requires Improvement"))
chk("a shouted state lowercases", lab("IN PROGRESS") == "progress", lab("IN PROGRESS"))
chk("every configured state reads in lower case",
    all(lab(s) == lab(s).lower() for s in
        ["In progress", "In review", "Requires improvement", "Submitted", "TO VERIFY"]))
chk("two states differing only in case give the same label",
    lab("requires improvement") == lab("Requires Improvement"))

print("\n2.1 the width is eleven, and 'improvement' survives it")
chk("the width is 11", M._WHEN_WIDTH == 11, str(M._WHEN_WIDTH))
chk("'improvement' is intact", lab("Requires improvement") == "improvement")
chk("it needs every cell", len("improvement") == M._WHEN_WIDTH)

print("\n2.2 the width is written down once")
src = pathlib.Path(_REPO + "/main.py").read_text()
chk("the column takes the constant, not a literal",
    'add_column("When", key="when", width=_WHEN_WIDTH)' in src)
chk("the number 11 appears once, in the constant",
    len(re.findall(r"(?m)^_WHEN_WIDTH = 11$", src)) == 1
    and not re.search(r'width=8\b', src))
chk("nothing still trims to 8", "_STATE_WIDTH" not in src)

print("\n2.3 the widest label a task puts in the column still fits")
import singularity
from datetime import datetime, timedelta
now = datetime.now(singularity.SingularityClient().tz)
widest = max(len(singularity.overdue_label(now - timedelta(days=d), now))
             for d in (1, 9, 99, 999, 5000))
chk("the longest overdue label fits", widest <= M._WHEN_WIDTH, f"{widest} cells")
chk("'all-day' fits", len("all-day") <= M._WHEN_WIDTH)
chk("a time fits", len("14:30") <= M._WHEN_WIDTH)

print("\n4.1 two states that end in the same word")
chk("their labels coincide", lab("In review") == lab("Needs review") == "review")
chk("and neither is empty", lab("In review") != "")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
