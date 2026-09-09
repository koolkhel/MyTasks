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
"""
import mailbox, email.utils, os, shutil, sys
from email.message import EmailMessage
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "fixtures", "sample_mail")
#: Built here first.  The fixture is only replaced once everything below has
#: run, so an error leaves what is committed untouched.
BUILD = ROOT + ".building"
if os.path.exists(BUILD):
    shutil.rmtree(BUILD)
box = mailbox.Maildir(BUILD, create=True)

# A maildir's cur/ and tmp/ are empty here -- every message is delivered to
# new/ -- and git tracks no empty directory, so a clone would arrive without
# them and mail.read() would refuse the fixture as "not a maildir".  Written
# by the generator too, so regenerating the fixture does not lose them.
KEEP = ("A maildir must have cur/, new/ and tmp/. Git tracks no empty "
        "directory, so without this file the directory vanishes on clone and "
        "the mailbox stops being a maildir -- which is how the mail suites "
        "passed here and failed on a fresh checkout.\n")
box.add_folder("Archive")

BASE = datetime(2026, 9, 8, 8, 0)
n = 0

def add(sender, subject, body, *, minutes, thread=None, seen=False, mid=None):
    """One message.  `thread` is the Message-ID this one answers."""
    global n
    n += 1
    m = EmailMessage()
    m["From"] = sender
    m["To"] = "me@corp.invalid"
    m["Subject"] = subject
    m["Date"] = email.utils.format_datetime(BASE + timedelta(minutes=minutes))
    m["Message-ID"] = mid or f"<sample-{n}@corp.invalid>"
    if thread:
        m["In-Reply-To"] = thread
        m["References"] = thread
    m.set_content(body)
    md = mailbox.MaildirMessage(m)
    if seen:
        md.add_flag("S")
    box.add(md)
    return m["Message-ID"]

# ---- a Jenkins job, four builds, the last one broken -------------------
job = None
for i, (num, verdict) in enumerate(
        [(841, "SUCCESS"), (842, "SUCCESS"), (843, "UNSTABLE"), (844, "FAILURE")]):
    mid = add("jenkins@ci.corp.invalid",
              f"Build {verdict.lower()}: deploy-prod #{num}",
              f"deploy-prod #{num} is {verdict}.\n"
              f"See https://ci.corp.invalid/job/deploy-prod/{num}/console\n",
              minutes=10 + i * 25, thread=job,
              mid=f"<jenkins.deploy-prod.{num}@ci.corp.invalid>")
    job = job or mid

# ---- one YouTrack issue, three updates --------------------------------
issue = None
for i, what in enumerate(["assigned to you",
                          "comment added by a.petrov",
                          "state changed to In Review"]):
    mid = add("youtrack@track.corp.invalid",
              f"ABC-1234: {what}",
              f"ABC-1234 -- {what}.\nhttps://track.corp.invalid/issue/ABC-1234\n",
              minutes=45 + i * 40, thread=issue,
              mid=f"<youtrack.ABC-1234.{i}@track.corp.invalid>")
    issue = issue or mid

# ---- one merge request, two notes -------------------------------------
mr = None
for i, what in enumerate(["new comment on !47", "!47 was approved"]):
    mid = add("gitlab@git.corp.invalid",
              f"Re: platform/api !47: raise the read timeout",
              f"{what}\nhttps://git.corp.invalid/platform/api/-/merge_requests/47\n",
              minutes=90 + i * 60, thread=mr,
              mid=f"<gitlab.mr47.{i}@git.corp.invalid>")
    mr = mr or mid

# ---- genuine one-offs -------------------------------------------------
add("jenkins@ci.corp.invalid", "Build failure: nightly-e2e #77",
    "nightly-e2e #77 FAILURE\nhttps://ci.corp.invalid/job/nightly-e2e/77/console\n",
    minutes=200)
add("wiki@docs.corp.invalid", "a.petrov shared a page with you: Runbook: failover",
    "Have a look before Thursday.\nhttps://docs.corp.invalid/pages/8821\n",
    minutes=260)
add("a.petrov@corp.invalid", "quick question about the release notes",
    "Can you confirm the cut-off date? No link, just a question.\n", minutes=300)
add("noreply@lists.corp.invalid", "[platform-team] weekly digest",
    "Three items this week.\nhttps://lists.corp.invalid/digest/2026-36\n",
    minutes=330, seen=True)
add("youtrack@track.corp.invalid", "ABC-99: mentioned you in a comment",
    "See ABC-99.\nhttps://track.corp.invalid/issue/ABC-99\n", minutes=380)
add("calendar-notification@corp.invalid", "Invitation: Platform sync @ Thu 15:00",
    "Join: https://meet.corp.invalid/platform-sync\n", minutes=400)

box.flush()
print(f"built {len(box)} messages in {ROOT}")
print("  folders:", box.list_folders())
print("  unread :", sum(1 for k in box.keys() if "S" not in box[k].get_flags()))

KEPT = ("cur", "tmp", ".Archive/cur", ".Archive/new", ".Archive/tmp")
for _sub in KEPT:
    _d = os.path.join(BUILD, _sub)
    os.makedirs(_d, exist_ok=True)
    if not os.listdir(_d):
        open(os.path.join(_d, ".gitkeep"), "w").write(KEEP)
print("  kept:", ", ".join(KEPT))

# Everything succeeded: swap the new mailbox in.
if os.path.exists(ROOT):
    shutil.rmtree(ROOT)
os.rename(BUILD, ROOT)
print(f"  installed at {os.path.relpath(ROOT, os.path.dirname(HERE))}")
