"""Narrowing the view to a search: what matches, what it hides, what it says.

Everything here is stubbed -- no account, no network, no mailbox. The calendar
is reached through a replaced `ical.fetch` rather than the real one, because
this shell has no macOS Calendar grant and a suite that asked for it would fail
for a reason that has nothing to do with searching.
"""
import asyncio, datetime as dt, sys
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
import main, ical, mail, tracker
from main import TaskApp, KeyBar, SearchInput
from singularity import Bucket
from textual.widgets import DataTable, Input

TODAY = dt.datetime.now(TZ).date()
WORK = "P-work-0001"
OTHER = "P-other-002"
CFG = ical.Config(work="WorkAcc", personal=("Me",))

ok = []
def check(name, got, want):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


# ------------------------------------------------------------- the fixtures

def so(t, v):
    t.raw["scheduleOrder"] = v
    return t

def triage(tid, title, project=None):
    """An undated, undeferred task: what the inbox holds."""
    return so(mk(tid, title, None, project=project), 1000)

def ev(title, hh=9, account="Me"):
    start = dt.datetime.combine(TODAY, dt.time(hh, 0))
    return ical.Event(title=title, account=account, calendar="c", start=start,
                      end=start + dt.timedelta(hours=1), all_day=False)

def issue(key, summary):
    return tracker.Issue(key=key, summary=summary, project="ZZA",
                         state="In progress", assignee="me",
                         base_url="https://track.invalid")

def thread(ident, subject, sender="someone@example.invalid", body="",
           count=1, minute=0):
    when = dt.datetime(2026, 9, 8, 8, minute, tzinfo=dt.timezone.utc)
    messages = tuple(
        mail.Message(sender=sender, subject=subject, when=when,
                     ident=f"<{ident}-{n}@example.invalid>", answers=None,
                     body=body, text=body, folder="Feed", key=f"{ident}{n}")
        for n in range(count)
    )
    return mail.Thread(messages)


async def settle(pilot, n=8):
    for _ in range(n):
        await pilot.pause()

def make(position=None, tasks=(), mails=(), events=(), issues=()):
    app = TaskApp(position) if position is not None else TaskApp()
    app.client = StubClient(list(tasks), reference=dt.datetime.now(TZ))
    app.work_project = WORK
    app.projects = {WORK: "Work", OTHER: "Other"}
    # Nothing may be reached for real: the mailbox is handed its threads and
    # the tracker its issues, and the calendar is replaced in `run` below.
    app.mail_config = None
    app.tracker_config = None
    app.calendar_config = CFG if events else None
    app._pending_mail = list(mails)
    app._pending_events = list(events)
    app._pending_issues = list(issues)
    return app

class run:
    """Start a board with the sources it was given already in place.

    The sources are attached after the first settle rather than before it:
    the board's own loaders run on mount, and one that answered afterwards
    would replace what a check had just put there.
    """

    def __init__(self, app, size=(120, 40)):
        self.app, self.size = app, size

    async def __aenter__(self):
        self.saved = ical.fetch
        ical.fetch = lambda cfg, day: list(self.app._pending_events)
        self.ctx = self.app.run_test(size=self.size)
        self.pilot = await self.ctx.__aenter__()
        await settle(self.pilot, 12)
        self.app.mail_threads = list(self.app._pending_mail)
        self.app.tracker_issues = list(self.app._pending_issues)
        if self.app._pending_events:
            self.app.events = list(self.app._pending_events)
            self.app.events_day = self.app.position
        self.app.repaint()
        await settle(self.pilot)
        return self.pilot

    async def __aexit__(self, *exc):
        ical.fetch = self.saved
        return await self.ctx.__aexit__(*exc)


def titles(app):
    return [app.search_text(t) for t in app.tasks]

def daybar(app):
    return str(app.query_one("#daybar").content)

def status(app):
    return str(app.query_one("#status").content)

