"""A recurring series, as the board reads it and as it puts it into words.

Nothing here reaches the store, starts an application or needs a terminal.
The rules below are built by hand from the shapes a real account was observed
to hold, and from the shapes it did not hold -- which is the more important
half: the store's own API documents the recurrence object as having no fields
at all, so every reader under test has to answer "I cannot read that" rather
than assume the shape held.

Every task here is invented.
"""
import datetime as dt
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
from harness import run_parts
import board
import singularity
from singularity import Task

ok = []
def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

#: The three rules the account was observed to hold, spelled the way the
#: store spells them -- including the `type` number that duplicates the tag,
#: because a reader that quietly depended on it would pass without it here.
WEEKLY = {"everyweek": {"days": [2], "interval": 1, "type": 1}}
WORKWEEK = {"everyweek": {"days": [1, 2, 3, 4, 5], "interval": 1, "type": 1}}
MONTHLY = {"everymonth": {"days": [{"dayNumber": 16}], "interval": 1, "type": 2}}
DAILY = {"everyday": {"interval": 1}}
#: A series' ending, in the one mode the account used: `limit` says never, and
#: the other two fields are inert -- `date` is a copy of the start, which is
#: exactly the trap the reader must not fall into.
ENDLESS = {"limit": 5, "date": "2024-09-03T21:00:00.000Z", "iterations": 105}


def series(repeat=WEEKLY, *, waits=False, next_time="2026-09-22T21:00:00.000Z",
           time=None, ending=ENDLESS, tid="S-1"):
    """A series task: one carrying a rule."""
    rec = {"repeat": repeat, "startTime": "2024-09-03T21:00:00.000Z",
           "lastTime": "2026-09-15T21:00:00.000Z",
           "lastGeneratedTaskId": "T-furthest", "ending": ending}
    if next_time is not None:
        rec["nextTime"] = next_time
    if waits:
        rec["onlyOnComplete"] = True
    if time is not None:
        rec["time"] = time
    return Task({"id": tid, "title": "a series", "checked": 0,
                 "deferred": False, "useTime": False, "recurrence": rec})


def occurrence(tid="T-1", of="S-1"):
    """An occurrence: one carrying a parent and no rule of its own."""
    return Task({"id": tid, "title": "an occurrence", "checked": 0,
                 "deferred": False, "useTime": False,
                 "recurrenceGeneratorId": of})


def plain(tid="P-1"):
    return Task({"id": tid, "title": "a plain task", "checked": 0,
                 "deferred": False, "useTime": False})


# --------------------------------------- 2.1 / 2.2 a series and an occurrence

def a_series_and_an_occurrence_are_told_apart():
    print("\n2.1 the facts a series carries, named for what they mean")
    s = series(waits=True, time="18:00")
    check("it is recurring, as it always was", s.recurring)
    check("it waits for completion", s.waits_for_completion)
    check("its next occurrence is read",
          s.next_occurrence.isoformat(), "2026-09-22T21:00:00+00:00")
    check("its time of day is the store's own string", s.series_time, "18:00")
    check("its rule is readable", s.repeat.readable)
    check("and it is known to run forever", s.ends_never)

    print("\n     a series that does not wait says so in the other direction")
    check("not waiting is False, not None",
          series(waits=False).waits_for_completion, False)

    print("\n2.2 which rows are series, which are occurrences, which neither")
    s, o, p = series(), occurrence(), plain()
    check("a series carries no parent", s.series_id, None)
    check("an occurrence names its series", o.series_id, "S-1")
    check("and carries no rule of its own", o.recurring, False)
    check("a plain task is neither", (p.recurring, p.series_id), (False, None))

    print("\n     a task with no rule reports nothing about one")
    check("no wait, no next, no time",
          (p.waits_for_completion, p.next_occurrence, p.series_time),
          (False, None, None))
    check("its rule is unreadable rather than absent", p.repeat.readable, False)
    check("and its ending was not read", p.ending_read, False)


# ------------------------------------------- 2.3 an unreadable rule, never a guess

