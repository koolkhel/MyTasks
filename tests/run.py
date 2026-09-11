"""Run the board's suites.

    python tests/run.py                 the self-contained suites
    python tests/run.py --store         those that talk to the task store
    python tests/run.py --tracker       those that talk to the issue tracker
    python tests/run.py --gateway       those that move mail on the server
    python tests/run.py --all           every tier this machine can run
    python tests/run.py t_bands t_add   named suites, wherever they live
    python tests/run.py --list          what would run, and nothing else

A tier is a directory, and that is a suite's whole declaration of what it
needs.  Nothing here imports a suite to classify it: several of them build a
client at module level, so importing one to read a marker would open a
connection and, for a few, create tasks.  A declaration you must execute the
file to read is not a declaration.

The default is the run a person can actually perform: the self-contained
tier needs no credentials and touches no network, so a fresh clone can
answer "did I break anything" before configuring anything.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from known_failures import KNOWN, signature
from testtoken import child_env, which_token

TESTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TESTS)
PYX = sys.executable

#: Directory, what a suite there needs, and what must be configured for it.
TIERS = {
    "stub": ("nothing beyond the repository", ()),
    # Reads the board's own configuration and asserts on it -- what the
    # calendar accounts are, that a full tracker configuration loads. No
    # network, but useless without a configured .env, and these four were
    # mistaken for self-contained: python-dotenv finds .env by walking up
    # from the calling module, and singularity.py sits beside it, so emptying
    # the environment does not hide it. Only a checkout without one does.
    "config": ("the board's own configuration",
               ("GREEN_TAG", "CALENDAR_PERSONAL",
                "YOUTRACK_BASE_URL", "YOUTRACK_TOKEN", "YOUTRACK_ASSIGNEE")),
    "store": ("the task store", ("SINGULARITY_TOKEN",)),
    "tracker": ("the issue tracker", ("YOUTRACK_BASE_URL", "YOUTRACK_TOKEN")),
    # Its own tier because none of the others describes it: these move a
    # real message on a real account, which no other suite here can do, and
    # they need a mailbox to read as well as a server to move it on. Never
    # run by default, and refused outright when either half is absent --
    # half-configured, they would archive mail and be unable to say where
    # it went.
    # The address is what says reviewing is configured at all; the identity
    # and the credential command are read under either their own names or the
    # ones they had when this spoke IMAP, so they are not named here -- the
    # suite's own guard reports them, and naming one spelling would refuse a
    # configuration that works.
    "gateway": ("the mail account, and a mailbox to read",
                ("MAIL_MAILDIR", "MAIL_FOLDERS", "MAIL_EWS_URL")),
}
#: What a suite calls the tasks it creates, so leftovers are recognisable.
TEST_PREFIX = "zz"
#: Seconds between suites that share an account.  Run back to back they
#: exhaust the store's quota, and it then refuses everything for tens of
#: minutes -- after which every remaining suite fails for a reason that has
#: nothing to do with the code.
GAP = 25
#: The store's own refusal.  Matched on the message because a suite reports
#: it no other way; a bare "429" would also match ordinary numbers.
THROTTLE = re.compile(r"ThrottlerException|HTTP 429")
CHECKS = re.compile(r"^\s*(?:\[(?:PASS|FAIL)\]|(?:ok|FAIL|PASS)\s"
                    r"|\d+/\d+\s+(?:ok|FAIL))")
SUMMARY = re.compile(r"^(\d+/\d+ checks passed|all passed|\d+ failed)", re.M)


def suites(tier):
    """The suites in a tier, by name, in a stable order."""
    where = os.path.join(TESTS, tier)
    if not os.path.isdir(where):
        return []
    return sorted(f[:-3] for f in os.listdir(where)
                  if f.startswith("t_") and f.endswith(".py"))


def find(name):
    """Which tier a named suite lives in."""
    for tier in TIERS:
        if name in suites(tier):
            return tier
    return None


def missing_for(tier):
    """Which of a tier's required settings are absent."""
    needed = TIERS[tier][1]
    if not needed:
        return []
    configured = {}
    env_file = os.path.join(REPO, ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                configured[k.strip()] = v.strip()
    return [k for k in needed
            if not (os.environ.get(k, "").strip() or configured.get(k, "").strip())]


def leftovers():
    """Tasks a suite created and did not remove, if the store can be asked.

    Reported rather than left to be noticed: a crashed suite leaves a task
    behind, and a task left there is not merely untidy -- it is counted into
    the next baseline and then reads as a change no code made. That happened
    during this change and cost an hour of looking for a regression that was
    never there.
    """
    try:
        sys.path.insert(0, REPO)
        from singularity import SingularityClient, Bucket
        from datetime import datetime, timedelta
        api = SingularityClient()
        today = datetime.now(api.tz).date()
        found = []
        for offset in range(-1, 3):
            day = today + timedelta(days=offset)
            found += [(str(day), t.title) for t in api.tasks_for_day(day).tasks
                      if t.title.startswith(TEST_PREFIX)]
        for bucket in Bucket:
            found += [(bucket.name, t.title) for t in api.tasks_at(bucket).tasks
                      if t.title.startswith(TEST_PREFIX)]
        return found
    except Exception as exc:
        return [("?", f"could not be checked: {type(exc).__name__}")]


def run_one(tier, name):
    started = time.time()
    try:
        p = subprocess.run([PYX, os.path.join(TESTS, tier, f"{name}.py")],
                           capture_output=True, text=True, timeout=600,
                           env=child_env(REPO))
        out, code = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired:
        out, code = "<timed out after 600s>", -9
    m = SUMMARY.search(out)
    return {
        "exit": code,
        "output": out,
        "summary": m.group(0) if m else None,
        "throttled": len(THROTTLE.findall(out)),
        "checks": [l.rstrip() for l in out.splitlines() if CHECKS.match(l)],
        "seconds": time.time() - started,
    }


def worse_than_known(name, got):
    """Did a listed suite fail in a way its entry does not describe?

    Without this the list absorbs a new fault: a suite recorded as failing
    one check goes on being reported as known when it starts failing three,
    and the entry hides exactly the regression it was meant to make visible.
    """
    if name not in KNOWN or got["exit"] == 0:
        return None
    expected, _ = KNOWN[name]
    actual = signature(got)
    return None if actual == expected else (expected, actual)


def report(name, got, known):
    mark = "ok  " if got["exit"] == 0 else "FAIL"
    note = ""
    differs = worse_than_known(name, got)
    if known and differs:
        was, now = differs
        mark = "FAIL"
        note = (f"  (listed as {was} failing, now {now} -- not the recorded"
                f" failure)")
    elif known and got["exit"] != 0:
        mark, note = "known", f"  ({known[1]})"
    elif known and got["exit"] == 0:
        mark, note = "FIXED", "  (listed as known to fail -- remove the entry)"
    if got["throttled"]:
        note += f"  [{got['throttled']} throttle errors]"
    print(f"  {mark:<6} {name:<14} {got['summary'] or '-'}{note}", flush=True)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("names", nargs="*", help="run only these suites")
    ap.add_argument("--config", action="store_true")
    ap.add_argument("--store", action="store_true")
    ap.add_argument("--tracker", action="store_true")
    ap.add_argument("--gateway", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.all:
        # Every tier this machine can run, and a line about each it cannot.
        # Refusing the whole run over one unconfigured tier would mean that
        # adding a tier took away the run everybody else was doing -- which
        # is what adding the gateway tier did, until this.
        wanted = []
        for tier in TIERS:
            absent = missing_for(tier)
            if absent:
                print(f"skipping {tier}: needs {', '.join(absent)}")
            else:
                wanted.append(tier)
    else:
        wanted = [t for t, on in (("config", args.config),
                                  ("store", args.store),
                                  ("tracker", args.tracker),
                                  ("gateway", args.gateway)) if on] or ["stub"]

    plan = []
    if args.names:
        plan = [(find(n) or "stub", n) for n in args.names]
        unknown = [n for t, n in plan if find(n) is None]
        if unknown:
            print(f"no such suite: {', '.join(unknown)}")
            return 2
    else:
        plan = [(t, n) for t in wanted for n in suites(t)]

    if args.list:
        for tier in TIERS:
            named = [n for t, n in plan if t == tier]
            if named:
                print(f"  {tier:<8} {len(named):>2}  ({TIERS[tier][0]})")
        print(f"  {'probes':<8} {len(suites('probes')):>2}  "
              f"(assert nothing; never run)")
        return 0

    # Refuse rather than start: a tier without its credentials produces a
    # wall of failures that say nothing about the code.
    for tier in sorted({t for t, _ in plan}):
        absent = missing_for(tier)
        if absent:
            print(f"{tier}: needs {', '.join(absent)}, which is not configured."
                  f"\nNothing was run.")
            return 2

    # The label is about the task store's token; a gateway run uses none.
    if any(t not in ("stub", "gateway") for t, _ in plan):
        label, tail = which_token(REPO)
        print(f"using {label} (ending {tail})")

    results = {}
    for i, (tier, name) in enumerate(plan):
        # Only the tiers that share an account are paced.
        # The mail gateway is not the store and has no quota to exhaust;
        # pacing it would only make a slow tier slower.
        if i and tier not in ("stub", "config", "gateway"):
            time.sleep(GAP)
        got = run_one(tier, name)
        results[name] = got
        report(name, got, KNOWN.get(name))

    failed = [n for n, r in results.items()
              if r["exit"] != 0 and (n not in KNOWN or worse_than_known(n, r))]
    known_failed = [n for n, r in results.items()
                    if r["exit"] != 0 and n in KNOWN
                    and not worse_than_known(n, r)]
    fixed = [n for n, r in results.items() if r["exit"] == 0 and n in KNOWN]
    throttles = sum(r["throttled"] for r in results.values())

    if any(t == "store" for t, _ in plan):
        left = leftovers()
        if left:
            print(f"\n{len(left)} task(s) left on the account by this run:")
            for where, title in left:
                print(f"  {where:<12} {title}")
            print("Delete them: a leftover is counted into the next baseline"
                  " and then reads as a regression.")

    ran = ", ".join(sorted({t for t, _ in plan}))
    print(f"\n{len(results) - len(failed) - len(known_failed)} passed, "
          f"{len(failed)} failed, {len(known_failed)} known to fail"
          f"{f', {len(fixed)} now passing' if fixed else ''}"
          f"  [{ran}]")
    if throttles:
        # A quota is not a verdict.  Reported as inconclusive because a
        # failure that is really a throttle is the most expensive false
        # signal this project has.
        print(f"\n{throttles} throttle errors: this run is INCONCLUSIVE."
              f"\nThe store refuses for tens of minutes once its quota is"
              f" spent. Wait, then run the tier again.")
        return 3
    for n in failed:
        print(f"\n--- {n} failed; run it alone with:"
              f"\n      {os.path.relpath(PYX, os.getcwd())} tests/run.py {n}")
        for line in results[n]["checks"]:
            if "FAIL" in line:
                print(f"      {line.strip()}")
    if fixed:
        print(f"\n{', '.join(fixed)} passed while listed as known to fail."
              f"\nRemove the entry from tests/known_failures.py.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