async def search(pilot, app, term, key="slash"):
    """Open the prompt with `key`, put `term` in it, and confirm."""
    await pilot.press(key)
    await settle(pilot)
    app.screen.query_one(Input).value = term
    await pilot.press("enter")
    await settle(pilot)


# ------------------------------------------------- 1. what a row reads as

async def t_reads_as():
    print("1.1 the searched text is the title the row carries")
    # Two rows, because the traps cannot all sit on one: a subject long
    # enough to be cut is long enough for the cut to take the thread count
    # away with it.  The short one carries the count and a bracket -- which
    # is escaped on the way into the cell and unescaped again when the cell
    # is parsed -- and the long one carries the cut.
    short = "build [urgent] failed"
    long = ("nightly job failed on the release branch, and then again on "
            "the one after it, and then again on the one after that")
    app = make(Bucket.INBOX, mails=[thread("z1", short, count=3, minute=1),
                                    thread("z2", long, minute=2)])
    async with run(app) as pilot:
        rows = {app.search_text(t): t for t in app.tasks if app.is_mail(t)}
        check("the searched text is the stored subject, for both",
              sorted(rows), sorted([short, long]))
        drawn_short = str(app.row_for(rows[short])[3])
        drawn_long = str(app.row_for(rows[long])[3])
        check("the drawn cell carries the thread count, the searched text does not",
              ("(3)" in drawn_short, "(3)" in short), (True, False))
        check("the long cell was cut to the column, the searched text was not",
              (len(drawn_long) < len(long), len(app.search_text(rows[long]))),
              (True, len(long)))
        await search(pilot, app, "after that")
        check("a word the column cut off is still found", len(app.tasks), 1)
        await search(pilot, app, "[urgent]")
        check("a bracket in a subject is searched for as itself", len(app.tasks), 1)
        await search(pilot, app, "(3)")
        check("the thread count is not part of what is searched", len(app.tasks), 0)

async def t_reads_as_every_kind():
    print("1.2 every kind of row answers with its own title")
    app = make(TODAY, tasks=[mk("t1", "a store task", TODAY)],
               events=[ev("a calendar event")], issues=[issue("ZZA-1", "an issue")])
    async with run(app) as pilot:
        got = {}
        for t in app.tasks:
            kind = ("issue" if app.is_tracker(t) else
                    "event" if app.is_event(t) else "task")
            got[kind] = app.search_text(t)
        check("the store task", got.get("task"), "a store task")
        check("the calendar event", got.get("event"), "a calendar event")
        # The issue's key is part of the title the row carries, so it is part
        # of what the search reads -- which is what lets a person find an
        # issue by its key, the way they refer to it everywhere else.
        check("the tracker issue, key and all", got.get("issue"), "ZZA-1 — an issue")
        check("none of them is empty", all(got.values()), True)
    app = make(Bucket.INBOX, mails=[thread("z1", "a mail subject")])
    async with run(app) as pilot:
        row = next(t for t in app.tasks if app.is_mail(t))
        check("the mail thread", app.search_text(row), "a mail subject")


# ------------------------------------------------------------ 2. the filter

async def t_none_by_default():
    print("2.1 a board opens with no search in force")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        check("no term is in force", app.searching, None)
        check("every row is drawn", sorted(titles(app)), ["alpha", "beta"])
        check("nothing is counted as hidden", app.hidden_by_search, 0)

async def t_narrows():
    print("2.2 a term narrows the view, and the count is what it removed")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha one"),
                                    triage("b", "beta"),
                                    triage("c", "alpha two")])
    async with run(app) as pilot:
        before = len(app.tasks)
        await search(pilot, app, "alpha")
        check("the term is in force", app.searching, "alpha")
        check("only the matching rows are drawn",
              sorted(titles(app)), ["alpha one", "alpha two"])
        check("the count is the number removed",
              app.hidden_by_search, before - len(app.tasks))
        check("and that number is one", app.hidden_by_search, 1)