def an_unreadable_repeat_is_never_guessed():
    print("\n2.3 a rule the board cannot read says so, and never raises")
    # The shapes that matter are the ones nobody has seen.  A yearly tag
    # almost certainly exists and the account had none; the rest are the ways
    # a hand-edited or newer store could differ.
    cases = {
        "the whole object is not an object": "nonsense",
        "no repeat at all": {},
        "an empty repeat": {"repeat": {}},
        "two tags at once": {"repeat": {"everyday": {"interval": 1},
                                        "everyweek": {"days": [1], "interval": 1}}},
        "a tag nobody has seen": {"repeat": {"everyyear": {"interval": 1}}},
        "a payload that is not an object": {"repeat": {"everyday": 7}},
        "a weekday out of range": {"repeat": {"everyweek": {"days": [9], "interval": 1}}},
        "an empty day list": {"repeat": {"everyweek": {"days": [], "interval": 1}}},
        "a weekly day that is not a number": {
            "repeat": {"everyweek": {"days": ["Tue"], "interval": 1}}},
        "a monthly day that is not an object": {
            "repeat": {"everymonth": {"days": [16], "interval": 1}}},
        "a month day out of range": {
            "repeat": {"everymonth": {"days": [{"dayNumber": 99}], "interval": 1}}},
        "an interval of zero": {"repeat": {"everyday": {"interval": 0}}},
        "an interval that is not a number": {"repeat": {"everyday": {"interval": "1"}}},
        "an interval that is a boolean": {"repeat": {"everyday": {"interval": True}}},
    }
    for name, rec in cases.items():
        try:
            got = singularity.parse_repeat(rec)
        except Exception as exc:                       # noqa: BLE001 - the point
            check(f"{name}: read without raising", f"raised {type(exc).__name__}", "no raise")
            continue
        check(f"{name}: reported unreadable", got.readable, False)

    print("\n     and the words for it are the admission, not a phrase")
    check("an unreadable rule is said to be unreadable",
          board.repeat_phrase(singularity.UNREADABLE), "repeat cannot be read")

    print("\n     a disagreeing type number is ignored, not trusted")
    # `type` duplicates the tag and can contradict it.  The tag is the key
    # the payload hangs off, so it wins and the rule still reads.
    lying = {"repeat": {"everyweek": {"days": [2], "interval": 1, "type": 99}}}
    got = singularity.parse_repeat(lying)
    check("the tag decides the kind", (got.readable, got.kind), (True, "everyweek"))


# ----------------------------------------------- 2.4 the ending, read narrowly

def the_ending_is_read_only_where_it_is_known():
    print("\n2.4 the one ending mode that is known, and the rest admitted")
    endless = series(ending=ENDLESS)
    check("the observed mode means it never ends", endless.ends_never)
    check("and counts as read", endless.ending_read)

    print("\n     any other mode is an ending the board cannot read")
    for limit in (0, 1, 2, 3, 4, 6, None, "5"):
        s = series(ending={"limit": limit, "date": "2024-09-03T21:00:00.000Z",
                           "iterations": 105})
        check(f"limit={limit!r}: not claimed to be endless", s.ends_never, False)
        check(f"limit={limit!r}: and not claimed to be read", s.ending_read, False)

    print("\n     the start date is never reported as the end")
    # The trap: in the observed mode `ending.date` is an exact copy of
    # `startTime`, so a reader that returned it would report the day a series
    # began as the day it stops.
    never, when = singularity.parse_ending(
        {"ending": {"limit": 2, "date": "2024-09-03T21:00:00.000Z"},
         "startTime": "2024-09-03T21:00:00.000Z"})
    check("an unread ending yields no date at all", (never, when), (False, None))
    check("a malformed ending is unread, not a crash",
          singularity.parse_ending({"ending": "soon"}), (False, None))


# --------------------------------------------------- 3.1 the rule, in words

