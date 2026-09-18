"""Get the terminal this board runs in allowed to read the calendar.

    .venv/bin/python calendar_access.py          # say what stands in the way
    .venv/bin/python calendar_access.py --fix    # put it right, then ask again
    .venv/bin/python calendar_access.py --quiet  # what run.sh does: speak only
                                                 # when something is wrong

Run it from inside the terminal you use for the board -- not from another
one.  macOS grants calendar access to the *application* that owns the
process, and for a program in a terminal that is the terminal emulator.
Asking from kitty gets kitty allowed; the board in cool-retro-term stays
refused.

Why the board can be refused without ever seeing a prompt: since 10.14 an
app must declare, in its Info.plist, why it wants the calendar
(`NSCalendarsUsageDescription`, and on Sonoma and later
`NSCalendarsFullAccessUsageDescription`).  A request from an app that
declares neither is denied on the spot and nothing is shown.  Most
terminals ship without those keys, because most terminals never expected
to read anyone's calendar.

What `--fix` does, and only with `--fix`:

  1. keeps a copy of the terminal's Info.plist beside it,
  2. adds the two keys, with one sentence each,
  3. re-signs the bundle ad hoc, because editing the plist broke whatever
     signature it had -- refused if the app carries a real developer
     signature, since replacing that would be worse than the problem,
  4. clears any earlier denial the system remembered for it,

and then tells you to quit the terminal and start it again: the system reads
the plist when the request is made, and the running app is the old one.
Run this again afterwards, without `--fix`, and the prompt appears.

Nothing here touches the board, its configuration or the calendar itself.
Nothing here grants anything: no command can, only the prompt.
"""
from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import terminal                                                  # noqa: E402
from terminal import USAGE_KEYS, plist_path, read_plist          # noqa: E402

#: What the system's answer means, in the words shown here.
STATUS_WORDS = {
    0: "not determined -- never asked, or asked by an app that could not be",
    1: "restricted by policy -- nothing here can change that",
    2: "denied -- refused once, and the system remembers",
    3: "granted in full",
    4: "granted for writing only -- the board needs to read",
}
FULL = 3
#: "Ask the system" -- the default for a status nobody handed in.
ASK = object()


def calendar_status() -> int | None:
    """The system's answer for *this* process, or None if EventKit is absent."""
    try:
        import ical
        return ical._status()
    except Exception:                       # not macOS, or pyobjc missing
        return None


def ask_now() -> tuple[bool, str]:
    """Make the request the board itself makes, and say how it went."""
    try:
        import ical
    except ImportError as exc:
        return False, f"the board's calendar module could not be imported: {exc}"
    try:
        ical._store()
    except ical.CalendarUnreadable as exc:
        return False, str(exc)
    return True, "granted in full"


def diagnose(app: str, *, run=subprocess.run, ppid: int | None = None,
             status=ASK) -> dict:
    """Everything the report says, gathered once.

    `status` is the system's answer, asked for unless given: a suite hands
    one in so that its checks do not depend on what this machine has been
    told.  The answer belongs to the application this process runs in, which
    is the one being asked about only when the two are the same.
    """
    host = terminal.host_app(ppid, run=run)
    missing = terminal.usage_keys_missing(app)
    return {
        "app": app,
        "bundle": terminal.bundle_id(app),
        "missing": missing,
        "declares_none": len(missing) == len(USAGE_KEYS),
        "signature": terminal.signature(app, run=run),
        "status": calendar_status() if status is ASK else status,
        "status_is_for": os.path.basename(host) if host else "this process",
        "same": bool(host) and os.path.realpath(host) == os.path.realpath(app),
    }


def words_for(status: int | None) -> str:
    if status is None:
        return "EventKit not available here"
    return STATUS_WORDS.get(status, str(status))


def something_wrong(d: dict) -> bool:
    """Whether there is anything a person should hear about."""
    return d["declares_none"] or (d["same"] and d["status"] not in (FULL, None))


def say(d: dict, out=print) -> None:
    out(f"terminal        {d['app']}")
    out(f"bundle          {d['bundle']}")
    out(f"signature       {d['signature']}")
    have = [k for k in USAGE_KEYS if k not in d["missing"]]
    out("usage keys      "
        + (", ".join(have) if have
           else "none -- the system will not ask on this app's behalf"))
    words = words_for(d["status"])
    if d["same"]:
        out(f"calendar        {words}")
    else:
        out(f"calendar        {words}  -- for {d['status_is_for']}, which this "
            f"runs in; not for {os.path.basename(d['app'])}")


def fix_command() -> str:
    return (f"{os.path.relpath(sys.executable, os.getcwd())} "
            f"{os.path.relpath(__file__, os.getcwd())} --fix")