async def t_every_source_inbox():
    print("2.3 each source is narrowed -- the inbox's two")
    app = make(Bucket.INBOX,
               tasks=[triage("a", "keep me"), triage("b", "drop me")],
               mails=[thread("z1", "keep this too", minute=1),
                      thread("z2", "drop this too", minute=2)])
    async with run(app) as pilot:
        await search(pilot, app, "keep")
        check("the store task that does not match is gone",
              "drop me" in titles(app), False)
        check("the store task that matches is drawn",
              "keep me" in titles(app), True)
        check("the mail thread that does not match is gone",
              "drop this too" in titles(app), False)
        check("the mail thread that matches is drawn",
              "keep this too" in titles(app), True)
        check("two rows are left", len(app.tasks), 2)

async def t_every_source_today():
    print("2.3 each source is narrowed -- today's three")
    app = make(TODAY,
               tasks=[mk("t1", "keep me", TODAY), mk("t2", "drop me", TODAY)],
               events=[ev("keep this event"), ev("drop this event", hh=10)],
               issues=[issue("ZZA-1", "keep this issue"),
                       issue("ZZA-2", "drop this issue")])
    async with run(app) as pilot:
        await search(pilot, app, "keep")
        got = titles(app)
        check("the store task that does not match is gone", "drop me" in got, False)
        check("the event that does not match is gone",
              "drop this event" in got, False)
        check("the issue that does not match is gone",
              "drop this issue" in got, False)
        check("one of each kind is left", sorted(got),
              ["ZZA-1 — keep this issue", "keep me", "keep this event"])
        check("three rows removed", app.hidden_by_search, 3)
        check("the issue count follows the narrowing", app.shown_issues, 1)

async def t_case_and_part():
    print("2.4 letter case does not matter, and part of a word matches")
    app = make(Bucket.INBOX, tasks=[triage("a", "Nightly BUILD failed"),
                                    triage("b", "something else")])
    async with run(app) as pilot:
        await search(pilot, app, "build")
        check("a differently cased term matches",
              titles(app), ["Nightly BUILD failed"])
        await search(pilot, app, "NIGHT")
        check("part of a word matches", titles(app), ["Nightly BUILD failed"])
        await search(pilot, app, "ночь".upper())
        check("a Cyrillic term folds too and matches nothing here",
              titles(app), [])

async def t_title_alone():
    print("2.5 the search reads the title alone")
    app = make(Bucket.INBOX,
               tasks=[triage("a", "a filed thing", project=WORK)],
               mails=[thread("z1", "a subject", sender="findme@example.invalid",
                             body="the body says findme")])
    async with run(app) as pilot:
        await search(pilot, app, "findme")
        check("a term only in the sender does not match", titles(app), [])
        await search(pilot, app, "Work")
        check("a term only in the project name does not match", titles(app), [])
        await search(pilot, app, "subject")
        check("a term in the subject does match", titles(app), ["a subject"])

async def t_order_kept():
    print("2.6 narrowing keeps the order of what survives")
    app = make(Bucket.INBOX, tasks=[triage(f"t{i}", f"keep {i}" if i % 2 else f"drop {i}")
                                    for i in range(6)])
    async with run(app) as pilot:
        full = titles(app)
        await search(pilot, app, "keep")
        kept = [t for t in full if "keep" in t]
        check("the survivors are in the order they had", titles(app), kept)

async def t_both_filters():
    print("2.7 the search and the work filter compose")
    app = make(Bucket.INBOX,
               tasks=[triage("a", "keep mine"), triage("b", "keep other")],
               mails=[thread("z1", "keep this mail")])
    async with run(app) as pilot:
        await pilot.press("w")          # all mail counts as work
        await settle(pilot)
        await search(pilot, app, "keep")
        check("a work row matching the term is still not drawn",
              "keep this mail" in titles(app), False)
        check("the tasks that match are drawn",
              sorted(titles(app)), ["keep mine", "keep other"])
        await pilot.press("escape")
        await settle(pilot)
        check("clearing the search leaves work hidden", app.hiding_work, True)
        check("and the mail is still not drawn",
              "keep this mail" in titles(app), False)
        await search(pilot, app, "keep")
        await pilot.press("w")
        await settle(pilot)
        check("clearing the work filter leaves the search in force",
              app.searching, "keep")
        check("and the mail now matches and is drawn",
              "keep this mail" in titles(app), True)

