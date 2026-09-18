#!/usr/bin/env bash
#
# Start the task board, setting the virtualenv up first if it isn't there.
#
#   ./run.sh                 today
#   ./run.sh 2026-09-05      a specific day
#   ./run.sh --cli           print today's tasks and exit, no TUI
#   ./run.sh --cli --open    same, hiding finished tasks
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

VENV=".venv"
PYTHON="$VENV/bin/python"
STAMP="$VENV/.requirements-stamp"

# Build the venv on first run.
if [[ ! -x "${PYTHON}" ]]; then
    echo "Creating ${VENV}..." >&2
    python3 -m venv "${VENV}"
    "${PYTHON}" -m pip install --quiet --upgrade pip
fi

# Reinstall whenever requirements.txt changes (the stamp is touched after a
# successful install, so a failed install is retried next time).
if [[ ! -f "${STAMP}" || requirements.txt -nt "${STAMP}" ]]; then
    echo "Installing dependencies..." >&2
    "${PYTHON}" -m pip install --quiet -r requirements.txt
    touch "${STAMP}"
fi

if [[ ! -f .env ]] && [[ -z "${SINGULARITY_TOKEN:-}" ]]; then
    echo "run.sh: no .env and no SINGULARITY_TOKEN in the environment." >&2
    echo "        Put 'SINGULARITY_TOKEN=<your token>' in .env first." >&2
    exit 1
fi

if [[ "${1:-}" == "--cli" ]]; then
    shift
    exec "${PYTHON}" singularity.py "$@"
fi

# The calendar is granted to the terminal, not to the board, and a terminal
# that declares no reason to want it is refused without a prompt.  Say so
# before the board starts -- only where a calendar is configured, only when
# something stands in the way, and never refusing to start: the board works
# without the calendar, and a launcher that would not start over it would
# break that from the other side.
calendar_configured() {
    [[ -n "${CALENDAR_WORK:-}${CALENDAR_PERSONAL:-}" ]] && return 0
    [[ -f .env ]] && grep -qE '^(CALENDAR_WORK|CALENDAR_PERSONAL)=.+' .env
}
if calendar_configured; then
    "${PYTHON}" calendar_access.py --quiet || true
fi

exec "${PYTHON}" main.py "$@"