def fix(app: str, d: dict, *, yes: bool, run=subprocess.run, ask=input,
        out=print) -> int:
    """Make the application one the system will ask about.  Returns an exit code."""
    if d["signature"] not in ("unsigned", "adhoc"):
        out(f"\n{d['app']} is signed by {d['signature']}.  Editing its plist would\n"
            "break that signature, and replacing it with an ad-hoc one is not\n"
            "something this script will do to a signed app.  Ask its authors for\n"
            "the calendar keys, or use a terminal that has them.")
        return 2
    if d["same"] and d["status"] == FULL:
        out("\nAlready allowed; nothing to fix.")
        return 0
    if not d["declares_none"] and d["status"] != 2:
        out("\nThis app already declares a reason to want the calendar; the system\n"
            "will ask on its behalf.  Run this without --fix, from inside it.")
        return 1
    plist = plist_path(app)
    backup = plist + ".before-calendar-access"
    steps = []
    if d["missing"]:
        steps.append(f"add {', '.join(d['missing'])} to {plist}\n"
                     f"     (a copy is kept at {backup})")
    steps.append(f"re-sign {app} ad hoc (it is {d['signature']} now)")
    steps.append(f"clear any earlier calendar denial for {d['bundle']}")
    out("\nThis will:")
    for i, s in enumerate(steps, 1):
        out(f"  {i}. {s}")
    if not yes:
        if ask("\nGo ahead? [y/N] ").strip().lower() not in ("y", "yes"):
            out("Nothing changed.")
            return 1
    if d["missing"]:
        if not os.path.exists(backup):
            shutil.copy2(plist, backup)
        info = read_plist(app)
        for key in d["missing"]:
            info[key] = USAGE_KEYS[key]
        with open(plist, "wb") as fh:
            plistlib.dump(info, fh)
        out(f"added {len(d['missing'])} key(s)")
    r = run(["codesign", "--force", "--deep", "--sign", "-", app],
            capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        out(f"re-signing failed:\n{(r.stderr or '').strip()}")
        return 2
    out("re-signed ad hoc")
    r = run(["tccutil", "reset", "Calendar", d["bundle"]],
            capture_output=True, text=True, encoding="utf-8")
    out("cleared the remembered answer" if r.returncode == 0
        else "could not clear the remembered answer: "
             f"{(r.stderr or r.stdout or '').strip()}")
    out(f"\nNow quit {os.path.basename(app)} completely, start it again, and run\n"
        f"    {fix_command().replace(' --fix', '')}\n"
        "from inside it.  The system will ask; answer Allow.")
    return 0


def main(argv=None, *, run=subprocess.run, ask=input, out=print, status=ASK,
         ppid: int | None = None) -> int:
    """The command.  `run`, `ask`, `status` and `ppid` are for a suite to hand in."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--app", help="the terminal's .app bundle, if not the one this runs in")
    ap.add_argument("--fix", action="store_true", help="add the keys, re-sign, clear the denial")
    ap.add_argument("--yes", action="store_true", help="with --fix: do not ask first")
    ap.add_argument("--quiet", action="store_true",
                    help="say nothing unless something stands in the way; never ask")
    args = ap.parse_args(argv)

    if sys.platform != "darwin":
        if not args.quiet:
            out("This is about macOS calendar access; there is nothing to do here.")
        return 0
    app = args.app or terminal.host_app(ppid, run=run)
    if app is None or not os.path.isdir(app):
        if not args.quiet:
            out("Could not find the application this terminal belongs to.\n"
                "Pass it: --app /Applications/YourTerminal.app")
        return 2
    d = diagnose(app, run=run, ppid=ppid, status=status)

    if args.quiet:
        # The launcher's mode: one short paragraph, only when it matters, and
        # never a request -- a prompt appearing under a board that is about
        # to start would be a prompt nobody could read.
        if not something_wrong(d):
            return 0
        out(f"run.sh: the calendar may not be readable from {os.path.basename(app)}")
        say(d, out=lambda line: out("        " + line))
        if d["declares_none"]:
            out("        The system will not ask on this app's behalf.  To put it right:\n"
                f"            {fix_command()}")
        else:
            out("        Change it in System Settings > Privacy & Security > Calendars,\n"
                "        then start the terminal afresh.")
        return 1

    say(d, out=out)
    if args.fix:
        return fix(app, d, yes=args.yes, run=run, ask=ask, out=out)
    if d["same"] and d["status"] == FULL:
        out("\nAlready allowed.  If the board still shows no events, the account\n"
            "names in .env are what to check next.")
        return 0
    if d["declares_none"]:
        out("\nAn app that declares no reason to want the calendar is refused without\n"
            f"a prompt.  Run this again with --fix:\n    {fix_command()}")
        return 1
    if not d["same"]:
        out(f"\nThe keys are there.  Run this from inside {os.path.basename(app)} to\n"
            "make the request as that app; a request from here would be attributed\n"
            "to this terminal instead.")
        return 1
    out("\nAsking the system now -- a prompt should appear...")
    ok, said = ask_now()
    out(said)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
