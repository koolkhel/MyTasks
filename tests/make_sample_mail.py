"""Build a sample maildir shaped like a corporate notification inbox.

Builds into a temporary directory and swaps it into place only once it is
complete, so a failure part way through leaves the committed fixture alone.
It used to delete the fixture as its first act, which made running it a risk
and so nobody did -- and it had been broken for a day without anyone noticing.

Everything here is invented: .invalid domains, made-up project keys, made-up
people.  No real message, address or project key appears.

Deliberately shaped to REVEAL the coalescing problem rather than hide it: of
15 messages, 9 belong to 3 threads.  A sample of unrelated one-offs would
make a naive one-row-per-message view look fine and teach us nothing.

`mail_folders` is a directory that HOLDS maildirs, one per folder, which is
the layout the real mail directory has and the only one the board reads.  It
built a second fixture until this change -- one maildir with its folders
hanging off it as dot-prefixed subdirectories -- and that went when the last
suite stopped reading it.

It is shaped from what was measured on the real folders, because the folding
rule turns on distinctions a tidy sample would not contain: messages naming
one issue and agreeing on where they point, messages naming one issue and
disagreeing, messages naming none, and groups anchored, part-anchored and
unanchored.
"""
import mailbox, email.utils, os, shutil, sys
from email.message import EmailMessage
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

# A maildir's cur/ and tmp/ are empty here -- every message is delivered to
# new/ -- and git tracks no empty directory, so a clone would arrive without
# them and mail.read() would refuse the folder as "not a maildir".  Written
# by the generator too, so regenerating the fixture does not lose them.
KEEP = ("A maildir must have cur/, new/ and tmp/. Git tracks no empty "
        "directory, so without this file the directory vanishes on clone and "
        "the mailbox stops being a maildir -- which is how the mail suites "
        "passed here and failed on a fresh checkout.\n")

#: The day every message is dated from.  Fixed rather than "now", so a
#: regenerated fixture is byte-comparable with the one committed.
BASE = datetime(2026, 9, 8, 8, 0)

# ===================================================================
# The flat fixture: a directory holding one maildir per folder.
# ===================================================================
FOLDERS_ROOT = os.path.join(HERE, "fixtures", "mail_folders")
FOLDERS_BUILD = FOLDERS_ROOT + ".building"
if os.path.exists(FOLDERS_BUILD):
    shutil.rmtree(FOLDERS_BUILD)
# The container must exist before a maildir can be made inside it: Maildir
# creates its own cur/new/tmp but not the directory holding it.
os.makedirs(FOLDERS_BUILD)

#: Invented, and deliberately not the shape of any real project's keys.
PROJ, OTHER = "ZZA", "ZZB"
GATE = "https://mail.corp.invalid"
_seq = 0


def deliver(folder, sender, subject, body, *, minutes, thread=None,
            seen=False, mid=None):
    """One message into one folder of the flat fixture."""
    global _seq
    _seq += 1
    box = mailbox.Maildir(os.path.join(FOLDERS_BUILD, folder), create=True)
    m = EmailMessage()
    m["From"] = sender
    m["To"] = "me@corp.invalid"
    m["Subject"] = subject
    m["Date"] = email.utils.format_datetime(BASE + timedelta(minutes=minutes))
    m["Message-ID"] = mid or f"<flat-{_seq}@corp.invalid>"
    if thread:
        m["In-Reply-To"] = thread
        m["References"] = thread
    m.set_content(body)
    md = mailbox.MaildirMessage(m)
    if seen:
        md.add_flag("S")
    box.add(md)
    box.flush()
    return m["Message-ID"]


def issue_url(key, anchor=None):
    u = f"https://track.corp.invalid/issue/{key}"
    return f"{u}#comment-{anchor}" if anchor else u


# -- YouTrack: one issue, five updates, agreeing on where they point ------
# Folds to one row.  Anchors on the middle three only, so "the earliest
# anchored address" cannot be "the earliest message's address".
# Two header chains, not one: most real notifications about an issue do
# carry In-Reply-To, but they do not all chain to the same message -- 1,056
# real messages give 385 header threads and 199 issues.  So the fixture must
# show header threading falling short of what folding achieves, or the rule
# would look like it were merely reproducing what the headers already say.
_chain = {}
for i, (what, anchor) in enumerate([("assigned to you", None),
                                    ("comment added", 11),
                                    ("comment added", 12),
                                    ("comment added", 13),
                                    ("state changed", None)]):
    _root = 0 if i < 3 else 3
    _parent = None if i == _root else _chain[_root]
    _mid = deliver("YouTrack", "youtrack@track.corp.invalid",
            f"{PROJ}-100: {what}",
            # The plain issue address FIRST and the anchor after, which is
            # how the real notifications are shaped: every message in a
            # group agrees on its first address, and the anchors differ.
            # Putting the anchor first split one issue into two rows,
            # because folding compares first addresses.
            f"{PROJ}-100 -- {what}.\n{issue_url(f'{PROJ}-100')}\n"
            + (f"{issue_url(f'{PROJ}-100', anchor)}\n" if anchor else ""),
            minutes=10 + i * 20, thread=_parent,
            mid=f"<yt.{PROJ}-100.{i}@track.corp.invalid>")
    _chain.setdefault(i, _mid)

