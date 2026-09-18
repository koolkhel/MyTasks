## Context

See proposal.md for why. What shapes the approach:

- macOS attributes a privacy request to the *responsible process*, which for
  anything started in a terminal is the terminal emulator's application. The
  board asks through EventKit; the answer it gets is the terminal's.
- An application whose Info.plist declares neither `NSCalendarsUsageDescription`
  nor `NSCalendarsFullAccessUsageDescription` is refused before the system
  records anything. Observed: cool-retro-term declares neither and is
  unsigned; kitty declares the older key only and is granted in full. So one
  key suffices, and "declares neither" is the silent case.
- Nothing grants a privacy permission from the command line. `tccutil` only
  resets. The only way in is to make the application one the system is willing
  to ask about, then let it ask.
- `ical.py` already holds the request, the status and the message table
  (`_ACCESS_TROUBLE`); status 0 has no entry and falls through to the message
  that names nothing.
- `run.sh` already does environment work before the board starts (the venv,
  the requirements, the token) and refuses to start only for the token.

## Goals / Non-Goals

**Goals:**

- One answer to "which application is asking", shared by the helper and the
  board.
- The board names the remedy in the fourth case, wherever it was started.
- The launcher says it earlier and in full, and never blocks.
- Every decision the helper makes is checkable without `/Applications`, a real
  `codesign`, or a real grant.

**Non-Goals:**

- Granting anything. The prompt is the system's.
- Editing a developer-signed terminal.
- Remembering that the check passed. The launcher reads no state back.

## Decisions

### A shared module, `terminal.py`

`host_app()` (walk the parent processes to the first executable inside an
`.app` bundle that is not inside a `.framework` -- a framework Python is a
bundle too), `declares_calendar_reason(app)` (either usage key present) and
`signature(app)` (`unsigned`, `adhoc`, or the signing authority) live in one
module. `calendar_access.py` imports it for the diagnosis and the fix; `ical.py`
imports it for the message. The alternative -- each keeping its own copy -- is
two answers to who is asking, which will drift the first time one is edited.

Every function takes the process it needs as an argument with a default
(`run=subprocess.run`, `ppid=os.getppid()`), so a suite hands in a fake and
none of it reaches the machine.

### The board's message reaches for the module only on the failure path

`ical._store()` consults `terminal` only when the status is still 0 after the
request returned. Reading the day costs nothing new; the two `ps` calls happen
once, when there is already something to explain.

### The launcher advises, then starts

```
run.sh
  venv, requirements, token        (as today)
  if CALENDAR_WORK or CALENDAR_PERSONAL is set, and not --cli:
      "$PYTHON" calendar_access.py --quiet || true
  exec main.py
```

`--quiet` prints only when there is something to say -- declares none, denied,
write-only -- and its exit code is ignored on purpose. The check is skipped
when no account is configured because the board would not read the calendar
anyway, and printing about a calendar nobody asked for would be noise on
every start.

Every start, not once: a marker would be the launcher's first read-back
state, the check is ~0.3 s and only runs when a calendar is configured, and
the state it checks can change underneath any marker (the terminal is
updated, the grant is revoked).

### The fix, and what it refuses

The keys are added with `plistlib`, with a copy kept beside the original.
Re-signing is `codesign --force --deep --sign -`; it is done only when the
application was unsigned or ad-hoc, because those have no signature worth
keeping. A developer signature is refused outright -- an ad-hoc re-sign of a
signed application also makes Gatekeeper treat it as new, which is worse than
the calendar. The remembered answer is cleared with `tccutil reset Calendar
<bundle-id>` so a prior silent refusal does not stand in the way of the prompt.

### Testing against a fake application

A stub suite builds `Something.app/Contents/Info.plist` in a temporary
directory with and without the keys, hands `terminal.signature` a `run` that
answers what `codesign` would, hands `host_app` a `ps` that answers a
synthetic parent chain (shell -> login -> the fake app, and the framework
Python case), and drives `calendar_access.fix` with `run` and `input` stubbed
so nothing is signed, reset or asked for real. The `run.sh` pre-flight is
checked as source -- the way `t_title` checks the entry point -- and by hand.

## Risks / Trade-offs

- **Re-signing an application under `/Applications`.** → Only unsigned or
  ad-hoc ones; a copy of the plist is kept; the person is asked first; the
  step list is printed before anything happens.
- **A future macOS may need a third key or refuse ad-hoc apps outright.** →
  The keys are one table in `terminal.py`; the helper reports the system's
  answer in the system's own terms, so a new refusal reads as what it is.
- **The pre-flight adds ~0.3 s to every start with a calendar configured.** →
  Measured on this machine; skipped entirely without a calendar.
- **`ps` output format.** → Only `ppid` and `comm` are read, both stable; a
  parse failure means "no host found" and the generic message, never a crash
  on the failure path.
