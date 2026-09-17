"""What a pasted line is read as, and what survives a round trip.

Pure functions only: nothing here builds a board, reaches an account or
touches a clipboard. Every line is invented.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import main
from harness import run_parts
from main import as_markdown, from_markdown
from singularity import CANCELLED, CHECKED, EMPTY

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------------ 2.2

def group_2_2():
    print("2.2 the decoration comes off and the box is read")

    print("\n  bullets of every kind")
    for line, why in (("- a hyphen", "a hyphen"),
                      ("* an asterisk", "an asterisk"),
                      ("+ a plus", "a plus")):
        check(why, from_markdown(line), (line.split(" ", 1)[1], False))
    check("a number with a full stop", from_markdown("1. numbered"),
          ("numbered", False))
    check("a number with a bracket", from_markdown("2) bracketed"),
          ("bracketed", False))
    check("a long number", from_markdown("137. still numbered"),
          ("still numbered", False))

    print("\n  a bullet needs its space, so a title is not eaten")
    # "-5 degrees" is a title, not an empty bullet followed by "5 degrees".
    check("a hyphen against a digit is part of the title",
          from_markdown("-5 degrees outside"), ("-5 degrees outside", False))
    check("a word beginning with a plus is a title",
          from_markdown("+VAT on the invoice"), ("+VAT on the invoice", False))

    print("\n  checkboxes")
    check("an empty box", from_markdown("- [ ] write the docs"),
          ("write the docs", False))
    check("a ticked box", from_markdown("- [x] fix the build"),
          ("fix the build", True))
    check("a ticked box in capitals", from_markdown("- [X] fix the build"),
          ("fix the build", True))
    # A box with no bullet in front of it is still a box.  Nothing else in
    # brackets is: only a space or a tick reads as one, so a title opening
    # with a word in brackets is left alone.
    check("a box with no bullet", from_markdown("[x] no bullet"),
          ("no bullet", True))
    check("a bracketed word is not a box",
          from_markdown("- [draft] finish the report"),
          ("[draft] finish the report", False))

    print("\n  indentation, which this board has nowhere to put")
    check("tabs", from_markdown("\t\t- an indented child"),
          ("an indented child", False))
    check("spaces", from_markdown("    - an indented child"),
          ("an indented child", False))
    check("tabs before a box", from_markdown("\t- [x] an indented finished child"),
          ("an indented finished child", True))

    print("\n  a line with no decoration at all")
    check("a plain line is a title in full", from_markdown("plain line"),
          ("plain line", False))
    check("and keeps its inner punctuation",
          from_markdown("review the 2.1 release notes"),
          ("review the 2.1 release notes", False))

    print("\n  nothing else in the line is interpreted")
    check("a trailing tag survives untouched",
          from_markdown("- ship v2 @done(2026-09-15)"),
          ("ship v2 @done(2026-09-15)", False))
    check("a date in brackets survives",
          from_markdown("- pay the invoice [due Friday]"),
          ("pay the invoice [due Friday]", False))
    check("a tag does not tick the box",
          from_markdown("- ship v2 @done(2026-09-15)")[1], False)


# ------------------------------------------------------------------ 2.3

def group_2_3():
    print("\n2.3 out and straight back")
    title = "fix the build before Friday"

    out = as_markdown(title, EMPTY)
    check("an unfinished row goes out and comes back unfinished",
          from_markdown(out), (title, False))

    out = as_markdown(title, CHECKED)
    check("a finished row goes out and comes back finished",
          from_markdown(out), (title, True))

    # The one thing the trip cannot carry.  Markdown has two boxes and this
    # board has three states, so cancelled comes back finished -- asserted
    # here as the documented loss rather than as equality, so that a change
    # which quietly started restoring it would show up as a failing check
    # rather than as a passing one.
    out = as_markdown(title, CANCELLED)
    check("a cancelled row comes back finished, with the title intact",
          from_markdown(out), (title, True))
    check("and no tildes are left in that title",
          "~" in from_markdown(as_markdown(title, CANCELLED))[0], False)

    print("\n  a title that looks like decoration survives the trip")
    for odd in ("- not really a bullet", "[x] not really a box",
                "~~not really struck~~", "1. not really numbered"):
        check(f"{odd!r} out and back",
              from_markdown(as_markdown(odd, EMPTY)), (odd, False))
    # The one title the trip still cannot carry whole: a finished task whose
    # own title is wrapped in tildes is indistinguishable from a cancelled
    # one, because that is exactly the line the board writes for cancelled.
    # Asserted as the known loss, so narrowing it further would show up here.
    check("a finished title wrapped in tildes loses them",
          from_markdown(as_markdown("~~struck~~", CHECKED)), ("struck", True))


# ------------------------------------------------------------------ 2.4

def group_2_4():
    print("\n2.4 a line that holds no task")
    check("an empty line", from_markdown(""), None)
    check("a line of spaces", from_markdown("    "), None)
    check("a line of tabs", from_markdown("\t\t"), None)
    check("a bullet with nothing after it", from_markdown("- "), None)
    check("a bare bullet", from_markdown("-"), None)
    check("a bare number", from_markdown("1."), None)
    check("a bullet and an empty box", from_markdown("- [ ]"), None)

    print("\n  a pasted block with blank lines in it")
    block = "- first\n\n- second\n   \n- third\n"
    read = [from_markdown(line) for line in block.splitlines()]
    check("five lines in", len(read), 5)
    check("three tasks out", [r for r in read if r],
          [("first", False), ("second", False), ("third", False)])
    check("and no task has an empty title",
          all(r[0].strip() for r in read if r), True)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    group_2_2,
    group_2_3,
    group_2_4,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