# -- YouTrack: one issue, three updates, no anchor anywhere --------------
# Folds to one row, and must fall through to the newest message's address.
# One chain: sometimes the headers already say what folding would.
_first = None
for i, what in enumerate(["created", "comment added", "resolved"]):
    _m = deliver("YouTrack", "youtrack@track.corp.invalid",
                 f"{PROJ}-200: {what}",
                 f"{PROJ}-200 -- {what}.\n{issue_url(f'{PROJ}-200')}\n",
                 minutes=200 + i * 15, thread=_first,
                 mid=f"<yt.{PROJ}-200.{i}@track.corp.invalid>")
    _first = _first or _m

# -- YouTrack: one already read, so it stays out of the queue ------------
deliver("YouTrack", "youtrack@track.corp.invalid",
        f"{PROJ}-300: comment added",
        f"{PROJ}-300 -- comment added.\n{issue_url(f'{PROJ}-300')}\n",
        minutes=300, seen=True, mid=f"<yt.{PROJ}-300.0@track.corp.invalid>")

# -- Gitlab: two merge requests that BOTH cite one issue ----------------
# The measured trap: same key, different addresses.  Must NOT fold, or
# reviewing one would file away the other, unread.
for i, mr in enumerate((47, 51)):
    deliver("Gitlab", "gitlab@git.corp.invalid",
            f"platform/api !{mr}: mentions {OTHER}-9",
            f"!{mr} mentions {OTHER}-9.\n"
            f"https://git.corp.invalid/platform/api/-/merge_requests/{mr}\n",
            minutes=400 + i * 10,
            mid=f"<gl.mr{mr}@git.corp.invalid>")

# -- Gitlab: a merge request thread, no issue named ---------------------
# Groups by header, exactly as before this change.
_mr = None
for i, what in enumerate(["new comment on !63", "!63 was approved"]):
    _mr = deliver("Gitlab", "gitlab@git.corp.invalid",
                  "Re: platform/api !63: retry the upload",
                  f"{what}\n"
                  "https://git.corp.invalid/platform/api/-/merge_requests/63\n",
                  minutes=430 + i * 20, thread=_mr,
                  mid=f"<gl.mr63.{i}@git.corp.invalid>") or _mr

# -- Jenkins: four builds, no issue key, no anchor ----------------------
# Folds not at all by key; the newest-address rule must survive untouched.
_job = None
for i, (num, verdict) in enumerate([(841, "SUCCESS"), (842, "SUCCESS"),
                                    (843, "UNSTABLE"), (844, "FAILURE")]):
    _job = deliver("Jenkins", "jenkins@ci.corp.invalid",
                   f"Build {verdict.lower()}: deploy-prod #{num}",
                   f"deploy-prod #{num} is {verdict}.\n"
                   f"https://ci.corp.invalid/job/deploy-prod/{num}/console\n",
                   minutes=500 + i * 25, thread=_job,
                   mid=f"<ci.deploy-prod.{num}@ci.corp.invalid>") or _job

# -- Jenkins: a version-like string that is NOT an issue key ------------
# `UTF-8` and friends match a letters-dash-digits pattern.  Recognition must
# come from the configured projects, so this folds with nothing.
deliver("Jenkins", "jenkins@ci.corp.invalid",
        "Build failure: nightly-e2e #77 (charset UTF-8, ISO-8601 dates)",
        "nightly-e2e #77 FAILURE\n"
        "https://ci.corp.invalid/job/nightly-e2e/77/console\n",
        minutes=600)

# -- a person, with nothing to open -------------------------------------
# The spec has a scenario for a row that points at nothing; without a message
# like this the fixture cannot exercise it.
deliver("Gitlab", "a.petrov@corp.invalid",
        "quick question about the release notes",
        "Can you confirm the cut-off date? No link, just a question.\n",
        minutes=700)

# -- the move target, empty ---------------------------------------------
mailbox.Maildir(os.path.join(FOLDERS_BUILD, "Archive"), create=True).flush()

for _folder in sorted(os.listdir(FOLDERS_BUILD)):
    for _sub in ("cur", "new", "tmp"):
        _d = os.path.join(FOLDERS_BUILD, _folder, _sub)
        os.makedirs(_d, exist_ok=True)
        if not os.listdir(_d):
            open(os.path.join(_d, ".gitkeep"), "w").write(KEEP)

_counts = {f: len(mailbox.Maildir(os.path.join(FOLDERS_BUILD, f),
                                  create=False).keys())
           for f in sorted(os.listdir(FOLDERS_BUILD))}
print(f"built {sum(_counts.values())} messages in {len(_counts)} folders")
for _f, _n in _counts.items():
    print(f"    {_f:<9} {_n}")

if os.path.exists(FOLDERS_ROOT):
    shutil.rmtree(FOLDERS_ROOT)
os.rename(FOLDERS_BUILD, FOLDERS_ROOT)
print(f"  installed at {os.path.relpath(FOLDERS_ROOT, os.path.dirname(HERE))}")
