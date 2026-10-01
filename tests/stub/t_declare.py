"""What a sender declares, and what the board does with it.

Folding used to be a guess: the board read an issue key out of a message's
words and paired it with the first address there, the pair being needed
because the key alone merged unrelated mail. Every sender in these folders
states what its message is about in a header, so the guess is gone and these
parts hold the new rule to what it promised.

The case that mattered is the one named below: review and build mail quotes an
issue it is not about, and 234 messages in the real folders do exactly that. A
declaration only the tracker makes cannot see any of them, which is the whole
reason this is safer and not merely tidier.

Nothing here reaches a real mailbox. Every message is built in a temporary
maildir and every project key, address and job name is invented.
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
import mailfixture as F
from harness import run_parts
import board
import mail
import tracker
from mail import Outcome

ok = []
def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"\n        got  {got!r}\n        want {want!r}")


TRK = tracker.Config(base_url="https://track.corp.invalid", token="z",
                     assignee="me", projects=("ZZA", "ZZB"), states=("open",))
ISSUE = "X-YouTrack-Issue"
PROJECT, REQUEST = "X-GitLab-Project-Id", "X-GitLab-MergeRequest-IID"
JOB, RESULT = "X-Jenkins-Job", "X-Jenkins-Result"


class Raw(dict):
    """Just enough of an email message for the reader: `get` by header name."""
    def get(self, name, default=None):
        return dict.get(self, name, default)


def read(folder):
    """Messages from a built maildir, as the board reads them."""
    path = F.build({"Feed": folder})
    return mail.read(mail.Config(path, ("Feed",)))


def folded(messages, config=TRK):
    """The rows the board would make of these messages."""
    class Of:
        tracker_config = config
        mail_fold = board.Board.mail_fold
    wanted = [m for m in messages if m.about is None or m.about.is_news]
    return mail.threads(wanted, fold=lambda m: Of.mail_fold(Of, m))


# ------------------------------------------- 2.1 what a message carries

def a_message_carries_what_its_sender_declared():
    print("\n2.1 the three declarations, read off the headers that carry them")
    check("an issue", mail.declared(Raw({ISSUE: "ZZA-1"})),
          mail.Declared("issue", ("ZZA-1",)))
    check("a merge request, from both of its identifiers",
          mail.declared(Raw({PROJECT: "41", REQUEST: "12"})),
          mail.Declared("review", ("41", "12")))
    check("a build job, with what became of it",
          mail.declared(Raw({JOB: "nightly", RESULT: "FAILURE"})),
          mail.Declared("build", ("nightly",), Outcome.FAILED))
    check("a message declaring nothing", mail.declared(Raw({})), None)

    print("\n     a declaration that names nothing is no declaration")
    check("an empty issue header", mail.declared(Raw({ISSUE: "   "})), None)
    check("half a merge request is none of one",
          (mail.declared(Raw({PROJECT: "41"})),
           mail.declared(Raw({REQUEST: "12"}))), (None, None))
    check("an empty job name", mail.declared(Raw({JOB: ""})), None)

    print("\n     and the reader puts it on the message")
    msgs = read([("about an issue", "body", {ISSUE: "ZZA-7"}),
                 ("about nothing", "body", {})])
    by = {m.subject: m.about for m in msgs}
    check("a declaring message carries it",
          by["about an issue"], mail.Declared("issue", ("ZZA-7",)))
    check("one that declares nothing carries None", by["about nothing"], None)


# ------------------------------------------- 2.2 what became of a build

def a_build_outcome_is_a_value_not_a_word():
    print("\n2.2 the outcomes that are recognised, and the one that is not")
    def outcome(word):
        return mail.declared(Raw({JOB: "j", RESULT: word})).outcome
    check("a failure", outcome("FAILURE"), Outcome.FAILED)
    check("a success", outcome("SUCCESS"), Outcome.SUCCEEDED)
    check("one stopped before it finished", outcome("ABORTED"), Outcome.STOPPED)

    print("\n     a word nobody has seen is neither kept out nor called a failure")
    for word in ("UNSTABLE", "NOT_BUILT", "", "failure", "ПРОВАЛ"):
        got = mail.declared(Raw({JOB: "j", RESULT: word}))
        check(f"{word!r}: unknown", got.outcome, Outcome.UNKNOWN)
        check(f"{word!r}: and therefore shown", got.is_news, True)

    print("\n     only a build is judged by its outcome at all")
    check("a failed build is news",
          mail.declared(Raw({JOB: "j", RESULT: "FAILURE"})).is_news, True)
    check("a succeeded one is not",
          mail.declared(Raw({JOB: "j", RESULT: "SUCCESS"})).is_news, False)
    check("a stopped one is not",
          mail.declared(Raw({JOB: "j", RESULT: "ABORTED"})).is_news, False)
    check("an issue is news whatever else it says",
          mail.declared(Raw({ISSUE: "ZZA-1"})).is_news, True)
    check("so is a merge request",
          mail.declared(Raw({PROJECT: "41", REQUEST: "9"})).is_news, True)

    print("\n     the outcome is outside the row key, so a job is one row")
    f = mail.declared(Raw({JOB: "j", RESULT: "FAILURE"}))
    s = mail.declared(Raw({JOB: "j", RESULT: "SUCCESS"}))
    check("two results, one key", f.row_key, s.row_key)


# --------------------------------------- 3.1 / 3.2 folding by declaration

def messages_fold_by_what_was_declared():
    print("\n3.1 one row per declared thing")
    rows = folded(read([
        ("first", "b", {ISSUE: "ZZA-1"}),
        ("second", "b", {ISSUE: "ZZA-1"}),
        ("another issue", "b", {ISSUE: "ZZA-2"}),
    ]))
    check("two issues, two rows", len(rows), 2)
    check("the pair folded", sorted(t.count for t in rows), [1, 2])

    print("\n     a merge request needs both of its identifiers")
    rows = folded(read([
        ("same number, project 41", "b", {PROJECT: "41", REQUEST: "7"}),
        ("same number, project 42", "b", {PROJECT: "42", REQUEST: "7"}),
        ("again in 41", "b", {PROJECT: "41", REQUEST: "7"}),
    ]))
    check("the number alone does not merge two projects", len(rows), 2)
    check("and the two in one project do fold",
          sorted(t.count for t in rows), [1, 2])

    print("\n3.2 mail quoting an issue it is not about")
    # The measured trap, and the reason the old rule had to pair the key with
    # an address.  These two name the same issue in their words; neither
    # declares it, because neither is the tracker.  They must not fold with
    # the issue's own notifications, nor with each other.
    quote = "about ZZA-9, see https://track.corp.invalid/issue/ZZA-9"
    rows = folded(read([
        ("the issue itself", quote, {ISSUE: "ZZA-9"}),
        ("a merge request mentioning it", quote, {PROJECT: "41", REQUEST: "5"}),
        ("another mentioning it", quote, {PROJECT: "41", REQUEST: "6"}),
        ("a build mentioning it", quote, {JOB: "j", RESULT: "FAILURE"}),
    ]))
    check("four senders, four rows", len(rows), 4)
    check("none of them folded", sorted(t.count for t in rows), [1, 1, 1, 1])
    check("and the issue's own row holds only its own message",
          [t.count for t in rows
           if t.about == mail.Declared("issue", ("ZZA-9",))], [1])

    print("\n     a letters-dash-digits string is read for nothing")
    rows = folded(read([
        ("charset UTF-8 and ISO-8601", "mentions ZZA-1 in passing", {}),
        ("also UTF-8", "mentions ZZA-1 too", {}),
    ]))
    check("no declaration, so no fold by what the words say", len(rows), 2)


def folding_needs_no_tracker_configured():
    print("\n3.3 a board with no tracker folds tracker mail correctly")
    # The old rule could not: it had to know which projects counted, to avoid
    # reading a version number as an issue key.  A declaration needs no list.
    msgs = read([("first", "b", {ISSUE: "ZZA-1"}),
                 ("second", "b", {ISSUE: "ZZA-1"}),
                 ("other", "b", {ISSUE: "ZZA-2"})])
    with_tracker = folded(msgs, config=TRK)
    without = folded(msgs, config=None)
    check("with a tracker configured", sorted(t.count for t in with_tracker), [1, 2])
    check("and without one, the same", sorted(t.count for t in without), [1, 2])

    print("\n     a project the tracker was never told about folds too")
    rows = folded(read([("a", "b", {ISSUE: "ZZZ-1"}),
                        ("b", "b", {ISSUE: "ZZZ-1"})]), config=TRK)
    check("the declaration is believed, not checked against a list",
          [t.count for t in rows], [2])


def what_declares_nothing_is_grouped_as_before():
    print("\n3.4 a sender that declares nothing keeps the old grouping")
    msgs = read([("a question", "no link at all", {"Message-ID": "<q1@x.invalid>"}),
                 ("Re: a question", "an answer", {"In-Reply-To": "<q1@x.invalid>"}),
                 ("unrelated", "something else", {})])
    rows = folded(msgs)
    check("the chain is one row and the stranger another", len(rows), 2)
    check("the chain holds both of its messages",
          sorted(t.count for t in rows), [1, 2])
    check("and neither row claims to be about anything",
          [t.about for t in rows], [None, None])


# ------------------------------------- 4.1 / 4.2 / 4.3 what is left out

def a_build_is_kept_only_where_it_failed():
    print("\n4.1 successes and stopped builds are left out, failures kept")
    msgs = read([("one", "b", {JOB: "deploy", RESULT: "SUCCESS"}),
                 ("two", "b", {JOB: "deploy", RESULT: "FAILURE"}),
                 ("three", "b", {JOB: "deploy", RESULT: "ABORTED"})])
    rows = folded(msgs)
    check("one row for the job", len(rows), 1)
    check("standing for the failure alone", rows[0].count, 1)
    check("and it is the failure", rows[0].newest.subject, "two")
    check("the ones left out count towards nothing",
          sum(t.count for t in rows), 1)

    print("\n4.2 a job with nothing worth showing has no row at all")
    rows = folded(read([("one", "b", {JOB: "quiet", RESULT: "SUCCESS"}),
                        ("two", "b", {JOB: "quiet", RESULT: "ABORTED"})]))
    check("no row stands for it", rows, [])

    print("\n     a job with both keeps only its failures")
    rows = folded(read([("ok1", "b", {JOB: "mixed", RESULT: "SUCCESS"}),
                        ("bad1", "b", {JOB: "mixed", RESULT: "FAILURE"}),
                        ("ok2", "b", {JOB: "mixed", RESULT: "SUCCESS"}),
                        ("bad2", "b", {JOB: "mixed", RESULT: "FAILURE"})]))
    check("one row", len(rows), 1)
    check("holding the two failures", rows[0].count, 2)
    check("and naming neither success",
          sorted(m.subject for m in rows[0].messages), ["bad1", "bad2"])


def only_build_mail_is_judged_that_way():
    print("\n4.3 every other sender is shown whatever it reports")
    rows = folded(read([
        ("the deploy succeeded", "b", {ISSUE: "ZZA-1"}),
        ("merge request: all checks passed", "b", {PROJECT: "41", REQUEST: "3"}),
        ("a note saying SUCCESS", "SUCCESS everywhere", {}),
    ]))
    check("all three are shown", len(rows), 3)
    check("none of them was weighed against an outcome",
          sorted(t.count for t in rows), [1, 1, 1])


#: The parts this suite is made of, in the order they run.  One list, read
#: by the runner to report and select them one at a time, and by the file
#: itself when it is run directly -- so both ways run the same parts.
PARTS = (
    a_message_carries_what_its_sender_declared,
    a_build_outcome_is_a_value_not_a_word,
    messages_fold_by_what_was_declared,
    folding_needs_no_tracker_configured,
    what_declares_nothing_is_grouped_as_before,
    a_build_is_kept_only_where_it_failed,
    only_build_mail_is_judged_that_way,
)

if __name__ == "__main__":
    raise SystemExit(run_parts(PARTS, ok))
