"""Nothing about the real account is in the tracked tree.

The suites read a real task store, a real tracker, a real calendar and a real
mail directory. Every one of those is a place a name, an address, a project
key or a token could be copied from into a file and then committed -- which
has happened here once, with a token that had to be removed from the history
afterwards.

So this greps the tracked tree for what the configuration actually holds:
every value in `.env`, and the account the mail gateway is pointed at. It
reports which setting leaked, never the value, and it greps the tracked tree
rather than the working directory -- an ignored file is not the danger, and
`.env` itself is where these values belong.

It lives in the tier that needs the board's own configuration for the obvious
reason: with no `.env` there is nothing to look for.
"""
import os
import subprocess
import sys

_TESTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)

ok = []


def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(f"{'  ok  ' if good else '  FAIL'} {name}"
          + ("" if good else f"\n        got  {got!r}\n        want {want!r}"))


#: Settings whose value names something public rather than something about
#: the person: the mail folders (whose names the fixture uses too, because
#: it is shaped like them), the archive's name, the directory they sit in,
#: the loopback address the gateway binds, and the command that reads the
#: keychain. A tracked file holding one of these has leaked nothing, and
#: every other setting is still scanned -- the project keys and the account
#: names among them.
PUBLIC = {
    "MAIL_FOLDERS", "MAIL_ARCHIVE_FOLDER", "MAIL_MAILDIR", "MAIL_IMAP_HOST",
    "MAIL_IMAP_PORT", "MAIL_IMAP_PASSWORD_COMMAND", "YOUTRACK_STATES",
}


def settings():
    """What the configuration holds, as `{name: value}`.

    Values are never printed by anything here; only the names are.
    """
    out = {}
    env = os.path.join(_REPO, ".env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            # Short values match half the tree: a one-letter tag or a bare
            # number says nothing about whether anything leaked.
            if len(value) >= 5:
                out[name.strip()] = value
    return out


def tracked_matches(needle):
    """Tracked files holding this string, by `git grep` over the index.

    Two greps, because they answer different questions: the work tree's
    tracked files, and what is staged. A value staged but not yet committed
    is exactly the case worth catching.
    """
    found = set()
    for extra in ((), ("--cached",)):
        done = subprocess.run(
            ["git", "-C", _REPO, "grep", "-lIF", *extra, "--", needle],
            capture_output=True, text=True)
        found |= {line for line in done.stdout.split("\n") if line.strip()}
    return sorted(found)


print("the search itself finds what is there")
# Without this the whole suite could pass by finding nothing at all -- a
# broken grep and a clean tree look identical from outside.
check("a string the tracked tree does hold is found",
      "tests/run.py" in tracked_matches("MAIL_EWS_URL"), True)
# Assembled rather than written, or the literal would be in this file and
# the check would find itself.
check("and one it does not is not",
      tracked_matches("zz-no-such-" + "string-in-this-repository"), [])

print("nothing from the configuration is in the tracked tree")
found = settings()
check("the configuration was read at all", len(found) >= 3, True)
leaked = {}
for name, value in found.items():
    if name in PUBLIC:
        continue
    where = tracked_matches(value)
    if where:
        leaked[name] = where
check("no setting's value appears in a tracked file", sorted(leaked), [])
check("and the settings skipped as public are the ones listed",
      sorted(n for n in found if n in PUBLIC),
      sorted(n for n in PUBLIC if n in found))

print("nor any domain the account uses")
# The gateway itself holds no account -- it takes the name at login -- so the
# account comes from `.env` like everything else, and is covered above. The
# domain is checked separately because a subject line or a signature carries
# it where the address itself does not, and one leaked domain names the
# employer as surely as the address does.
domains = sorted({value.split("@", 1)[1].split("/")[0]
                  for name, value in found.items()
                  if name not in PUBLIC and "@" in value
                  and "." in value.split("@")[-1]})
check("the configuration named at least one domain to look for",
      bool(domains), True)
for domain in domains:
    check("no tracked file names it", tracked_matches(domain), [])

print("and no token")
for name in ("SINGULARITY_TOKEN", "SINGULARITY_TEST_TOKEN", "YOUTRACK_TOKEN"):
    value = found.get(name)
    if not value:
        continue
    check(f"{name} is not in the tracked tree", tracked_matches(value), [])
    check(f"{name} is not in the committed history",
          subprocess.run(["git", "-C", _REPO, "log", "--all", "-S", value,
                          "--oneline"], capture_output=True,
                         text=True).stdout.strip(), "")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