async def t_writes_nothing():
    print("2.8 nothing is written")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        app.client.calls.clear()
        await search(pilot, app, "alpha")
        await search(pilot, app, "bet")
        await pilot.press("escape")
        await settle(pilot)
        check("the store was not asked to change anything",
              app.client.calls, [])


# ----------------------------------------------------- 3. the keys and prompt

async def t_prompt_opens():
    print("3.1 the key opens the prompt and the term takes effect")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        await pilot.press("slash")
        await settle(pilot)
        check("the prompt is on screen", isinstance(app.screen, SearchInput), True)
        app.screen.query_one(Input).value = "alph"
        await pilot.press("enter")
        await settle(pilot)
        check("the prompt is gone", isinstance(app.screen, SearchInput), False)
        check("the term is in force", app.searching, "alph")
        check("the view is narrowed", titles(app), ["alpha"])

async def t_every_key():
    print("3.2 every bound key opens it, in either layout")
    for key in ("slash", "semicolon", "ж"):
        app = make(Bucket.INBOX, tasks=[triage("a", "alpha")])
        async with run(app) as pilot:
            await pilot.press(key)
            await settle(pilot)
            check(f"{key} opens the prompt",
                  isinstance(app.screen, SearchInput), True)

async def t_escape_clears():
    print("3.3 escape clears the search")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        await search(pilot, app, "alpha")
        check("narrowed first", len(app.tasks), 1)
        await pilot.press("escape")
        await settle(pilot)
        check("no term is in force", app.searching, None)
        check("every row is back", sorted(titles(app)), ["alpha", "beta"])
        check("nothing is counted as hidden", app.hidden_by_search, 0)
        # And again, with nothing to clear.
        await pilot.press("escape")
        await settle(pilot)
        check("escape with no search in force does nothing",
              (app.searching, sorted(titles(app))), (None, ["alpha", "beta"]))

    print("\n  and it clears the marked rows along with the search")
    # Escape is this board's one answer to "never mind".  Clearing one of the
    # two things a person set and not the other would leave them pressing it
    # and watching half of what they did survive.
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        table.move_cursor(row=0)
        await settle(pilot, 2)
        await pilot.press("v")
        table.move_cursor(row=1)
        await settle(pilot, 2)
        await pilot.press("v")
        await search(pilot, app, "alpha")
        check("two rows marked and a search in force",
              (len(app.marked), app.searching, len(app.tasks)), (2, "alpha", 1))
        await pilot.press("escape")
        await settle(pilot)
        check("one press cleared both",
              (app.marked, app.searching), ([], None))
        check("and every row is back", sorted(titles(app)), ["alpha", "beta"])

    print("\n  marks alone are cleared by it too")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        table = app.query_one(DataTable)
        table.move_cursor(row=0)
        await settle(pilot, 2)
        await pilot.press("v")
        check("one marked, no search", (len(app.marked), app.searching), (1, None))
        await pilot.press("escape")
        await settle(pilot)
        check("escape clears the mark with no search in force", app.marked, [])

async def t_cancel_and_empty():
    print("3.4 cancelling keeps the search, an empty term clears it")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta")])
    async with run(app) as pilot:
        await search(pilot, app, "alpha")
        await pilot.press("slash")
        await settle(pilot)
        check("the prompt opens carrying the term in force",
              app.screen.query_one(Input).value, "alpha")
        await pilot.press("escape")
        await settle(pilot)
        check("cancelling left the search exactly as it was",
              app.searching, "alpha")
        check("and the view with it", titles(app), ["alpha"])
        await search(pilot, app, "")
        check("an empty term clears the search", app.searching, None)
        check("and every row is back", sorted(titles(app)), ["alpha", "beta"])