def a_repeat_in_words():
    print("\n3.1 a rule a person can check against their intention")
    said = {
        "every day":                    {"everyday": {"interval": 1}},
        "every 3 days":                 {"everyday": {"interval": 3}},
        "every week on Tue":            WEEKLY,
        "every weekday":                WORKWEEK,
        "every 2 weeks on Tue":         {"everyweek": {"days": [2], "interval": 2}},
        "every week on Mon, Wed, Fri":  {"everyweek": {"days": [1, 3, 5], "interval": 1}},
        "every day of the week":        {"everyweek": {"days": [0, 1, 2, 3, 4, 5, 6],
                                                       "interval": 1}},
        "every month on the 16th":      MONTHLY,
        "every month on the 1st":       {"everymonth": {"days": [{"dayNumber": 1}],
                                                        "interval": 1}},
        "every month on the 2nd":       {"everymonth": {"days": [{"dayNumber": 2}],
                                                        "interval": 1}},
        "every month on the 3rd":       {"everymonth": {"days": [{"dayNumber": 3}],
                                                        "interval": 1}},
        "every month on the 11th":      {"everymonth": {"days": [{"dayNumber": 11}],
                                                        "interval": 1}},
        "every month on the 21st":      {"everymonth": {"days": [{"dayNumber": 21}],
                                                        "interval": 1}},
        "every month on the 31st":      {"everymonth": {"days": [{"dayNumber": 31}],
                                                        "interval": 1}},
        "every 6 months on the 1st and 31st": {
            "everymonth": {"days": [{"dayNumber": 31}, {"dayNumber": 1}],
                           "interval": 6}},
    }
    for want, repeat in said.items():
        got = board.repeat_phrase(singularity.parse_repeat({"repeat": repeat}))
        check(f"{want!r}", got, want)

    print("\n     Sunday is the store's day zero, not Monday")
    # Read off a real account: a weekly series on day 1 fell on a Monday.  The
    # other convention would phrase a working-week series as Tue to Sat.
    check("day 0 is Sunday",
          board.repeat_phrase(singularity.parse_repeat(
              {"repeat": {"everyweek": {"days": [0], "interval": 1}}})),
          "every week on Sun")
    check("days 1 to 5 are the working week, not Tue to Sat",
          board.repeat_phrase(singularity.parse_repeat({"repeat": WORKWEEK})),
          "every weekday")


# ------------------------------------------- 3.2 the line a series shows

def the_facts_a_series_shows():
    print("\n3.2 the facts line: the rule, the stacking, what is queued, the end")
    waiting = board.series_facts(series(repeat=WEEKLY, waits=True), queued=1,
                                 furthest=dt.date(2026, 9, 22))
    check("a waiting series names the waiting",
          waiting, "every week on Tue  ·  waits for completion  ·  "
                   "1 queued to 22 Sep 2026  ·  no end")

    stacking = board.series_facts(series(repeat=WORKWEEK), queued=60,
                                  furthest=dt.date(2027, 11, 5))
    check("a stacking series says so rather than staying silent",
          stacking, "every weekday  ·  piles up  ·  "
                    "60 queued to 05 Nov 2027  ·  no end")

    print("\n     both directions are named, so neither reads as a failure")
    check("the waiting one says which", "waits for completion" in waiting)
    check("the stacking one says which", "piles up" in stacking)
    check("and they are not the same word",
          "piles up" in waiting, False)

    print("\n     nothing queued, and a time of day")
    check("an empty queue is said, not omitted",
          board.series_facts(series(repeat=DAILY, time="18:00"), queued=0),
          "every day  ·  at 18:00  ·  piles up  ·  none queued  ·  no end")

    print("\n     an unreadable rule still gets a line")
    bare = Task({"id": "S-x", "title": "odd", "checked": 0, "deferred": False,
                 "useTime": False,
                 "recurrence": {"repeat": {"everyyear": {"interval": 1}},
                                "ending": {"limit": 2}}})
    got = board.series_facts(bare, queued=3, furthest=dt.date(2027, 1, 1))
    check("it admits the rule and reports the rest",
          got, "repeat cannot be read  ·  piles up  ·  "
               "3 queued to 01 Jan 2027  ·  end cannot be read")
    check("and never phrases a rule it did not read",
          "every" in got.split("·")[0], False)


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    a_series_and_an_occurrence_are_told_apart,
    an_unreadable_repeat_is_never_guessed,
    the_ending_is_read_only_where_it_is_known,
    a_repeat_in_words,
    the_facts_a_series_shows,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
