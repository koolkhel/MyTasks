"""Which calendars a configuration names: an account, a calendar, or neither.

Invented account and calendar names throughout.  Nothing here comes from a
real machine, nothing here is a real person's calendar, and nothing here
touches the framework, a file or the network -- which is what lets it run in
the tier that needs nothing beyond the repository, on a machine that has no
calendar at all and no pyobjc installed.

The names are not ASCII on purpose.  The rule this checks turns on
composition, and a fixture written in ASCII would agree with a broken rule.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import unicodedata
import ical
from parts import run_parts

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


def cfg(*names, work=""):
    """A configuration naming these entries, none of them work unless said."""
    return ical.Config(work=work, personal=tuple(names))


#: Two invented accounts.
HOME, WORK = "Домашний", "Контора"

#: What an invented machine offers: (account, calendar, identifier).  Every
#: title here is distinct, so a part naming one of them is asking about one
#: thing; the cases where names collide get fixtures of their own below.
OFFERED = (
    (HOME, "Семейный", "h1"),
    (HOME, "Поездки", "h2"),
    (WORK, "Смены", "w1"),
    (WORK, "Дежурства", "w2"),
)

#: A machine where one name is an account and is also some other account's
#: calendar.  There is no precedence to appeal to between the two, so the
#: rule reads both, and this is the fixture that says so.
BOTH = (
    (HOME, "Семейный", "b1"),
    (WORK, HOME, "b2"),
)

#: One title in each of its two forms.  Asserted to differ before anything is
#: checked against them: were they equal the checks below would pass without
#: the rule doing anything at all, which is the way a fixture lies.
COMPOSED = unicodedata.normalize("NFC", "Майский")
DECOMPOSED = unicodedata.normalize("NFD", "Майский")


def the_fixture_is_worth_checking_against():
    print("the two forms of the name really are different strings")
    check("composed and decomposed differ", COMPOSED == DECOMPOSED, False)
    check("and are the same name", COMPOSED,
          unicodedata.normalize("NFC", DECOMPOSED))


def naming_an_account():
    print("an entry naming an account reads every calendar in it")
    chosen = ical.select(cfg(HOME), OFFERED)
    check("all of that account", chosen.identifiers, ("h1", "h2"))
    check("and none of the other", chosen.unmatched, ())


def naming_a_calendar():
    print("an entry naming a calendar reads that calendar")
    chosen = ical.select(cfg("Смены"), OFFERED)
    check("that one", chosen.identifiers, ("w1",))
    check("nothing unmatched", chosen.unmatched, ())


def naming_a_calendar_leaves_its_account_alone():
    print("naming one calendar does not bring in the rest of its account")
    chosen = ical.select(cfg("Семейный"), OFFERED)
    check("only the calendar named", chosen.identifiers, ("h1",))
    check("its account's other calendar is not read", "h2" in chosen.identifiers,
          False)


def a_name_that_is_both():
    print("a name belonging to an account and to a calendar reads both")
    chosen = ical.select(cfg(HOME), BOTH)
    check("the account's calendar and the like-named one",
          chosen.identifiers, ("b1", "b2"))
    check("nothing unmatched", chosen.unmatched, ())


def named_twice_read_once():
    print("a calendar named by its account and by itself is read once")
    chosen = ical.select(cfg(HOME, "Семейный"), OFFERED)
    check("once, not twice", chosen.identifiers.count("h1"), 1)
    check("and the account's other calendar is still there",
          chosen.identifiers, ("h1", "h2"))
    check("in the order the machine offered them",
          chosen.identifiers, tuple(i for _, _, i in OFFERED if i.startswith("h")))


def composition_does_not_decide_a_match():
    print("a name matches whichever way either side is composed")
    machine_composed = ((HOME, COMPOSED, "d1"),)
    machine_decomposed = ((HOME, DECOMPOSED, "d1"),)
    check("decomposed entry, composed calendar",
          ical.select(cfg(DECOMPOSED), machine_composed).identifiers, ("d1",))
    check("composed entry, decomposed calendar",
          ical.select(cfg(COMPOSED), machine_decomposed).identifiers, ("d1",))
    check("and neither is reported unmatched",
          (ical.select(cfg(DECOMPOSED), machine_composed).unmatched,
           ical.select(cfg(COMPOSED), machine_decomposed).unmatched), ((), ()))


def case_does_not_decide_a_match():
    print("a name matches whatever case it is written in")
    chosen = ical.select(cfg(HOME.upper(), "смены"), OFFERED)
    check("the account, upper-cased", "h1" in chosen.identifiers, True)
    check("the calendar, lower-cased", "w1" in chosen.identifiers, True)
    check("nothing unmatched", chosen.unmatched, ())


def a_name_matching_nothing():
    print("an entry naming nothing is reported, and the rest are still read")
    chosen = ical.select(cfg(HOME, "Нет такого"), OFFERED)
    check("what did match is still selected", chosen.identifiers, ("h1", "h2"))
    check("and only the one that did not is reported",
          chosen.unmatched, ("Нет такого",))
    check("it is named in the words the board says",
          "Нет такого" in ical.unmatched_message(chosen.unmatched), True)


def unmatched_entries_keep_the_order_they_were_configured():
    print("several unmatched entries are reported in the order they were typed")
    chosen = ical.select(cfg("Зет", "Альфа"), OFFERED)
    check("as configured, not sorted", chosen.unmatched, ("Зет", "Альфа"))
    check("nothing was selected", chosen.identifiers, ())


def nothing_configured():
    print("a configuration naming nothing selects nothing and reports nothing")
    chosen = ical.select(cfg(), OFFERED)
    check("no calendar", chosen.identifiers, ())
    check("no complaint", chosen.unmatched, ())
    check("and the board is given no message to show",
          ical.unmatched_message(chosen.unmatched), "")


def work_is_matched_the_same_way():
    print("what counts as work matches an account or a calendar, alike")
    check("the work account's event", cfg(work=HOME).is_work(HOME, "Семейный"), True)
    check("a calendar named as work",
          cfg(work="Семейный").is_work(HOME, "Семейный"), True)
    check("an event named by neither",
          cfg(work=WORK).is_work(HOME, "Семейный"), False)
    check("no work configured, nothing is work",
          cfg().is_work(HOME, "Семейный"), False)
    check("composition does not decide it",
          cfg(work=DECOMPOSED).is_work(HOME, COMPOSED), True)
    check("nor does case", cfg(work=HOME.upper()).is_work(HOME, "Семейный"), True)
    check("an untitled account and calendar are not work",
          cfg(work=HOME).is_work("", ""), False)


#: The parts this suite is made of, in the order they run.  One list, read by
#: the runner to report and select them one at a time, and by the file itself
#: when it is run directly -- so both ways run the same parts.
PARTS = (
    the_fixture_is_worth_checking_against,
    naming_an_account,
    naming_a_calendar,
    naming_a_calendar_leaves_its_account_alone,
    a_name_that_is_both,
    named_twice_read_once,
    composition_does_not_decide_a_match,
    case_does_not_decide_a_match,
    a_name_matching_nothing,
    unmatched_entries_keep_the_order_they_were_configured,
    nothing_configured,
    work_is_matched_the_same_way,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