def t_no_collision():
    print("3.5 no two actions answer the same key")
    taken = {}
    for binding in TaskApp.BINDINGS:
        for key in binding.key.split(","):
            taken.setdefault(key.strip(), []).append(binding.action)
    shared = {k: v for k, v in taken.items() if len(v) > 1}
    check("no key is bound twice", shared, {})
    check("the search key is bound", "slash" in taken, True)
    check("and reaches the other layout",
          ("semicolon" in taken, "ж" in taken), (True, True))
    check("the key that carries / in a Russian layout still means did-today",
          taken.get("full_stop"), ["done_for_today"])


# ------------------------------------------------------ 4. what the board says

async def t_daybar_names_term():
    print("4.1 the day bar names the term, in every view")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha")])
    async with run(app) as pilot:
        await search(pilot, app, "alpha")
        check("the inbox names it", 'search "alpha"' in daybar(app), True)
        check("and says how to get out", "esc clears" in daybar(app), True)
        await pilot.press("s")
        await settle(pilot)
        check("the someday view names it too",
              'search "alpha"' in daybar(app), True)
        await pilot.press("t")
        await settle(pilot)
        check("and a calendar day", 'search "alpha"' in daybar(app), True)

async def t_status_counts():
    print("4.2 the status line reports the count, beside the others")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta"),
                                    triage("c", "gamma")])
    async with run(app) as pilot:
        await search(pilot, app, "alpha")
        check("the removed count is reported",
              "2 hidden by search" in status(app), True)
        check("the shown count is the number of rows drawn",
              "1 task(s)" in status(app), True)

async def t_says_when_it_hides_nothing_and_everything():
    print("4.3 said when it hides nothing, and when it hides everything")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "alphabet")])
    async with run(app) as pilot:
        await search(pilot, app, "alpha")
        check("it hid nothing", app.hidden_by_search, 0)
        check("the day bar still says a search is in force",
              'search "alpha"' in daybar(app), True)
        await search(pilot, app, "nothing matches this")
        check("it hid everything", len(app.tasks), 0)
        check("the day bar still names the term",
              'search "nothing matches this"' in daybar(app), True)

async def t_silent_with_no_search():
    print("4.4 with no search in force the board says nothing about one")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha")])
    async with run(app) as pilot:
        check("the day bar says nothing", "search" in daybar(app), False)
        check("the status line says nothing", "hidden by search" in status(app), False)

async def t_both_reported():
    print("4.5 both filters are reported, neither replacing the other")
    app = make(TODAY, tasks=[mk("t1", "keep mine", TODAY),
                             mk("t2", "keep work", TODAY, project=WORK),
                             mk("t3", "drop mine", TODAY)])
    async with run(app) as pilot:
        await pilot.press("w")
        await settle(pilot)
        await search(pilot, app, "keep")
        check("the work filter is reported", "work hidden" in daybar(app), True)
        check("the search is reported", 'search "keep"' in daybar(app), True)
        check("the search's count is on the status line",
              "hidden by search" in status(app), True)
        check("the work count is too", "work hidden" in status(app), True)


# ------------------------------------------------- 5. selection and redraws

async def t_selection():
    print("5.1 the selection lands on a row that is drawn")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha"), triage("b", "beta"),
                                    triage("c", "gamma")])
    async with run(app) as pilot:
        await search(pilot, app, "gamma")
        check("the selection is on a drawn row",
              app._selected_id in [t.id for t in app.tasks], True)
        await search(pilot, app, "nothing matches")
        check("nothing is drawn", len(app.tasks), 0)
        check("and nothing is selected", app._selected_id, None)
        check("the board reports the view as empty",
              "0 task(s)" in status(app), True)
        await pilot.press("escape")
        await settle(pilot)
        check("clearing puts a selection back",
              app._selected_id in [t.id for t in app.tasks], True)

