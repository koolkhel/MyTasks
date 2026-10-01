"""The real mailbox still declares what the board folds by.

Folding reads headers that three notification systems set. None of them is
promised by anybody: a server upgrade can rename one, and the board would
quietly stop folding and say nothing, because falling back to grouping by
reply headers is not an error. This suite is what makes that visible.

Counts only. No subject, sender, folder, project key, job name or issue is
read out of a message or printed, here or anywhere this writes: the mailbox
is somebody's real one and this repository is public. What it needs to know
is whether the declarations are there, never what they say.

Nothing is created, changed or moved. One read, and the mailbox is left
exactly as it was found.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import mail

ok = []
def check(name, got, want=True):
    good = got == want
    ok.append(good)
    print(("  ok  " if good else "  FAIL"), name,
          "" if good else f"  (got {got!r}, want {want!r})")


config = mail.load_config()
if config is None:
    print("no mailbox configured; nothing to check")
    raise SystemExit(0)

print("the real folders are read once, and nothing is written")
messages = mail.read(config)
print(f"  {len(messages)} message(s) in the configured folders")
check("there is mail to look at", len(messages) > 0)

print("\nhow many of them declare what they are about")
kinds = {}
for message in messages:
    kinds[message.about.kind if message.about else "nothing"] = (
        kinds.get(message.about.kind if message.about else "nothing", 0) + 1)
for kind in ("issue", "review", "build", "nothing"):
    print(f"  {kind:9} {kinds.get(kind, 0)}")
declaring = len(messages) - kinds.get("nothing", 0)
check("most of the mailbox declares something", declaring > len(messages) // 2,
      True)
if declaring <= len(messages) // 2:
    print("  a sender has probably renamed or dropped a header · check "
          "mail.ISSUE_HEADERS, REVIEW_HEADERS and BUILD_HEADERS against a "
          "message, and until then the board groups that sender by reply "
          "headers, which is noisier but loses nothing")

print("\nevery kind the board knows is still present")
for kind in ("issue", "review", "build"):
    check(f"{kind} mail is still arriving", kinds.get(kind, 0) > 0)

print("\nbuilds still declare an outcome the board recognises")
builds = [m for m in messages if m.about and m.about.kind == "build"]
unknown = [m for m in builds if m.about.outcome is mail.Outcome.UNKNOWN]
print(f"  {len(builds)} build message(s), {len(unknown)} with an unrecognised outcome")
check("the outcomes are words the board knows", not unknown,
      True)
if unknown:
    print("  an unrecognised outcome is shown rather than hidden, so nothing "
          "is lost · widen mail.OUTCOMES once somebody has looked at what the "
          "server now says")

print("\nfolding by declaration beats grouping by reply headers")
news = [m for m in messages if m.about is None or m.about.is_news]
by_header = mail.threads(news, fold=lambda m: m.about.row_key if m.about else None)
by_chain = mail.threads(news)
print(f"  {len(news)} message(s) shown · {len(by_header)} rows folded · "
      f"{len(by_chain)} rows by reply headers alone")
check("folding makes fewer rows than the headers alone",
      len(by_header) < len(by_chain))

print("\nnothing shown is in more than one row")
seen = [m.ident for row in by_header for m in row.messages]
check("every message appears exactly once", len(seen), len(set(seen)))
check("and every message shown is in a row", len(seen), len(news))

print(f"\n{sum(ok)}/{len(ok)} checks passed")
raise SystemExit(0 if all(ok) else 1)
