"""The configured version field, read off the real tracker.  Read-only.

Counts only: no issue key, no summary, no person's name and no version value
is printed or asserted against a literal.  What is checked is that the board's
parse agrees with the account's own answer, which needs no knowledge of what
that answer happens to be today.

Makes the one request the board makes, twice, and writes nothing.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
sys.path.insert(0, _TESTS)
import requests
import tracker
from dataclasses import replace

ok = []
def chk(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

config = tracker.load_config()
if config is None:
    print("t_version6: no tracker is configured; this suite needs one.")
    sys.exit(1)
if not config.version_field:
    print("t_version6: no version field is configured.\n"
          "            Put YOUTRACK_VERSION_FIELD=<the field's name> in .env,\n"
          "            or set it in the environment for this run.")
    sys.exit(1)


class Recording:
    """A session that records what was asked and then really asks it."""

    def __init__(self):
        self.calls = []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        return requests.get(url, **kw)


def raw_issues(session):
    """The account's own answer to the request the board makes."""
    response = session.get(
        f"{config.base_url}/api/issues",
        headers={"Authorization": f"Bearer {config.token}",
                 "Accept": "application/json"},
        params={"query": config.query, "fields": tracker.ISSUE_FIELDS,
                "$top": tracker.MAX_ISSUES},
        timeout=tracker.TIMEOUT_SECONDS,
    )
    return response.json()


def carried(raw):
    """How many values the configured field holds on this issue, raw."""
    for field in raw.get("customFields") or []:
        if field.get("name") == config.version_field:
            value = field.get("value")
            if isinstance(value, dict):
                return 1
            if isinstance(value, list):
                return len([v for v in value if isinstance(v, dict)])
    return 0


def t_read_off_the_account():
    print("7.1 the configured field is read off the account")
    session = Recording()
    raw = raw_issues(session)
    parsed = tracker.parse(raw, config)
    print(f"  the tracker reports {len(raw)} issue(s); "
          f"{len(parsed)} of them are the board's")
    # The account's own answer, counted independently of the parse.  Matching
    # two numbers derived different ways says the field is read whatever it
    # happens to hold today -- which is what keeps this suite's result from
    # depending on the day it runs.
    by_key = {r.get("idReadable"): carried(r) for r in raw}
    expected = sum(1 for i in parsed if by_key.get(i.key))
    got = sum(1 for i in parsed if i.versions)
    print(f"  {got} of them carry a version, {len(parsed) - got} carry none")
    chk("as many issues carry a version as the account says do",
        got == expected, f"{got} parsed, {expected} in the answer")
    chk("and each carries as many as the account gives it",
        all(len(i.versions) == by_key.get(i.key, 0) for i in parsed))
    chk("an issue carrying none carries an empty tuple, not a failure",
        all(i.versions == () for i in parsed if not by_key.get(i.key)))
    chk("every version read is a non-empty name",
        all(v and isinstance(v, str) for i in parsed for v in i.versions))
    chk("and nothing else about the issues changed",
        all(i.key and i.state and i.assignee for i in parsed))


def t_costs_no_request():
    print("7.2 configuring it changes nothing about the request")
    with_field, without = Recording(), Recording()
    tracker.fetch(config, session=with_field)
    tracker.fetch(replace(config, version_field=""), session=without)
    chk("one request either way",
        len(with_field.calls) == len(without.calls) == 1,
        f"{len(with_field.calls)} and {len(without.calls)}")
    chk("to the same address", with_field.calls[0][0] == without.calls[0][0])
    chk("asking for the same fields",
        with_field.calls[0][1]["params"] == without.calls[0][1]["params"])
    chk("and the field's name is in neither request",
        config.version_field not in str(with_field.calls[0][1]["params"]))


for fn in (t_read_off_the_account, t_costs_no_request):
    fn()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
