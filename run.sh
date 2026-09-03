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

exec "${PYTHON}" main.py "$@"
