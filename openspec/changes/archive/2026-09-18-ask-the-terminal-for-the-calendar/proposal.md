## Why

The board in cool-retro-term shows no calendar and never asks for one. macOS
grants calendar access to the application that owns the process -- the
terminal emulator -- and refuses, without a prompt, any application whose
Info.plist declares no reason to want it. cool-retro-term declares none. The
board's request is turned away before the system records anything, so the
status stays "not determined", and the board falls through to the one message
in its table that names no remedy: "the calendar could not be read".

The spec already requires the board to name what would put it right. In this
case it names nothing, and the remedy is the least obvious of the four:
nothing in Privacy & Security can help, because the terminal never appears
there.

## What Changes

- A helper, `calendar_access.py`, says which application owns the terminal,
  whether it declares a reason to want the calendar, how it is signed, and
  what the system currently answers -- and, only when asked with `--fix`, adds
  the two usage keys to an unsigned or ad-hoc-signed terminal, re-signs it ad
  hoc, and clears any denial the system remembered. A developer-signed
  terminal is refused: replacing a real signature would be worse than the
  problem. An already-allowed one is left alone.
- The board's own message for a calendar it cannot read gains the fourth
  case: where the request could not even be made, it names the terminal and
  the helper.
- `run.sh` checks before starting the board, whenever a calendar account is
  configured, and prints the diagnosis and the fix when there is something to
  say. It never refuses to start: the board is required to work without the
  calendar, and a launcher that would not start over one would break that
  from the other side.
- What the helper and the board share -- which application owns this process,
  and what its Info.plist declares -- moves into one small module both import,
  so there is one answer to "who is asking".

Recorded assumptions:

- The pre-flight runs on every start where a calendar is configured, at a
  cost of one short Python process. A marker file to run it once would be the
  first state the launcher reads back, and the board keeps none.
- Either usage key suffices for the system to ask -- kitty declares only the
  older one and is granted -- so what is refused silently is declaring
  neither. Both are added because Sonoma and later read the newer name.
- This is about making the terminal one the system will ask about. It does
  not, and cannot, grant anything: no command grants a privacy permission,
  only the prompt does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: "The board works when the calendar cannot be read" gains the
  case where the request cannot be made; two requirements are added, one for
  the launcher's check and one for the helper.

## Impact

- `calendar_access.py` (new, currently untracked), `terminal.py` (new, the
  shared module), `ical.py` (the fourth message), `run.sh` (the pre-flight).
- A new stub suite exercising the helper's decisions against a fake `.app`
  bundle in a temporary directory, with `codesign`, `tccutil` and `ps`
  answered by stubs -- nothing under `/Applications` is read or written by a
  test, and no real grant is requested.
- `README.md`: a line under configuration about the calendar and the
  terminal.
