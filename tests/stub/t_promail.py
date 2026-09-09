"""The mail layer's half of promote-a-message-to-a-task.

Every run works on a fresh copy of the synthetic sample maildir, so a run
that marks messages read cannot affect the next one.  Counts and file names
only are printed -- never a subject, sender or body.
"""
import hashlib
import os
import shutil
import sys
import tempfile

import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import mail

SAMPLE = _os.path.join(_TESTS, "fixtures", "sample_mail")
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{' · ' + detail if detail else ''}")
    if not ok:
        fails.append(name)


def fresh():
    where = tempfile.mkdtemp(prefix="promail.")
    box = os.path.join(where, "mail")
    shutil.copytree(SAMPLE, box)
    return box


def where_is(root, key):
    """The file a maildir key names, relative to the folder it is in."""
    for area in ("new", "cur"):
        here = os.path.join(root, area)
        if not os.path.isdir(here):
            continue
        for name in os.listdir(here):
            if name.split(":")[0] == key:
                return os.path.join(area, name)
    return None


def census(root):
    """Every file under the maildir: its path, and a digest of its bytes."""
    out = {}
    for base, _dirs, names in os.walk(root):
        for name in names:
            full = os.path.join(base, name)
            rel = os.path.relpath(full, root)
            with open(full, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def uniq(rel):
    """The maildir key a file name carries, without its flags."""
    return os.path.basename(rel).split(":")[0]


# How many messages the sample yields when nothing has been done to it.  Not
# the file count: one sample message is deliberately unparseable, and it is
# passed over rather than shown.
WHOLE = len(mail.read(mail.Config(fresh(), ())))

# -- 1.1  where a message was read from ------------------------------------
box = fresh()
for area in ("cur", "new", "tmp"):
    os.makedirs(os.path.join(box, ".Reports", area), exist_ok=True)
inbox_files = sorted(os.listdir(os.path.join(box, "new")))
moved = inbox_files[0]
shutil.move(os.path.join(box, "new", moved), os.path.join(box, ".Reports", "new", moved))

cfg = mail.Config(box, ("Reports",))
found = mail.read(cfg)
folders = sorted({m.folder for m in found})
check("1.1 the folder is recorded", folders == ["", "Reports"], f"folders={folders}")
check("1.1 the mailbox's own inbox is the empty folder",
      sum(1 for m in found if m.folder == "") == WHOLE - 1,
      f"{sum(1 for m in found if m.folder == '')} in the inbox of {WHOLE}")
check("1.1 a named folder is named", sum(1 for m in found if m.folder == "Reports") == 1)
check("1.1 every message carries a key", all(m.key for m in found))
check("1.1 the key addresses the message",
      all(where_is(mail._folder_path(cfg, m.folder), m.key) for m in found))

# -- 1.2  a message with no Message-ID of its own --------------------------
box = fresh()
target = sorted(os.listdir(os.path.join(box, "new")))[0]
full = os.path.join(box, "new", target)
raw = open(full, "rb").read()
stripped = b"\n".join(
    line for line in raw.split(b"\n") if not line.lower().startswith(b"message-id:")
)
open(full, "wb").write(stripped)
cfg = mail.Config(box, ())
found = mail.read(cfg)
nameless = [m for m in found if m.ident.startswith("<key:")]
check("1.2 a message with no identity falls back to its key", len(nameless) == 1,
      f"{len(nameless)} of {len(found)}")
check("1.2 and is still addressable by that key",
      bool(nameless) and nameless[0].key == target)

# -- 4.1  unread only ------------------------------------------------------
box = fresh()
cfg = mail.Config(box, ())
before = mail.read(cfg)
check("4.1 the sample is all unread to begin with", len(before) > 1, f"{len(before)}")

# flag one read the way another program would: rename it
one = before[0]
was_at = where_is(box, one.key)
os.rename(os.path.join(box, was_at),
          os.path.join(box, "cur", f"{one.key}:2,S"))
after = mail.read(cfg)
check("4.1 a message flagged read by another program is gone",
      len(after) == len(before) - 1 and one.key not in {m.key for m in after},
      f"{len(before)} -> {len(after)}")

# a message moved into cur/ with no flags is unread there too
box = fresh()
cfg = mail.Config(box, ())
first = sorted(os.listdir(os.path.join(box, "new")))[0]
shutil.move(os.path.join(box, "new", first), os.path.join(box, "cur", first))
found = mail.read(cfg)
check("4.1 an unflagged message in cur/ counts as unread",
      len(found) == len(before), f"{len(found)}")

# -- 4.2  marking read takes it out of the queue ---------------------------
box = fresh()
cfg = mail.Config(box, ())
found = mail.read(cfg)
groups = mail.threads(found)
biggest = max(groups, key=lambda t: t.count)
mail.mark_read(cfg, list(biggest.messages))
left = mail.read(cfg)
check("4.2 the thread's messages are gone from the queue",
      len(left) == len(found) - biggest.count,
      f"{len(found)} - {biggest.count} -> {len(left)}")
check("4.2 the thread itself is gone",
      biggest.newest.ident not in {t.newest.ident for t in mail.threads(left)})
flagged = [f for f in os.listdir(os.path.join(box, "cur")) if ":2,S" in f]
check("4.2 the flag is in the file name", len(flagged) == biggest.count,
      f"{len(flagged)} named read")
check("4.2 a marked message left the new area for the current one",
      all(where_is(box, m.key).startswith("cur") for m in biggest.messages))

# marking one already read is not an error
mail.mark_read(cfg, [biggest.messages[0]])
check("4.2 marking an already-read message again is quiet", True)

# -- 4.4/4.5  marking unread again puts it back ----------------------------
box = fresh()
cfg = mail.Config(box, ())
found = mail.read(cfg)
picked = mail.threads(found)[0]
mail.mark_read(cfg, list(picked.messages))
check("4.4 the thread is out of the queue to begin with",
      picked.newest.ident not in {t.newest.ident for t in mail.threads(mail.read(cfg))})
mail.mark_unread(cfg, list(picked.messages))
back = mail.read(cfg)
check("4.4 marking unread puts the thread back",
      len(back) == len(found)
      and picked.newest.ident in {t.newest.ident for t in mail.threads(back)},
      f"{len(found)} -> {len(back)}")
check("4.5 it stays in the current area rather than the new one",
      all(where_is(box, m.key).startswith("cur") for m in picked.messages))
check("4.5 and carries no seen flag",
      all(":2,S" not in where_is(box, m.key) for m in picked.messages))
mail.mark_unread(cfg, list(picked.messages))
check("4.4 marking an already-unread message again is quiet",
      len(mail.read(cfg)) == len(found))

# -- 4.6  nothing else about the mailbox changed ---------------------------
box = fresh()
cfg = mail.Config(box, ())
found = mail.read(cfg)
was = census(box)
picked = mail.threads(found)[0]
mail.mark_read(cfg, list(picked.messages))
now = census(box)

was_by_key = {uniq(k): (k, v) for k, v in was.items()}
now_by_key = {uniq(k): (k, v) for k, v in now.items()}
promoted = {m.key for m in picked.messages}

check("4.6 no message was removed or added",
      set(was_by_key) == set(now_by_key),
      f"{len(was)} -> {len(now)} files")
check("4.6 no message's content differs",
      all(was_by_key[k][1] == now_by_key[k][1] for k in was_by_key),
      f"{len(was_by_key)} byte-identical")
check("4.6 no message changed folder",
      all(os.path.dirname(os.path.dirname(was_by_key[k][0]))
          == os.path.dirname(os.path.dirname(now_by_key[k][0]))
          for k in was_by_key),
      "every message in the folder it was read from")
check("4.6 nothing but the promoted messages was renamed",
      {k for k in was_by_key if was_by_key[k][0] != now_by_key[k][0]} == promoted,
      f"{picked.count} of {len(was_by_key)} renamed")
check("4.6 an untouched message is untouched",
      all(was_by_key[k] == now_by_key[k] for k in set(was_by_key) - promoted),
      f"{len(set(was_by_key) - promoted)} left alone")

# -- a mailbox that cannot be written --------------------------------------
box = fresh()
cfg = mail.Config(box, ())
found = mail.read(cfg)
one = found[0]
os.chmod(os.path.join(box, "new"), 0o500)
os.chmod(os.path.join(box, "cur"), 0o500)
try:
    mail.mark_read(cfg, [one])
    check("4.3 an unwritable mailbox is reported", False, "no exception")
except mail.MailboxUnwritable as exc:
    check("4.3 an unwritable mailbox is reported", True, str(exc))
finally:
    os.chmod(os.path.join(box, "new"), 0o700)
    os.chmod(os.path.join(box, "cur"), 0o700)

try:
    mail.mark_read(mail.Config("", ()), [one])
    check("4.3 no mailbox is reported too", False, "no exception")
except mail.MailboxUnwritable:
    check("4.3 no mailbox is reported too", True)

print()
print(f"{len(fails)} failed" if fails else "all passed")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
