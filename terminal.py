"""Which application this process belongs to, and what it declares.

macOS grants a privacy permission -- the calendar's among them -- to the
application responsible for a process, and for anything started in a
terminal that is the terminal emulator.  So when the board asks for the
calendar, the answer is the terminal's; and when the system refuses without
a prompt, it is because the terminal's Info.plist declares no reason to want
what was asked for.

Two things ask these questions: the board itself, when it has to explain a
calendar it could not read, and `calendar_access.py`, which puts the
terminal in a position to be asked.  One module, so there is one answer to
"who is asking" rather than two that drift apart.

Every function takes the process it needs as an argument with a default,
so a suite hands in a fake and nothing here reaches the machine.
"""
from __future__ import annotations

import os
import plistlib
import subprocess

#: What the system reads before it will ask the person, and the one sentence
#: it shows in its own prompt.  Both names, because the newer one arrived
#: with Sonoma and an older system still reads the older -- and either one
#: is enough for the system to ask: kitty declares only the older and is
#: granted.  What is refused without a prompt is declaring neither.
USAGE_KEYS = {
    "NSCalendarsUsageDescription":
        "The task board in this terminal shows the day's calendar events "
        "beside its tasks.",
    "NSCalendarsFullAccessUsageDescription":
        "The task board in this terminal shows the day's calendar events "
        "beside its tasks.",
}


def host_app(ppid: int | None = None, run=subprocess.run) -> str | None:
    """The .app bundle that owns this process, found up the parent chain.

    The shell, the multiplexer, the login process: none of them is what the
    system attributes a request to.  The first ancestor whose executable
    lives inside an app bundle is -- starting from the parent, because a
    framework Python is itself a bundle (`Python.app` inside
    `Python.framework`) and owns nothing.  None where the chain reaches the
    top without one, or where `ps` cannot be read: a caller then says less,
    never nothing.
    """
    pid = os.getppid() if ppid is None else ppid
    for _ in range(20):
        try:
            out = run(["ps", "-o", "ppid=,comm=", "-p", str(pid)],
                      capture_output=True, text=True, encoding="utf-8",
                      check=True).stdout.split(None, 1)
        except (subprocess.CalledProcessError, OSError, ValueError):
            return None
        if len(out) < 2:
            return None
        try:
            parent = int(out[0])
        except ValueError:
            return None
        exe = out[1].strip()
        if ".app/Contents/MacOS/" in exe and ".framework/" not in exe:
            return exe.split("/Contents/MacOS/")[0]
        if parent <= 1:
            return None
        pid = parent
    return None


def plist_path(app: str) -> str:
    return os.path.join(app, "Contents", "Info.plist")


def read_plist(app: str) -> dict:
    with open(plist_path(app), "rb") as fh:
        return plistlib.load(fh)


def bundle_id(app: str) -> str:
    return str(read_plist(app).get("CFBundleIdentifier") or "?")


def usage_keys_missing(app: str) -> list[str]:
    """Which of the calendar keys the application does not declare."""
    info = read_plist(app)
    return [k for k in USAGE_KEYS if k not in info]


def declares_calendar_reason(app: str) -> bool:
    """Whether the system will ask on this application's behalf at all."""
    return len(usage_keys_missing(app)) < len(USAGE_KEYS)


def signature(app: str, run=subprocess.run) -> str:
    """"unsigned", "adhoc", or the signing authority's name.

    What decides whether the application may be re-signed: an unsigned or
    ad-hoc one has no signature worth keeping, a developer-signed one does.
    """
    r = run(["codesign", "-dv", "--verbose=2", app],
            capture_output=True, text=True, encoding="utf-8")
    text = (r.stdout or "") + (r.stderr or "")
    if "not signed at all" in text:
        return "unsigned"
    if "Signature=adhoc" in text:
        return "adhoc"
    for line in text.splitlines():
        if line.startswith("Authority="):
            return line.split("=", 1)[1]
    return "signed"
