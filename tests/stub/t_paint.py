"""What the board would draw, asked without a terminal.

No application is started here and no table is built: this suite hands a
`board.Board` the state a view would have and reads back the rows, the cells
and the line under them.  That is the whole point of it -- if deciding what to
draw ever needs a screen again, this file stops working, and nothing else in
the tier would notice.

`run_test` appears nowhere below, deliberately.  A check here that reached for
a Textual application would still pass while proving nothing.

Every task, event, issue and message is invented.
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
from harness import *
import board
import ical
import mail
import singularity
import tracker
from singularity import Bucket

TZ = local_tz()
TODAY = dt.datetime.now(TZ).date()
NOW = dt.datetime.combine(TODAY, dt.time(12, 0), tzinfo=TZ)

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

CAL = ical.Config(work="WorkAcc", personal=("Me",))
TRACK = tracker.Config(base_url="https://tracker.invalid", token="zz",
                       assignee="me", projects=("ZZA",), states=("open",))

def timed(tid, title, hh, checked=0):
    """A task of the day, at an hour."""
    t = mk(tid, title, TODAY, checked=checked, timed=True)
    t.raw["start"] = iso_z(dt.datetime.combine(TODAY, dt.time(hh, 0), tzinfo=TZ))
    return t

def event(title, hh, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False)

def issue(key, summary):
    return tracker.Issue(key=key, summary=summary, project="ZZA",
                         state="open", assignee="me",
                         base_url="https://tracker.invalid",
                         priority="Major", priority_value="Major")

def message(subject, sender, hh):
    when = dt.datetime.combine(TODAY, dt.time(hh, 0), tzinfo=TZ)
    return mail.Message(sender=sender, subject=subject, when=when,
                        ident=f"<{subject}@invalid>", answers=None,
                        body="", text=subject)

def thread(*messages):
    return mail.Thread(messages=tuple(messages))


def painting(position=TODAY, *, tasks=(), events=(), issues=(), threads=(),
             marked=(), searching="", hiding_work=False, notice=None,
             fetched=True, projects=None, green_tag=None, reference=None,
             width=60, **paint):
    """What the board would draw, given exactly this and nothing else.

    Every argument the board reads is named here, so a check can change one
    of them and nothing else.  Where the application would measure the
    screen, this passes a number: that is the arrangement under test.
    """
    rows = list(tasks)
    made = board.Board(
        base=rows, pending={}, tasks=rows, position=position,
        reference=reference, tz=TZ, now=NOW, projects=projects or {},
        marked=list(marked), marked_rows={t.id: t for t in rows},
        searching=searching, hiding_work=hiding_work, work_project="P-work",
        window_reason_now=None, work_override=None, green_tag=green_tag,
        tracker_issues=list(issues), tracker_config=TRACK,
        events=list(events), events_day=position, calendar_config=CAL,
        mail_threads=list(threads), notice=notice, fetched=fetched,
        title_width=width, late_colour="#d17e92",
    )
    return made, made.paint(**paint)


def titles(answer):
    return [t.display_title for t in answer.rows]


# ------------------------------------------- 1. the rows, with no screen at all

def one_view_of_every_source():
    print("\n1.1 a day's rows, decided with nothing started")
    made, answer = painting(
        tasks=[timed("T-1", "write it up", 9), timed("T-2", "ship it", 15)],
        events=[event("standup", 10)],
        issues=[issue("ZZA-1", "an issue")],
    )
    check("every source is on it",
          len(answer.rows), 4)
    check("the day's own tasks are there",
          [t.display_title for t in answer.rows if not
           (made.is_event(t) or made.is_tracker(t) or made.is_mail(t))],
          ["write it up", "ship it"])
    check("the event is placed by its hour, between the two tasks",
          titles(answer).index("standup"), 1)
    check("the tracker's block sits below the day's unfinished work",
          titles(answer)[-1], "ZZA-1 — an issue")
    check("and the counts say what each source contributed",
          (answer.shown_issues, answer.shown_events, answer.shown_mail),
          (1, 1, 0))


def the_inbox_holds_mail():
    print("\n1.2 the inbox, where mail belongs and the tracker does not")
    made, answer = painting(
        Bucket.INBOX,
        tasks=[mk("T-3", "triage this")],
        issues=[issue("ZZA-2", "not here")],
        threads=[thread(message("a subject", "someone@invalid", 8),
                        message("re: a subject", "someone@invalid", 9))],
    )
    check("the task and the thread are drawn", len(answer.rows), 2)
    check("mail follows the tasks rather than leading them",
          made.is_mail(answer.rows[-1]), True)
    check("the tracker's rows are not in the inbox", answer.shown_issues, 0)
    check("one thread is shown", answer.shown_mail, 1)
    check("and the messages behind it are counted", answer.shown_messages, 2)


def the_filters_take_rows_away():
    print("\n1.3 what the search and the work filter withhold")
    rows = [timed("T-4", "alpha", 9), timed("T-5", "beta", 10)]
    made, answer = painting(tasks=rows, searching="alp")
    check("only the matching row is drawn", titles(answer), ["alpha"])
    check("and the number withheld is reported", answer.hidden_by_search, 1)
    made, answer = painting(tasks=rows, searching="ALP")
    check("the search does not mind the case", titles(answer), ["alpha"])
    made, answer = painting(tasks=rows)
    check("with no search nothing is withheld",
          (len(answer.rows), answer.hidden_by_search), (2, 0))


# --------------------------------------------- 2. the cells, likewise unscreened

def the_cells_are_text():
    print("\n2.1 every cell of a row, as text, with no table to hold it")
    made, answer = painting(tasks=[timed("T-6", "a plain task", 9)])
    cells = made.row_for(answer.rows[0])
    check("five cells", len(cells), 5)
    check("the second carries the row's own mark",
          cells[1], board.MARKS[singularity.EMPTY])
    check("the fourth is the title", cells[3].plain, "a plain task")


def a_finished_task_is_struck():
    print("\n2.2 finishedness is in the cell, not in a colour")
    made, answer = painting(
        tasks=[timed("T-7", "done and dusted", 9, checked=singularity.CHECKED)])
    title = made.row_for(answer.rows[0])[3]
    check("the title reads as it was written", title.plain, "done and dusted")
    check("and it is struck through",
          any("strike" in str(s.style) for s in title.spans), True)


def a_marked_row_keeps_its_own_mark():
    print("\n2.3 a marked row says so beside its own mark")
    made, answer = painting(tasks=[timed("T-8", "taking this one", 9)],
                            marked=["T-8"])
    cell = made.row_for(answer.rows[0])[1]
    check("the copy mark leads the row's own", cell[0], board.COPY_MARK)
    check("and the row's own mark is still there", len(cell), 2)


def a_long_title_says_it_was_cut():
    print("\n2.4 a title too long for the column says so")
    made, answer = painting(tasks=[timed("T-9", "x" * 200, 9)], width=40)
    title = made.row_for(answer.rows[0])[3]
    check("cut to the width it was given", len(title.plain), 40)
    check("and it ends in an ellipsis", title.plain.endswith("…"), True)


# ------------------------------------------------------ 3. the line under them

def the_line_counts_what_is_drawn():
    print("\n3.1 the status line, composed without a bar to write it on")
    made, answer = painting(
        tasks=[timed("T-10", "one", 9), timed("T-11", "two", 10,
                                              checked=singularity.CHECKED)],
        events=[event("standup", 11)],
        issues=[issue("ZZA-3", "an issue")],
    )
    check("it is one line", "\n" in answer.status, False)
    check("the tasks are counted, and the tracker's rows are not among them",
          answer.status.startswith("2 task(s) · 1 done"), True)
    check("the issue is counted beside them", "1 tracked" in answer.status, True)
    check("and so is the event", "1 event(s)" in answer.status, True)
    check("it is not an error", answer.status_error, False)


def the_line_says_what_was_withheld():
    print("\n3.2 what a filter took away is said beside the count, not instead")
    made, answer = painting(
        tasks=[timed("T-12", "alpha", 9), timed("T-13", "beta", 10)],
        searching="alp")
    check("the row count is the number of rows drawn",
          answer.status.startswith("1 task(s)"), True)
    check("and the withheld row is reported beside it",
          "1 hidden by search" in answer.status, True)


def the_line_counts_the_marks():
    print("\n3.3 every mark is counted, including one this view cannot draw")
    made, answer = painting(tasks=[timed("T-14", "here", 9)],
                            marked=["T-14", "T-elsewhere"])
    check("both marks are counted", "2 marked" in answer.status, True)


def a_notice_outranks_the_counts():
    print("\n3.4 a notice, and a view whose tasks have not arrived")
    made, answer = painting(tasks=[timed("T-15", "here", 9)],
                            notice=("Something failed", True))
    check("the notice is what the line says", answer.status, "Something failed")
    check("and it is an error", answer.status_error, True)
    made, answer = painting(tasks=[], fetched=False)
    check("before the fetch the line says so", answer.status, "Loading…")
    check("and that is not an error", answer.status_error, False)


# ------------------------------------------------------------- 4. the cursor

def the_cursor_follows_the_row():
    print("\n4.1 where the cursor lands, decided without a table")
    rows = [timed("T-16", "first", 9), timed("T-17", "second", 10),
            timed("T-18", "third", 11)]
    made, answer = painting(tasks=rows, keep="T-17", previous=0,
                            scroll=4, drawn_for=TODAY)
    check("it follows the row it was on", answer.cursor, 1)
    check("and the view is held where it was", answer.scroll, 4)


def a_gone_row_keeps_the_line():
    print("\n4.2 the row it was on has gone, in the same view")
    rows = [timed("T-19", "first", 9), timed("T-20", "second", 10)]
    made, answer = painting(tasks=rows, keep="T-gone", previous=1,
                            scroll=7, drawn_for=TODAY)
    check("the line the departed row had is kept", answer.cursor, 1)
    check("and the view still does not move", answer.scroll, 7)


def another_view_begins_at_its_beginning():
    print("\n4.3 a different view carries nothing over")
    rows = [timed("T-21", "first", 9), timed("T-22", "second", 10)]
    made, answer = painting(tasks=rows, keep="T-gone", previous=1,
                            scroll=200, drawn_for=Bucket.INBOX)
    check("it begins at the top", answer.cursor, 0)
    check("and the position it was scrolled to is dropped", answer.scroll, 0)


def no_rows_means_no_cursor():
    print("\n4.4 a view holding nothing")
    made, answer = painting(tasks=[], keep="T-gone", previous=3, scroll=5,
                            drawn_for=TODAY)
    check("there is no row to be on", answer.cursor, None)
    check("and the line says the view is empty",
          answer.status.startswith("0 task(s)"), True)


# ------------------------------------------------- 5. and it needs no terminal

def nothing_here_touched_a_screen():
    print("\n5.1 what this suite did not need")
    # Not "did this file mention an application" -- it could mention one and
    # still be honest.  This is the stronger statement: deciding what the
    # board draws did not need the application to exist at all, so importing
    # it never happened, in this process or anything this file pulled in.
    check("the application was never imported", "main" in sys.modules, False)
    check("and the module under test names no widget",
          any(line.startswith("from textual.widgets")
              or line.startswith("from textual.app")
              for line in open(board.__file__, encoding="utf-8")),
          False)


for part in (one_view_of_every_source, the_inbox_holds_mail,
             the_filters_take_rows_away, the_cells_are_text,
             a_finished_task_is_struck, a_marked_row_keeps_its_own_mark,
             a_long_title_says_it_was_cut, the_line_counts_what_is_drawn,
             the_line_says_what_was_withheld, the_line_counts_the_marks,
             a_notice_outranks_the_counts, the_cursor_follows_the_row,
             a_gone_row_keeps_the_line, another_view_begins_at_its_beginning,
             no_rows_means_no_cursor, nothing_here_touched_a_screen):
    part()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