async def t_follows_between_views():
    print("5.2 the search follows the person between views")
    app = make(Bucket.INBOX, tasks=[triage("a", "keep me"), triage("b", "drop me"),
                                    so(mk("c", "keep dated", TODAY), 1000),
                                    so(mk("d", "drop dated", TODAY), 2000)])
    async with run(app) as pilot:
        await search(pilot, app, "keep")
        check("the inbox is narrowed", titles(app), ["keep me"])
        await pilot.press("t")
        await settle(pilot)
        check("the term is still in force", app.searching, "keep")
        check("and today is narrowed by it", titles(app), ["keep dated"])
        await pilot.press("s")
        await settle(pilot)
        check("and the someday view too", app.searching, "keep")

async def t_rows_arriving():
    print("5.3 rows arriving are narrowed too")
    app = make(Bucket.INBOX, tasks=[triage("a", "keep me")],
               mails=[thread("z1", "keep this mail")])
    async with run(app) as pilot:
        await search(pilot, app, "keep")
        check("two rows to start", len(app.tasks), 2)
        app._base.append(triage("b", "drop me later"))
        app.mail_threads.append(thread("z2", "drop this mail", minute=5))
        app.mail_threads.append(thread("z3", "keep this mail too", minute=6))
        app.repaint()
        await settle(pilot)
        got = titles(app)
        check("the task that arrived and does not match is not drawn",
              "drop me later" in got, False)
        check("the mail that arrived and does not match is not drawn",
              "drop this mail" in got, False)
        check("the mail that arrived and does match is drawn",
              "keep this mail too" in got, True)
        check("two rows arrived, one of them matching", len(app.tasks), 3)

async def t_redraw_keeps_it():
    print("5.4 a redraw nobody asked for leaves the search in force")
    app = make(Bucket.INBOX, tasks=[triage("a", "keep me"), triage("b", "drop me")])
    async with run(app) as pilot:
        await search(pilot, app, "keep")
        was = titles(app)
        app.repaint()
        await settle(pilot)
        check("the term survives", app.searching, "keep")
        check("and the rows are the same", titles(app), was)


# ------------------------------------------------------ 6. help and the key bar

def t_help():
    print("6.1 help names the key, in English only")
    text = main.Help.TEXT
    check("the search key is named", "/ or ;" in text, True)
    check("escape is named as the way out", "clear the search" in text, True)
    cyrillic = [c for c in text if "Ѐ" <= c <= "ӿ"]
    check("no key is spelled in another alphabet", cyrillic, [])

async def t_keybar():
    print("6.2 the key bar names the action once, by its English key")
    app = make(Bucket.INBOX, tasks=[triage("a", "alpha")])
    async with run(app) as pilot:
        entries = app.query_one(KeyBar).entries()
        named = [e for e in entries if e[1] == "Search"]
        check("named once", len(named), 1)
        check("by the slash", named[0][0], "/")
        check("and escape is not given a permanent entry",
              [e for e in entries if e[1] == "Clear search"], [])


# ------------------------------------------------------------------- runner


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    t_reads_as,
    t_reads_as_every_kind,
    t_none_by_default,
    t_narrows,
    t_every_source_inbox,
    t_every_source_today,
    t_case_and_part,
    t_title_alone,
    t_order_kept,
    t_both_filters,
    t_writes_nothing,
    t_prompt_opens,
    t_every_key,
    t_escape_clears,
    t_cancel_and_empty,
    t_no_collision,
    t_daybar_names_term,
    t_status_counts,
    t_says_when_it_hides_nothing_and_everything,
    t_silent_with_no_search,
    t_both_reported,
    t_selection,
    t_follows_between_views,
    t_rows_arriving,
    t_redraw_keeps_it,
    t_help,
    t_keybar,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
